"""Automatic stereo disparity prior when no starting point is placed (fix batch V, H2)."""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("al_dic")

from scipy.ndimage import gaussian_filter, map_coordinates  # noqa: E402

from al_dic_3d.calibration import CameraIntrinsics, StereoRig  # noqa: E402
from al_dic_3d.matching.disparity_prior import estimate_disparity_prior  # noqa: E402
from al_dic_3d.matching.primitives import make_dicpara  # noqa: E402
from al_dic_3d.matching.stereo import accept_field, stereo_match_pair  # noqa: E402

H, W = 420, 900


def _speckle(seed: int = 3) -> np.ndarray:
    img = gaussian_filter(np.random.default_rng(seed).random((H, W)), 2.0)
    return 20 + 200 * (img - img.min()) / (img.max() - img.min())


def _warp(img: np.ndarray, dx_fn) -> np.ndarray:
    """right(x, y) = left(x - dx(x, y), y - dy): features move by (+dx, +dy)."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
    dx, dy = dx_fn(xx, yy)
    return map_coordinates(img, [yy - dy, xx - dx], order=3, mode="nearest")


def _grid() -> np.ndarray:
    xs, ys = np.meshgrid(np.arange(140, 520, 16.0), np.arange(120, 300, 16.0))
    return np.column_stack([xs.ravel(), ys.ravel()])


def _rig() -> StereoRig:
    # Rectified rig: R = I, T along x -> epipolar lines are image rows.
    intr = CameraIntrinsics(fx=2000.0, fy=2000.0, cx=W / 2, cy=H / 2)
    return StereoRig(
        cameras={"L": intr, "R": intr},
        extrinsics={("L", "R"): (np.eye(3), np.array([-150.0, 0.0, 0.0]))},
    )


def test_a_large_disparity_is_found_without_a_starting_point():
    left = _speckle()
    right = _warp(left, lambda x, y: (np.full_like(x, 170.0), np.zeros_like(y)))
    pts = _grid()
    para = make_dicpara(img_size=(H, W), roi=(100, 560, 80, 340), winsize=24)

    blind, *_ = accept_field(stereo_match_pair(left, right, pts, para, search_radius=48))
    assert blind.valid.mean() < 0.2  # +/-48 px around zero cannot reach 170 px

    prior = estimate_disparity_prior(left, right, pts, rig=_rig())
    assert prior is not None and prior.n_accepted >= 3
    assert abs(prior.median[0] - 170) <= 1 and abs(prior.median[1]) <= 1
    field, *_ = accept_field(
        stereo_match_pair(left, right, pts, para, search_radius=48, disparity_offset=prior.offsets)
    )
    assert field.valid.mean() > 0.95
    assert np.allclose(field.d[field.valid], (170.0, 0.0), atol=0.05)


def test_a_disparity_gradient_gives_an_affine_prior():
    left = _speckle(5)

    def shift(x, y):
        return 120.0 + 0.08 * (x - 300.0), np.zeros_like(y)

    right = _warp(left, shift)
    pts = _grid()
    prior = estimate_disparity_prior(left, right, pts)
    assert prior is not None and prior.model == "affine"
    # right(x) = left(x - dx(x)): a left feature at x lands at x_R with
    # x_R - dx(x_R) = x, i.e. a disparity of (96 + 0.08 x) / 0.92.
    truth = (96.0 + 0.08 * pts[:, 0]) / 0.92
    assert np.abs(prior.offsets[:, 0] - truth).max() < 4.0  # well inside the NCC box
    assert "probe patches" in prior.describe()


def test_matches_off_the_epipolar_line_are_rejected():
    left = _speckle(7)
    # A pure vertical shift contradicts the rectified rig (epipolar lines = rows).
    right = _warp(left, lambda x, y: (np.zeros_like(x), np.full_like(y, 40.0)))
    pts = _grid()
    assert estimate_disparity_prior(left, right, pts, rig=_rig()) is None
    assert estimate_disparity_prior(left, right, pts) is not None  # no rig: accepted


def test_a_textureless_scene_gives_no_prior():
    flat = np.full((H, W), 128.0)
    assert estimate_disparity_prior(flat, flat, _grid()) is None


def test_probes_stay_inside_the_mask():
    left = _speckle(9)
    right = _warp(left, lambda x, y: (np.full_like(x, 60.0), np.zeros_like(y)))
    mask = np.zeros((H, W))
    mask[100:320, 300:560] = 1.0
    pts = _grid()
    prior = estimate_disparity_prior(left, right, pts, mask=mask)
    assert prior is not None and abs(prior.median[0] - 60) <= 1


def test_without_a_point_the_probes_seed_the_propagation():
    from al_dic_3d.matching.strategies._common import stereo_search_centre
    from al_dic_3d.matching.temporal import build_grid_mesh

    left = _speckle(11)

    def shift(x, y):  # a curved disparity field no single offset or plane fits
        return 150.0 + 0.0012 * (x - 450.0) ** 2, np.zeros_like(y)

    right = _warp(left, shift)
    para = make_dicpara(img_size=(H, W), roi=(120, 500, 110, 310), winsize=24, winstepsize=16)
    mesh = build_grid_mesh(para, H, W)
    coords = np.asarray(mesh.coordinates_fem, dtype=np.float64)

    seed_u0, centre, note = stereo_search_centre(
        None, None, left, right, mesh, None, _rig(), para, search_radius=24
    )
    assert "propagated from the probes" in note
    field, *_ = accept_field(
        stereo_match_pair(
            left, right, coords, para, search_radius=24, disparity_offset=centre, seed_u0=seed_u0
        )
    )
    assert field.valid.mean() > 0.95
    # The disparity varies by ~50 px over the ROI: one centred box of +/-24 px
    # could not have covered it, the propagation did.
    assert np.nanmax(field.d[:, 0]) - np.nanmin(field.d[:, 0]) > 40

    # A placed point (or explicit offset) is left alone.
    kept = stereo_search_centre(
        None, (5.0, 0.0), left, right, mesh, None, None, para, search_radius=24
    )
    assert kept == (None, (5.0, 0.0), "frame-1 stereo match")
