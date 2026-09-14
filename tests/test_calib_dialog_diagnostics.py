"""WP6: the calibration dialog shows the diagnostics (brief, section 5.3).

* the result colour follows the highest severity;
* the findings appear as translated text built from the code and the values;
* the covered radius is drawn on the pair preview;
* the saved calibration carries the numbers as ``meta_*`` nodes.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import numpy as np
import pytest

pytest.importorskip("PySide6")

from al_dic.gui.theme import COLORS  # noqa: E402

from al_dic_3d.calibration import run_calibration  # noqa: E402
from al_dic_3d.calibration.diagnostics import (  # noqa: E402
    EXTRAPOLATION_CHECK_SKIPPED,
    EXTRAPOLATION_UNDETERMINED,
    LENS_MODEL_INADEQUATE,
    LOW_COVERAGE,
    MODEL_CHECK_SKIPPED,
    Finding,
)
from al_dic_3d.gui.app import create_app  # noqa: E402
from al_dic_3d.gui.calibration_findings import finding_text  # noqa: E402
from al_dic_3d.gui.dialogs.calibration_dialog import CalibrationDialog  # noqa: E402
from al_dic_3d.gui.dialogs.calibration_support import overlay_panel  # noqa: E402
from tests.test_calib_extrapolation import SIZE, _central_poses, _corner_poses  # noqa: E402
from tests.test_calib_pipeline import wide_stereo  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    from al_dic_3d.i18n import install_translators

    app = create_app([])
    # Another module installs zh_CN on the shared application; the sentences
    # below are checked in the English source language.
    install_translators(app, locale="en")
    return app


def _payload(poses):
    left, right = wide_stereo(poses)
    run = run_calibration(left, right, SIZE, options={})
    stats = dict(run.stats, diagnostics=run.diagnostics, pair_max={})
    return (left, right, run.result, stats), run


VALUES = {
    EXTRAPOLATION_UNDETERMINED: {"cover_ratio": 0.63, "disagreement_outside_px": 1.977},
    LOW_COVERAGE: {"cover_ratio": 0.65},
    LENS_MODEL_INADEQUATE: {"residual_excess": 22.94, "residual_field_ratio": 7.57},
    EXTRAPOLATION_CHECK_SKIPPED: {"reason": "need >= 3 usable views"},
    MODEL_CHECK_SKIPPED: {"cells": 2},
}
EXPECTED = {
    EXTRAPOLATION_UNDETERMINED: ("63%", "1.98 px"),
    LOW_COVERAGE: ("65%",),
    LENS_MODEL_INADEQUATE: ("22.9", "7.6"),
    EXTRAPOLATION_CHECK_SKIPPED: ("skipped",),
    MODEL_CHECK_SKIPPED: ("2",),
}


@pytest.mark.parametrize("code", sorted(VALUES))
def test_each_finding_reads_as_a_sentence_with_its_numbers(qapp, code):
    finding = Finding(code, "warning", "R", VALUES[code], "english default")
    text = finding_text(finding)
    assert text.startswith("Camera R") and "english default" not in text
    for part in EXPECTED[code]:
        assert part in text


def test_with_k3_fixed_the_sentence_does_not_advise_fixing_k3(qapp):
    values = dict(VALUES[EXTRAPOLATION_UNDETERMINED], chosen_model="k3 fixed")
    text = finding_text(Finding(EXTRAPOLATION_UNDETERMINED, "warning", "R", values, "en"))
    assert "With k3 fixed" in text and "1.98 px" in text
    assert "fix k3 for a low-distortion lens" not in text


def test_a_refined_board_is_not_suggested_again(qapp):
    values = dict(VALUES[LENS_MODEL_INADEQUATE], board_refined=True)
    text = finding_text(Finding(LENS_MODEL_INADEQUATE, "warning", "L", values, "en"))
    assert "already optimised" in text and "22.9" in text
    assert "Optimize board shape" not in text
    plain = Finding(LENS_MODEL_INADEQUATE, "warning", "L", VALUES[LENS_MODEL_INADEQUATE], "en")
    nominal = finding_text(plain)
    assert "Optimize board shape" in nominal


def test_an_unknown_code_falls_back_to_the_english_message(qapp):
    assert finding_text(Finding("NEW_CODE", "info", "L", {}, "a new check")) == "a new check"


def test_a_warning_turns_the_result_amber_and_lists_the_finding(qapp):
    dialog = CalibrationDialog()
    payload, run = _payload(_central_poses())
    dialog._on_solved(payload)
    text = dialog._result_lbl.text()
    warning = next(f for f in run.diagnostics.findings if f.code == EXTRAPOLATION_UNDETERMINED)
    assert finding_text(warning) in text
    assert COLORS.WARNING in dialog._result_lbl.styleSheet()
    dialog.close()


def test_a_clean_calibration_stays_green(qapp):
    dialog = CalibrationDialog()
    payload, run = _payload(_corner_poses())
    assert run.diagnostics.worst_severity != "warning"
    dialog._on_solved(payload)
    assert COLORS.SUCCESS in dialog._result_lbl.styleSheet()
    dialog.close()


def test_the_covered_radius_is_drawn_on_the_preview(qapp, tmp_path):
    from PIL import Image

    path = tmp_path / "board.png"
    Image.fromarray(np.full((120, 160), 90, np.uint8)).save(path)
    square = np.array([[20.0, 20.0], [140.0, 20.0], [140.0, 100.0], [20.0, 100.0]])
    plain = overlay_panel(str(path), None, height=None)
    drawn = overlay_panel(str(path), None, height=None, outline=square)
    changed = np.any(drawn != plain, axis=2)
    assert changed[20, 60] and changed[60, 140] and not changed[60, 80]


def test_the_saved_calibration_carries_the_diagnostics(qapp, tmp_path, monkeypatch):
    import cv2

    dialog = CalibrationDialog()
    payload, run = _payload(_central_poses())
    dialog._board_combo.setCurrentIndex(0)
    dialog._on_solved(payload)
    target = tmp_path / "rig.yml"
    monkeypatch.setattr(
        "PySide6.QtWidgets.QFileDialog.getSaveFileName",
        staticmethod(lambda *_a, **_k: (str(target), "")),
    )
    dialog._on_accept()
    fs = cv2.FileStorage(str(target), cv2.FILE_STORAGE_READ)
    try:
        assert f"{EXTRAPOLATION_UNDETERMINED}:L" in fs.getNode("meta_findings").string()
        assert fs.getNode("meta_cover_ratio_left").real() == pytest.approx(
            run.diagnostics.cameras["L"].cover_ratio
        )
    finally:
        fs.release()
    dialog.close()


def test_the_preview_shows_the_outline_once_solved(qapp):
    dialog = CalibrationDialog()
    payload, run = _payload(_central_poses())
    dialog._on_solved(payload)
    outlines = dialog._coverage_outlines()
    assert set(outlines) == {"L", "R"} and len(outlines["L"]) > 10
    dialog.close()
