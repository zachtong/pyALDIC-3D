"""Validate stereo_match_pair against a synthetic L1<->R1 pair with known disparity.

A speckle left image is warped by a known homography (a mildly tilted plane) to
produce the right image, so every left point's true right correspondence is
``H @ p``. The matcher must recover it to sub-pixel accuracy via NCC seed +
local IC-GN, and flag off-image points invalid.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.ndimage import gaussian_filter

from al_dic_3d.matching.primitives import make_local_dicpara
from al_dic_3d.matching.stereo import stereo_match_pair

cv2 = pytest.importorskip("cv2")


def _speckle(h: int, w: int, sigma: float = 2.3, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    f = gaussian_filter(rng.standard_normal((h, w)), sigma=sigma, mode="nearest")
    f -= f.min()
    f /= f.max()
    return 20.0 + 215.0 * f


def _apply_h(H: np.ndarray, pts: np.ndarray) -> np.ndarray:
    ph = np.column_stack([pts, np.ones(len(pts))])
    q = ph @ H.T
    return q[:, :2] / q[:, 2:3]


def _grid(h: int, w: int, margin: int, step: int) -> np.ndarray:
    xs = np.arange(margin, w - margin, step, dtype=np.float64)
    ys = np.arange(margin, h - margin, step, dtype=np.float64)
    gx, gy = np.meshgrid(xs, ys)
    return np.column_stack([gx.ravel(), gy.ravel()])


def test_stereo_match_recovers_known_disparity():
    h = w = 260
    left = _speckle(h, w)
    # Horizontal disparity ~15-25 px with a mild scale/perspective so it varies.
    H = np.array([[1.02, 0.0, 15.0], [0.0, 1.0, 2.0], [8e-5, 0.0, 1.0]], dtype=np.float64)
    right = cv2.warpPerspective(
        left, H, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT
    )

    pts = _grid(h, w, margin=70, step=22)
    para = make_local_dicpara(img_size=(h, w), roi=(30, w - 30, 30, h - 30), winsize=32)

    field = stereo_match_pair(left, right, pts, para, search_radius=48)

    gt = _apply_h(H, pts)
    err = np.linalg.norm(field.right_pts - gt, axis=1)
    assert field.valid.mean() > 0.9, f"only {field.valid.mean():.0%} points matched"
    assert np.nanmedian(err[field.valid]) < 0.1
    assert np.nanmax(err[field.valid]) < 0.3


def test_stereo_match_honors_disparity_offset():
    """With a large baseline, a coarse offset prior keeps the NCC search small."""
    h = w = 260
    left = _speckle(h, w)
    H = np.array([[1.0, 0.0, 40.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], dtype=np.float64)
    right = cv2.warpPerspective(
        left, H, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT
    )
    pts = _grid(h, w, margin=80, step=24)
    para = make_local_dicpara(img_size=(h, w), roi=(30, w - 30, 30, h - 30), winsize=32)

    # Small residual search (12 px) only works because the offset absorbs the 40 px.
    field = stereo_match_pair(
        left, right, pts, para, disparity_offset=(40.0, 0.0), search_radius=12
    )
    gt = _apply_h(H, pts)
    err = np.linalg.norm(field.right_pts - gt, axis=1)
    assert field.valid.mean() > 0.9
    assert np.nanmedian(err[field.valid]) < 0.1


def test_stereo_match_flags_offimage_points_invalid():
    h = w = 220
    left = _speckle(h, w)
    right = left.copy()
    pts = np.array([[3.0, 3.0], [w - 3.0, h - 3.0], [w / 2, h / 2]])
    para = make_local_dicpara(img_size=(h, w), roi=(20, w - 20, 20, h - 20), winsize=32)
    field = stereo_match_pair(left, right, pts, para, search_radius=20)
    assert not field.valid[0] and not field.valid[1]  # corners: window off-image
    assert field.valid[2]
    assert np.isnan(field.d[0]).all()
