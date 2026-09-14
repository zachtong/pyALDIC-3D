"""The calibration checks judge a calibration against the board it was fitted with.

Found by the real-photo check of the calibration diagnostics (brief section
7.4, 2026-09-14): on two sets of hand-held dot-board photos the board, not the
lens, left most of the residual. Freeing the board points (release-object) cut
the per-view RMS three to four times. When the user optimises the board shape
(bundle adjustment) or uses the release-object solve, the checks must use the
refined board, or the lens-model check keeps blaming the lens for the board.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

import tests.synth_calib as sc
from al_dic_3d.calibration import BoardDetection
from al_dic_3d.calibration import pipeline as pl
from al_dic_3d.calibration.diagnostics import diagnose_calibration
from al_dic_3d.calibration.solve import calibrate_mono
from tests.test_calib_enhancements import CHESS, _analytic_detections, _warp_z

SIZE = (sc.IMG_W, sc.IMG_H)
EXTENT = ((CHESS.cols - 1) * CHESS.square_size, (CHESS.rows - 1) * CHESS.square_size)
WARP_MM = 0.5
NOISE_PX = 0.02


@pytest.fixture(scope="module")
def warped():
    """Views of a board warped by 0.5 mm, detected with the nominal flat lattice."""
    rig = sc.make_rig()
    obj = CHESS.object_points()
    poses = sc.board_poses(EXTENT, n=12)
    dl, dr = _analytic_detections(rig, poses, obj, WARP_MM, NOISE_PX, seed=5)
    board = obj.copy()
    board[:, 2] += _warp_z(obj, WARP_MM)
    return rig, dl, dr, board


def test_calibrate_mono_fits_a_non_planar_board_from_an_initial_guess(warped):
    rig, dl, _dr, board = warped
    curved = [replace(d, object_points=board) for d in dl]
    truth = rig.cameras["L"]
    mono = calibrate_mono(curved, SIZE, initial=replace(truth, fx=truth.fx * 1.01))
    assert mono.rms < 2 * NOISE_PX
    assert mono.intrinsics.fx == pytest.approx(truth.fx, rel=2e-3)
    fixed = calibrate_mono(curved, SIZE, fix_k3=True, initial=replace(truth, k3=0.3))
    assert fixed.intrinsics.k3 == 0.0


def test_diagnostics_use_the_board_shape_the_bundle_refined(warped, monkeypatch):
    rig, dl, dr, board = warped
    ids = np.arange(len(board), dtype=np.int64)

    def bundle(_left, _right, _base, **kwargs):
        assert kwargs["board_morphology"] is True
        info = {"rms_before": 1.0, "rms_after": NOISE_PX, "n_views": 12, "n_mono_views": 0,
                "board_points": board, "board_ids": ids, "board_z_range": WARP_MM}  # fmt: skip
        return rig, info  # the true rig and the true board shape

    monkeypatch.setattr(pl, "bundle_refine", bundle)
    run = pl.run_calibration(dl, dr, SIZE, options={"bundle": True, "board_morphology": True})
    for cam in ("L", "R"):
        assert run.diagnostics.cameras[cam].residual_rms_px < 2 * NOISE_PX
    flat = diagnose_calibration(rig, dl, dr, SIZE)  # the same rig against the flat lattice
    assert flat.cameras["L"].residual_rms_px > 5 * NOISE_PX


def test_a_bundle_without_board_shape_keeps_the_nominal_board(warped, monkeypatch):
    rig, dl, dr, _board = warped
    seen = {}
    real = pl.diagnose_calibration

    def diagnose(rig_, left, right, *args, **kwargs):
        seen["left"] = left
        return real(rig_, left, right, *args, **kwargs)

    monkeypatch.setattr(pl, "bundle_refine", lambda *_a, **_k: (rig, {
        "rms_before": 1.0, "rms_after": 0.5, "n_views": 12, "n_mono_views": 0}))  # fmt: skip
    monkeypatch.setattr(pl, "diagnose_calibration", diagnose)
    run = pl.run_calibration(dl, dr, SIZE, options={"bundle": True})
    assert all(a is b for a, b in zip(seen["left"], run.result.detections["L"], strict=True))


def test_release_object_solve_is_judged_with_its_refined_board(warped):
    _rig, dl, dr, _board = warped
    run = pl.run_calibration(dl, dr, SIZE, options={"release_object": True})
    mono = run.result.mono["L"]
    assert mono.method == "release_object"
    assert mono.board_points is not None and mono.board_points.shape == (CHESS.cols * CHESS.rows, 3)
    assert np.ptp(mono.board_points[:, 2]) > 0.2  # the warp is seen
    for cam in ("L", "R"):
        assert run.diagnostics.cameras[cam].residual_rms_px < 2 * NOISE_PX


def test_views_outside_the_refined_board_are_left_out():
    obj = CHESS.object_points()
    det = BoardDetection(ok=True, image_points=np.zeros((3, 2)), object_points=obj[:3],
                         ids=np.array([0, 1, 999]))  # fmt: skip
    out = pl.with_board([det], np.arange(len(obj)), obj + 1.0)
    assert not out[0].ok
