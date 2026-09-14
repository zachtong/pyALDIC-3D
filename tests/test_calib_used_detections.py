"""WP0: the stereo result exposes the detections its final solve used.

For dot targets ``calibrate_stereo`` subtracts the modelled eccentricity bias
from its own copies of the dot centres and solves on those. Checks that
describe the final calibration (diagnostics, residuals, bundle adjustment)
must see the same points, so they are returned with the result.
"""

from __future__ import annotations

import numpy as np

import tests.synth_calib as sc
import tests.synth_calib_points as sp
from al_dic_3d.calibration import (
    BoardDetection,
    ChessboardSpec,
    CircleGridSpec,
    calibrate_mono,
    calibrate_stereo,
)

CHESS = ChessboardSpec(cols=9, rows=7, square_size=12.0)
DOTS = CircleGridSpec(cols=9, rows=7, spacing=12.0, dot_diameter=6.0)
SIZE = (sc.IMG_W, sc.IMG_H)


def _views(spec):
    rig = sc.make_rig()
    pts = spec.object_points()
    poses = sc.board_poses((float(np.ptp(pts[:, 0])), float(np.ptp(pts[:, 1]))), n=12)
    left = sp.detections(spec, rig, poses, "L", noise_px=0.02, seed=1)
    right = sp.detections(spec, rig, poses, "R", noise_px=0.02, seed=2)
    return left, right


def test_chessboard_detections_are_returned_unchanged():
    left, right = _views(CHESS)
    result = calibrate_stereo(left, right, SIZE)
    assert set(result.detections) == {"L", "R"}
    assert result.detections["L"] == tuple(left)
    assert result.detections["R"] == tuple(right)


def test_dot_detections_are_the_eccentricity_corrected_ones():
    left, right = _views(DOTS)
    # A failed view must keep its place in the index-paired lists.
    left[3] = BoardDetection(ok=False, reason="test: not detected")
    result = calibrate_stereo(left, right, SIZE, dot_radius_mm=DOTS.dot_mm / 2.0)
    used_l = result.detections["L"]
    assert len(used_l) == len(left) and not used_l[3].ok
    moved = [
        float(np.abs(used.image_points - orig.image_points).max())
        for used, orig in zip(used_l, left, strict=True)
        if orig.ok
    ]
    assert min(moved) > 1e-4  # every usable view was corrected
    # They are what the final mono solve saw: re-solving reproduces it (to the
    # last bits; OpenCV's threaded sums are not bit-reproducible).
    for cam in ("L", "R"):
        again = calibrate_mono(result.detections[cam], SIZE)
        final = result.mono[cam].intrinsics
        np.testing.assert_allclose(again.intrinsics.K, final.K, rtol=1e-9)
        np.testing.assert_allclose(  # k3 is ill-conditioned: looser
            again.intrinsics.dist_coeffs, final.dist_coeffs, rtol=1e-5, atol=1e-9
        )
        np.testing.assert_array_equal(again.view_indices, result.mono[cam].view_indices)


def test_the_new_field_defaults_for_older_constructors():
    from dataclasses import fields

    from al_dic_3d.calibration.solve import StereoResult

    field = {f.name: f for f in fields(StereoResult)}["detections"]
    assert field.default_factory() == {}


# ---- both entry points bundle-adjust on the points the solve used (E4) ------------
#
# On the stereo_gt circle grid, bundle adjustment on the uncorrected centres
# brought the scale bias back (length error -5.65 +/- 0.40 ue against -0.42 for
# the corrected stereo solve); on result.detections it stays at -0.62 ue.


def _capture_bundle(monkeypatch) -> dict:
    import al_dic_3d.calibration as calib

    seen: dict = {}
    real_solve = calib.calibrate_stereo

    def solve(*args, **kwargs):
        seen["result"] = real_solve(*args, **kwargs)
        return seen["result"]

    def bundle(left, right, base, **_kwargs):
        seen["left"], seen["right"] = list(left), list(right)
        return base.rig, {"rms_before": 0.0, "rms_after": 0.0, "n_views": 0, "n_mono_views": 0}

    monkeypatch.setattr(calib, "calibrate_stereo", solve)
    monkeypatch.setattr(calib, "bundle_refine", bundle)
    return seen


def _same_objects(got, want) -> bool:
    return len(got) == len(want) and all(a is b for a, b in zip(got, want, strict=True))


def test_cli_bundle_adjusts_on_the_corrected_detections(tmp_path, monkeypatch):
    import al_dic_3d.calibration as calib
    import al_dic_3d.pathsafe as pathsafe
    from al_dic_3d.cli import main

    left, right = _views(DOTS)
    queue = iter([*left, *right])  # the CLI detects every left image, then every right one
    monkeypatch.setattr(calib, "detect_board", lambda _img, _spec: next(queue))
    blank = np.zeros((SIZE[1], SIZE[0]), np.uint8)
    monkeypatch.setattr(pathsafe, "imread_unicode", lambda _f: blank)
    for i in range(len(left)):
        (tmp_path / f"L_{i:02d}.png").touch()
        (tmp_path / f"R_{i:02d}.png").touch()
    seen = _capture_bundle(monkeypatch)
    code = main(
        [
            "calibrate",
            "--left", str(tmp_path / "L_*.png"),
            "--right", str(tmp_path / "R_*.png"),
            "--output", str(tmp_path / "rig.yml"),
            "--board", "circles", "--cols", "9", "--rows", "7",
            "--spacing", "12", "--dot", "6", "--bundle",
        ]
    )  # fmt: skip
    assert code == 0
    assert _same_objects(seen["left"], seen["result"].detections["L"])
    assert _same_objects(seen["right"], seen["result"].detections["R"])


def test_gui_worker_bundle_adjusts_on_the_corrected_detections(monkeypatch):
    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    import pytest

    pytest.importorskip("PySide6")
    import al_dic_3d.calibration as calib
    from al_dic_3d.gui.app import create_app
    from al_dic_3d.gui.dialogs import calibration_support

    create_app([])
    left, right = _views(DOTS)
    seen = _capture_bundle(monkeypatch)
    # The worker module imported calibrate_stereo by name at import time.
    monkeypatch.setattr(calibration_support, "calibrate_stereo", calib.calibrate_stereo)
    options = dict(zero_tangent=True, fix_k3=False, dot_radius_mm=DOTS.dot_mm / 2.0, bundle=True)
    worker = calibration_support.CalibWorker(
        [], [], DOTS, options, detections=(left, right), image_size=SIZE
    )
    errors: list[str] = []
    worker.failed.connect(errors.append)
    worker.run()  # synchronously, on this thread
    assert not errors
    assert _same_objects(seen["left"], seen["result"].detections["L"])
    assert _same_objects(seen["right"], seen["result"].detections["R"])
