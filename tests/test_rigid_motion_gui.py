"""Offscreen tests of the Strain window's RIGID MOTION section and its controller."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import numpy as np
import pytest

pytest.importorskip("PySide6")
pytest.importorskip("cv2")

from al_dic_3d.gui.app import create_app  # noqa: E402
from al_dic_3d.gui.controller import WorkflowController  # noqa: E402
from al_dic_3d.gui.controllers.rigid_motion_controller import (  # noqa: E402
    STATE_OFF,
    STATE_REMOVED,
    STATE_WAITING,
    RigidMotionController3D,
)
from al_dic_3d.gui.controllers.strain_controller import StrainController3D  # noqa: E402
from al_dic_3d.gui.rigid_motion_text import rigid_motion_label_suffix  # noqa: E402
from al_dic_3d.gui.state import GuiSignals  # noqa: E402
from al_dic_3d.gui.strain_window import StrainWindow3D  # noqa: E402
from al_dic_3d.matching.contracts import TRACKED, CorrespondenceSet  # noqa: E402
from al_dic_3d.reconstruct import Reconstruction3D  # noqa: E402
from al_dic_3d.runner import RunResult  # noqa: E402

Z0 = 245.0
TILT = 2.87e-3
IMG = 400


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


def _rot_x(a: float) -> np.ndarray:
    c, s = np.cos(a), np.sin(a)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])


def _result(nx: int = 17, step_px: float = 16.0) -> RunResult:
    """A flat plate that bows (bowl) and tilts rigidly by TILT about x."""
    ii, jj = np.meshgrid(np.arange(nx), np.arange(nx))
    ii, jj = ii.ravel(), jj.ravel()
    ref_2d = np.column_stack([ii * step_px + 40.0, jj * step_px + 40.0])
    xw = (ii - (nx - 1) / 2.0) * 0.5
    yw = (jj - (nx - 1) / 2.0) * 0.5
    ref = np.column_stack([xw, yw, np.full_like(xw, Z0)])
    frames = [ref]
    for k in (1, 2):
        bowl = np.zeros((xw.size, 3))
        bowl[:, 2] = 2e-4 * k * (xw**2 + yw**2)
        frames.append((ref + bowl) @ _rot_x(k * TILT).T + np.array([0.0, -0.26 * k, 0.14 * k]))
    points = np.stack(frames)
    n_frames, n_pts = points.shape[:2]
    rec = Reconstruction3D(
        points,
        points - points[0][None],
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
        meta={"image_size": (IMG, IMG)},
    )


def _workflow() -> WorkflowController:
    wc = WorkflowController()
    wc.state.draft.winstepsize = 16
    wc.state.result = _result()
    return wc


def _left_half() -> np.ndarray:
    mask = np.zeros((IMG, IMG), dtype=bool)
    mask[:, :170] = True
    return mask


# --- controller (Qt-free) ----------------------------------------------------------


def test_controller_applies_and_restores_through_the_draft():
    wc = _workflow()
    raw = wc.state.result.reconstruction
    rbm = RigidMotionController3D(wc)

    rbm.apply("rigid", None)

    assert wc.state.draft.rigid_motion_mode == "rigid" and wc.state.dirty
    assert wc.state.result.rigid_motion.raw is raw
    assert rbm.status().state == STATE_REMOVED
    rows = rbm.rows()
    assert [r.frame for r in rows] == [1, 2, 3] and rows[0].status == "reference"
    assert rows[1].angle_mrad == pytest.approx(TILT * 1e3, abs=1e-6)

    rbm.apply("off", None)
    assert wc.state.result.reconstruction is raw
    assert rbm.status().state == STATE_OFF and rbm.rows() == []


def test_an_unusable_region_changes_nothing():
    wc = _workflow()
    before = wc.state.result
    tiny = np.zeros((IMG, IMG), dtype=bool)
    tiny[40, 40] = True  # one node

    with pytest.raises(ValueError, match="at least 3"):
        RigidMotionController3D(wc).apply("rigid", tiny)

    assert wc.state.result is before
    assert wc.state.draft.rigid_motion_mode == "off"
    assert wc.state.draft.rigid_motion_region_array is None


def test_the_setting_waits_for_a_result():
    wc = WorkflowController()
    rbm = RigidMotionController3D(wc)
    rbm.apply("translation", None)
    assert wc.state.draft.rigid_motion_mode == "translation"
    assert rbm.status().state == STATE_WAITING


def test_strain_knows_which_setting_it_was_computed_under():
    wc = _workflow()
    rbm = RigidMotionController3D(wc)
    rbm.apply("rigid", None)
    StrainController3D(wc).compute_and_store({})
    assert not rbm.strain_is_stale()

    rbm.apply("translation", None)
    assert rbm.strain_is_stale()
    rbm.apply("rigid", None)
    assert not rbm.strain_is_stale()


# --- strain window ---------------------------------------------------------------


def _set_mode(win: StrainWindow3D, mode: str) -> None:
    combo = win.rigid_motion_panel()._mode
    combo.setCurrentIndex(combo.findData(mode))


def test_switching_the_mode_swaps_the_result_but_keeps_the_view(qapp):
    wc = _workflow()
    signals = GuiSignals()
    win = StrainWindow3D(wc, signals)
    win.show()
    win.set_strain_frame(2)
    win.param_panel().set_specimen_R(np.eye(3))
    fired = []
    signals.results_changed.connect(lambda: fired.append(1))

    _set_mode(win, "rigid")

    assert fired and wc.state.result.rigid_motion is not None
    assert win.strain_current_frame() == 2  # same run: frame kept...
    assert win.param_panel().specimen_R() is not None  # ...and the specimen picks
    panel = win.rigid_motion_panel()
    assert panel.row_count() == 3
    assert panel.cell_text(1, 4) == f"{TILT * 1e3:.3f}"
    assert "289" in panel.status_text()  # "... fitted on 289 points" (17 x 17 nodes)
    win.close()


def test_a_drawn_region_limits_the_fit_and_use_all_clears_it(qapp):
    wc = _workflow()
    win = StrainWindow3D(wc, GuiSignals())
    _set_mode(win, "rigid")
    all_points = int(wc.state.result.rigid_motion.fit.n_used[0])

    roi = win.rigid_motion_roi()
    roi.add_rectangle(0, 0, 169, IMG - 1)
    win._canvas.roi_mask_edited.emit()

    fit = wc.state.result.rigid_motion.fit
    assert wc.state.draft.rigid_motion_region_array is not None
    assert 3 <= int(fit.n_used[0]) < all_points

    win.rigid_motion_panel().use_all_requested.emit()
    assert wc.state.draft.rigid_motion_region_array is None
    assert int(wc.state.result.rigid_motion.fit.n_used[0]) == all_points
    win.close()


def test_displacement_shows_before_strain_and_slopes_after(qapp):
    wc = _workflow()
    win = StrainWindow3D(wc, GuiSignals())
    buttons = win._field_selector._buttons
    assert buttons["W"].isEnabled() and not buttons["dwdx"].isEnabled()
    assert not buttons["exx"].isEnabled()

    win.trigger_compute()
    assert buttons["dwdx"].isEnabled() and buttons["exx"].isEnabled()
    win.close()


def test_labels_say_the_rigid_motion_is_removed(qapp):
    wc = _workflow()
    win = StrainWindow3D(wc, GuiSignals())
    assert rigid_motion_label_suffix(wc.state.result) == ""
    assert win._overlay_label("W").startswith("W (")

    _set_mode(win, "rigid")
    suffix = rigid_motion_label_suffix(wc.state.result)
    assert "rigid motion removed" in suffix
    assert win._overlay_label("W").endswith(suffix)
    assert win._overlay_label("dwdx").startswith("∂w/∂x (mrad)")
    win.close()


def test_changing_the_setting_marks_computed_strain_stale(qapp):
    wc = _workflow()
    win = StrainWindow3D(wc, GuiSignals())
    win.trigger_compute()
    assert win._stale_lbl.text() == ""

    _set_mode(win, "translation")
    assert "Rigid-motion" in win._stale_lbl.text()

    _set_mode(win, "off")
    assert win._stale_lbl.text() == ""
    win.close()


def test_main_window_labels_it_and_keeps_the_camera_for_the_same_run(qapp, monkeypatch):
    from al_dic_3d.gui.main_window import MainWindow3D

    win = MainWindow3D()
    win.controller.state.result = _result()
    win.signals.results_changed.emit()
    area = win._canvas_area
    resets: list[int] = []
    monkeypatch.setattr(area._view3d, "request_camera_reset", lambda: resets.append(1))

    RigidMotionController3D(win.controller).apply("rigid", None)
    win.signals.results_changed.emit()
    assert "rigid motion removed" in area._display_label()
    assert resets == []  # same run: the 3D view keeps its camera for comparing

    win.controller.state.result = _result()  # a new run
    win.signals.results_changed.emit()
    assert resets == [1]
    assert "rigid motion removed" not in area._display_label()
    win.close()


def test_exported_figures_carry_the_label(qapp):
    from al_dic_3d.gui.dialogs.export_dialog import ExportDialog
    from al_dic_3d.run_rigid import with_rigid_motion

    raw = _result()
    plain = ExportDialog(raw, extra_params={})
    assert "rigid motion" not in plain.field_display("W")[1]
    plain.close()

    corrected = ExportDialog(with_rigid_motion(raw, "translation", None), extra_params={})
    assert corrected.field_display("W")[1].endswith(rigid_motion_label_suffix(corrected._result))
    corrected.close()


def test_the_panel_is_locked_while_strain_computes(qapp):
    wc = _workflow()
    win = StrainWindow3D(wc, GuiSignals())

    class _Running:
        def isRunning(self) -> bool:  # noqa: N802 - mirrors QThread
            return True

    win._worker = _Running()
    win._refresh_rigid_motion()
    assert not win.rigid_motion_panel()._mode.isEnabled()
    win._worker = None
    win._refresh_rigid_motion()
    assert win.rigid_motion_panel()._mode.isEnabled()
    win.close()
