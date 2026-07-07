"""D12 built-in calibration synthetic parity gate.

Renders board views through a known distorted stereo rig (``synth_calib``) and
asserts that detection recovers analytic point projections and the solver
recovers the true camera parameters. Tolerances are ~3-5x the measured values
on this deterministic dataset (chessboard solve measured: rms 0.015 px,
fx 0.003 %, cx 0.07 px, baseline 1.8 um, R 0.002 deg).
"""

import dataclasses

import numpy as np
import pytest

from al_dic_3d.calibration import (
    CharucoSpec,
    ChessboardSpec,
    CircleGridSpec,
    CodedCircleGridSpec,
    calibrate_stereo,
    detect_board,
    from_opencv_yaml,
    summarize,
    to_opencv_yaml,
)
from tests import synth_calib as sc

CHESS = ChessboardSpec(cols=9, rows=7, square_size=12.0)
CHARUCO = CharucoSpec(squares_x=10, squares_y=8, square_size=12.0, marker_size=9.0)
CODED = CodedCircleGridSpec(cols=11, rows=9, spacing=12.0)


def _extent(spec):
    if isinstance(spec, CharucoSpec):
        return (spec.squares_x * spec.square_size, spec.squares_y * spec.square_size)
    pitch = spec.square_size if isinstance(spec, ChessboardSpec) else spec.spacing
    return ((spec.cols - 1) * pitch, (spec.rows - 1) * pitch)


def _render_and_detect(spec, rig):
    poses = sc.board_poses(_extent(spec), n=18)
    lefts, rights = sc.render_stereo_set(spec, rig, poses)
    dl = [detect_board(im, spec) for im in lefts]
    dr = [detect_board(im, spec) for im in rights]
    return poses, dl, dr


@pytest.fixture(scope="module")
def rig():
    return sc.make_rig()


@pytest.fixture(scope="module")
def chess_set(rig):
    return _render_and_detect(CHESS, rig)


@pytest.fixture(scope="module")
def coded_set(rig):
    return _render_and_detect(CODED, rig)


def _detection_errors(spec, poses, detections, rig, cam):
    errs = []
    for pose, det in zip(poses, detections, strict=True):
        assert det.ok, f"{cam}: {det.reason}"
        gt = sc.gt_pixels(spec, pose, rig, cam)
        errs.append(np.linalg.norm(det.image_points - gt[det.ids], axis=1))
    return np.concatenate(errs)


def _rotation_err_deg(R_est, R_gt):
    return float(np.degrees(np.arccos(np.clip((np.trace(R_est @ R_gt.T) - 1.0) / 2.0, -1.0, 1.0))))


# --------------------------------------------------------------------------- #
# Detection accuracy vs analytic projections
# --------------------------------------------------------------------------- #


def test_chessboard_detection_accuracy(rig, chess_set):
    poses, dl, dr = chess_set
    for cam, dets in (("L", dl), ("R", dr)):
        err = _detection_errors(CHESS, poses, dets, rig, cam)
        assert err.mean() < 0.05 and err.max() < 0.15


def test_coded_grid_detection_accuracy(rig, coded_set):
    poses, dl, dr = coded_set
    for cam, dets in (("L", dl), ("R", dr)):
        err = _detection_errors(CODED, poses, dets, rig, cam)
        assert err.mean() < 0.1 and err.max() < 0.25
        # partial views allowed, but most of the 99-dot lattice must index
        assert min(d.n_points for d in dets) >= 80


def test_charuco_detection_accuracy(rig):
    poses = sc.board_poses(_extent(CHARUCO), n=3)
    lefts, _ = sc.render_stereo_set(CHARUCO, rig, poses)
    for pose, img in zip(poses, lefts, strict=True):
        det = detect_board(img, CHARUCO)
        assert det.ok, det.reason
        gt = sc.gt_pixels(CHARUCO, pose, rig, "L")
        err = np.linalg.norm(det.image_points - gt[det.ids], axis=1)
        assert err.mean() < 0.15 and err.max() < 0.4


def test_circle_grid_detection_accuracy(rig):
    spec = CircleGridSpec(cols=9, rows=7, spacing=13.0)
    poses = sc.board_poses(_extent(spec), n=2)
    lefts, _ = sc.render_stereo_set(spec, rig, poses)
    for pose, img in zip(poses, lefts, strict=True):
        det = detect_board(img, spec)
        assert det.ok, det.reason
        gt = sc.gt_pixels(spec, pose, rig, "L")
        err = np.linalg.norm(det.image_points - gt, axis=1)
        assert err.mean() < 0.15


def test_detectors_fail_gracefully_on_noise():
    rng = np.random.default_rng(0)
    noise = rng.uniform(0, 255, (300, 400)).astype(np.uint8)
    for spec in (CHESS, CHARUCO, CODED, CircleGridSpec(cols=9, rows=7, spacing=13.0)):
        det = detect_board(noise, spec)
        assert not det.ok and det.reason


def test_coded_detector_requires_fiducials(rig):
    plain = CircleGridSpec(cols=11, rows=9, spacing=12.0)
    poses = sc.board_poses(_extent(plain), n=1)
    lefts, _ = sc.render_stereo_set(plain, rig, poses)
    det = detect_board(lefts[0], CODED)  # same lattice, but no rings anywhere
    assert not det.ok and "fiducial" in det.reason


