"""Validation of match_points against synthetic speckle with known displacement.

Proves the keystone 2D-solver coupling: local IC-GN at scattered points recovers a
known sub-pixel displacement, computes a small ZNSSD, and flags edge points invalid.
Requires the ``al_dic`` engine (installed in the ``pyaldic3d`` env / CI).
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.ndimage import gaussian_filter, map_coordinates

from al_dic_3d.matching.primitives import make_local_dicpara, match_points


def _speckle(h: int = 220, w: int = 220, sigma: float = 2.5, seed: int = 3) -> np.ndarray:
    rng = np.random.default_rng(seed)
    f = gaussian_filter(rng.standard_normal((h, w)), sigma=sigma, mode="nearest")
    f -= f.min()
    f /= f.max()
    return 20.0 + 215.0 * f


def _warp_uniform(ref: np.ndarray, u: float, v: float) -> np.ndarray:
    """def(x) = ref(x - (u, v)) — a rigid sub-pixel shift (Lagrangian == Eulerian)."""
    h, w = ref.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    return map_coordinates(ref, [yy - v, xx - u], order=5, mode="nearest").reshape(h, w)


def _interior_points(h: int, w: int, margin: int = 45, step: int = 24) -> np.ndarray:
    xs = np.arange(margin, w - margin, step, dtype=np.float64)
    ys = np.arange(margin, h - margin, step, dtype=np.float64)
    gx, gy = np.meshgrid(xs, ys)
    return np.column_stack([gx.ravel(), gy.ravel()])


def _para(ref: np.ndarray):
    h, w = ref.shape
    return make_local_dicpara(img_size=(h, w), roi=(20, w - 20, 20, h - 20), winsize=32)


def test_match_points_recovers_subpixel_shift():
    ref = _speckle()
    u_true, v_true = 1.7, -0.9
    dfm = _warp_uniform(ref, u_true, v_true)
    pts = _interior_points(*ref.shape)
    para = _para(ref)

    U, znssd, valid = match_points(ref, dfm, pts, np.zeros_like(pts), para)

    assert valid.all(), f"{(~valid).sum()} of {len(pts)} points failed to converge"
    assert np.nanmax(np.abs(U[:, 0] - u_true)) < 0.05
    assert np.nanmax(np.abs(U[:, 1] - v_true)) < 0.05
    assert np.nanmax(znssd) < 0.05  # near-perfect correlation on clean speckle


def test_match_points_recovers_zero_shift_with_low_znssd():
    ref = _speckle()
    pts = _interior_points(*ref.shape)
    para = _para(ref)
    U, znssd, valid = match_points(ref, ref, pts, np.zeros_like(pts), para)
    assert valid.all()
    assert np.nanmax(np.abs(U)) < 1e-3
    assert np.nanmax(znssd) < 1e-6  # identical images -> ZNSSD ~ 0


def test_edge_points_are_invalid():
    ref = _speckle()
    dfm = _warp_uniform(ref, 1.0, 0.0)
    h, w = ref.shape
    # Points within half a subset of the border must be rejected as holes.
    pts = np.array([[2.0, 2.0], [w - 2.0, h - 2.0], [w / 2, h / 2]])
    para = _para(ref)
    U, znssd, valid = match_points(ref, dfm, pts, np.zeros_like(pts), para)
    assert not valid[0] and not valid[1]  # corners rejected
    assert valid[2]  # centre converges
    assert np.isnan(U[0]).all() and np.isnan(znssd[0])


def test_znssd_in_range_and_nan_for_invalid():
    ref = _speckle()
    dfm = _warp_uniform(ref, 0.5, 0.5)
    pts = _interior_points(*ref.shape)
    para = _para(ref)
    _, znssd, valid = match_points(ref, dfm, pts, np.zeros_like(pts), para)
    finite = np.isfinite(znssd)
    assert (znssd[finite] >= 0).all() and (znssd[finite] <= 4.0).all()
    assert np.array_equal(finite, valid)


def test_bad_initial_guess_still_converges_for_small_motion():
    # IC-GN basin: a wrong-by-2px U0 should still land on the true small shift.
    ref = _speckle()
    u_true, v_true = 0.8, 0.3
    dfm = _warp_uniform(ref, u_true, v_true)
    pts = _interior_points(*ref.shape)
    para = _para(ref)
    U0 = np.full_like(pts, 2.0)  # deliberately off
    U, _, valid = match_points(ref, dfm, pts, U0, para)
    conv = valid & np.isfinite(U[:, 0])
    assert conv.mean() > 0.8
    assert np.nanmedian(np.abs(U[conv, 0] - u_true)) < 0.1


@pytest.mark.parametrize("winsize", [16, 32, 48])
def test_various_subset_sizes(winsize: int):
    ref = _speckle()
    dfm = _warp_uniform(ref, 1.2, 0.4)
    pts = _interior_points(*ref.shape, margin=60)
    para = make_local_dicpara(img_size=ref.shape, roi=(20, 200, 20, 200), winsize=winsize)
    U, _, valid = match_points(ref, dfm, pts, np.zeros_like(pts), para)
    assert valid.mean() > 0.9
    assert np.nanmedian(np.abs(U[:, 0] - 1.2)) < 0.05


def test_dicpara_default_enables_al_global_step():
    # Audit contract (2026-07-07): the 3D layer runs the FULL AL-DIC global
    # step by default, mirroring the MATLAB trusted path's UseGlobal=true.
    from al_dic_3d.matching.primitives import make_dicpara

    para = make_dicpara(img_size=(128, 128), roi=(16, 112, 16, 112))
    assert para.use_global_step is True
    assert para.admm_max_iter == 3

    local = make_dicpara(img_size=(128, 128), roi=(16, 112, 16, 112), use_global_step=False)
    assert local.use_global_step is False
