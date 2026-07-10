"""Background frame-decode prefetcher (P2.2) — kills the scrub freeze.

Scrubbing used to re-decode every frame synchronously on the GUI thread
(imread + float64 normalize + pixmap: 100–300 ms per 2448x2048 frame). This
prefetcher keeps a small LRU of READY grayscale ``QPixmap``s keyed by file
path and decodes ahead on a single-thread ``QThreadPool``:

* the worker decodes to ``QImage`` (``QPixmap`` must only be created on the
  GUI thread) via :func:`al_dic_3d.gui.widgets.image_view.gray_to_qimage`;
* delivery is a queued signal back to the GUI thread, where the cheap
  ``QPixmap.fromImage`` conversion happens;
* ``CanvasArea3D.render()`` blits the cached pixmap when hot and falls back
  to the synchronous ``set_image_file`` when cold (correctness first) while
  the worker warms current/next/prev;
* ``invalidate()`` (images changed) bumps a generation counter so in-flight
  decodes of stale paths are dropped on arrival.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QThreadPool
from PySide6.QtGui import QImage, QPixmap

from al_dic_3d.gui.widgets.image_view import gray_to_qimage, load_gray_image
from al_dic_3d.gui.workers import PoolTask
from al_dic_3d.viz3d.lru import LRUCache

PREFETCH_CACHE_SIZE = 8  # ready full-resolution frames (~5 MB each at 2448x2048)


def _decode(path: str) -> QImage:
    """Worker-side decode: file -> normalized 8-bit grayscale QImage."""
    return gray_to_qimage(load_gray_image(path))


class FramePrefetcher(QObject):
    """LRU of ready grayscale ``QPixmap``s keyed by image-file path."""

    def __init__(self, parent: QObject | None = None, capacity: int = PREFETCH_CACHE_SIZE) -> None:
        super().__init__(parent)
        self._cache: LRUCache[str, QPixmap] = LRUCache(capacity)
        self._pending: set[str] = set()
        self._generation = 0
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(1)  # decodes are big; keep them ordered

    # -- GUI-thread API ------------------------------------------------------

    def get(self, path) -> QPixmap | None:
        """The ready pixmap for *path*, or None (miss -> caller decodes sync)."""
        return self._cache.get(str(path))

    def store(self, path, pixmap: QPixmap) -> None:
        """Adopt a pixmap decoded elsewhere (the sync fallback) into the cache."""
        key = str(path)
        self._cache[key] = pixmap
        self._pending.discard(key)

    def request(self, paths) -> None:
        """Queue background decodes for paths not already cached or pending."""
        for path in paths:
            if path is None:
                continue
            key = str(path)
            if key in self._cache or key in self._pending:
                continue
            self._pending.add(key)
            task = PoolTask(_decode, key, tag=(key, self._generation))
            task.signals.done.connect(self._on_decoded)
            task.signals.failed.connect(self._on_decode_failed)
            self._pool.start(task)

    def invalidate(self) -> None:
        """Images changed: every cached/pending frame is stale by definition."""
        self._generation += 1
        self._cache.clear()
        self._pending.clear()

    def wait_idle(self, timeout_ms: int = 10_000) -> bool:
        """Join outstanding decode jobs (tests / teardown)."""
        return self._pool.waitForDone(timeout_ms)

    def __len__(self) -> int:
        return len(self._cache)

    # -- queued deliveries (GUI thread) ---------------------------------------

    def _on_decoded(self, tag: tuple[str, int], image: QImage) -> None:
        path, generation = tag
        self._pending.discard(path)
        if generation != self._generation or image.isNull():
            return  # stale (images changed mid-decode) or unreadable frame
        self._cache[path] = QPixmap.fromImage(image)  # GUI thread only

    def _on_decode_failed(self, tag: tuple[str, int], _message: str) -> None:
        # Unreadable frames simply stay cold; render() keeps its sync fallback
        # (which surfaces the failure through the existing canvas-clear path).
        self._pending.discard(tag[0])
