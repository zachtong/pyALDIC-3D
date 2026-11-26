"""Board detection over image files, several at a time (Qt-free).

The GUI calibration worker and ``al-dic-3d calibrate`` both read every board
image and detect the board in it. One image's decode and detection do not
depend on another's, and OpenCV and NumPy release the GIL for the heavy parts,
so a thread pool runs them side by side. Results and callbacks keep the input
order, and each image is decoded once: its size comes back with its detection,
so callers need not read the first image again for the calibration's image
size.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from al_dic_3d.calibration.boards import BoardSpec
from al_dic_3d.calibration.detect import BoardDetection, detect_board

# Each worker holds one decoded frame and the coarse search's buffers (about
# 0.3 GB for a 20 MP frame); the memory-hungry full-resolution fallback is
# rationed separately (detect._FULL_SB_MEMORY). The pool stays small even on
# many-core machines.
MAX_WORKERS = 8


class UnreadableImageError(ValueError):
    """A board image could not be read or decoded."""

    def __init__(self, path: str) -> None:
        super().__init__(f"cannot read image: {path}")
        self.path = path


@dataclass(frozen=True)
class FileDetections:
    """Per-file detections and image sizes, in input order."""

    detections: tuple[BoardDetection, ...]
    sizes: tuple[tuple[int, int], ...]  # (width, height) of each image


def default_workers(n_files: int) -> int:
    """Threads for ``n_files`` images: one per core, at most :data:`MAX_WORKERS`."""
    return max(1, min(MAX_WORKERS, os.cpu_count() or 1, n_files))


def _read_and_detect(path: str, spec: BoardSpec) -> tuple[BoardDetection, tuple[int, int]]:
    from al_dic_3d.pathsafe import imread_unicode

    image = imread_unicode(path)
    if image is None:
        raise UnreadableImageError(path)
    return detect_board(image, spec), (int(image.shape[1]), int(image.shape[0]))


def detect_files(
    paths: Sequence[str | Path],
    spec: BoardSpec,
    *,
    workers: int | None = None,
    on_result: Callable[[int, BoardDetection], None] | None = None,
) -> FileDetections:
    """Read each file and detect the board in it; results in input order.

    ``on_result(index, detection)`` runs on the calling thread, in input order,
    once that file and every earlier one are done, so progress output reads like
    the sequential loop's. ``workers`` defaults to :func:`default_workers`; 1
    runs everything on the calling thread. A file that cannot be read raises
    :class:`UnreadableImageError` (a ``ValueError``) after the files before it
    are reported, as the sequential loop did; files not yet started are
    cancelled. A board that is not found is not an error: its detection has
    ``ok=False`` and a ``reason``.
    """
    names = [str(p) for p in paths]
    n_workers = default_workers(len(names)) if workers is None else max(1, int(workers))
    detections: list[BoardDetection] = []
    sizes: list[tuple[int, int]] = []

    def accept(index: int, done: tuple[BoardDetection, tuple[int, int]]) -> None:
        detections.append(done[0])
        sizes.append(done[1])
        if on_result is not None:
            on_result(index, done[0])

    if n_workers == 1 or len(names) <= 1:
        for k, name in enumerate(names):
            accept(k, _read_and_detect(name, spec))
    else:
        with ThreadPoolExecutor(n_workers, thread_name_prefix="board-detect") as pool:
            futures = [pool.submit(_read_and_detect, name, spec) for name in names]
            try:
                for k, future in enumerate(futures):
                    accept(k, future.result())
            except BaseException:
                for future in futures:
                    future.cancel()
                raise
    return FileDetections(tuple(detections), tuple(sizes))
