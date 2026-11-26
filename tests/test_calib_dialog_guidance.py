"""The calibration dialog helps a new user get a chessboard calibration right.

Offscreen, without image files: ``detect_files`` is replaced by a stand-in
returning point-level synthetic detections with chosen image sizes.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

from dataclasses import replace  # noqa: E402

import pytest  # noqa: E402

pytest.importorskip("PySide6")
pytest.importorskip("cv2")

from al_dic.gui.theme import COLORS  # noqa: E402

from al_dic_3d.calibration import BoardDetection, FileDetections  # noqa: E402
from al_dic_3d.gui.app import create_app  # noqa: E402
from al_dic_3d.gui.dialogs.calibration_dialog import CalibrationDialog  # noqa: E402
from tests.test_calib_image_sizes import SIZE_L, SIZE_R, _two_resolution_views  # noqa: E402

# conftest stubs the discard question for leaked dialogs; the tests of the
# question itself put the real one back.
_REAL_CONFIRM_DISCARD = CalibrationDialog._confirm_discard
_NOT_FOUND = BoardDetection(ok=False, method="sb", reason="chessboard not found")


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


def _fake_detect(monkeypatch, left, right, sizes_l, sizes_r):
    import al_dic_3d.calibration as calib

    detections = [*left, *right]
    sizes = [*sizes_l, *sizes_r]

    def fake(paths, _spec, *, workers=None, on_result=None) -> FileDetections:
        assert len(paths) == len(detections)
        for k, det in enumerate(detections):
            if on_result is not None:
                on_result(k, det)
        return FileDetections(tuple(detections), tuple(sizes))

    monkeypatch.setattr(calib, "detect_files", fake)


def _dialog(n: int, tmp_path) -> CalibrationDialog:
    dlg = CalibrationDialog()
    dlg._files_l = [str(tmp_path / f"L_{k:02d}.png") for k in range(n)]
    dlg._files_r = [str(tmp_path / f"R_{k:02d}.png") for k in range(n)]
    dlg._refresh_table()
    return dlg


def _run(dlg: CalibrationDialog, *, recalibrate: bool = False) -> None:
    from PySide6.QtCore import QCoreApplication

    dlg._start(recalibrate=recalibrate)
    assert dlg._worker is not None, dlg._status.text()
    assert dlg._worker.wait(120_000)
    QCoreApplication.processEvents()  # deliver the queued signals


def _solved(monkeypatch, tmp_path, sizes=(SIZE_L, SIZE_R), left=None, right=None):
    _truth, views_l, views_r = _two_resolution_views()
    left = views_l if left is None else left
    right = views_r if right is None else right
    _fake_detect(monkeypatch, left, right, [sizes[0]] * len(left), [sizes[1]] * len(right))
    dlg = _dialog(len(left), tmp_path)
    _run(dlg)
    assert dlg._result is not None, dlg._status.text()
    return dlg


def _select_board(dlg: CalibrationDialog, board: str) -> None:
    by_id = {dlg._board_combo.itemData(i): i for i in range(dlg._board_combo.count())}
    dlg._board_combo.setCurrentIndex(by_id[board])


# ---- item 1: the board spec is remembered, the board distance is shown ------------


def test_the_board_spec_is_remembered_between_sessions(qapp):
    dlg = CalibrationDialog()
    _select_board(dlg, "charuco")
    dlg._cols.setValue(11)
    dlg._rows.setValue(8)
    dlg._square.setValue(15.0)
    dlg._marker.setValue(11.0)
    dlg._legacy.setChecked(True)
    dlg._remember_board()

    again = CalibrationDialog()
    assert again._board_combo.currentData() == "charuco"
    assert (again._cols.value(), again._rows.value()) == (11, 8)
    assert again._square.value() == pytest.approx(15.0)
    assert again._marker.value() == pytest.approx(11.0)
    assert again._legacy.isChecked()


def test_starting_a_calibration_remembers_the_board(qapp, tmp_path, monkeypatch):
    _fake_detect(monkeypatch, [_NOT_FOUND] * 6, [_NOT_FOUND] * 6, [SIZE_L] * 6, [SIZE_L] * 6)
    dlg = _dialog(6, tmp_path)
    dlg._square.setValue(10.0)
    _run(dlg)
    assert CalibrationDialog()._square.value() == pytest.approx(10.0)


def test_unreadable_settings_leave_the_defaults(qapp):
    from al_dic_3d.gui import persistence

    persistence.set_group_values("calibration_board", {"cols": "many", "board": "nonsense"})
    dlg = CalibrationDialog()
    assert dlg._board_combo.currentData() == "chessboard" and dlg._cols.value() == 9


def test_the_result_shows_the_board_distance_from_the_left_camera(qapp, tmp_path, monkeypatch):
    dlg = _solved(monkeypatch, tmp_path)
    lo, hi = dlg._stats["distance_min"], dlg._stats["distance_max"]
    assert 300.0 < lo < hi < 700.0  # the synthetic poses sit 410-550 mm away
    expected = dlg.tr("Board distance from the left camera {0:.0f}-{1:.0f} mm").format(lo, hi)
    assert expected in dlg._result_lbl.text().splitlines()


# ---- item 2: a failed calibration says what to check --------------------------------


def test_board_found_nowhere_names_the_inner_corners_and_fills_the_table(
    qapp, tmp_path, monkeypatch
):
    _fake_detect(monkeypatch, [_NOT_FOUND] * 8, [_NOT_FOUND] * 8, [SIZE_L] * 8, [SIZE_L] * 8)
    dlg = _dialog(8, tmp_path)
    _run(dlg)
    status = dlg._status.text()
    assert status.startswith(dlg.tr("The board was not found in any image."))
    assert (
        dlg.tr("For a chessboard, count the INNER corners: a board of 10 x 8 squares has 9 x 7.")
        in status
    )
    assert "need >= 3 usable views" not in status
    first = dlg._table.topLevelItem(0)
    assert first.text(3) == "0/0"
    assert first.text(6) == dlg.tr("L: {0}").format("chessboard not found")
    assert first.toolTip(6) == first.text(6)  # the narrow column can be read in full
    assert not dlg._accept_btn.isEnabled() and not dlg._recal_btn.isEnabled()


def test_board_found_in_too_few_pairs_says_how_many(qapp, tmp_path, monkeypatch):
    _truth, left, right = _two_resolution_views()
    left = [d if k < 4 else _NOT_FOUND for k, d in enumerate(left)]
    sizes_l, sizes_r = [SIZE_L] * len(left), [SIZE_R] * len(right)
    _fake_detect(monkeypatch, left, right, sizes_l, sizes_r)
    dlg = _dialog(len(left), tmp_path)
    _run(dlg)
    expected = dlg.tr(
        "The board was found in both images of only {0} of {1} pairs (the solve needs {2})."
    ).format(4, len(left), 6)
    assert dlg._status.text().startswith(expected)
    assert dlg._table.topLevelItem(0).text(3) == f"{left[0].n_points}/{right[0].n_points}"
    assert dlg._table.topLevelItem(5).text(6) == dlg.tr("L: {0}").format("chessboard not found")


@pytest.mark.parametrize(
    ("board", "label", "hint"),
    [
        ("chessboard", "Inner corners (columns x rows)", "count the INNER corners"),
        ("charuco", "Squares (columns x rows)", "count the SQUARES"),
        ("circles", "Dots (columns x rows)", "count the DOTS"),
        ("coded", "Dots (columns x rows)", "count the DOTS"),
    ],
)
def test_the_size_fields_say_what_each_board_counts(qapp, board, label, hint):
    dlg = CalibrationDialog()
    _select_board(dlg, board)
    assert dlg._count_lbl.text() == dlg.tr(label)
    assert hint in dlg._cols.toolTip() and dlg._rows.toolTip() == dlg._cols.toolTip()


def test_fewer_pairs_than_the_solve_needs_are_refused_up_front(qapp, tmp_path):
    dlg = _dialog(5, tmp_path)
    dlg._start(recalibrate=False)
    assert dlg._worker is None
    assert "6" in dlg._status.text()


# ---- item 3: image sizes ------------------------------------------------------------


def test_each_camera_keeps_its_own_image_size(qapp, tmp_path, monkeypatch):
    dlg = _solved(monkeypatch, tmp_path)
    cam_r = dlg._result.rig.cameras["R"]
    assert (cam_r.width, cam_r.height) == SIZE_R
    assert dlg._cached_sizes == (SIZE_L, SIZE_R)
    _run(dlg, recalibrate=True)  # Recalibrate keeps both sizes without reading images
    assert (dlg._result.rig.cameras["R"].width, dlg._result.rig.cameras["R"].height) == SIZE_R


def test_images_of_two_sizes_in_one_camera_are_refused(qapp, tmp_path, monkeypatch):
    _truth, left, right = _two_resolution_views()
    sizes_l = [SIZE_L] * len(left)
    sizes_l[3] = (320, 256)
    _fake_detect(monkeypatch, left, right, sizes_l, [SIZE_R] * len(right))
    dlg = _dialog(len(left), tmp_path)
    _run(dlg)
    assert dlg._result is None
    status = dlg._status.text()
    assert status.startswith("left camera: the board images are not all the same size")
    assert "L_03.png is 320x256" in status and "L_00.png is 640x512" in status
    assert not dlg._recal_btn.isEnabled()  # nothing was detected that a re-solve could use


# ---- item 5: small dialog issues ---------------------------------------------------------


def test_solver_warnings_are_drawn_in_the_warning_colour(qapp, tmp_path, monkeypatch):
    clean = _solved(monkeypatch, tmp_path)
    assert not clean._result.warnings
    assert COLORS.SUCCESS in clean._result_lbl.styleSheet()

    _truth, left, right = _two_resolution_views()
    mixed = [replace(d, method="classic") if k % 3 == 0 else d for k, d in enumerate(left)]
    warned = _solved(monkeypatch, tmp_path, left=mixed, right=right)
    assert warned._result.warnings  # mixed chessboard detectors
    assert COLORS.WARNING in warned._result_lbl.styleSheet()


def test_cancel_asks_before_discarding_an_unsaved_calibration(qapp, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    monkeypatch.setattr(CalibrationDialog, "_confirm_discard", _REAL_CONFIRM_DISCARD)
    asked: list[str] = []

    def answer(reply):
        def question(_parent, title, _text, *_args, **_kwargs):
            asked.append(title)
            return reply

        return question

    empty = CalibrationDialog()
    monkeypatch.setattr(
        QMessageBox, "question", staticmethod(answer(QMessageBox.StandardButton.No))
    )
    closed: list[int] = []
    empty.finished.connect(closed.append)
    empty.reject()
    assert closed and not asked  # nothing to lose: no question

    dlg = _solved(monkeypatch, tmp_path)
    dlg.finished.connect(closed.append)
    closed.clear()
    dlg.reject()  # Cancel and Esc both end here
    assert asked and not closed  # "No": the dialog stays open with its result
    monkeypatch.setattr(
        QMessageBox, "question", staticmethod(answer(QMessageBox.StandardButton.Yes))
    )
    dlg.reject()
    assert closed