# --------------------------------------------------------------------------- #
# Stereo solve parity
# --------------------------------------------------------------------------- #


def _assert_rig_close(res, rig, *, fx_rel, cx_px, k1_abs, base_mm, r_deg):
    gt_l = rig.cameras["L"]
    est_l = res.rig.cameras["L"]
    assert abs(est_l.fx - gt_l.fx) / gt_l.fx < fx_rel
    assert abs(est_l.cx - gt_l.cx) < cx_px
    assert abs(est_l.cy - gt_l.cy) < cx_px
    assert abs(est_l.k1 - gt_l.k1) < k1_abs
    r_gt, t_gt = rig.pose("R")
    r_e, t_e = res.rig.pose("R")
    assert abs(np.linalg.norm(t_e) - np.linalg.norm(t_gt)) < base_mm
    assert _rotation_err_deg(r_e, r_gt) < r_deg


def test_chessboard_stereo_gate(rig, chess_set):
    _poses, dl, dr = chess_set
    res = calibrate_stereo(dl, dr, (sc.IMG_W, sc.IMG_H))
    assert res.n_pairs_used == 18
    assert res.rms < 0.05
    assert res.epipolar_rms < 0.05
    _assert_rig_close(res, rig, fx_rel=5e-4, cx_px=0.5, k1_abs=5e-3, base_mm=0.05, r_deg=0.05)


def test_coded_grid_stereo_gate(rig, coded_set):
    _poses, dl, dr = coded_set
    res = calibrate_stereo(dl, dr, (sc.IMG_W, sc.IMG_H), dot_radius_mm=CODED.dot_mm / 2)
    assert res.n_pairs_used == 18
    assert res.rms < 0.15
    _assert_rig_close(res, rig, fx_rel=2e-3, cx_px=1.0, k1_abs=5e-3, base_mm=0.1, r_deg=0.1)


def test_tangential_recovery():
    rig_t = sc.make_rig(tangential=True)
    poses = sc.board_poses(_extent(CHESS), n=18)
    lefts, rights = sc.render_stereo_set(CHESS, rig_t, poses)
    dl = [detect_board(im, CHESS) for im in lefts]
    dr = [detect_board(im, CHESS) for im in rights]
    res = calibrate_stereo(dl, dr, (sc.IMG_W, sc.IMG_H), zero_tangent=False)
    est_l = res.rig.cameras["L"]
    assert abs(est_l.p1 - rig_t.cameras["L"].p1) < 1e-4
    assert abs(est_l.p2 - rig_t.cameras["L"].p2) < 1e-4
    _assert_rig_close(res, rig_t, fx_rel=1e-3, cx_px=1.0, k1_abs=5e-3, base_mm=0.05, r_deg=0.05)


def test_release_object_method(rig, chess_set):
    _poses, dl, dr = chess_set
    res = calibrate_stereo(dl, dr, (sc.IMG_W, sc.IMG_H), release_object=True)
    assert res.mono["L"].method == "release_object"
    assert res.rms < 0.1
    _assert_rig_close(res, rig, fx_rel=2e-3, cx_px=1.0, k1_abs=1e-2, base_mm=0.1, r_deg=0.1)


def test_rejection_loop_drops_corrupted_pair(rig, chess_set):
    _poses, dl, dr = chess_set
    bad = dataclasses.replace(dr[4], image_points=dr[4].image_points + 4.0)
    res = calibrate_stereo(dl, [*dr[:4], bad, *dr[5:]], (sc.IMG_W, sc.IMG_H))
    assert res.n_pairs_used == 17
    rejected = [p for p in res.pairs if not p.used]
    assert len(rejected) == 1 and rejected[0].index == 4
    assert "rejected" in rejected[0].note
    assert res.rms < 0.05  # survivors solve cleanly


def test_solve_input_validation(chess_set):
    _poses, dl, dr = chess_set
    with pytest.raises(ValueError, match="view counts differ"):
        calibrate_stereo(dl[:5], dr[:4], (sc.IMG_W, sc.IMG_H))
    with pytest.raises(ValueError, match="usable stereo pairs"):
        calibrate_stereo(dl[:5], dr[:5], (sc.IMG_W, sc.IMG_H))


# --------------------------------------------------------------------------- #
# Report / YAML funnel
# --------------------------------------------------------------------------- #


def test_yaml_round_trip_and_summary(tmp_path, rig, chess_set):
    _poses, dl, dr = chess_set
    res = calibrate_stereo(dl, dr, (sc.IMG_W, sc.IMG_H))
    stats = summarize(res, dl, dr, (sc.IMG_W, sc.IMG_H))
    assert 0.0 < stats["coverage_left"] <= 1.0
    assert stats["n_pairs_used"] == 18
    assert stats["tilt_max_deg"] > 20.0  # the pose set includes strong tilts

    path = to_opencv_yaml(
        res.rig, tmp_path / "builtin.yml", meta={"rms_px": res.rms, "source": "builtin"}
    )
    back = from_opencv_yaml(path)
    for cam in ("L", "R"):
        assert np.allclose(back.cameras[cam].K, res.rig.cameras[cam].K)
        assert np.allclose(back.cameras[cam].dist_coeffs, res.rig.cameras[cam].dist_coeffs)
    r0, t0 = res.rig.pose("R")
    r1, t1 = back.pose("R")
    assert np.allclose(r0, r1) and np.allclose(t0, t1)
