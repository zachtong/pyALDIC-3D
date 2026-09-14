"""Canvas and save-dialog details from fix batch V (M10 and the lows).

- Save dialogs propose a path in the data's folder, never a bare file name
  (that resolves against the working directory; the 2D 0.8.0 fix).
- The canvas's log messages go through ``tr()``.
- Velocity is labelled per frame until a frame rate is given.
- The mesh-overlay controls say what they are and show their whole value.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QLabel  # noqa: E402

from al_dic_3d.gui import persistence  # noqa: E402
from al_dic_3d.gui.app import create_app  # noqa: E402
from al_dic_3d.gui.main_window import MainWindow3D  # noqa: E402
from al_dic_3d.gui.panels.canvas_area import CanvasArea3D  # noqa: E402

SAVE_DIALOG = "PySide6.QtWidgets.QFileDialog.getSaveFileName"


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


@pytest.fixture
def win(qapp):
    window = MainWindow3D()
    yield window
    window.close()


def _record_dialog(monkeypatch, answer: str = ""):
    """Replace the save dialog; returns the list of proposed paths."""
    proposed: list[str] = []

    def fake(_parent, _title, start, _filter, *_a, **_k):
        proposed.append(start)
        return answer, ""

    monkeypatch.setattr(SAVE_DIALOG, staticmethod(fake))
    return proposed


def _marked_tr(monkeypatch, cls) -> None:
    """Make ``cls.tr`` visibly mark every string it translates."""
    monkeypatch.setattr(cls, "tr", lambda _self, text, *_a: f"<<{text}>>")


def _log_capture(window) -> list[tuple[str, str]]:
    messages: list[tuple[str, str]] = []
    window.signals.log.connect(lambda text, level: messages.append((text, level)))
    return messages


# ---- save paths -----------------------------------------------------------------


def test_suggested_save_path_is_never_a_bare_file_name(qapp, tmp_path):
    image = tmp_path / "images" / "L_000.png"
    image.parent.mkdir()
    image.write_bytes(b"")
    assert persistence.suggested_save_path("m.png", "mask", near=image) == str(
        image.parent / "m.png"
    )
    persistence.set_last_dir("mask", tmp_path)
    assert persistence.suggested_save_path("m.png", "mask") == str(tmp_path / "m.png")
    persistence.settings().setValue("last_dir/mask", str(tmp_path / "gone"))
    assert persistence.suggested_save_path("m.png", "mask") == str(Path.home() / "m.png")


def test_mask_save_starts_in_the_image_folder_and_remembers_the_choice(
    win, tmp_path, monkeypatch
):
    image = tmp_path / "images" / "L_000.png"
    image.parent.mkdir()
    image.write_bytes(b"")
    win.controller.state.draft.left = [str(image)]
    saved: list[str] = []
    stub = SimpleNamespace(mask=np.ones((4, 4), bool), save_mask=saved.append)
    monkeypatch.setattr(CanvasArea3D, "roi_ctrl", property(lambda _self: stub))
    target = tmp_path / "masks" / "roi.png"
    target.parent.mkdir()
    proposed = _record_dialog(monkeypatch, str(target))
    _marked_tr(monkeypatch, CanvasArea3D)
    messages = _log_capture(win)

    win._canvas_area.roi_save()

    assert proposed == [str(image.parent / "roi_mask.png")]
    assert saved == [str(target)]
    assert persistence.last_dir("mask") == str(target.parent)
    assert messages[-1] == (f"<<ROI mask saved to {target}>>", "success")


def test_calibration_save_dialogs_start_in_a_real_folder(qapp, tmp_path, monkeypatch):
    from al_dic_3d.gui.dialogs.calibration_dialog import CalibrationDialog
    from al_dic_3d.gui.dialogs.manual_params_dialog import ManualParamsDialog

    proposed = _record_dialog(monkeypatch)
    board = tmp_path / "board" / "L_01.png"
    board.parent.mkdir()
    dlg = CalibrationDialog()
    dlg._files_l = [str(board)]
    dlg._result = object()  # a solved calibration; the dialog is cancelled
    dlg._on_accept()
    assert proposed[-1] == str(board.parent / "calibration.yml")
    dlg.close()

    persistence.set_last_dir("calibration", tmp_path)
    manual = ManualParamsDialog()
    manual._trans[0].setValue(-100.0)  # a non-zero baseline reaches the dialog
    manual._on_save()
    assert proposed[-1] == str(tmp_path / "calibration.yml")
    manual.close()


def test_log_save_starts_in_a_real_folder(win, monkeypatch):
    proposed = _record_dialog(monkeypatch)
    win._right._on_save_log()
    assert Path(proposed[-1]).is_absolute()


# ---- canvas log messages ------------------------------------------------------------


def test_canvas_log_messages_are_translated(win, monkeypatch):
    canvas = win._canvas_area
    _marked_tr(monkeypatch, CanvasArea3D)
    messages = _log_capture(win)

    canvas.roi_import("mask.png")  # no images yet
    canvas.roi_save()  # no ROI yet
    draft = win.controller.state.draft
    draft.seed_points = [(1.0, 2.0), (30.0, 40.0)]
    draft.seed_point = draft.seed_points[0]
    canvas._on_seed_remove(29.0, 41.0)
    canvas.clear_seed()
    canvas._copy_canvas_to_clipboard()
    canvas._on_overlay_error("boom")

    texts = [text for text, _level in messages]
    assert texts == [
        "<<Load images before importing an ROI mask>>",
        "<<No ROI mask to save — draw one first>>",
        "<<Starting point removed at (30.0, 40.0)>>",
        "<<Starting points cleared>>",
        "<<Canvas image copied to the clipboard>>",
        "<<Could not draw the overlay: boom>>",
    ]


def test_velocity_is_labelled_per_frame_until_a_rate_is_given(win):
    signals = win.signals
    signals.display_field = "velocity"
    signals.display_unit = "mm"
    signals.frame_rate_known = False
    assert win._canvas_area._display_label() == "|V| (mm/frame)"
    signals.frame_rate_known = True
    assert win._canvas_area._display_label() == "|V| (mm/s)"


# ---- mesh overlay controls ------------------------------------------------------------


def test_mesh_overlay_controls_are_labelled_and_show_their_value(qapp):
    from al_dic_3d.gui.state import GuiSignals
    from al_dic_3d.gui.widgets.mesh_appearance import MeshAppearanceControls

    controls = MeshAppearanceControls(GuiSignals())
    controls.show()
    qapp.processEvents()
    assert any(label.text().strip() for label in controls.findChildren(QLabel))
    spin = controls._width_spin
    spin.setValue(8)
    qapp.processEvents()
    edit = spin.lineEdit()
    # A fixed 56 px box elided "1 px" to "1 p." beside its arrows.
    assert edit.width() >= edit.fontMetrics().horizontalAdvance(edit.text())
    controls.close()
