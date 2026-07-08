"""Offscreen tests of the strain post-processing window (Batch C).

Strain is post-processing now: the GUI pipeline runs with
``compute_strain=False`` and the ``StrainWindow3D`` computes on demand via
``StrainController3D`` (frozen ``dataclasses.replace`` writeback). These tests
cover the full-pipeline integration path (auto-open + compute through the
window) plus fast synthetic-result checks of the coordinate systems, the
3-point specimen frame, and the window's decoupling contracts.
"""

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
from al_dic_3d.gui.controllers.strain_controller import StrainController3D  # noqa: E402
from al_dic_3d.gui.main_window import MainWindow3D  # noqa: E402
from al_dic_3d.gui.state import GuiSignals  # noqa: E402
from al_dic_3d.gui.strain_window import StrainWindow3D  # noqa: E402
from al_dic_3d.matching.contracts import TRACKED, CorrespondenceSet  # noqa: E402
from al_dic_3d.reconstruct import Reconstruction3D  # noqa: E402
from al_dic_3d.runner import RunResult  # noqa: E402

Z0 = 800.0


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


# ---------------------------------------------------------------------------
# Synthetic result: a tilted plane under uniaxial stretch. The tilt guarantees
# the per-node tangent frame differs from the camera axes, so switching the
# coordinate system MUST change the strain values.
# ---------------------------------------------------------------------------


def _synthetic_result(nx: int = 17, step_px: float = 16.0) -> RunResult:
    ii, jj = np.meshgrid(np.arange(nx), np.arange(nx))
    ii, jj = ii.ravel(), jj.ravel()
    ref_2d = np.column_stack([ii * step_px + 40.0, jj * step_px + 40.0])
    xw = (ii - (nx - 1) / 2.0) * 2.0
    yw = (jj - (nx - 1) / 2.0) * 2.0
    ref_3d = np.column_stack([xw, yw, Z0 + 0.5 * xw])  # tilted about Y
    disp = np.column_stack([0.02 * xw, np.zeros_like(xw), np.zeros_like(xw)])

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


def _synthetic_controller() -> WorkflowController:
    ctrl = WorkflowController()
    ctrl.state.draft.winstepsize = 16
    ctrl.state.result = _synthetic_result()
    return ctrl


# ---------------------------------------------------------------------------
# Fast synthetic-result tests
# ---------------------------------------------------------------------------


def test_trigger_compute_populates_strain_and_enables_ui(qapp):
    ctrl = _synthetic_controller()
    signals = GuiSignals()
    win = StrainWindow3D(ctrl, signals)
    win.show()

    # before compute: strain fields locked, export locked
    assert ctrl.state.result.strain is None
    assert not win._field_selector._buttons["exx"].isEnabled()
    assert not win._export_btn.isEnabled()

    fired = []
    signals.results_changed.connect(lambda: fired.append(1))
    win.trigger_compute()

    result = ctrl.state.result
    assert result.strain is not None and result.strain.n_frames == 3
    assert fired  # writeback notified the app
    assert win._field_selector._buttons["von_mises"].isEnabled()
    assert win._export_btn.isEnabled()
    assert not win.is_stale()

    # rendering a strain frame produces an overlay pixmap only with a
    # background image; without images the window must not crash.
    win.set_strain_frame(1)
    win.close()


def test_coordinate_system_switch_changes_values(qapp):
    ctrl = _synthetic_controller()
    win = StrainWindow3D(ctrl, GuiSignals())

    assert win.param_panel().coordinate() == "local"  # fitted plane is DEFAULT
    win.trigger_compute()
    exx_local = ctrl.state.result.strain.exx[1].copy()

    win.param_panel().set_coordinate("camera0")
    assert win.is_stale()  # param change marks the result stale
    win.trigger_compute()
    exx_cam = ctrl.state.result.strain.exx[1]

    finite = np.isfinite(exx_local) & np.isfinite(exx_cam)
    assert finite.any()
    # tilted plane: tangent-frame exx must differ from camera-frame exx
    assert np.nanmax(np.abs(exx_local[finite] - exx_cam[finite])) > 1e-4
    win.close()


def test_specimen_frame_from_three_picked_nodes(qapp):
    ctrl = _synthetic_controller()
    sc = StrainController3D(ctrl)
    result = ctrl.state.result

    # snap three clicks (near exact node positions) to node indices
    nx = 17
    o_i, x_i, y_i = 8 * nx + 8, 8 * nx + 9, 9 * nx + 8
    picked = [
        sc.nearest_valid_node(result.ref_coords[i][0] + 1.0, result.ref_coords[i][1] - 1.0)
        for i in (o_i, x_i, y_i)
    ]
    assert picked == [o_i, x_i, y_i]

    r, t = sc.specimen_frame_from_nodes(picked)
    assert np.allclose(r.T @ r, np.eye(3), atol=1e-9)  # orthonormal
    assert np.allclose(t, result.reconstruction.points[0][o_i])

    strain = sc.compute(
        {"strain_size": 5, "smooth_sigma": 0.0, "coordinate": "specific", "specimen_R": r}
    )
    assert np.isfinite(strain.exx[1]).any()


