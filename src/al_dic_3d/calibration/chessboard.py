"""Chessboard corners: coarse-to-fine search, full-resolution refinement (Qt-free).

:func:`find_chessboard` is the chessboard path of
:func:`~al_dic_3d.calibration.detect.detect_board`:

1. ``findChessboardCornersSB`` (NORMALIZE|EXHAUSTIVE) on copies downscaled to
   a longer side of 1024, then 2048 px (large frames only), the corners
   confirmed and refined at full resolution;
2. otherwise ``findChessboardCornersSB`` at full resolution
   (NORMALIZE|EXHAUSTIVE|ACCURACY — sub-pixel accurate, Duda&Frese 2018);
3. otherwise the classic ``findChessboardCorners`` + ``cornerSubPix``.

Every start ends in the same full-resolution ``cornerSubPix``, so the corners
do not depend on which search found the board; ``method`` records the
detector ("sb" or "classic") and the solver reports mixes. Orientation is
canonicalized so the 180-degree ambiguity cannot desync the L/R corner
indexing. cv2 imported lazily.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.calibration.boards import ChessboardSpec

_NOT_FOUND = "chessboard not found (SB and classic detectors)"

# Coarse-to-fine search. findChessboardCornersSB's cost grows with the pixel
# count, three-fold again with CALIB_CB_ACCURACY's internal upsampling: about
# 1 s for a 5 MP and 3 s for a 20 MP frame, i.e. minutes for a 25-pair set. SB
# finds a board down to ~6 px squares, and the full-resolution cornerSubPix
# lands on the same corner from any start inside its window (measured on
# rendered 5-20 MP sets: corners within 5e-4 px of the full-resolution SB
# start, from 2-12x downscaled starts). So the board is first searched on
# downscaled copies whose longer side is one of these, smallest first, and
# refined at full resolution. A level less than _COARSE_MIN_FACTOR smaller than
# the image is skipped; a view no level finds falls through to full-resolution
# SB, then the classic detector.
_COARSE_SIDES = (1024, 2048)
_COARSE_MIN_FACTOR = 1.5
# Largest move the full-resolution refinement may make from an up-scaled
# corner: this fraction of the corner spacing (further: it slid towards another
# corner) and this many downscale factors + 2 px (the coarse search's own error
# stays within ~1.1x the factor). Beyond either the downscaled result is not used.
_COARSE_MAX_MOVE = 0.25
_COARSE_MOVE_PER_SCALE = 3.0

# Full-resolution SB with CALIB_CB_ACCURACY peaks at ~330 bytes per pixel of
# process memory (measured: 6.2 GB for a 20 MP frame, 3.1 GB for 10 MP; the
# coarse searches stay under 0.25 GB). Detection runs several images at a time
# (batch_detect), so these searches share a budget: they run side by side while
# their estimates fit, and a frame whose estimate exceeds it runs alone.
_FULL_SB_BYTES_PER_PX = 340
_FULL_SB_BUDGET_BYTES = 4 << 30


@dataclass(frozen=True)
class ChessboardCorners:
    """Refined corners of one view, or why there are none."""

    points: NDArray[np.float64] | None  # (cols*rows, 2) px, canonical order; None if not found
    method: str  # "sb" | "classic": the detector that found (or last searched for) the board
    reason: str = ""  # failure reason when ``points`` is None


class _MemoryBudget:
    """Admits jobs while their estimated peak memory fits a shared budget."""

    def __init__(self, budget: int) -> None:
        self._budget = budget
        self._used = 0
        self._cond = threading.Condition()

    @contextmanager
    def reserve(self, nbytes: int) -> Iterator[None]:
        with self._cond:  # an oversized job waits until it can run alone
            self._cond.wait_for(lambda: self._used == 0 or self._used + nbytes <= self._budget)
            self._used += nbytes
        try:
            yield
        finally:
            with self._cond:
                self._used -= nbytes
                self._cond.notify_all()


_FULL_SB_MEMORY = _MemoryBudget(_FULL_SB_BUDGET_BYTES)


def _canonicalize(corners: NDArray[np.float64]) -> NDArray[np.float64]:
    """Resolve the 180-degree ordering ambiguity of a plain checkerboard.

    OpenCV may return the corner sequence starting from either end depending on
    board pose. Enforce: the first corner is the one closer to the image
    top-left (by x+y sum), so both cameras of a pair index the same physical
    corner as long as neither camera is rotated ~90+ degrees w.r.t. the other.
    """
    if corners[0].sum() > corners[-1].sum():
        return corners[::-1].copy()
    return corners


def _downscaled(
    gray: NDArray[np.uint8], side: int
) -> tuple[NDArray[np.uint8], NDArray[np.float64]]:
    """``gray`` resized to longer side ``side`` (area average) and its (x, y) scale to full size."""
    import cv2

    h, w = gray.shape
    scale = max(h, w) / side
    ws, hs = max(1, round(w / scale)), max(1, round(h / scale))
    small = cv2.resize(gray, (ws, hs), interpolation=cv2.INTER_AREA)
    return small, np.array([w / ws, h / hs])


def _to_full(pts: NDArray, scale: NDArray[np.float64]) -> NDArray[np.float64]:
    """Corner positions on a downscaled copy -> full-resolution pixels (pixel centres)."""
    return (np.asarray(pts, dtype=np.float64).reshape(-1, 2) + 0.5) * scale - 0.5


def _corner_spacing(pts: NDArray[np.float64], spec: ChessboardSpec) -> float:
    """Median distance between neighbouring corners along the rows (px)."""
    grid = pts.reshape(spec.rows, spec.cols, 2)
    return float(np.median(np.linalg.norm(np.diff(grid, axis=1), axis=2)))


def _refine_window(spacing: float) -> int:
    """Half-size of the ``cornerSubPix`` window for a corner spacing (px)."""
    return int(np.clip(spacing * 0.4, 4, 15))


def _refine_corners(
    gray: NDArray[np.uint8], pts: NDArray[np.float64], spec: ChessboardSpec
) -> tuple[NDArray[np.float64], float]:
    """Full-resolution ``cornerSubPix`` of ordered corners -> (refined, corner spacing px).

    Gradient-based sub-pixel refinement on top of either detector. SB's Radon
    localization is tuned for sharp real images and leaves ~0.1-0.3 px of error
    on band-limited/blurred edges, where cornerSubPix converges to ~0.01 px
    (measured on the synthetic gate); on sharp images the refinement moves
    corners negligibly. Window adapts to the projected square size.
    """
    import cv2

    spacing = _corner_spacing(pts, spec)
    win = _refine_window(spacing)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 1e-4)
    refined = np.asarray(
        cv2.cornerSubPix(gray, np.float32(pts).reshape(-1, 1, 2), (win, win), (-1, -1), criteria),
        dtype=np.float64,
    ).reshape(-1, 2)
    return refined, spacing


def _refine_upscaled(
    gray: NDArray[np.uint8],
    pts: NDArray[np.float64],
    spec: ChessboardSpec,
    scale: NDArray[np.float64],
) -> NDArray[np.float64] | None:
    """Refine corners found on a copy downscaled by ``scale``; None when not trustworthy.

    Distrusted, so the caller falls back to a finer search: a corner whose
    refinement window plus the coarse localisation error (2 x scale) does not
    fit inside the image, since a downscaled search cannot localise corners at
    the frame edge (one sat 59 px off at 6 px from the edge on a rendered
    4096x2448 view, where full-resolution SB was right), and a refinement that
    moves a corner further than the coarse search can be wrong (about 1x
    scale, measured at 3-12x) or towards another corner.
    """
    h, w = gray.shape
    s = float(np.max(scale))
    margin = _refine_window(_corner_spacing(pts, spec)) + 2.0 * s
    x, y = pts[:, 0], pts[:, 1]
    if x.min() < margin or y.min() < margin or x.max() > w - 1 - margin or y.max() > h - 1 - margin:
        return None
    refined, spacing = _refine_corners(gray, pts, spec)
    limit = min(_COARSE_MAX_MOVE * spacing, _COARSE_MOVE_PER_SCALE * s + 2.0)
    if np.linalg.norm(refined - pts, axis=1).max() > limit:
        return None
    return refined


def _coarse_sb(
    gray: NDArray[np.uint8], spec: ChessboardSpec, side: int
) -> NDArray[np.float64] | None:
    """SB corners found on a copy downscaled to longer side ``side``, refined at full size.

    None when the coarse search fails or the refinement does not confirm it.
    """
    import cv2

    small, scale = _downscaled(gray, side)
    # No CALIB_CB_ACCURACY: its upsampling only sharpens SB's own sub-pixel
    # estimate, which the full-resolution refinement replaces.
    flags = cv2.CALIB_CB_NORMALIZE_IMAGE | cv2.CALIB_CB_EXHAUSTIVE
    found, corners = cv2.findChessboardCornersSB(small, spec.pattern_size, flags=flags)
    if not found:
        return None
    pts = _canonicalize(_to_full(corners, scale))
    if pts.shape[0] != spec.cols * spec.rows:
        return None
    return _refine_upscaled(gray, pts, spec, scale)


def find_chessboard(gray: NDArray[np.uint8], spec: ChessboardSpec) -> ChessboardCorners:
    """Refined corners of ``spec``'s board in an 8-bit grayscale view (see the module notes)."""
    for side in _COARSE_SIDES:
        if max(gray.shape) < _COARSE_MIN_FACTOR * side:
            break
        pts = _coarse_sb(gray, spec, side)
        if pts is not None:
            return ChessboardCorners(pts, "sb")
    return _find_full(gray, spec)


