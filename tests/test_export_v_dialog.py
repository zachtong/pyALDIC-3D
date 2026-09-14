"""Export dialog + parameters describe the run and what the canvas shows.

Fix batch V: H1/H3/H6 (stale result, run step, parameters JSON from the live
draft), M1 (units: exports always mm, prefilled ranges applied to the wrong
field / unit), M4 camera/range plumbing, and the export lows (zero written shown
green, colorbar errors swallowed, pyplot in worker threads, 4-decimal strain
ranges, the stale ``[viz3d]`` install hint, the blocking Preview render).
"""

from __future__ import annotations

import json
import os
import threading
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import numpy as np
import pytest

from al_dic_3d.export import (
    FieldImageConfig,
    VizExportHint,
    export_params,
    render_field_frame,
    run_mesh_step,
)
from tests.synth_export import grid_result, write_gray_frames

# ---------------------------------------------------------------------------
# Qt-free: parameters JSON + run step (H3 / H6)
# ---------------------------------------------------------------------------


def test_parameters_json_prefers_what_the_run_recorded(tmp_path):
    result = grid_result(run_step=16)
    draft_now = {"winsize": 64, "winstepsize": 8, "strain_size": 7, "quality_gate": True}
    result.meta["quality_gate"] = False
    path = export_params(tmp_path, "p", "20260913000000", result, draft_now)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["winsize"] == 32 and data["winstepsize"] == 16  # the run's, not the draft's
    assert data["quality_gate"] is False  # recorded by the run
    assert data["strain_size"] == 7  # not recorded by the run: caller's value fills the gap


def test_run_mesh_step_prefers_run_params_then_node_spacing():
    assert run_mesh_step(grid_result(step=16.0, run_step=16)) == 16
    assert run_mesh_step(grid_result(step=12.0, run_step=None)) == 12  # old session
    assert run_mesh_step(grid_result(step=12.0, run_step=None), default=9) == 12


# ---------------------------------------------------------------------------
# Qt-free: display units (M1)
# ---------------------------------------------------------------------------


def test_render_scales_values_and_honours_a_fixed_range_in_display_units():
    result = grid_result(n_frames=2)
    mm = render_field_frame(result, "L", "U", 1, None, FieldImageConfig("U"), mesh_step=16)
    um = render_field_frame(
        result, "L", "U", 1, None, FieldImageConfig("U", value_scale=1000.0), mesh_step=16
    )
    assert um[1] == pytest.approx(mm[1] * 1000.0) and um[2] == pytest.approx(mm[2] * 1000.0)
    # A fixed range typed in µm applies to µm data: not one flat colour.
    lo, hi = um[1], um[2]
    fixed = FieldImageConfig("U", auto_range=False, vmin=lo, vmax=hi, value_scale=1000.0)
    img, _, _ = render_field_frame(result, "L", "U", 1, None, fixed, mesh_step=16)
    inside = img[60:160, 60:160].reshape(-1, 3)
    assert len(np.unique(inside, axis=0)) > 20


def test_velocity_field_is_the_frame_to_frame_displacement():
    from al_dic_3d.export import field_frame

    result = grid_result(n_frames=3)
    rec = result.reconstruction
    assert np.isnan(field_frame(result, "velocity", 0)).all()
    np.testing.assert_allclose(
        field_frame(result, "velocity", 2),
        np.linalg.norm(rec.displacement[2] - rec.displacement[1], axis=1),
    )


# ---------------------------------------------------------------------------
# Qt-free lows: colorbar
# ---------------------------------------------------------------------------


def test_attach_colorbar_raises_instead_of_silently_dropping_the_bar(monkeypatch):
    from al_dic_3d.export import ColorbarStyle, attach_colorbar
    from al_dic_3d.export import colorbar as cb_mod

    def boom(*a, **k):
        raise ValueError("font cache exploded")

    monkeypatch.setattr(cb_mod, "_render_bar", boom)
    with pytest.raises(RuntimeError, match="colorbar"):
        attach_colorbar(np.zeros((40, 60, 3), np.uint8), ColorbarStyle(), "turbo", 0, 1, "U")


