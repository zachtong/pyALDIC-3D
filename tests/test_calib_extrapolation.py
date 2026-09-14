"""WP1: the extrapolation check (calibration diagnostics brief, section 6).

Beyond the radius the calibration points reach (``r_cover``) the fitted lens
distortion is an extrapolation. Two equally good fits of the same views, k3
free and k3 fixed, disagree there when the data do not determine the
projection; ``EXTRAPOLATION_UNDETERMINED`` reports it.

Synthetic points through a known wide-angle camera (true k3 = 0) with 0.03 px
noise: boards kept in the image centre must raise the finding, boards that
reach all four corners must not.
"""

from __future__ import annotations

import numpy as np
import pytest

import tests.synth_calib_points as sp
from al_dic_3d.calibration import CameraIntrinsics, ChessboardSpec, StereoRig
from al_dic_3d.calibration.diagnostics import (
    EXTRAPOLATION_THRESHOLD_PX,
    EXTRAPOLATION_UNDETERMINED,
    CameraDiagnostics,
    DiagnosticThresholds,
    alternative_model_disagreement,
    diagnose_calibration,
    diagnose_camera,
)

W, H = 800, 600
CAM = CameraIntrinsics(
    fx=700.0, fy=700.0, cx=(W - 1) / 2, cy=(H - 1) / 2, k1=-0.25, k2=0.08, width=W, height=H
)
BOARD = ChessboardSpec(cols=9, rows=7, square_size=20.0)
EXTENT = (160.0, 120.0)
SIZE = (W, H)
NOISE = 0.03


def _mono_rig(cam: CameraIntrinsics = CAM) -> StereoRig:
    return StereoRig(cameras={"L": cam}, extrinsics={})


def _central_poses():
    """The board stays inside the central half of the image."""
    angles = [(0, 0, 0), (25, 0, 5), (-25, 0, -5), (0, 25, 10), (0, -25, -10),
              (18, 18, 0), (-18, -18, 15), (18, -18, -15), (-18, 18, 0), (0, 0, 30)]  # fmt: skip
    return [sp.pose_at(EXTENT, (0.0, 0.0, 1000.0), a) for a in angles]


def _corner_poses():
    """The central views plus close views pushed into each image corner.

    Reaches 98 % of the corner radius; the free/fixed k3 disagreement outside
    is then 0.02-0.06 px over three noise seeds (0.6-1.6 px at 68 % coverage).
    """
    corners = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for z, tilt in ((520.0, 12.0), (600.0, -12.0)):
                centre = (sx * 0.85 * z * (W / 2) / CAM.fx, sy * 0.85 * z * (H / 2) / CAM.fy, z)
                corners.append(sp.pose_at(EXTENT, centre, (tilt * sy, -tilt * sx, 0.0)))
    return _central_poses() + corners


def _dets(poses, seed=0):
    return sp.detections(BOARD, _mono_rig(), poses, "L", noise_px=NOISE, seed=seed)


def test_board_kept_in_the_centre_is_flagged():
    diag = diagnose_camera("L", CAM, _dets(_central_poses()), SIZE)
    assert isinstance(diag.camera_diagnostics, CameraDiagnostics)
    d = diag.camera_diagnostics
    assert d.cover_ratio < 0.5
    assert d.disagreement_inside_px < 0.05  # both fits agree where there are data
    assert d.disagreement_outside_px > EXTRAPOLATION_THRESHOLD_PX
    codes = [f.code for f in diag.findings]
    assert EXTRAPOLATION_UNDETERMINED in codes
    finding = next(f for f in diag.findings if f.code == EXTRAPOLATION_UNDETERMINED)
    assert finding.severity == "warning" and finding.camera == "L"
    assert finding.values["disagreement_outside_px"] == pytest.approx(d.disagreement_outside_px)
    assert finding.values["cover_ratio"] == pytest.approx(d.cover_ratio)
    assert "corner" in finding.message_en and "k3" in finding.message_en


def test_board_reaching_the_corners_is_not_flagged():
    diag = diagnose_camera("L", CAM, _dets(_corner_poses()), SIZE)
    d = diag.camera_diagnostics
    assert d.cover_ratio > 0.8
    assert d.disagreement_outside_px < EXTRAPOLATION_THRESHOLD_PX
    assert EXTRAPOLATION_UNDETERMINED not in [f.code for f in diag.findings]


def test_thresholds_are_overridable():
    dets = _dets(_corner_poses())
    strict = DiagnosticThresholds(extrapolation_px=0.0)
    strict = diagnose_camera("L", CAM, dets, SIZE, thresholds=strict)
    assert EXTRAPOLATION_UNDETERMINED in [f.code for f in strict.findings]
    lax = DiagnosticThresholds(extrapolation_px=1e9)
    lax = diagnose_camera("L", CAM, _dets(_central_poses()), SIZE, thresholds=lax)
    assert EXTRAPOLATION_UNDETERMINED not in [f.code for f in lax.findings]


