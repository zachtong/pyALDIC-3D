"""Importing a calibration in the sidebar: the format follows the file, bad rigs are red.

A DICe XML picked under the default ``opencv_yaml`` Format failed with
"cannot open OpenCV calibration file: <long path>"; under ``opencorr`` it
showed a green "fx 0  fy 0 | baseline 0.0 mm" and Run was ready.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

from pathlib import Path  # noqa: E402

import pytest  # noqa: E402

pytest.importorskip("PySide6")
pytest.importorskip("cv2")

from al_dic.gui.theme import COLORS  # noqa: E402

from al_dic_3d.gui.app import create_app  # noqa: E402
from al_dic_3d.gui.controller import WorkflowController  # noqa: E402
from al_dic_3d.gui.state import GuiSignals  # noqa: E402
from al_dic_3d.gui.widgets.calibration_section import CalibrationSection3D  # noqa: E402
from al_dic_3d.gui.widgets.next_step_hint import NextStepHint  # noqa: E402
from tests.test_calibration_import_checks import _QUICKSTART_DICE, _write_yaml  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


def _pick(monkeypatch, section: CalibrationSection3D, path: Path) -> None:
    monkeypatch.setattr(
        "PySide6.QtWidgets.QFileDialog.getOpenFileName",
        staticmethod(lambda *_a, **_k: (str(path), "")),
    )
    section._on_calib_browse()


def test_picking_a_dice_file_selects_the_dice_format(qapp, monkeypatch):
    section = CalibrationSection3D(WorkflowController(), GuiSignals())
    assert section.format_combo.currentText() == "opencv_yaml"
    _pick(monkeypatch, section, _QUICKSTART_DICE)
    assert section.format_combo.currentText() == "dice"
    assert section.controller.state.draft.calibration_format == "dice"
    assert "baseline" in section.status_label.text()
    assert COLORS.SUCCESS in section.status_label.styleSheet()


def test_an_ambiguous_file_keeps_the_chosen_format(qapp, monkeypatch, tmp_path):
    section = CalibrationSection3D(WorkflowController(), GuiSignals())
    section.format_combo.setCurrentText("matchid")
    f = tmp_path / "calibration.txt"
    f.write_text("nothing to see", encoding="utf-8")
    _pick(monkeypatch, section, f)
    assert section.format_combo.currentText() == "matchid"
    assert COLORS.DANGER in section.status_label.styleSheet()


def test_the_wrong_format_is_red_with_the_reason_first(qapp, monkeypatch):
    section = CalibrationSection3D(WorkflowController(), GuiSignals())
    _pick(monkeypatch, section, _QUICKSTART_DICE)
    section.format_combo.setCurrentText("opencorr")  # the user insists
    text = section.status_label.text()
    assert COLORS.DANGER in section.status_label.styleSheet()
    assert "not an OpenCorr calibration CSV" in text and "fx 0" not in text
    assert "choose the format 'dice'" in text


def test_a_zero_baseline_is_red(qapp, monkeypatch, tmp_path):
    section = CalibrationSection3D(WorkflowController(), GuiSignals())
    _pick(monkeypatch, section, _write_yaml(tmp_path / "flat.yml", T=(0.0, 0.0, 0.0)))
    assert COLORS.DANGER in section.status_label.styleSheet()
    assert "baseline" in section.status_label.text() and "zero" in section.status_label.text()


def test_the_next_step_names_a_broken_calibration_before_the_roi(qapp):
    hint = NextStepHint()
    issues = ["ROI not set", "calibration file cannot be read: the file does not exist (x.yml)"]
    assert "calibration file cannot be read" in hint.message_for(issues)
    assert hint.message_for(["ROI not set"]) == hint.tr("Draw the ROI on the left camera, frame 1")