def test_pick_flow_through_window(qapp):
    ctrl = _synthetic_controller()
    win = StrainWindow3D(ctrl, GuiSignals())
    panel = win.param_panel()
    panel.set_coordinate("specific")
    assert not panel.compute_allowed()  # Compute locked until 3 points picked

    win._start_pick()
    ref = ctrl.state.result.ref_coords
    nx = 17
    for i in (8 * nx + 8, 8 * nx + 9, 9 * nx + 8):
        win._on_point_picked(float(ref[i][0]), float(ref[i][1]))

    assert panel.specimen_R() is not None
    assert panel.compute_allowed()
    assert len(win._pick_items) == 6  # 3 markers + 3 labels
    win.trigger_compute()
    assert ctrl.state.result.strain is not None
    win.close()


def test_private_frame_never_touches_gui_signals(qapp):
    ctrl = _synthetic_controller()
    signals = GuiSignals()
    win = StrainWindow3D(ctrl, signals)
    win.trigger_compute()
    win.set_strain_frame(2)
    assert win.strain_current_frame() == 2
    assert signals.current_frame == 0  # main-window frame untouched
    win.close()


def test_dirty_hint_shows_until_recompute(qapp):
    ctrl = _synthetic_controller()
    win = StrainWindow3D(ctrl, GuiSignals())
    win.trigger_compute()
    assert win._stale_lbl.text() == ""
    win.param_panel()._win_spin.setValue(win.param_panel()._win_spin.value() + 2)
    assert win.is_stale() and win._stale_lbl.text()
    win.trigger_compute()
    assert not win.is_stale() and win._stale_lbl.text() == ""
    win.close()


def test_override_whitelist_rejects_pipeline_keys(qapp):
    sc = StrainController3D(_synthetic_controller())
    with pytest.raises(ValueError, match="not allowed"):
        sc.compute({"strain_size": 5, "winsize": 64})


def test_open_strain_button_enablement_after_project_open(qapp):
    # Fresh window, no results: button disabled and open refused.
    win = MainWindow3D()
    win.show()
    assert not win._right._strain_window_btn.isEnabled()
    win._open_strain_window()
    assert win._strain_window is None

    # Project-open path: results appear WITHOUT a run (run_state stays idle);
    # results_changed alone must enable the button (the known-bug fix).
    win.controller.state.result = _synthetic_result()
    win.signals.results_changed.emit()
    assert win._right._strain_window_btn.isEnabled()

    win._right.open_strain_window_requested.emit()
    assert win._strain_window is not None and win._strain_window.isVisible()
    win.close()
    assert win._strain_window is None  # cascade close


def test_workflow_panel_has_no_strain_checkbox(qapp):
    win = MainWindow3D()
    assert not hasattr(win._left, "_strain_cb")
    win.close()


# ---------------------------------------------------------------------------
# Full-pipeline integration (one real run, module-scoped scene)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def scene(tmp_path_factory):
    from tests import synth_parity

    d = tmp_path_factory.mktemp("strain_win_scene")
    return synth_parity.build_parity_scene(d, img=200, n_frames=3, seed=7)


def test_run_auto_opens_window_and_compute_renders(qapp, scene):
    win = MainWindow3D()
    win.show()
    draft = win.controller.state.draft
    draft.left = sorted(str(p) for p in scene["dir"].glob("L_*.png"))
    draft.right = sorted(str(p) for p in scene["dir"].glob("R_*.png"))
    draft.calibration_file = scene["dir"] / "calib.yml"
    draft.calibration_format = "opencv_yaml"
    draft.roi = (35, 165, 35, 165)
    win._left.refresh_all()
    win.signals.images_changed.emit()
    win.signals.roi_changed.emit()

    win.controller.run()
    win._right._on_done()  # -> run_state "done" -> auto-open (2D idiom)

    assert win.controller.state.result.strain is None  # pipeline skips strain
    sw = win._strain_window
    assert sw is not None and sw.isVisible()
    assert win._right._strain_window_btn.isEnabled()

    sw.trigger_compute()
    result = win.controller.state.result
    assert result.strain is not None
    assert result.strain.exx.shape == (3, result.reconstruction.n_pts)

    # deformed frame render: background image + scatter overlay + colorbar
    sw.set_strain_frame(1)
    sw._render()
    assert not sw._canvas._overlay_item.pixmap().isNull()
    assert sw._colorbar.isVisible()

    # reference-geometry toggle re-renders without error
    sw._deformed_cb.setChecked(False)
    assert not sw._canvas._overlay_item.pixmap().isNull()
    win.close()
