"""Offscreen tests of the D12 calibration dialogs (built-in + manual entry)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import numpy as np
import pytest

pytest.importorskip("PySide6")
cv2 = pytest.importorskip("cv2")

from al_dic_3d.calibration import ChessboardSpec, from_opencv_yaml  # noqa: E402
from al_dic_3d.gui.app import create_app  # noqa: E402
from al_dic_3d.gui.dialogs.calibration_dialog import CalibrationDialog  # noqa: E402
from al_dic_3d.gui.dialogs.manual_params_dialog import ManualParamsDialog  # noqa: E402
from tests import synth_calib as sc  # noqa: E402

SPEC = ChessboardSpec(cols=9, rows=7, square_size=12.0)


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


@pytest.fixture(scope="module")
def dataset(tmp_path_factory):
    out = tmp_path_factory.mktemp("dlg_imgs")
    rig = sc.make_rig()
    extent = ((SPEC.cols - 1) * SPEC.square_size, (SPEC.rows - 1) * SPEC.square_size)
    poses = sc.board_poses(extent, n=8)
    lefts, rights = sc.render_stereo_set(SPEC, rig, poses)
    for k, (im_l, im_r) in enumerate(zip(lefts, rights, strict=True)):
        cv2.imwrite(str(out / f"L_{k:02d}.png"), np.clip(im_l * 256, 0, 65535).astype(np.uint16))
        cv2.imwrite(str(out / f"R_{k:02d}.png"), np.clip(im_r * 256, 0, 65535).astype(np.uint16))
    return out, rig


def _run_solve(dlg: CalibrationDialog) -> None:
    """Kick off the worker and pump the event loop until it reports back."""
    from PySide6.QtCore import QCoreApplication

    dlg._start(recalibrate=False)
    assert dlg._worker is not None
    assert dlg._worker.wait(120_000)
    QCoreApplication.processEvents()  # deliver the queued finished_ok signal


def test_board_form_visibility_follows_family(qapp):
    dlg = CalibrationDialog()
    by_id = {dlg._board_combo.itemData(i): i for i in range(dlg._board_combo.count())}
    dlg._board_combo.setCurrentIndex(by_id["chessboard"])
    assert not dlg._spacing.isVisibleTo(dlg) and dlg._square.isVisibleTo(dlg)
    dlg._board_combo.setCurrentIndex(by_id["charuco"])
    assert dlg._marker.isVisibleTo(dlg) and dlg._legacy.isVisibleTo(dlg)
    dlg._board_combo.setCurrentIndex(by_id["coded"])
    assert dlg._spacing.isVisibleTo(dlg) and not dlg._square.isVisibleTo(dlg)
    assert dlg._ecc.isVisibleTo(dlg)


def test_calibration_dialog_end_to_end(qapp, dataset, tmp_path, monkeypatch):
    imgdir, rig = dataset
    dlg = CalibrationDialog()
    dlg._files_l = sorted(str(p) for p in imgdir.glob("L_*.png"))
    dlg._files_r = sorted(str(p) for p in imgdir.glob("R_*.png"))
    dlg._refresh_table()
    assert dlg._table.topLevelItemCount() == 8

    _run_solve(dlg)
    assert dlg._result is not None, dlg._status.text()
    assert dlg._result.n_pairs_used >= 6
    assert dlg._accept_btn.isEnabled()
    assert "RMS" in dlg._result_lbl.text()
    # table shows per-pair numbers and the bars widget has the data
    assert dlg._table.topLevelItem(0).text(4)
    assert len(dlg._bars._pairs) == 8

    # recalibrate path reuses cached detections (fast, no re-detect)
    _run_solve_recal(dlg)
    assert dlg._result is not None

    # accept -> YAML written to the chosen path and loadable by the importer
    target = tmp_path / "accepted.yml"
    monkeypatch.setattr(
        "PySide6.QtWidgets.QFileDialog.getSaveFileName",
        staticmethod(lambda *_a, **_k: (str(target), "")),
    )
    dlg._on_accept()
    assert dlg.saved_path is not None and target.exists()
    back = from_opencv_yaml(target)
    assert abs(back.cameras["L"].fx - rig.cameras["L"].fx) / rig.cameras["L"].fx < 0.01


def _run_solve_recal(dlg: CalibrationDialog) -> None:
    from PySide6.QtCore import QCoreApplication

    dlg._start(recalibrate=True)
    assert dlg._worker.wait(120_000)
    QCoreApplication.processEvents()


def test_calibration_dialog_rejects_unbalanced_sets(qapp):
    dlg = CalibrationDialog()
    dlg._files_l = ["a.png", "b.png", "c.png"]
    dlg._files_r = ["a.png"]
    dlg._start(recalibrate=False)
    assert dlg._worker is None  # refused before spawning a worker
    assert dlg._status.text()


def test_manual_dialog_builds_rig_and_saves(qapp, tmp_path, monkeypatch):
    dlg = ManualParamsDialog()
    for spins in (dlg._left[1], dlg._right[1]):
        spins["fx"].setValue(1500.0)
        spins["fy"].setValue(1510.0)
        spins["cx"].setValue(320.0)
        spins["cy"].setValue(256.0)
        spins["k1"].setValue(-0.05)
    dlg._angles[1].setValue(12.0)  # Ry
    dlg._trans[0].setValue(-100.0)

    rig = dlg._rig()
    assert rig.cameras["L"].fx == 1500.0
    r, t = rig.pose("R")
    assert abs(np.degrees(np.arccos(np.clip((np.trace(r) - 1) / 2, -1, 1))) - 12.0) < 1e-6
    assert np.allclose(t, [-100.0, 0.0, 0.0])

    target = tmp_path / "manual.yml"
    monkeypatch.setattr(
        "PySide6.QtWidgets.QFileDialog.getSaveFileName",
        staticmethod(lambda *_a, **_k: (str(target), "")),
    )
    dlg._on_save()
    assert dlg.saved_path is not None
    back = from_opencv_yaml(target)
    assert back.cameras["R"].k1 == pytest.approx(-0.05)
    assert back.pose("R")[1][0] == pytest.approx(-100.0)


def test_manual_dialog_blocks_zero_baseline(qapp, monkeypatch):
    dlg = ManualParamsDialog()
    called = {"n": 0}
    monkeypatch.setattr(
        "PySide6.QtWidgets.QFileDialog.getSaveFileName",
        staticmethod(lambda *_a, **_k: called.__setitem__("n", called["n"] + 1) or ("", "")),
    )
    dlg._on_save()  # T = 0 -> refuse before the file dialog
    assert called["n"] == 0 and dlg.saved_path is None


def test_preview_and_bundle_and_verify(qapp, dataset, tmp_path, monkeypatch):
    imgdir, rig = dataset
    dlg = CalibrationDialog()
    dlg._files_l = sorted(str(p) for p in imgdir.glob("L_*.png"))
    dlg._files_r = sorted(str(p) for p in imgdir.glob("R_*.png"))
    dlg._refresh_table()
    dlg._bundle.setChecked(True)
    _run_solve(dlg)
    assert dlg._result is not None, dlg._status.text()
    assert "Bundle adjustment" in dlg._result_lbl.text()

    # row selection renders the L|R overlay preview
    dlg._table.setCurrentItem(dlg._table.topLevelItem(0))
    assert dlg._preview.pixmap() is not None and not dlg._preview.pixmap().isNull()

    # known-distance verification against the first (in-set) pair
    picks = iter([dlg._files_l[0], dlg._files_r[0]])
    monkeypatch.setattr(
        "PySide6.QtWidgets.QFileDialog.getOpenFileName",
        staticmethod(lambda *_a, **_k: (next(picks), "")),
    )
    dlg._on_verify()
    assert "scale error" in dlg._verify_lbl.text()

    # 1:1 board PDF
    target = tmp_path / "board.pdf"
    monkeypatch.setattr(
        "PySide6.QtWidgets.QFileDialog.getSaveFileName",
        staticmethod(lambda *_a, **_k: (str(target), "")),
    )
    dlg._on_print_board()
    assert target.exists() and target.stat().st_size > 5_000


def test_morphology_and_detection_persistence(qapp, dataset, tmp_path, monkeypatch):
    imgdir, _rig = dataset
    dlg = CalibrationDialog()
    dlg._files_l = sorted(str(p) for p in imgdir.glob("L_*.png"))
    dlg._files_r = sorted(str(p) for p in imgdir.glob("R_*.png"))
    dlg._refresh_table()
    dlg._bundle.setChecked(True)
    assert dlg._morph.isEnabled()  # gated on the bundle checkbox
    dlg._morph.setChecked(True)
    _run_solve(dlg)
    assert dlg._result is not None, dlg._status.text()
    assert "z-range" in dlg._result_lbl.text()  # board flatness reported
    assert dlg._table.topLevelItem(0).text(5)  # Max E column filled

    # save detections, load them into a FRESH dialog, re-solve without images
    det_file = tmp_path / "det.npz"
    monkeypatch.setattr(
        "PySide6.QtWidgets.QFileDialog.getSaveFileName",
        staticmethod(lambda *_a, **_k: (str(det_file), "")),
    )
    dlg._on_save_detections()
    assert det_file.exists()

    dlg2 = CalibrationDialog()
    monkeypatch.setattr(
        "PySide6.QtWidgets.QFileDialog.getOpenFileName",
        staticmethod(lambda *_a, **_k: (str(det_file), "")),
    )
    dlg2._on_load_detections()
    assert dlg2._detections is not None and dlg2._recal_btn.isEnabled()
    _run_solve_recal(dlg2)
    assert dlg2._result is not None and dlg2._result.n_pairs_used >= 6


def test_sidebar_has_three_entry_buttons(qapp):
    from al_dic_3d.gui.main_window import MainWindow3D

    win = MainWindow3D()
    left = win._left
    assert left._calibrate_btn.text()
    assert left._calib_btn.text()
    assert left._manual_btn.text()
    # the built-in calibrator is the visually primary action
    assert left._calibrate_btn.property("class") == "btn-primary"