def test_colorbar_never_touches_pyplot(monkeypatch):
    import matplotlib.pyplot as plt

    from al_dic_3d.export import render_colorbar_strip

    def banned(*a, **k):
        raise AssertionError("pyplot used from an export worker")

    for name in ("subplots", "figure", "close", "get_cmap"):
        monkeypatch.setattr(plt, name, banned)
    strip = render_colorbar_strip(120, "viridis", 0.0, 1.0, "U (mm)")
    assert strip.shape[0] == 120 and strip.std() > 0


def test_colorbars_render_concurrently_from_threads():
    from al_dic_3d.export import render_colorbar_strip

    errors: list[BaseException] = []

    def work():
        try:
            for _ in range(3):
                render_colorbar_strip(80, "turbo", -1.0, 1.0, "εxx")
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=work) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors


def test_vtu_install_hint_names_the_real_fix(tmp_path, monkeypatch):
    import sys

    from al_dic_3d.export.vtu import export_vtu_series

    monkeypatch.setitem(sys.modules, "pyvista", None)
    with pytest.raises(ImportError) as info:
        export_vtu_series(tmp_path, "t", "20260913000000", grid_result(), ["U"])
    assert "pip install pyvista" in str(info.value)


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------


@pytest.fixture()
def qapp():
    pytest.importorskip("PySide6")
    from al_dic_3d.gui.app import create_app

    return create_app([])


def _dialog(result, tmp_path, *, hint=None, roi=True, draft_step=16, **kw):
    from al_dic_3d.gui.dialogs.export_dialog import ExportDialog
    from al_dic_3d.project.draft import ProjectDraft

    left = write_gray_frames(tmp_path, "L", result.reconstruction.n_frames, (200, 200))
    right = write_gray_frames(tmp_path, "R", result.reconstruction.n_frames, (200, 200))
    draft = ProjectDraft(left=left, right=right, winstepsize=draft_step)
    if roi:
        mask = np.zeros((200, 200), np.uint8)
        mask[:, :120] = 255
        draft.roi_mask_array = mask
    dlg = ExportDialog(result, extra_params={}, draft=draft, hint=hint, **kw)
    out = tmp_path / "out"
    out.mkdir(exist_ok=True)
    dlg._folder_edit.setText(str(out))
    return dlg


def test_dialog_uses_the_run_step_not_the_edited_draft(qapp, tmp_path):
    result = grid_result(run_step=16)
    dlg = _dialog(result, tmp_path, draft_step=8)  # user changed the step after the run
    assert dlg.mesh_step == 16
    dlg.close()
    old = grid_result(step=12.0, run_step=None)  # a result saved before run_params existed
    dlg = _dialog(old, tmp_path, draft_step=8)
    assert dlg.mesh_step == 12
    dlg.close()


def test_dialog_result_api_detects_a_stale_dialog(qapp, tmp_path):
    result = grid_result()
    dlg = _dialog(result, tmp_path)
    assert dlg.result is result and dlg.matches(result)
    assert not dlg.matches(grid_result())
    assert not dlg.matches(None)
    with pytest.raises(AttributeError):
        dlg.result = grid_result()
    dlg.close()


def test_rows_prefill_only_the_canvas_field_and_follow_its_auto_setting(qapp, tmp_path):
    hint = VizExportHint(
        current_field="W", auto_range=False, vmin=-150.0, vmax=200.0, display_unit="µm"
    )
    dlg = _dialog(grid_result(), tmp_path, hint=hint)
    rows = {r.field_id: r for r in dlg._images_tab.field_rows}
    w = rows["W"].config()
    assert not w.auto_range and (w.vmin, w.vmax) == (-150.0, 200.0)
    for fid in ("U", "V", "exx"):
        other = rows[fid].config()
        assert other.auto_range  # no canvas range belongs to these fields
        assert (other.vmin, other.vmax) != (-150.0, 200.0)
    dlg.close()