def _find_full(gray: NDArray[np.uint8], spec: ChessboardSpec) -> ChessboardCorners:
    """SB at full resolution, then the classic detector as fallback."""
    import cv2

    flags = cv2.CALIB_CB_NORMALIZE_IMAGE | cv2.CALIB_CB_EXHAUSTIVE | cv2.CALIB_CB_ACCURACY
    with _FULL_SB_MEMORY.reserve(_FULL_SB_BYTES_PER_PX * gray.size):
        found, corners = cv2.findChessboardCornersSB(gray, spec.pattern_size, flags=flags)
    if not found:
        return _find_classic(gray, spec)
    pts = _canonicalize(np.asarray(corners, dtype=np.float64).reshape(-1, 2))
    n = spec.cols * spec.rows
    if pts.shape[0] != n:
        return ChessboardCorners(None, "sb", f"expected {n} corners, got {pts.shape[0]}")
    return ChessboardCorners(_refine_corners(gray, pts, spec)[0], "sb")


def _find_classic(gray: NDArray[np.uint8], spec: ChessboardSpec) -> ChessboardCorners:
    """The classic detector, refined at full resolution.

    On a frame holding no complete board (partly out of view, the commonest
    failure) its search took 7-51 s per 10 MP view, against 0.1-1 s on a copy
    of longer side 2048 (measured on a rendered 4096x2448 set; the copy also
    found 39 of 44 visible boards against 38 at full size). Frames the largest
    coarse level applies to are therefore searched at that size first; the
    full-size search runs only when that copy shows a board whose corners it
    cannot confirm, and on smaller frames, as before.
    """
    method, n = "classic", spec.cols * spec.rows
    side = _COARSE_SIDES[-1]
    if max(gray.shape) >= _COARSE_MIN_FACTOR * side:
        small, scale = _downscaled(gray, side)
        corners = _classic_corners(small, spec)
        if corners is None:
            return ChessboardCorners(None, method, _NOT_FOUND)
        pts = _canonicalize(_to_full(corners, scale))
        refined = _refine_upscaled(gray, pts, spec, scale) if pts.shape[0] == n else None
        if refined is not None:
            return ChessboardCorners(refined, method)
    corners = _classic_corners(gray, spec)
    if corners is None:
        return ChessboardCorners(None, method, _NOT_FOUND)
    pts = _canonicalize(np.asarray(corners, dtype=np.float64).reshape(-1, 2))
    if pts.shape[0] != n:
        return ChessboardCorners(None, method, f"expected {n} corners, got {pts.shape[0]}")
    return ChessboardCorners(_refine_corners(gray, pts, spec)[0], method)


def _classic_corners(image: NDArray[np.uint8], spec: ChessboardSpec) -> NDArray | None:
    """``findChessboardCorners`` + its 11x11 ``cornerSubPix`` on ``image``; None if not found."""
    import cv2

    flags = cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE
    found, corners = cv2.findChessboardCorners(image, spec.pattern_size, flags=flags)
    if not found:
        return None
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-3)
    return cv2.cornerSubPix(image, np.float32(corners), (11, 11), (-1, -1), criteria)


def chessboard_sharpness(
    gray: NDArray[np.uint8], spec: ChessboardSpec, pts: NDArray[np.float64]
) -> float:
    """``estimateChessboardSharpness``: edge rise distance (px), NaN if OpenCV cannot tell."""
    import cv2

    try:
        return float(
            cv2.estimateChessboardSharpness(gray, spec.pattern_size, np.float32(pts))[0][0]
        )
    except cv2.error:
        return float("nan")
