"""Rigid-body-motion removal (al_dic_3d.reconstruct.rigid).

Every test builds point clouds with a KNOWN rigid motion (and, where relevant, a
known non-rigid deformation) so the fit and the correction are checked exactly.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from al_dic_3d.matching.contracts import INVALID, TRACKED
from al_dic_3d.reconstruct import Reconstruction3D
from al_dic_3d.reconstruct.rigid import (
    FIT_DEGENERATE,
    FIT_OK,
    FIT_REFERENCE,
    FIT_TOO_FEW,
    apply_rigid_motion,
    fit_rigid_motion,
    region_to_nodes,
)
from al_dic_3d.strain3d import compute_surface_strain

Z0 = 245.0  # mm, a working distance like the thermal-warpage rig
TILT = 2.87e-3  # rad, the rigid tilt measured on the warpage data set


def _rot(axis, angle: float) -> np.ndarray:
    """Rotation matrix about ``axis`` by ``angle`` (Rodrigues)."""
    k = np.asarray(axis, dtype=np.float64)
    k = k / np.linalg.norm(k)
    kx = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(angle) * kx + (1 - np.cos(angle)) * (kx @ kx)


def _grid(nx: int = 15, ny: int = 13, step_mm: float = 0.5, step_px: float = 16.0):
    """Reference nodes: 2D pixel coords and centred world x/y (mm)."""
    ii, jj = np.meshgrid(np.arange(nx), np.arange(ny))
    ii, jj = ii.ravel(), jj.ravel()
    ref_2d = np.column_stack([ii * step_px + 40.0, jj * step_px + 40.0])
    x = (ii - (nx - 1) / 2.0) * step_mm
    y = (jj - (ny - 1) / 2.0) * step_mm
    return ref_2d, x, y, ii, jj


def _curved_surface() -> np.ndarray:
    """A gently curved, tilted reference surface (not a plane)."""
    _, x, y, _, _ = _grid()
    z = Z0 + 0.15 * x - 0.08 * y + 0.01 * (x**2 - 0.5 * y**2)
    return np.column_stack([x, y, z])


def _recon(*frames: np.ndarray) -> Reconstruction3D:
    points = np.stack([np.asarray(f, dtype=np.float64) for f in frames])
    reproj = np.zeros(points.shape[:2])
    source = np.full(points.shape[:2], TRACKED, np.uint8)
    return Reconstruction3D(points, points - points[0][None], reproj, source)


def _move(p: np.ndarray, rot: np.ndarray, t) -> np.ndarray:
    return p @ rot.T + np.asarray(t, dtype=np.float64)


# --- exact recovery --------------------------------------------------------------


def test_rigid_mode_recovers_a_known_motion_exactly():
    p1 = _curved_surface()
    rot, t = _rot([0.3, 1.0, 0.2], TILT), np.array([0.33, -0.9, 0.14])
    rec = _recon(p1, _move(p1, rot, t))

    fit = fit_rigid_motion(rec, "rigid")

    assert fit.status == (FIT_REFERENCE, FIT_OK)
    assert np.allclose(fit.rotation[1], rot, atol=1e-12)
    assert np.allclose(fit.translation[1], t, atol=1e-9)
    assert fit.rms[1] < 1e-9
    assert fit.n_used[1] == p1.shape[0]
    assert abs(fit.angle_rad()[1] - TILT) < 1e-12
    out = apply_rigid_motion(rec, fit)
    assert np.allclose(out.displacement[1], 0.0, atol=1e-9)


def test_rigid_mode_keeps_a_deformation_that_has_no_net_rotation():
    # A symmetric bowl plus a uniform in-plane expansion about the centroid has no
    # best-fit rotation, so removing the rigid motion leaves d - mean(d).
    _, x, y, _, _ = _grid()
    p1 = np.column_stack([x, y, np.full_like(x, Z0)])
    d = np.column_stack([1e-3 * x, 1e-3 * y, 4e-4 * (x**2 + y**2)])
    rot, t = _rot([1.0, 0.2, 0.0], TILT), np.array([-0.003, -0.26, 0.14])
    rec = _recon(p1, _move(p1 + d, rot, t))

    out = apply_rigid_motion(rec, fit_rigid_motion(rec, "rigid"))

    assert np.allclose(out.displacement[1], d - d.mean(axis=0), atol=1e-9)


def test_planar_surface_gives_a_proper_rotation_not_a_reflection():
    _, x, y, _, _ = _grid()
    p1 = np.column_stack([x, y, np.full_like(x, Z0)])  # exactly planar: rank-2 cross-covariance
    rot = _rot([0.0, 0.0, 1.0], 0.05)
    rec = _recon(p1, _move(p1, rot, [0.1, 0.2, 0.0]))

    fit = fit_rigid_motion(rec, "rigid")

    assert np.linalg.det(fit.rotation[1]) == pytest.approx(1.0, abs=1e-12)
    assert np.allclose(fit.rotation[1], rot, atol=1e-12)


def test_each_frame_is_fitted_against_the_reference_independently():
    p1 = _curved_surface()
    motions = [(_rot([1, 0, 0], 1e-3), [0.0, 0.1, 0.0]), (_rot([0, 1, 0], -2e-3), [0.2, 0.0, 0.05])]
    rec = _recon(p1, *[_move(p1, r, t) for r, t in motions])

    fit = fit_rigid_motion(rec, "rigid")

    assert fit.status == (FIT_REFERENCE, FIT_OK, FIT_OK)
    for k, (rot, t) in enumerate(motions, start=1):
        assert np.allclose(fit.rotation[k], rot, atol=1e-12)
        assert np.allclose(fit.translation[k], t, atol=1e-9)


def test_centroid_shift_reports_how_far_the_region_moved():
    # The world translation t depends on the origin (the left camera, ~245 mm
    # away); the centroid shift is what the region itself moved.
    p1 = _curved_surface()
    rot, t = _rot([1, 0, 0], TILT), np.array([0.0, -0.26, 0.14])
    p2 = _move(p1, rot, t)
    fit = fit_rigid_motion(_recon(p1, p2), "rigid")

    assert np.allclose(fit.centroid_shift[1], p2.mean(axis=0) - p1.mean(axis=0), atol=1e-9)
    assert np.allclose(fit.centroid_shift[0], 0.0)


# --- translation mode ------------------------------------------------------------


def test_translation_mode_removes_the_mean_displacement_only():
    p1 = _curved_surface()
    rot, t = _rot([0.3, 1.0, 0.2], TILT), np.array([0.33, -0.9, 0.14])
    p2 = _move(p1, rot, t)
    rec = _recon(p1, p2)

    fit = fit_rigid_motion(rec, "translation")
    out = apply_rigid_motion(rec, fit)

    assert np.array_equal(fit.rotation[1], np.eye(3))
    assert np.allclose(fit.translation[1], (p2 - p1).mean(axis=0), atol=1e-12)
    assert np.allclose(out.displacement[1].mean(axis=0), 0.0, atol=1e-12)
    assert np.allclose(out.displacement[1], (p2 - p1) - (p2 - p1).mean(axis=0), atol=1e-12)


# --- region and invalid points ---------------------------------------------------


def test_node_mask_limits_the_fit_to_the_region():
    p1 = _curved_surface()
    rot, t = _rot([0.2, 1.0, 0.0], TILT), np.array([0.05, -0.2, 0.1])
    p2 = _move(p1, rot, t)
    region = p1[:, 0] < 0.0
    p2[~region] += np.array([0.0, 0.0, 0.03]) * (p1[~region, 0:1] ** 2)  # bending outside
    rec = _recon(p1, p2)

    inside = fit_rigid_motion(rec, "rigid", node_mask=region)
    everywhere = fit_rigid_motion(rec, "rigid")

    assert inside.n_used[1] == int(region.sum())
    assert np.allclose(inside.rotation[1], rot, atol=1e-12)
    assert np.allclose(inside.translation[1], t, atol=1e-9)
    assert not np.allclose(everywhere.rotation[1], rot, atol=1e-9)


def test_nan_nodes_are_left_out_and_stay_nan():
    p1 = _curved_surface()
    rot, t = _rot([1.0, 1.0, 0.0], TILT), np.array([0.1, 0.0, -0.05])
    p2 = _move(p1, rot, t)
    p1[3] = np.nan  # invalid at the reference
    p2[10] = np.nan  # lost in frame 1
    rec = _recon(p1, p2)

    fit = fit_rigid_motion(rec, "rigid")
    out = apply_rigid_motion(rec, fit)

    assert fit.n_used[1] == p1.shape[0] - 2
    assert np.allclose(fit.rotation[1], rot, atol=1e-12)
    assert np.isnan(out.points[1, 10]).all() and np.isnan(out.displacement[1, 3]).all()
    finite = np.isfinite(out.displacement[1]).all(axis=1)
    assert np.allclose(out.displacement[1][finite], 0.0, atol=1e-9)


@pytest.mark.parametrize(
    ("mode", "pick", "status"),
    [
        ("rigid", "two", FIT_TOO_FEW),
        ("rigid", "row", FIT_DEGENERATE),
        ("translation", "none", FIT_TOO_FEW),
    ],
)
def test_an_impossible_fit_invalidates_that_frame(mode, pick, status):
    _, x, y, ii, jj = _grid()
    p1 = np.column_stack([x, y, np.full_like(x, Z0)])
    rec = _recon(p1, p1 + 0.01, p1 + 0.02)
    region = {
        "two": np.isin(np.arange(x.size), [0, 1]),
        "row": jj == 4,  # one straight grid row: collinear
        "none": np.zeros(x.size, dtype=bool),
    }[pick]

    fit = fit_rigid_motion(rec, mode, node_mask=region)
    out = apply_rigid_motion(rec, fit)

    assert fit.status == (FIT_REFERENCE, status, status)
    assert np.isnan(fit.rotation[1]).all() and np.isnan(fit.translation[1]).all()
    assert np.isnan(out.points[1]).all() and np.isnan(out.reproj_error[1]).all()
    assert (out.source[1] == INVALID).all()
    assert np.array_equal(out.points[0], rec.points[0])


def test_translation_mode_needs_only_one_point():
    p1 = _curved_surface()
    rec = _recon(p1, p1 + np.array([0.0, 0.1, 0.0]))
    one = np.zeros(p1.shape[0], dtype=bool)
    one[7] = True

    fit = fit_rigid_motion(rec, "translation", node_mask=one)

    assert fit.status[1] == FIT_OK and fit.n_used[1] == 1


# --- contract ---------------------------------------------------------------------


def test_reference_frame_is_an_exact_copy_and_inputs_are_not_mutated():
    p1 = _curved_surface()
    rec = _recon(p1, _move(p1, _rot([0, 1, 0], TILT), [0.1, 0.2, 0.3]))
    before = (rec.points.copy(), rec.displacement.copy(), rec.source.copy())

    out = apply_rigid_motion(rec, fit_rigid_motion(rec, "rigid"))

    assert np.array_equal(out.points[0], rec.points[0])
    assert np.array_equal(rec.points, before[0])
    assert np.array_equal(rec.displacement, before[1])
    assert np.array_equal(rec.source, before[2])


def test_refitting_a_corrected_reconstruction_finds_no_motion():
    p1 = _curved_surface()
    rec = _recon(p1, _move(p1, _rot([0.4, 1, 0.1], TILT), [0.1, -0.2, 0.3]))
    once = apply_rigid_motion(rec, fit_rigid_motion(rec, "rigid"))

    again = fit_rigid_motion(once, "rigid")

    assert np.allclose(again.rotation[1], np.eye(3), atol=1e-12)
    assert np.allclose(again.translation[1], 0.0, atol=1e-9)


def test_unknown_mode_is_rejected():
    rec = _recon(_curved_surface(), _curved_surface())
    with pytest.raises(ValueError, match="mode"):
        fit_rigid_motion(rec, "off")


def test_mismatched_inputs_are_rejected():
    p1 = _curved_surface()
    rec = _recon(p1, p1 + 0.01)
    with pytest.raises(ValueError, match="node_mask"):
        fit_rigid_motion(rec, "rigid", node_mask=np.ones(5, dtype=bool))
    three = _recon(p1, p1 + 0.01, p1 + 0.02)
    with pytest.raises(ValueError, match="frames"):
        apply_rigid_motion(three, fit_rigid_motion(rec, "rigid"))


def test_to_meta_is_strict_json_with_units():
    _, x, y, _, jj = _grid()
    p1 = np.column_stack([x, y, np.full_like(x, Z0)])
    rec = _recon(p1, _move(p1, _rot([1, 0, 0], TILT), [0.0, -0.26, 0.14]), p1)
    region = jj == 4  # collinear -> both moving frames fail in rigid mode...
    failed = fit_rigid_motion(rec, "rigid", node_mask=region)
    ok = fit_rigid_motion(rec, "rigid")

    for fit in (failed, ok):
        meta = fit.to_meta()
        json.dumps(meta, allow_nan=False)  # NaN must come out as null
        assert meta["mode"] == "rigid"
        assert len(meta["centroid_shift_um"]) == rec.n_frames
    meta = ok.to_meta()
    assert meta["rotation_angle_mrad"][1] == pytest.approx(TILT * 1e3, abs=1e-9)
    assert meta["status"] == [FIT_REFERENCE, FIT_OK, FIT_OK]
    assert failed.to_meta()["centroid_shift_um"][1] == [None, None, None]


# --- region mask -> nodes -----------------------------------------------------------


def test_region_to_nodes_uses_the_nearest_pixel_like_the_display():
    from al_dic_3d.viz3d.surface import nodes_in_mask

    rng = np.random.default_rng(3)
    mask = rng.random((60, 80)) > 0.5
    coords = np.column_stack([rng.uniform(-5, 85, 400), rng.uniform(-5, 65, 400)])
    coords[:7] = np.nan

    assert np.array_equal(region_to_nodes(coords, mask), nodes_in_mask(coords, mask))
    as_png = mask.astype(np.uint8) * 255  # a mask read back from an image file
    assert np.array_equal(region_to_nodes(coords, as_png), region_to_nodes(coords, mask))


# --- why it matters: strain is invariant, slopes are not ---------------------------


def test_green_lagrange_strain_is_unchanged_but_slopes_lose_the_rigid_tilt():
    ref_2d, x, y, ii, jj = _grid(nx=21, ny=21)
    p1 = np.column_stack([x, y, np.full_like(x, Z0)])
    bowl = np.column_stack([1e-3 * x, 8e-4 * y, 4e-4 * (x**2 + y**2)])
    tilted = _move(p1 + bowl, _rot([1.0, 0.0, 0.0], TILT), [-0.003, -0.26, 0.14])
    raw = _recon(p1, tilted)
    corrected = apply_rigid_motion(raw, fit_rigid_motion(raw, "rigid"))

    s_raw = compute_surface_strain(raw, ref_2d, strain_size=7, winstepsize=16)
    s_cor = compute_surface_strain(corrected, ref_2d, strain_size=7, winstepsize=16)

    interior = (ii >= 4) & (ii <= 16) & (jj >= 4) & (jj <= 16)
    for comp in ("exx", "eyy", "exy"):
        diff = getattr(s_raw, comp)[1][interior] - getattr(s_cor, comp)[1][interior]
        assert np.nanmax(np.abs(diff)) < 1e-9, comp
    tilt_removed = np.nanmean(s_raw.dwdy[1][interior] - s_cor.dwdy[1][interior])
    assert abs(abs(tilt_removed) - TILT) < 0.02 * TILT
    assert abs(np.nanmean(s_cor.dwdy[1][interior])) < 0.02 * TILT
