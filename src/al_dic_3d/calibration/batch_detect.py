"""Board detection over image files, several at a time (Qt-free).

The GUI calibration worker and ``al-dic-3d calibrate`` both read every board
image and detect the board in it. One image's decode and detection do not
depend on another's, and OpenCV and NumPy release the GIL for the heavy parts,
so a thread pool runs them side by side. Results and callbacks keep the input
order, and each image is decoded once: its size comes back with its detection,
so callers need not read the first image again for the calibration's image
size.

Both callers then run the same checks before solving: each camera's images
share one size (:func:`stereo_image_sizes`), and enough pairs show the board,
else :func:`detection_shortfall` says what to check first.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from al_dic_3d.calibration.boards import BoardSpec, board_count_hint
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


class MixedImageSizeError(ValueError):
    """One camera's board images are not all the same size.

    ``camera`` is ``"left"`` or ``"right"``; ``path`` / ``size`` name the first
    image whose size differs from the camera's first image
    (``first_path`` / ``first_size``). Sizes are ``(width, height)``.
    """

    def __init__(
        self,
        camera: str,
        path: str,
        size: tuple[int, int],
        first_path: str,
        first_size: tuple[int, int],
    ) -> None:
        super().__init__(
            f"the {camera} board images are not all the same size: {Path(path).name} is "
            f"{size[0]}x{size[1]}, {Path(first_path).name} is {first_size[0]}x{first_size[1]}; "
            "calibrate each camera with images of one size"
        )
        self.camera = camera
        self.path = path
        self.size = size
        self.first_path = first_path
        self.first_size = first_size


@dataclass(frozen=True)
class FileDetections:
    """Per-file detections and image sizes, in input order."""

    detections: tuple[BoardDetection, ...]
    sizes: tuple[tuple[int, int], ...]  # (width, height) of each image


def _camera_size(camera: str, paths: Sequence[str], sizes: Sequence[tuple[int, int]]):
    first = (int(sizes[0][0]), int(sizes[0][1]))
    for path, size in zip(paths, sizes, strict=True):
        size = (int(size[0]), int(size[1]))
        if size != first:
            raise MixedImageSizeError(camera, str(path), size, str(paths[0]), first)
    return first


def stereo_image_sizes(
    paths: Sequence[str | Path], sizes: Sequence[tuple[int, int]], n_left: int
) -> tuple[tuple[int, int], tuple[int, int]]:
    """``(left size, right size)`` of a calibration set, each ``(width, height)``.

    ``paths`` / ``sizes`` list every left image, then every right one (as
    :func:`detect_files` takes and returns them); the first ``n_left`` are the
    left camera's. Each camera's images must share one size: a cropped or
    binned image would otherwise be solved with another image's size. The two
    cameras may differ (each keeps its own size in the calibration). Raises
    :class:`MixedImageSizeError` naming the first image that differs.
    """
    names = [str(p) for p in paths]
    if len(names) != len(sizes) or not 0 < n_left < len(names):
        raise ValueError(
            f"need left and right images with one size each, got {len(names)} paths, "
            f"{len(sizes)} sizes, {n_left} left"
        )
    return (
        _camera_size("left", names[:n_left], sizes[:n_left]),
        _camera_size("right", names[n_left:], sizes[n_left:]),
    )


@dataclass(frozen=True)
class DetectionCount:
    """How many calibration images and pairs show the board."""

    images: int  # images of either camera with the board found
    pairs: int  # pairs with the board found in both images
    total_pairs: int


def count_detections(
    left: Sequence[BoardDetection], right: Sequence[BoardDetection]
) -> DetectionCount:
    """Count the found boards of an index-paired left/right detection list."""
    found_l = [bool(d is not None and d.ok) for d in left]
    found_r = [bool(d is not None and d.ok) for d in right]
    pairs = sum(1 for a, b in zip(found_l, found_r, strict=False) if a and b)
    return DetectionCount(sum(found_l) + sum(found_r), pairs, min(len(left), len(right)))


def detection_shortfall(
    left: Sequence[BoardDetection],
    right: Sequence[BoardDetection],
    spec: BoardSpec,
    min_pairs: int,
) -> str | None:
    """Why the board detections cannot be calibrated, with what to check (English).

    ``None`` when at least ``min_pairs`` pairs show the board in both images,
    or when fewer pairs were given at all (the solver's own message says
    so). Otherwise the board size is the first thing to check, before the
    solver fails with a count of usable views that says nothing about why.
    """
    count = count_detections(left, right)
    if count.pairs >= min_pairs or count.total_pairs < min_pairs:
        return None
    if count.images == 0:
        lead = "the board was not found in any image"
    else:
        lead = (
            f"the board was found in both images of only {count.pairs} of "
            f"{count.total_pairs} pairs (the solve needs {min_pairs})"
        )
    return f"{lead}. {board_count_hint(spec)}"


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