def test_media_configs_carry_the_display_unit_and_velocity_rate(qapp, tmp_path):
    hint = VizExportHint(current_field="U", display_unit="µm", frame_rate=25.0)
    dlg = _dialog(grid_result(), tmp_path, hint=hint)
    cfgs = {c.field_id: c for c in dlg._images_tab._rows.configs()}
    assert cfgs["U"].value_scale == pytest.approx(1000.0) and cfgs["U"].label == "U (µm)"
    assert cfgs["mag"].label == "|D| (µm)"
    assert cfgs["velocity"].value_scale == pytest.approx(25_000.0)
    assert cfgs["velocity"].label == "|V| (µm/s)"
    assert cfgs["exx"].value_scale == 1.0 and cfgs["exx"].label == "εxx"
    dlg.close()


def test_velocity_stays_per_frame_until_a_frame_rate_is_given(qapp, tmp_path):
    hint = VizExportHint(display_unit="mm", frame_rate=1.0, frame_rate_known=False)
    dlg = _dialog(grid_result(), tmp_path, hint=hint)
    vel = dlg._images_tab._rows.row_for("velocity").config()
    assert vel.value_scale == pytest.approx(1.0)
    assert vel.label == "|V| (mm/frame)"
    dlg.close()


def test_unticking_auto_seeds_the_range_from_the_data(qapp, tmp_path):
    hint = VizExportHint(current_field="U", display_unit="µm")
    dlg = _dialog(grid_result(), tmp_path, hint=hint)
    row = next(r for r in dlg._images_tab.field_rows if r.field_id == "V")
    row._auto_check.setChecked(False)
    cfg = row.config()
    assert cfg.vmax > cfg.vmin and cfg.vmax > 1.0  # µm-scale values, not 0..1
    dlg.close()


def test_strain_sized_ranges_keep_their_precision(qapp, tmp_path):
    dlg = _dialog(grid_result(), tmp_path)
    row = next(r for r in dlg._images_tab.field_rows if r.field_id == "exx")
    row.set_appearance(auto=False, vmin=1.234e-5, vmax=3.5e-4)
    cfg = row.config()
    assert cfg.vmin == pytest.approx(1.234e-5, rel=1e-6)
    assert cfg.vmax == pytest.approx(3.5e-4, rel=1e-6)
    dlg.close()


def test_image_tab_passes_units_masks_and_the_run_step(qapp, tmp_path, monkeypatch):
    import al_dic_3d.export as export_mod

    captured = {}

    def fake(*args, **kwargs):
        captured["args"] = args
        captured.update(kwargs)
        return export_mod.ExportOutcome()

    monkeypatch.setattr(export_mod, "export_image_frames", fake)
    hint = VizExportHint(current_field="U", display_unit="cm")
    dlg = _dialog(grid_result(run_step=16), tmp_path, hint=hint, draft_step=8)
    dlg._images_tab._camera_row._combo.setCurrentIndex(2)  # Left + Right
    dlg._images_tab.start_export()
    assert dlg.wait_for_export()
    configs = captured["args"][5]
    u = next(c for c in configs if c.field_id == "U")
    assert u.value_scale == pytest.approx(0.1) and u.label == "U (cm)"
    assert captured["mesh_step"] == 16
    assert captured["roi_mask"] is not None
    # Not warped on the GUI thread: the exporter warps in its worker ...
    assert captured["right_roi_mask"] is None
    # ... unless the Preview already did, in which case that warp is reused.
    warped = dlg.right_roi_mask()
    assert warped is not None
    dlg._images_tab.start_export()
    assert dlg.wait_for_export()
    assert captured["right_roi_mask"] is warped
    dlg.close()


def test_zero_written_is_a_red_failure_not_green(qapp, tmp_path, monkeypatch):
    from al_dic.gui.theme import COLORS

    import al_dic_3d.export as export_mod

    def nothing(*args, **kwargs):
        return export_mod.ExportOutcome()

    monkeypatch.setattr(export_mod, "export_image_frames", nothing)
    dlg = _dialog(grid_result(), tmp_path)
    tab = dlg._images_tab
    tab.start_export()
    assert dlg.wait_for_export()
    status = tab._progress._status
    assert "Wrote 0" not in status.text()
    assert COLORS.DANGER.lower() in status.styleSheet().lower()
    assert COLORS.SUCCESS.lower() not in status.styleSheet().lower()
    dlg.close()


