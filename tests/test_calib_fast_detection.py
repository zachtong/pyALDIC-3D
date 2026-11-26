"""Fast chessboard detection: coarse-to-fine search, 16-bit conversion, memory budget.

Large frames are searched on a downscaled copy and refined at full resolution;
the corners must match the full-resolution detector and the analytic truth.
Corners the downscaled search cannot localise fall back to the full-resolution
detectors, and the memory-hungry full-resolution SB search is rationed.
"""

from __future__ import annotations

import threading

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from al_dic_3d.calibration import ChessboardSpec, detect_board  # noqa: E402
from al_dic_3d.calibration import chessboard as cb  # noqa: E402
from al_dic_3d.calibration.detect import to_gray_u8  # noqa: E402

SPEC = ChessboardSpec(cols=9, rows=7, square_size=10.0)


def _board_homography(width: int, height: int, px_per_mm: float) -> np.ndarray:
    """Board mm -> image px: a tilted, rolled board centred in the frame."""
    f = 6000.0
    z = f / px_per_mm
    a, b, c = np.deg2rad([20.0, -15.0, 10.0])
    rx = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
    ry = np.array([[np.cos(b), 0, np.sin(b)], [0, 1, 0], [-np.sin(b), 0, np.cos(b)]])
    rz = np.array([[np.cos(c), -np.sin(c), 0], [np.sin(c), np.cos(c), 0], [0, 0, 1]])
    rot = rz @ ry @ rx
    centre = np.array([(SPEC.cols - 1) * SPEC.square_size, (SPEC.rows - 1) * SPEC.square_size, 0])
    t = np.array([0.0, 0.0, z]) - rot @ (centre / 2.0)
    k = np.array([[f, 0, (width - 1) / 2.0], [0, f, (height - 1) / 2.0], [0, 0, 1]])
    return k @ np.column_stack([rot[:, 0], rot[:, 1], t])


def _render(width: int, height: int, px_per_mm: float, seed: int = 0):
    """8-bit chessboard view with exact corners -> (image, true corners (n, 2)).

    The board is band-limited in board space (``tanh`` of a sine per axis), so its
    0.5 iso-lines are exactly the projected grid lines and every inner corner
    sits exactly at the homography image of its lattice point.
    """
    hom = _board_homography(width, height, px_per_mm)
    inv = np.linalg.inv(hom)
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float64)
    q = np.tensordot(inv, np.stack([xx, yy, np.ones_like(xx)]), axes=1)
    u, v = q[0] / q[2], q[1] / q[2]
    sq = SPEC.square_size
    sharp = sq * px_per_mm / np.pi  # edge rise ~1 image px
    s_u = np.tanh(sharp * np.sin(np.pi * u / sq))
    s_v = np.tanh(sharp * np.sin(np.pi * v / sq))
    inside = (u > -sq) & (u < SPEC.cols * sq) & (v > -sq) & (v < SPEC.rows * sq)
    level = np.where(inside, 0.5 + 0.5 * s_u * s_v, 1.0)
    rng = np.random.default_rng(seed)
    image = np.clip(np.round(20.0 + 215.0 * level + rng.normal(0, 1.0, level.shape)), 0, 255)
    obj = SPEC.object_points()
    proj = np.column_stack([obj[:, :2], np.ones(len(obj))]) @ hom.T
    return image.astype(np.uint8), proj[:, :2] / proj[:, 2:3]


def _corner_error(points: np.ndarray, truth: np.ndarray) -> np.ndarray:
    """Per-corner error, either canonical order (the detector picks the start corner)."""
    e1 = np.linalg.norm(points - truth, axis=1)
    e2 = np.linalg.norm(points - truth[::-1], axis=1)
    return e1 if e1.mean() < e2.mean() else e2


@pytest.fixture(scope="module")
def large_view():
    return _render(2600, 2000, 12.0)  # ~120 px squares; coarse level 1024 applies


def _spy_sb(monkeypatch) -> list[tuple[int, int]]:
    """Record the image shape of every findChessboardCornersSB call."""
    shapes: list[tuple[int, int]] = []
    real = cv2.findChessboardCornersSB

    def spy(image, *args, **kwargs):
        shapes.append(tuple(image.shape[:2]))
        return real(image, *args, **kwargs)

    monkeypatch.setattr(cv2, "findChessboardCornersSB", spy)
    return shapes


def test_coarse_to_fine_matches_full_resolution_and_truth(large_view, monkeypatch):
    image, truth = large_view
    shapes = _spy_sb(monkeypatch)
    det = detect_board(image, SPEC)
    assert det.ok and det.method == "sb"
    assert shapes == [(788, 1024)]  # one coarse search, no full-resolution SB
    assert _corner_error(det.image_points, truth).max() < 0.05
    # Full-resolution SB misses this 120 px-square view and the classic detector
    # takes over; both starts end in the same full-resolution refinement.
    full = cb._find_full(image, SPEC)
    assert full.points is not None
    assert np.abs(det.image_points - full.points).max() < 2e-3
    full_sharpness = cb.chessboard_sharpness(image, SPEC, full.points)
    assert det.sharpness == pytest.approx(full_sharpness, rel=1e-3)


def test_unconfirmed_coarse_corners_fall_back_to_full_resolution(large_view, monkeypatch):
    image, truth = large_view
    monkeypatch.setattr(cb, "_COARSE_MAX_MOVE", -1.0)  # no refinement confirms
    shapes = _spy_sb(monkeypatch)
    det = detect_board(image, SPEC)
    assert det.ok and det.method in ("sb", "classic")
    assert shapes == [(788, 1024), image.shape]
    assert _corner_error(det.image_points, truth).max() < 0.05


