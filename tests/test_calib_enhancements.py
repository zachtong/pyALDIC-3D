"""C3 enhancement gates: board printout, known-distance verify, bundle adjust."""

import dataclasses

import numpy as np
import pytest

from al_dic_3d.calibration import (
    BoardDetection,
    ChessboardSpec,
    CircleGridSpec,
    bundle_refine,
    calibrate_stereo,
    detect_board,
    save_board_pdf,
    spec_summary,
    verify_known_distance,
)
from tests import synth_calib as sc

CHESS = ChessboardSpec(cols=9, rows=7, square_size=12.0)


@pytest.fixture(scope="module")
def rig():
    return sc.make_rig()


@pytest.fixture(scope="module")
def chess_set(rig):
    extent = ((CHESS.cols - 1) * CHESS.square_size, (CHESS.rows - 1) * CHESS.square_size)
    poses = sc.board_poses(extent, n=18)
    lefts, rights = sc.render_stereo_set(CHESS, rig, poses)
    dl = [detect_board(im, CHESS) for im in lefts]
    dr = [detect_board(im, CHESS) for im in rights]
    return dl, dr


@pytest.fixture(scope="module")
def base_result(chess_set):
    dl, dr = chess_set
    return calibrate_stereo(dl, dr, (sc.IMG_W, sc.IMG_H))


# --------------------------------------------------------------------------- #
# printout
# --------------------------------------------------------------------------- #


def test_board_pdf_written_at_scale(tmp_path):
    path = save_board_pdf(CHESS, tmp_path / "board.pdf")
    assert path.exists() and path.stat().st_size > 5_000
    assert "chessboard" in spec_summary(CHESS)


def test_board_pdf_rejects_oversize():
    huge = ChessboardSpec(cols=30, rows=22, square_size=15.0)
    with pytest.raises(ValueError, match="exceeds"):
        save_board_pdf(huge, "never_written.pdf")


# --------------------------------------------------------------------------- #
# known-distance verification
# --------------------------------------------------------------------------- #


def test_verification_confirms_good_calibration(rig, chess_set, base_result):
    dl, dr = chess_set
    v = verify_known_distance(base_result.rig, dl[0], dr[0], CHESS)
    assert v.n_points == 63
    assert abs(v.scale_error) < 1e-3  # < 0.1% pitch error on the synthetic gate
    assert v.distance_rmse < 0.05  # mm
    assert v.plane_rms < 0.05  # flat board reconstructs flat


def test_verification_flags_bad_baseline(rig, chess_set, base_result):
    # A 2% baseline error must show up as ~2% scale error — the iDICs point:
    # reprojection RMS alone would NOT catch a mis-scaled calibration.
    dl, dr = chess_set
    r, t = base_result.rig.pose("R")
    bad_rig = dataclasses.replace(base_result.rig, extrinsics={("L", "R"): (r, t * 1.02)})
    v = verify_known_distance(bad_rig, dl[0], dr[0], CHESS)
    assert abs(v.scale_error) > 0.015


def test_verification_input_validation(rig, chess_set, base_result):
    dl, _dr = chess_set
    with pytest.raises(ValueError, match="not detected"):
        verify_known_distance(base_result.rig, dl[0], BoardDetection(ok=False, reason="x"), CHESS)
    with pytest.raises(ValueError, match="asymmetric"):
        verify_known_distance(
            base_result.rig,
            dl[0],
            dl[0],
            CircleGridSpec(cols=4, rows=5, spacing=10, asymmetric=True),
        )


# --------------------------------------------------------------------------- #
# bundle adjustment
# --------------------------------------------------------------------------- #


def _fx_err(rig_est, rig_gt) -> float:
    return abs(rig_est.cameras["L"].fx - rig_gt.cameras["L"].fx) / rig_gt.cameras["L"].fx


def test_bundle_keeps_gate_accuracy(rig, chess_set, base_result):
    dl, dr = chess_set
    new_rig, info = bundle_refine(dl, dr, base_result)
    assert info["rms_after"] <= info["rms_before"] + 1e-9
    assert info["n_views"] == 18
    assert _fx_err(new_rig, rig) < 5e-4
    assert abs(new_rig.cameras["L"].cx - rig.cameras["L"].cx) < 0.5
    r_gt, t_gt = rig.pose("R")
    r_e, t_e = new_rig.pose("R")
    assert abs(np.linalg.norm(t_e) - np.linalg.norm(t_gt)) < 0.05
    ang = np.degrees(np.arccos(np.clip((np.trace(r_e @ r_gt.T) - 1) / 2, -1, 1)))
    assert ang < 0.05


def test_bundle_robust_to_point_outliers(rig, chess_set):
    # Corrupt 5 individual corners in ONE left view by 8 px. The robust
    # per-point loss must hold the solve near truth.
    dl, dr = chess_set
    rng = np.random.default_rng(11)
    pts = dl[3].image_points.copy()
    idx = rng.choice(len(pts), 5, replace=False)
    pts[idx] += 8.0
    dl_bad = [*dl[:3], dataclasses.replace(dl[3], image_points=pts), *dl[4:]]

    base = calibrate_stereo(dl_bad, dr, (sc.IMG_W, sc.IMG_H), reject_rms=50.0)
    new_rig, _info = bundle_refine(dl_bad, dr, base)
    assert _fx_err(new_rig, rig) < 1e-3
    assert abs(new_rig.cameras["L"].cx - rig.cameras["L"].cx) < 1.0


def test_bundle_uses_mono_only_views(rig, chess_set, base_result):
    # Blind the right camera on 4 views: stereoCalibrate loses those pairs
    # entirely, but the bundle keeps their LEFT mono residuals.
    dl, dr = chess_set
    dr_holes = list(dr)
    for i in (2, 5, 9, 14):
        dr_holes[i] = BoardDetection(ok=False, reason="blinded")
    base = calibrate_stereo(dl, dr_holes, (sc.IMG_W, sc.IMG_H))
    new_rig, info = bundle_refine(dl, dr_holes, base)
    assert info["n_views"] == 18
    assert info["n_mono_views"] == 4
    assert _fx_err(new_rig, rig) < 5e-4


def test_bundle_input_validation(chess_set, base_result):
    dl, dr = chess_set
    with pytest.raises(ValueError, match="view counts differ"):
        bundle_refine(dl[:4], dr[:5], base_result)
    empty = [BoardDetection(ok=False, reason="x")] * 4
    with pytest.raises(ValueError, match="usable views"):
        bundle_refine(empty, empty, base_result)
