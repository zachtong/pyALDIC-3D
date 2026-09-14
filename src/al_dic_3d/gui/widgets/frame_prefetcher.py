"""Background frame-decode prefetcher (P2.2, V-view) — kills the scrub freeze.

Scrubbing used to re-decode every frame synchronously on the GUI thread
(imread + float64 normalize + pixmap: 200–300 ms per 12 Mpx frame). This
prefetcher keeps a small LRU of READY 8-bit grayscale frames keyed by file path
and decodes on a private ``QThreadPool``:

* workers decode to ``QImage`` via
  :func:`al_dic_3d.gui.widgets.image_view.decode_gray_qimage` (``QPixmap`` must
  only be created on the GUI thread); :meth:`get` wraps a cached frame as a
  ``QPixmap`` on demand (~7 ms at 12 Mpx), so the cache holds 1 byte/pixel
  instead of a 4 byte/pixel pixmap, and is bounded by entries AND bytes;
* deliveries are queued signals back to the GUI thread; :attr:`frame_ready`
  announces each landed frame so a view waiting for it can show it;
* :meth:`request` is a NAVIGATION request: it replaces the wanted set, and a
  queued decode whose path is no longer wanted is skipped when it reaches a
  worker (fast scrubbing no longer leaves a backlog of stale decodes);
  :meth:`request_now` queues the frame the user is looking at ahead of warming;
* :meth:`invalidate` (images changed) bumps a generation counter so in-flight
  decodes of stale paths are dropped on arrival.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QThreadPool, Signal
from PySide6.QtGui import QImage, QPixmap

from al_dic_3d.gui.widgets.image_view import decode_gray_qimage
from al_dic_3d.gui.workers import PoolTask
from al_dic_3d.viz3d.sized_cache import SizedLRUCache

PREFETCH_CACHE_SIZE = 8  # ready frames kept (entry cap)
PREFETCH_CACHE_BYTES = 192 * 1024 * 1024  # 16 frames of 12 Mpx at 1 byte/pixel
PREFETCH_THREADS = 2  # the frame on screen is never stuck behind a warming decode
_PRIORITY_NOW = 10  # the frame the user is waiting for
_PRIORITY_WARM = 0


def _image_bytes(image: QImage) -> int:
    return int(image.sizeInBytes())


class FramePrefetcher(QObject):
    """LRU of ready grayscale frames keyed by image-file path."""

    frame_ready = Signal(str)  # a decoded frame landed in the cache (GUI thread)
    frame_failed = Signal(str, str)  # (path, "ErrorType: message")

    def __init__(
        self,
        parent: QObject | None = None,
        capacity: int = PREFETCH_CACHE_SIZE,
        max_bytes: int = PREFETCH_CACHE_BYTES,
    ) -> None:
        super().__init__(parent)
        self._cache: SizedLRUCache[str, QImage] = SizedLRUCache(
            capacity, max_bytes, sizer=_image_bytes
        )
        # path -> (priority, token) of its NEWEST queued decode; only that
        # task's delivery clears (or re-queues) the entry.
        self._pending: dict[str, tuple[int, int]] = {}
        self._wanted: frozenset[str] = frozenset()  # read by workers (atomic swap)
        self._generation = 0
        # In-flight tasks, held until their delivery lands, so each task's
        # signal emitter is released on the GUI thread (never by the pool's
        # worker thread that deletes the finished runnable).
        self._tasks: dict[int, PoolTask] = {}
        self._next_token = 0
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(PREFETCH_THREADS)

    # -- GUI-thread API ------------------------------------------------------

    def get(self, path) -> QPixmap | None:
        """The ready frame for *path* as a ``QPixmap``, or None (miss)."""
        image = self._cache.get(str(path))
        return None if image is None else QPixmap.fromImage(image)

    def has(self, path) -> bool:
        """True when *path* is decoded and cached (no recency refresh)."""
        return str(path) in self._cache

    def store(self, path, pixmap: QPixmap) -> None:
        """Adopt a pixmap decoded elsewhere into the cache (compact copy)."""
        self.store_image(path, pixmap.toImage().convertToFormat(QImage.Format.Format_Grayscale8))

    def store_image(self, path, image: QImage) -> None:
        """Adopt a grayscale ``QImage`` decoded elsewhere (the sync fallback)."""
        key = str(path)
        if image is None or image.isNull():
            return
        self._cache[key] = image
        self._pending.pop(key, None)  # an in-flight decode of it is moot now

    def request(self, paths) -> None:
        """Navigation request: warm *paths*; queued decodes of others are dropped."""
        keys = [str(p) for p in paths if p is not None]
        self._wanted = frozenset(keys)
        for key in keys:
            self._submit(key, _PRIORITY_WARM)

    def request_now(self, path) -> None:
        """Queue *path* ahead of warming decodes (the frame on screen next)."""
        key = str(path)
        self._wanted = self._wanted | {key}
        self._submit(key, _PRIORITY_NOW)

    def invalidate(self) -> None:
        """Images changed: every cached/pending frame is stale by definition."""
        self._generation += 1
        self._cache.clear()
        self._pending.clear()
        self._wanted = frozenset()

    def wait_idle(self, timeout_ms: int = 10_000) -> bool:
        """Join outstanding decode jobs (tests / teardown)."""
        return self._pool.waitForDone(timeout_ms)

    def __len__(self) -> int:
        return len(self._cache)

    # -- internals -------------------------------------------------------------

    def _submit(self, key: str, priority: int) -> None:
        if key in self._cache:
            return
        queued = self._pending.get(key)
        if queued is not None and queued[0] >= priority:
            return  # already queued at least this urgently
        self._next_token += 1
        token = self._next_token
        self._pending[key] = (priority, token)
        task = PoolTask(self._decode_if_wanted, key, tag=(key, self._generation, token))
        task.signals.done.connect(self._on_decoded)
        task.signals.failed.connect(self._on_decode_failed)
        self._tasks[token] = task
        self._pool.start(task, priority)

    def _decode_if_wanted(self, key: str) -> QImage | None:
        """Worker thread: skip paths navigation moved away from, else decode."""
        if key not in self._wanted:
            return None
        return decode_gray_qimage(key)

    # -- queued deliveries (GUI thread) ---------------------------------------

    def _release(self, path: str, token: int) -> bool:
        """Drop *path*'s pending entry if *token* owns it; True when it did."""
        entry = self._pending.get(path)
        if entry is None or entry[1] != token:
            return False  # a newer decode owns the entry, or it was cleared
        del self._pending[path]
        return True

    def _on_decoded(self, tag: tuple[str, int, int], image: QImage | None) -> None:
        path, generation, token = tag
        self._tasks.pop(token, None)
        if generation != self._generation:
            return  # stale (images changed mid-decode)
        owner = self._release(path, token)
        if image is None:  # skipped as unwanted when it reached a worker
            if owner and path in self._wanted and path not in self._cache:
                self._submit(path, _PRIORITY_WARM)  # wanted again meanwhile
            return
        if image.isNull() or path in self._cache:
            return  # unreadable frame, or a duplicate (priority re-queue)
        self._cache[path] = image
        self.frame_ready.emit(path)

    def _on_decode_failed(self, tag: tuple[str, int, int], message: str) -> None:
        path, generation, token = tag
        self._tasks.pop(token, None)
        if generation == self._generation:
            self._release(path, token)
            self.frame_failed.emit(path, message)
