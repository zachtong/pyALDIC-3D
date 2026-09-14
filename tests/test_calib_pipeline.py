"""WP6: one calibration pipeline for the CLI and the GUI, and where its findings go.

``run_calibration`` runs the solve, the optional bundle adjustment, the
diagnostics and the summary once for both entry points, so no check can be
forgotten in one of them (calibration diagnostics brief, section 5.2). The
numbers reach ``summarize`` and the saved YAML as ``meta_*`` nodes, which the
importer ignores (section 5.3).
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

import tests.synth_calib as sc
import tests.synth_calib_points as sp
from al_dic_3d.calibration import ChessboardSpec, StereoRig, to_opencv_yaml
from al_dic_3d.calibration import pipeline as pl
from al_dic_3d.calibration.diagnostics import (
    EXTRAPOLATION_UNDETERMINED,
    coverage_outline,
    diagnose_calibration,
)
from al_dic_3d.calibration.geometry import undistort_points
from tests.test_calib_extrapolation import BOARD as WIDE_BOARD
from tests.test_calib_extrapolation import CAM, _central_poses, _corner_poses
from tests.test_calib_extrapolation import SIZE as WIDE_SIZE

CHESS = ChessboardSpec(cols=9, rows=7, square_size=12.0)
SIZE = (sc.IMG_W, sc.IMG_H)
KEYS = (
    "r_cover", "r_corner", "cover_ratio", "extrapolation_disagreement_px",
    "residual_excess", "residual_field",
)  # fmt: skip


def _stereo_views():
    rig = sc.make_rig()
    poses = sc.board_poses((96.0, 72.0), n=12)
    left = sp.detections(CHESS, rig, poses, "L", noise_px=0.02, seed=1)
    right = sp.detections(CHESS, rig, poses, "R", noise_px=0.02, seed=2)
    return left, right


def wide_stereo(poses, seed: int = 0):
    """Two copies of the wide-angle test camera, 60 mm apart."""
    rig = StereoRig(
        cameras={"L": CAM, "R": CAM},
        extrinsics={("L", "R"): (np.eye(3), np.array([-60.0, 0.0, 0.0]))},
    )
    left = sp.detections(WIDE_BOARD, rig, poses, "L", noise_px=0.03, seed=seed)
    right = sp.detections(WIDE_BOARD, rig, poses, "R", noise_px=0.03, seed=seed + 1)
    return left, right


def test_run_calibration_returns_the_solve_diagnostics_and_summary():
    left, right = _stereo_views()
    run = pl.run_calibration(left, right, SIZE, options={})
    assert set(run.diagnostics.cameras) == {"L", "R"}
    assert run.bundle_info is None
    for cam in ("left", "right"):
        for key in KEYS:
            assert f"{key}_{cam}" in run.stats
    assert run.stats["r_cover_left"] == pytest.approx(run.diagnostics.cameras["L"].r_cover)
    assert "rms_px" in run.stats and "coverage_left" in run.stats  # the existing keys stay


def test_bundle_adjustment_is_diagnosed_on_the_final_rig(monkeypatch):
    left, right = _stereo_views()
    seen: dict = {}
    real_diagnose = pl.diagnose_calibration

    def bundle(dl, dr, base, **_kwargs):
        seen["bundle_left"] = list(dl)
        shifted = replace(base.rig.cameras["L"], fx=1234.5)
        rig = StereoRig(cameras={"L": shifted, "R": base.rig.cameras["R"]},
                        extrinsics=base.rig.extrinsics)  # fmt: skip
        return rig, {"rms_before": 1.0, "rms_after": 0.5, "n_views": 12, "n_mono_views": 0}

    def diagnose(rig, *args, **kwargs):
        seen["rig"] = rig
        return real_diagnose(rig, *args, **kwargs)

    monkeypatch.setattr(pl, "bundle_refine", bundle)
    monkeypatch.setattr(pl, "diagnose_calibration", diagnose)
    run = pl.run_calibration(left, right, SIZE, options={"bundle": True})
    assert all(a is b for a, b in zip(seen["bundle_left"], run.result.detections["L"], strict=True))
    assert seen["rig"].cameras["L"].fx == 1234.5 and run.result.rig.cameras["L"].fx == 1234.5
    assert run.bundle_info["rms_after"] == 0.5 and run.stats["ba_rms_after"] == 0.5


def test_findings_reach_the_summary_as_codes():
    left, right = wide_stereo(_central_poses())
    run = pl.run_calibration(left, right, WIDE_SIZE, options={})
    codes = [f"{f.code}:{f.camera}" for f in run.diagnostics.findings]
    assert f"{EXTRAPOLATION_UNDETERMINED}:L" in codes
    assert run.stats["findings"] == ";".join(codes)


def test_the_saved_yaml_carries_the_diagnostics_as_meta_nodes(tmp_path):
    import cv2

    left, right = _stereo_views()
    run = pl.run_calibration(left, right, SIZE, options={})
    plain = to_opencv_yaml(run.result.rig, tmp_path / "plain.yml")
    rich = to_opencv_yaml(run.result.rig, tmp_path / "rich.yml", meta=run.diagnostics.summary())
    fs_plain = cv2.FileStorage(str(plain), cv2.FILE_STORAGE_READ)
    fs_rich = cv2.FileStorage(str(rich), cv2.FILE_STORAGE_READ)
    try:
        for name in fs_plain.root().keys():  # the calibration itself is unchanged
            np.testing.assert_array_equal(fs_plain.getNode(name).mat(), fs_rich.getNode(name).mat())
        assert fs_rich.getNode("meta_r_cover_left").real() == pytest.approx(
            run.diagnostics.cameras["L"].r_cover, rel=1e-9
        )
        assert fs_rich.getNode("meta_findings").isString()
    finally:
        fs_plain.release()
        fs_rich.release()
    from al_dic_3d.calibration import from_opencv_yaml

    assert from_opencv_yaml(rich).cameras["L"].fx == run.result.rig.cameras["L"].fx


def test_summary_marks_missing_numbers_as_nan():
    left, right = wide_stereo(_corner_poses())
    diag = diagnose_calibration(
        StereoRig(cameras={"L": CAM, "R": CAM}, extrinsics={}), left[:2], right, WIDE_SIZE
    )
    summary = diag.summary()
    assert np.isnan(summary["extrapolation_disagreement_px_left"])
    assert summary["findings"].startswith("EXTRAPOLATION_CHECK_SKIPPED:L")


def test_the_covered_radius_outline_lies_on_that_radius():
    outline = coverage_outline(CAM, 0.3)
    xy = undistort_points(outline, CAM)
    np.testing.assert_allclose(np.hypot(xy[:, 0], xy[:, 1]), 0.3, rtol=1e-6)
    assert np.all((outline >= 0) & (outline <= np.array(WIDE_SIZE) - 1))
    assert coverage_outline(CAM, float("nan")).shape == (0, 2)