def test_upscaled_corners_are_distrusted_at_the_frame_edge_or_after_long_moves(large_view):
    image, truth = large_view
    order = truth if truth[0].sum() < truth[-1].sum() else truth[::-1]  # canonical order
    scale = np.array([2.5, 2.5])
    start = order + np.array([1.5, -1.0])  # a typical coarse localisation error
    refined = cb._refine_upscaled(image, start, SPEC, scale)
    assert refined is not None and np.linalg.norm(refined - order, axis=1).max() < 0.05
    # The same corners with the top row 8 px below the frame edge: no margin.
    top = int(order[:, 1].min()) - 8
    crop = np.ascontiguousarray(image[top:])
    assert cb._refine_upscaled(crop, start - [0, top], SPEC, scale) is None
    # A start 6 px off is beyond what a 0.5x "downscale" can explain.
    assert cb._refine_upscaled(image, order + [6.0, 0.0], SPEC, np.array([0.5, 0.5])) is None


def test_frames_near_the_coarse_size_use_only_full_resolution(monkeypatch):
    image, truth = _render(1400, 1100, 6.0, seed=1)  # longer side < 1.5 x 1024
    shapes = _spy_sb(monkeypatch)
    det = detect_board(image, SPEC)
    assert det.ok
    assert shapes == [image.shape]
    assert _corner_error(det.image_points, truth).max() < 0.05


def _without_sb(monkeypatch) -> list[tuple[int, int]]:
    """Make every SB search fail; record the image shape of every classic call."""
    shapes: list[tuple[int, int]] = []
    real = cv2.findChessboardCorners

    def spy(image, *args, **kwargs):
        shapes.append(tuple(image.shape[:2]))
        return real(image, *args, **kwargs)

    monkeypatch.setattr(cv2, "findChessboardCornersSB", lambda *_a, **_k: (False, None))
    monkeypatch.setattr(cv2, "findChessboardCorners", spy)
    return shapes


def test_classic_fallback_searches_large_frames_downscaled(monkeypatch):
    image, truth = _render(3200, 2400, 13.0, seed=2)  # longer side >= 1.5 x 2048
    shapes = _without_sb(monkeypatch)
    det = detect_board(image, SPEC)
    assert det.ok and det.method == "classic"
    assert shapes == [(1536, 2048)]
    assert _corner_error(det.image_points, truth).max() < 0.05


def test_classic_fallback_keeps_full_resolution_on_smaller_frames(monkeypatch):
    image, truth = _render(1400, 1100, 6.0, seed=1)
    shapes = _without_sb(monkeypatch)
    det = detect_board(image, SPEC)
    assert det.ok and det.method == "classic"
    assert shapes == [image.shape]
    assert _corner_error(det.image_points, truth).max() < 0.05


def test_a_missing_board_still_reports_a_reason():
    blank = np.full((2000, 2600), 128, np.uint8)
    det = detect_board(blank, SPEC)
    assert not det.ok
    assert det.reason == "chessboard not found (SB and classic detectors)"


def test_memory_budget_admits_jobs_while_they_fit():
    import time
    from concurrent.futures import ThreadPoolExecutor

    budget = cb._MemoryBudget(100)
    lock = threading.Lock()
    state = {"now": 0, "peak": 0, "alone": True}

    def job(nbytes: int) -> None:
        with budget.reserve(nbytes):
            with lock:
                state["now"] += nbytes
                state["peak"] = max(state["peak"], state["now"])
                if nbytes > 100 and state["now"] != nbytes:
                    state["alone"] = False
            time.sleep(0.02)
            with lock:
                state["now"] -= nbytes

    with ThreadPoolExecutor(6) as pool:
        list(pool.map(job, [30, 30, 30, 30, 60, 60, 150, 30, 30]))
    assert state["peak"] <= 150  # within budget, or one oversized job alone
    assert state["alone"]
    with ThreadPoolExecutor(6) as pool:  # small jobs do run side by side
        state["peak"] = 0
        list(pool.map(job, [30] * 6))
    assert 60 <= state["peak"] <= 90


def _reference_gray(arr: np.ndarray) -> np.ndarray:
    """The generic float64 min-max stretch ``to_gray_u8`` applies to non-8-bit input."""
    a = arr.astype(np.float64)
    lo, hi = float(a.min()), float(a.max())
    if hi <= lo:
        return np.zeros(a.shape, np.uint8)
    return np.clip((a - lo) / (hi - lo) * 255.0, 0, 255).astype(np.uint8)


def test_uint16_gray_conversion_is_bit_identical_to_the_float_path():
    rng = np.random.default_rng(3)
    img = rng.integers(300, 3900, (257, 311), dtype=np.uint16)  # 12-bit data
    np.testing.assert_array_equal(to_gray_u8(img), _reference_gray(img))
    full = rng.integers(0, 65536, (64, 80), dtype=np.uint16)
    np.testing.assert_array_equal(to_gray_u8(full), _reference_gray(full))
    flat = np.full((10, 12), 777, np.uint16)
    np.testing.assert_array_equal(to_gray_u8(flat), np.zeros((10, 12), np.uint8))
    bgr = rng.integers(0, 4096, (40, 50, 3), dtype=np.uint16)
    expected = _reference_gray(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY))
    np.testing.assert_array_equal(to_gray_u8(bgr), expected)