def test_view3d_tab_passes_camera_units_roi_and_fixed_range(qapp, tmp_path, monkeypatch):
    import al_dic_3d.export as export_mod

    calls: dict = {}

    def fake_frames(*args, **kwargs):
        calls["frames"] = kwargs
        return export_mod.ExportOutcome()

    def fake_turntable(*args, **kwargs):
        calls["turntable"] = kwargs
        return export_mod.ExportOutcome()

    monkeypatch.setattr(export_mod, "export_view3d_frames", fake_frames)
    monkeypatch.setattr(export_mod, "export_view3d_turntable", fake_turntable)
    cam = ((1.0, 2.0, 3.0), (0.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    hint = VizExportHint(
        current_field="W", auto_range=False, vmin=-2.0, vmax=3.0, display_unit="µm"
    )
    dlg = _dialog(grid_result(), tmp_path, hint=hint, camera_provider=lambda: cam)
    tab = dlg._view3d_tab
    assert tab._field_combo.currentData() == "W"
    tab._turntable_check.setChecked(True)
    tab.start_export()
    assert dlg.wait_for_export()
    for key in ("frames", "turntable"):
        kw = calls[key]
        assert kw["camera"] == cam
        assert kw["value_scale"] == pytest.approx(1000.0)
        assert kw["field_label"] == "W (µm)"
        assert kw["auto_range"] is False and (kw["vmin"], kw["vmax"]) == (-2.0, 3.0)
        assert kw["roi_mask"] is not None
    dlg.close()


def _wait(predicate, timeout=20.0):
    from PySide6.QtCore import QCoreApplication

    deadline = time.monotonic() + timeout
    while not predicate():
        QCoreApplication.processEvents()
        if time.monotonic() > deadline:
            return False
        time.sleep(0.01)
    return True


def test_preview_renders_off_the_gui_thread(qapp, tmp_path, monkeypatch):
    import al_dic_3d.export as export_mod

    threads: list[str] = []
    real = export_mod.render_field_frame

    def spy(*args, **kwargs):
        threads.append(threading.current_thread().name)
        return real(*args, **kwargs)

    monkeypatch.setattr(export_mod, "render_field_frame", spy)
    dlg = _dialog(grid_result(), tmp_path)
    tab = dlg._preview_tab
    dlg._tabs.setCurrentWidget(tab)
    tab._request_preview()

    def shown() -> bool:
        pix = tab._preview_label.pixmap()
        return pix is not None and not pix.isNull()

    assert _wait(shown)
    assert threads and all(name != threading.main_thread().name for name in threads)
    dlg.close()


def test_hidden_preview_does_not_render_on_images_tab_edits(qapp, tmp_path, monkeypatch):
    import al_dic_3d.export as export_mod

    calls: list[int] = []
    real = export_mod.render_field_frame

    def spy(*args, **kwargs):
        calls.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(export_mod, "render_field_frame", spy)
    dlg = _dialog(grid_result(), tmp_path)
    dlg._tabs.setCurrentWidget(dlg._images_tab)
    dlg._preview_tab._request_preview()  # what the debounce timer fires
    assert not dlg._preview_tab._inflight and calls == []
    dlg.close()


def test_preview_right_camera_uses_the_warped_mask(qapp, tmp_path, monkeypatch):
    import al_dic_3d.export as export_mod

    seen: list = []
    real = export_mod.render_field_frame

    def spy(*args, **kwargs):
        seen.append((args[1], kwargs.get("roi_mask")))
        return real(*args, **kwargs)

    monkeypatch.setattr(export_mod, "render_field_frame", spy)
    dlg = _dialog(grid_result(), tmp_path)
    tab = dlg._preview_tab
    dlg._tabs.setCurrentWidget(tab)
    tab._camera_combo.setCurrentIndex(tab._camera_combo.findData("R"))
    tab._render_preview()
    cam, mask = seen[-1]
    assert cam == "R" and mask is not None
    np.testing.assert_array_equal(mask, dlg.right_roi_mask())
    dlg.close()
