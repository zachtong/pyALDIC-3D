"""Batch Q — offscreen GUI: units + velocity (Q1/Q2), strain type + edge trim
panel (Q3/Q4), reference-update section (Q5), associate action (Q6),
include-results save prompt (Q7), advanced knobs + mesh appearance (Q8)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("PySide6")

from al_dic_3d.gui.app import create_app  # noqa: E402
from al_dic_3d.gui.controller import WorkflowController  # noqa: E402
from al_dic_3d.gui.display_units import (  # noqa: E402
    display_field_key,
    field_display_factor,
    field_label,
)
from al_dic_3d.gui.main_window import MainWindow3D  # noqa: E402
from al_dic_3d.gui.state import GuiSignals  # noqa: E402
from al_dic_3d.matching.contracts import TRACKED, CorrespondenceSet  # noqa: E402
from al_dic_3d.reconstruct import Reconstruction3D  # noqa: E402
from al_dic_3d.runner import RunResult  # noqa: E402

Z0 = 800.0


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


def _synthetic_result(nx: int = 9, step_px: float = 16.0, eps: float = 0.02) -> RunResult:
    """Flat plane under uniaxial stretch (3 frames) — velocity/strain testable."""
    ii, jj = np.meshgrid(np.arange(nx), np.arange(nx))
    ii, jj = ii.ravel(), jj.ravel()
    ref_2d = np.column_stack([ii * step_px + 40.0, jj * step_px + 40.0])
    xw = (ii - (nx - 1) / 2.0) * 2.0
    yw = (jj - (nx - 1) / 2.0) * 2.0
    ref_3d = np.column_stack([xw, yw, np.full_like(xw, Z0)])
    disp = np.column_stack([eps * xw, np.zeros_like(xw), np.zeros_like(xw)])

    points = np.stack([ref_3d, ref_3d + disp, ref_3d + 2.0 * disp])
    displacement = points - points[0][None]
    n_frames, n_pts = points.shape[:2]
    rec = Reconstruction3D(
        points,
        displacement,
        np.zeros((n_frames, n_pts)),
        np.full((n_frames, n_pts), TRACKED, np.uint8),
    )
    x_img = np.stack([ref_2d] * n_frames)
    cs = CorrespondenceSet(
        strategy="track_both",
        xL=x_img.copy(),
        xR=x_img.copy(),
        quality=np.zeros((n_frames, n_pts)),
        source=np.full((n_frames, n_pts), TRACKED, np.uint8),
    )
    return RunResult(
        strategy="track_both",
        ref_coords=ref_2d,
        correspondence=cs,
        reconstruction=rec,
        strain=None,
        meta={},
    )


# ---------------------------------------------------------------------------
# Q1 — display units
# ---------------------------------------------------------------------------


def test_display_unit_helpers():
    assert field_display_factor("U", "µm") == 1000.0
    assert field_display_factor("mag", "m") == 0.001
    assert field_display_factor("velocity", "cm") == pytest.approx(0.1)
    assert field_display_factor("exx", "µm") == 1.0  # strain: never converted
    assert field_label("U", "µm") == "U (µm)"
    assert field_label("mag", "mm") == "|D| (mm)"
    assert field_label("velocity", "cm") == "|V| (cm/s)"
    assert field_label("exx", "µm") == "εxx"
    # cache keys: unit (and fps for velocity) are part of the key
    assert display_field_key("U", "µm", 1.0) != display_field_key("U", "mm", 1.0)
    assert display_field_key("velocity", "mm", 1.0) != display_field_key("velocity", "mm", 2.0)
    assert display_field_key("exx", "µm", 1.0) == "exx"


def test_units_section_updates_signals_and_emits(qapp):
    win = MainWindow3D()
    units = win._right._units
    fired = []
    win.signals.display_changed.connect(lambda: fired.append(1))
    units._unit_combo.setCurrentText("µm")
    assert win.signals.display_unit == "µm"
    units._fps_spin.setValue(24.0)
    assert win.signals.frame_rate == pytest.approx(24.0)
    assert len(fired) >= 2
    win.close()


def test_view_state_round_trips_units_and_mesh_appearance(qapp):
    win = MainWindow3D()
    s = win.signals
    s.display_unit = "µm"
    s.frame_rate = 12.5
    s.mesh_line_color = "#3b82f6"
    s.mesh_line_width = 4
    vs = win._capture_view_state()
    win.close()

    win2 = MainWindow3D()
    assert win2.signals.display_unit == "mm"  # fresh default
    win2._right.apply_view_state(vs, n_frames=1)
    assert win2.signals.display_unit == "µm"
    assert win2.signals.frame_rate == pytest.approx(12.5)
    assert win2.signals.mesh_line_color == "#3b82f6"
    assert win2.signals.mesh_line_width == 4
    assert win2._right._units._unit_combo.currentText() == "µm"
    win2.close()


# ---------------------------------------------------------------------------
# Q2 — velocity field
# ---------------------------------------------------------------------------


def test_velocity_values_and_frame_rate_dependence(qapp):
    win = MainWindow3D()
    result = _synthetic_result()
    win.controller.state.result = result
    win.signals.display_field = "velocity"
    win.signals.frame_rate = 1.0
    canvas = win._canvas_area

    v0 = canvas._field_values(result, 0)
    assert np.isnan(v0).all()  # frame 0: no predecessor
    v1 = canvas._field_values(result, 1)
    step = result.reconstruction.displacement[1] - result.reconstruction.displacement[0]
    assert np.allclose(v1, np.linalg.norm(step, axis=1))

    win.signals.frame_rate = 10.0  # velocity scales linearly with fps
    v1_fast = canvas._field_values(result, 1)
    assert np.allclose(v1_fast, 10.0 * v1)
    win.close()


def test_velocity_button_enabled_only_with_results(qapp):
    win = MainWindow3D()
    btn = win._right._field_selector._buttons["velocity"]
    assert not btn.isEnabled()  # no results yet
    win.controller.state.result = _synthetic_result()
    win.signals.results_changed.emit()
    assert btn.isEnabled()
    win.controller.state.result = None
    win.signals.results_changed.emit()
    assert not btn.isEnabled()
    win.close()


# ---------------------------------------------------------------------------
# Q3 / Q4 — strain window panel + compute integration
# ---------------------------------------------------------------------------


def _strain_window(qapp):
    from al_dic_3d.gui.strain_window import StrainWindow3D

    ctrl = WorkflowController()
    ctrl.state.draft.winstepsize = 16
    ctrl.state.result = _synthetic_result(nx=17)
    return StrainWindow3D(ctrl, GuiSignals())


def test_strain_panel_override_carries_type_and_trim(qapp):
    win = _strain_window(qapp)
    panel = win.param_panel()
    override = panel.get_override()
    assert override["strain_type"] == "green_lagrange"
    assert override["edge_trim_alpha"] == pytest.approx(0.7)  # 2D-calibrated default

    panel.mark_clean()
    panel.set_strain_type("infinitesimal")
    assert panel.is_dirty()  # Q3: stale hint invalidation on change
    panel.mark_clean()
    panel._edge_trim_spin.setValue(0.3)
    assert panel.is_dirty()  # Q4: same for the trim coefficient
    assert panel.get_override()["edge_trim_alpha"] == pytest.approx(0.3)
    win.close()


def test_strain_type_changes_computed_values(qapp):
    win = _strain_window(qapp)
    win.trigger_compute()
    gl = win.controller.state.result.strain
    assert gl is not None and gl.n_trimmed is not None  # trim active (alpha 0.7)
    assert int(gl.n_trimmed[1]) > 0  # A6-1: the biased outer boundary ring is trimmed
    gl_exx = np.nanmedian(gl.exx[1])  # nanmedian over the exact interior

    win.param_panel().set_strain_type("infinitesimal")
    win.trigger_compute()
    inf_exx = np.nanmedian(win.controller.state.result.strain.exx[1])
    eps = 0.02
    assert inf_exx == pytest.approx(eps, rel=1e-4)
    assert gl_exx == pytest.approx(eps + 0.5 * eps**2, rel=1e-4)
    assert gl_exx > inf_exx
    win.close()


def test_trim_readout_follows_render(qapp):
    win = _strain_window(qapp)
    win.trigger_compute()
    readout = win.param_panel()._edge_trim_readout
    assert readout.isVisibleTo(win.param_panel())  # n_trimmed array present
    assert "0" in readout.text()

    # A session-reloaded strain (no n_trimmed bookkeeping) hides the readout.
    win.param_panel().set_trim_readout(None, 10)
    assert not readout.isVisibleTo(win.param_panel())
    win.close()


# ---------------------------------------------------------------------------
# Q5 — reference-update section
# ---------------------------------------------------------------------------


def test_ref_update_visible_only_in_incremental(qapp):
    win = MainWindow3D()
    left = win._left
    ref = left._ref_update
    assert not ref.isVisibleTo(left)  # accumulative default: hidden
    left._mode_combo.setCurrentIndex(left._mode_combo.findData("incremental"))
    assert ref.isVisibleTo(left)
    assert win.controller.state.draft.reference_mode == "incremental"
    left._mode_combo.setCurrentIndex(left._mode_combo.findData("accumulative"))
    assert not ref.isVisibleTo(left)
    win.close()


def test_ref_update_writes_draft(qapp):
    win = MainWindow3D()
    left = win._left
    left._mode_combo.setCurrentIndex(left._mode_combo.findData("incremental"))
    ref = left._ref_update
    draft = win.controller.state.draft

    ref._mode_combo.setCurrentIndex(ref._mode_combo.findData("every_n"))
    ref._n_spin.setValue(5)
    assert draft.ref_update_mode == "every_n" and draft.ref_update_n == 5

    ref._mode_combo.setCurrentIndex(ref._mode_combo.findData("custom"))
    ref._frames_edit.setText("10, 5, 5")
    ref._frames_edit.editingFinished.emit()
    assert draft.ref_update_frames == [5, 10]  # sorted, deduplicated

    ref._frames_edit.setText("5, x")
    ref._frames_edit.editingFinished.emit()
    assert draft.ref_update_frames is None  # invalid text -> no frames
    assert ref._frames_hint.isVisibleTo(ref)
    win.close()


def test_ref_update_survives_refresh_all(qapp):
    win = MainWindow3D()
    draft = win.controller.state.draft
    draft.reference_mode = "incremental"
    draft.ref_update_mode = "custom"
    draft.ref_update_frames = [3, 7]
    win._left.refresh_all()
    ref = win._left._ref_update
    assert ref._mode_combo.currentData() == "custom"
    assert ref._frames_edit.text() == "3, 7"
    assert ref.isVisibleTo(win._left)
    win.close()


# ---------------------------------------------------------------------------
# Q6 — associate menu action
# ---------------------------------------------------------------------------


def test_file_menu_offers_association_on_windows(qapp):
    import sys

    win = MainWindow3D()
    # Keep every intermediate wrapper alive: shiboken may hand transient
    # wrappers C++ ownership, and collecting them would delete the menus.
    bar = win.menuBar()
    actions = bar.actions()
    file_action = actions[0]
    file_menu = file_action.menu()
    texts = [a.text() for a in file_menu.actions()]
    has_assoc = any("Associate .aldic3d" in t for t in texts)
    assert has_assoc == (sys.platform == "win32")
    del file_menu, file_action, actions, bar
    win.close()


# ---------------------------------------------------------------------------
# Q7 — include-results save prompt routing
# ---------------------------------------------------------------------------


def _capture_save(win, monkeypatch):
    calls = []

    def _fake_save(path, *, include_results=True):
        calls.append((Path(path), include_results))
        return Path(path)

    monkeypatch.setattr(win.controller, "save_project", _fake_save)
    return calls


def test_save_prompt_no_saves_config_only(qapp, monkeypatch, tmp_path):
    win = MainWindow3D()
    win.controller.state.result = _synthetic_result()
    calls = _capture_save(win, monkeypatch)
    prompts = []
    monkeypatch.setattr(
        MainWindow3D, "_prompt_include_results", lambda self, est: prompts.append(est) or "no"
    )
    assert win._write_project(tmp_path / "p.aldic3d") is True
    assert calls == [(tmp_path / "p.aldic3d", False)]
    assert prompts and "MB" in prompts[0]  # nbytes-derived size estimate shown
    win.close()


def test_save_prompt_cancel_aborts(qapp, monkeypatch, tmp_path):
    win = MainWindow3D()
    win.controller.state.result = _synthetic_result()
    calls = _capture_save(win, monkeypatch)
    monkeypatch.setattr(MainWindow3D, "_prompt_include_results", lambda self, est: "cancel")
    assert win._write_project(tmp_path / "p.aldic3d") is False
    assert calls == []
    win.close()


def test_save_without_results_never_prompts(qapp, monkeypatch, tmp_path):
    win = MainWindow3D()
    calls = _capture_save(win, monkeypatch)

    def _boom(self, est):
        raise AssertionError("prompt must not appear without results")

    monkeypatch.setattr(MainWindow3D, "_prompt_include_results", _boom)
    assert win._write_project(tmp_path / "p.aldic3d") is True
    assert calls == [(tmp_path / "p.aldic3d", True)]
    win.close()


# ---------------------------------------------------------------------------
# Q8 — advanced knobs + mesh appearance
# ---------------------------------------------------------------------------


def test_fft_auto_expand_checkbox_writes_draft(qapp):
    win = MainWindow3D()
    cb = win._left._fft_expand_cb
    assert cb.isChecked() and win.controller.state.draft.fft_auto_expand is True
    cb.setChecked(False)
    assert win.controller.state.draft.fft_auto_expand is False
    win.controller.state.draft.fft_auto_expand = True
    win._left.refresh_all()
    assert cb.isChecked()
    win.close()


def test_mesh_appearance_flows_to_overlay(qapp):
    win = MainWindow3D()
    controls = win._canvas_area._mesh_appearance
    overlay = win._canvas_area._mesh_overlay
    controls._width_spin.setValue(5)  # emits display_changed -> render()
    assert win.signals.mesh_line_width == 5
    assert overlay._edge_width == 5
    win.signals.mesh_line_color = "#ff0000"
    win.signals.display_changed.emit()
    assert overlay._edge_color_str == "#ff0000"
    win.close()