def test_the_user_choice_of_k3_does_not_change_what_is_compared():
    dets = _dets(_central_poses())
    free = diagnose_camera("L", CAM, dets, SIZE, fix_k3=False).camera_diagnostics
    fixed = diagnose_camera("L", CAM, dets, SIZE, fix_k3=True).camera_diagnostics
    assert free.disagreement_outside_px == pytest.approx(fixed.disagreement_outside_px, rel=1e-6)
    assert free.chosen_model == "k3 free" and fixed.chosen_model == "k3 fixed"


def test_with_k3_fixed_the_advice_is_not_to_fix_k3():
    # The comparison stays the same (above); the advice must fit the user's choice.
    diag = diagnose_camera("L", CAM, _dets(_central_poses()), SIZE, fix_k3=True)
    finding = next(f for f in diag.findings if f.code == EXTRAPOLATION_UNDETERMINED)
    assert finding.values["chosen_model"] == "k3 fixed"
    assert "With k3 fixed" in finding.message_en
    assert "fix k3." not in finding.message_en


def test_the_solve_own_fit_is_reused(monkeypatch):
    from al_dic_3d.calibration import calibrate_mono
    from al_dic_3d.calibration import diagnostics as diag_mod

    dets = _dets(_central_poses())
    own = calibrate_mono(dets, SIZE)
    calls = []
    real = diag_mod.calibrate_mono
    counting = lambda *a, **k: calls.append(k) or real(*a, **k)  # noqa: E731
    monkeypatch.setattr(diag_mod, "calibrate_mono", counting)
    diagnose_camera("L", own.intrinsics, dets, SIZE, mono=own)
    assert len(calls) == 1 and calls[0]["fix_k3"] is True  # only the alternative fit


def test_too_few_views_skip_the_check_without_failing():
    diag = diagnose_camera("L", CAM, _dets(_central_poses()[:2]), SIZE)
    d = diag.camera_diagnostics
    assert np.isnan(d.disagreement_outside_px)
    assert [f.code for f in diag.findings] == ["EXTRAPOLATION_CHECK_SKIPPED"]
    assert diag.findings[0].severity == "info"


# ---- the disagreement construction and its degenerate cases -------------------------


def _other(k3: float) -> CameraIntrinsics:
    from dataclasses import replace

    return replace(CAM, k3=k3)


def test_identical_models_do_not_disagree():
    out = alternative_model_disagreement(CAM, CAM, SIZE, r_cover=0.3)
    assert out.inside_px == pytest.approx(0.0, abs=1e-9)
    assert out.outside_px == pytest.approx(0.0, abs=1e-9)
    assert out.affine_fit == "inside r_cover"


def test_a_k3_difference_shows_outside_not_inside():
    out = alternative_model_disagreement(CAM, _other(0.5), SIZE, r_cover=0.2)
    assert out.inside_px < 0.05 * out.outside_px
    assert out.outside_px > 1.0


def test_nothing_outside_when_the_points_reach_the_corners():
    out = alternative_model_disagreement(CAM, _other(0.5), SIZE, r_cover=10.0)
    assert np.isnan(out.outside_px) and np.isfinite(out.inside_px)


def test_too_few_nodes_inside_fall_back_to_the_whole_sensor():
    out = alternative_model_disagreement(CAM, _other(0.5), SIZE, r_cover=1e-4)
    assert out.affine_fit == "whole sensor"
    assert np.isfinite(out.outside_px)


def test_no_coverage_radius_means_no_numbers():
    out = alternative_model_disagreement(CAM, _other(0.5), SIZE, r_cover=float("nan"))
    assert np.isnan(out.inside_px) and np.isnan(out.outside_px)
    assert out.affine_fit == "not computed"


def test_stereo_entry_point_reports_both_cameras():
    from al_dic_3d.calibration import calibrate_stereo
    from tests import synth_calib as sc

    rig = sc.make_rig()
    spec = ChessboardSpec(cols=9, rows=7, square_size=12.0)
    poses = sc.board_poses((96.0, 72.0), n=12)
    left = sp.detections(spec, rig, poses, "L", noise_px=0.02, seed=1)
    right = sp.detections(spec, rig, poses, "R", noise_px=0.02, seed=2)
    result = calibrate_stereo(left, right, (sc.IMG_W, sc.IMG_H))
    diag = diagnose_calibration(
        result.rig, result.detections["L"], result.detections["R"], (sc.IMG_W, sc.IMG_H),
        mono=result.mono,
    )  # fmt: skip
    assert set(diag.cameras) == {"L", "R"}
    for d in diag.cameras.values():
        assert 0.0 < d.cover_ratio <= 1.5 and d.n_points > 0
    assert diag.seconds > 0.0
    assert all(f.camera in ("L", "R") for f in diag.findings)
