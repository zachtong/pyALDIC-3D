"""Offscreen smoke test of the Qt shell (Phase 4, pyALDIC-style 3-column window).

Constructs the real MainWindow3D under the offscreen Qt platform, drives the
draft through the sidebar/panel APIs, renders a result overlay, and asserts the
view stays in sync — no display required; skipped if PySide6 is absent.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import numpy as np
import pytest

pytest.importorskip("PySide6")
cv2 = pytest.importorskip("cv2")

from al_dic_3d.gui.app import create_app  # noqa: E402
from al_dic_3d.gui.main_window import MainWindow3D  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


@pytest.fixture(scope="module")
def scene(tmp_path_factory):
    from tests import synth_parity

    d = tmp_path_factory.mktemp("gui_scene")
    return synth_parity.build_parity_scene(d, img=200, n_frames=3, seed=7)


def _loaded_window(scene) -> MainWindow3D:
    win = MainWindow3D()
    win.show()  # offscreen show: isVisible() works without a real display
    draft = win.controller.state.draft
    draft.left = sorted(str(p) for p in scene["dir"].glob("L_*.png"))
    draft.right = sorted(str(p) for p in scene["dir"].glob("R_*.png"))
    draft.calibration_file = scene["dir"] / "calib.yml"
    draft.calibration_format = "opencv_yaml"
    draft.roi = (35, 165, 35, 165)
    win._left.refresh_all()
    win.signals.images_changed.emit()
    win.signals.roi_changed.emit()
    return win


def test_three_column_window_constructs(qapp):
    win = MainWindow3D()
    assert win._left.width() == 320 or win._left.minimumWidth() <= 320
    assert win.windowTitle()
    assert win.menuBar().actions()  # File + Settings menus exist
    win.close()


def test_theme_stylesheet_is_applied(qapp):
    assert len(qapp.styleSheet()) > 100  # the shared pyALDIC dark theme


def test_sidebar_populates_draft_and_canvas_shows_image(qapp, scene):
    win = _loaded_window(scene)
    assert win._canvas_area.canvas.has_image  # frame visible on the canvas
    # pair table + badge reflect the load
    assert win._left._pair_list.topLevelItemCount() == 3
    # calibration preview succeeded (green status, not the error text)
    assert "fx" in win._left._calib_status.text()
    # readiness reflects a complete draft
    win._right.refresh_readiness()
    assert "Ready" in win._right._ready_lbl.text()
    win.close()


def test_roi_toolbox_mask_updates_draft(qapp, scene):
    win = _loaded_window(scene)
    area = win._canvas_area
    draft = win.controller.state.draft

    # Arm a rect tool from the toolbar path and stamp through the mask engine.
    win._left.roi_toolbar.draw_requested.emit("rect", "add")
    ctrl = area.roi_ctrl
    assert ctrl is not None and ctrl.shape == (200, 200)
    ctrl.add_rectangle(10, 20, 150, 160, "add")
    area.commit_roi_mask()

    # draft.roi follows the mask bounding box; the mask itself is persisted.
    assert draft.roi == (10, 150, 20, 160)
    assert draft.roi_mask_array is not None and draft.roi_mask_array.any()
    assert "10" in win._left._roi_bbox_lbl.text()  # sidebar readout follows

    # Cut a hole: bbox unchanged, mask smaller.
    n_before = int(np.count_nonzero(draft.roi_mask_array))
    ctrl.add_circle(80, 90, 20, "cut")
    area.commit_roi_mask()
    assert int(np.count_nonzero(draft.roi_mask_array)) < n_before
    assert draft.roi == (10, 150, 20, 160)

    # Invert + clear round-trip through the toolbar signals.
    win._left.roi_toolbar.invert_requested.emit()
    assert draft.roi_mask_array is not None
    win._left.roi_toolbar.clear_requested.emit()
    assert draft.roi_mask_array is None and draft.roi is None
    win.close()


def test_shape_commit_releases_toolbar_highlight(qapp, scene):
    win = _loaded_window(scene)
    toolbar = win._left.roi_toolbar
    toolbar._on_shape_selected("circle", "cut")
    assert toolbar._active_mode == "cut"
    # canvas one-shot commit emits drawing_finished -> toolbar deactivates
    win._canvas_area.canvas.drawing_finished.emit()
    assert toolbar._active_mode is None
    win.close()


def test_refine_brush_via_toolbar(qapp, scene):
    win = _loaded_window(scene)
    canvas = win._canvas_area.canvas
    win._left.roi_toolbar.brush_requested.emit("paint", 12)
    assert canvas._tool == "brush" and canvas._brush_radius == 12
    win._left.roi_toolbar.brush_radius_changed.emit(20)
    assert canvas._brush_radius == 20
    # paint a stroke programmatically; the draft picks up the refinement mask
    assert canvas._ensure_brush_buffers()
    from PySide6.QtCore import QPointF

    canvas._brush_stroke_to(QPointF(100.0, 100.0))
    canvas.brush_changed.emit()
    assert win.controller.state.draft.refinement_mask_array is not None
    win._left.roi_toolbar.brush_clear_requested.emit()
    assert win.controller.state.draft.refinement_mask_array is None
    win.close()


def test_mesh_preview_builds_from_draft(qapp, scene):
    win = _loaded_window(scene)
    area = win._canvas_area
    assert area._grid_cb.isChecked()  # default on
    area._generate_preview_mesh()  # bypass the debounce timer
    assert area.wait_mesh_preview()  # P2.3: the build runs on a worker now
    overlay = area._mesh_overlay
    assert overlay.isVisible() and overlay._edge_path is not None
    assert area._hover_coords is not None and len(area._hover_coords) > 4

    # hover near a node shows the subset window (requires Show Subset)
    area._subset_cb.setChecked(True)
    x, y = float(area._hover_coords[0, 0]), float(area._hover_coords[0, 1])
    area._on_scene_hover(x + 1.0, y + 1.0)
    assert overlay._hover_idx is not None
    assert overlay._hover_winsize == float(win.controller.state.draft.winsize)

    # unchecking Grid disables + unchecks Subset and hides the overlay
    area._grid_cb.setChecked(False)
    assert not area._subset_cb.isChecked() and not area._subset_cb.isEnabled()
    assert not overlay.isVisible()
    win.close()


def test_run_and_overlay_render(qapp, scene):
    win = _loaded_window(scene)
    win.controller.run()  # synchronous headless run (worker thread tested elsewhere)
    win._right._on_done()

    result = win.controller.state.result
    # Batch C: the GUI pipeline never computes strain (post-processing window).
    assert result is not None and result.strain is None
    # DENSE field overlay rendered on the canvas + colorbar visible
    win.signals.set_current_frame(1, 3)
    win._canvas_area.render()
    canvas = win._canvas_area.canvas
    assert not canvas._overlay_item.pixmap().isNull()
    assert win._canvas_area._colorbar.isVisible()
    # the dense overlay is a grid-resolution image scaled to pixel coords
    assert canvas._overlay_item.scale() >= 1.0
    # the node-dot layer and its "Show Points" toggle were removed (F1.4):
    # the dense field is the only result rendering on the canvas
    assert not hasattr(win._canvas_area, "_show_points_cb")
    # colorbar range = 2–98 percentile of the visible values (G2.3, 2D parity)
    disp_u = result.reconstruction.displacement[1][:, 0]
    finite = disp_u[np.isfinite(disp_u)]
    lo, hi = np.nanpercentile(finite, [2.0, 98.0])
    assert win.signals.color_min == pytest.approx(float(lo))
    assert win.signals.color_max == pytest.approx(float(hi))

    # the main field selector offers ONLY clean displacement fields now
    assert set(win._right._field_selector._buttons) == {"U", "V", "W", "mag"}

    # switching camera swaps the background image (right frame exists)
    win.signals.set_camera("R")
    win._canvas_area.render()
    assert win._canvas_area.canvas.has_image
    win.close()


def test_init_guess_section_maps_to_draft(qapp, scene):
    win = _loaded_window(scene)
    draft = win.controller.state.draft
    widget = win._left.init_guess_widget

    # Starting Point is the DEFAULT: radio checked, seed panel visible.
    assert draft.init_guess == "seed"
    assert widget._rb_seed.isChecked() and widget._seed_panel.isVisible()

    widget._rb_prev.setChecked(True)
    assert draft.init_guess == "previous"
    assert not widget._seed_panel.isVisible()
    widget._rb_fft.setChecked(True)
    assert draft.init_guess == "fft"
    widget._rb_seed.setChecked(True)
    assert draft.init_guess == "seed"

    # The config card mirrors the choice through its INIT row.
    win._canvas_area._config_overlay.refresh()
    assert win._canvas_area._config_overlay._init_lbl.text() == "Starting Point"
    win.close()


def test_seed_placement_one_shot_updates_draft(qapp, scene):
    from PySide6.QtCore import QPointF

    win = _loaded_window(scene)
    draft = win.controller.state.draft
    widget = win._left.init_guess_widget
    canvas = win._canvas_area.canvas

    # Toggling "Place point…" arms the canvas seed tool and jumps to L frame 1.
    win.signals.set_camera("R")
    widget._btn_place.setChecked(True)
    assert canvas._tool == "seed"
    assert win.signals.current_camera == "L" and win.signals.current_frame == 0

    # One click places the point, resets the tool, and releases the toggle.
    canvas._commit_seed_click(QPointF(84.0, 61.0))
    assert draft.seed_point == (84.0, 61.0)
    assert canvas._tool == "select"
    assert not widget._btn_place.isChecked()
    assert canvas._seed_marker is not None  # accent marker at the point

    # A second placement replaces the previous point (never accumulates).
    widget._btn_place.setChecked(True)
    canvas._commit_seed_click(QPointF(90.0, 70.0))
    assert draft.seed_point == (90.0, 70.0)

    # Esc cancels the armed tool without touching the stored point.
    widget._btn_place.setChecked(True)
    canvas.set_seed_tool(False)
    canvas.drawing_finished.emit()
    assert draft.seed_point == (90.0, 70.0) and not widget._btn_place.isChecked()

    # Clear drops the point and the marker.
    widget.clear_seed_requested.emit()
    assert draft.seed_point is None
    assert canvas._seed_marker is None
    win.close()


def test_seed_survives_gui_session_roundtrip(qapp, scene, tmp_path):
    win = _loaded_window(scene)
    win.controller.state.draft.seed_point = (12.5, 34.0)
    win.controller.state.draft.init_guess = "seed"
    from al_dic_3d.project import load_session, save_session

    path = save_session(win.controller.state, tmp_path / "seed.aldic3d")
    loaded = load_session(path)
    assert loaded.draft.seed_point == (12.5, 34.0)
    assert loaded.draft.init_guess == "seed"
    win.close()


def test_right_camera_mask_warp_keeps_hole(qapp, scene):
    win = _loaded_window(scene)
    area = win._canvas_area

    # Draw a holed ROI mask on the LEFT camera, frame 1.
    ctrl = area.roi_ctrl
    ctrl.add_rectangle(40, 40, 160, 160, "add")
    ctrl.add_circle(100, 100, 15, "cut")
    area.commit_roi_mask()

    win.controller.run()
    win._right._on_done()
    result = win.controller.state.result

    warped = area._right_roi_mask(result)
    assert warped is not None and warped.dtype == bool and warped.any()

    # The hole survives the warp. In-hole nodes are invalid (no texture under
    # the mask), so map the hole CENTER into the right image with the median
    # disparity of the nearest finite correspondences (smooth stereo field).
    cs = result.correspondence
    xl0, xr0 = cs.xL[0], cs.xR[0]
    ok = np.isfinite(xl0).all(axis=1) & np.isfinite(xr0).all(axis=1)

    def right_of(px: float, py: float) -> tuple[int, int]:
        d = np.linalg.norm(xl0 - [px, py], axis=1)
        d[~ok] = np.inf
        near = np.argsort(d)[:6]
        disp = np.median(xr0[near] - xl0[near], axis=0)
        return int(round(px + disp[0])), int(round(py + disp[1]))

    hx, hy = right_of(100.0, 100.0)  # hole center
    sx, sy = right_of(70.0, 70.0)  # solid region
    assert not warped[hy, hx]  # hole stays transparent
    assert warped[sy, sx]  # solid region stays opaque

    # The RIGHT-camera dense render consumes the warped mask without error.
    win.signals.set_camera("R")
    win.signals.set_current_frame(1, 3)
    area.render()
    assert not area.canvas._overlay_item.pixmap().isNull()
    win.close()


def test_view3d_checkbox_switches_stack_and_matches_2d_view(qapp, scene, monkeypatch):
    # F3.2: the toggle is a CHECKBOX next to Show Grid / Show Subset, and the
    # 3D render receives the drawn ROI mask + the SAME field/colormap/range as
    # the 2D dense view (shared signals).
    from PySide6.QtWidgets import QCheckBox

    win = _loaded_window(scene)
    area = win._canvas_area
    assert isinstance(area._view3d_cb, QCheckBox)
    assert not hasattr(area, "_view3d_btn")  # the toolbar button is gone

    ctrl = area.roi_ctrl
    ctrl.add_rectangle(40, 40, 160, 160, "add")
    ctrl.add_circle(100, 100, 15, "cut")  # holed ROI
    area.commit_roi_mask()

    win.controller.run()
    win._right._on_done()

    # Render the 2D view first: auto range writes the shared signals.
    win.signals.set_current_frame(1, 3)
    area.render()
    lo_2d, hi_2d = win.signals.color_min, win.signals.color_max

    calls = {}

    def record_update(points, vals, **kw):
        calls.update(kw)
        calls["points"] = points

    monkeypatch.setattr(area._view3d, "update_view", record_update)
    area._view3d_cb.setChecked(True)
    assert area._stack.currentIndex() == 1  # stack switched to the 3D page
    assert calls["roi_mask"] is not None and calls["roi_mask"].dtype == bool
    assert not calls["roi_mask"][100, 100]  # the drawn hole reaches the 3D view
    assert calls["ref_coords"] is not None
    assert calls["cmap"] == win.signals.colormap
    # Same frame, same field, same auto-range contract as the 2D view.
    assert calls["vmin"] == pytest.approx(lo_2d) and calls["vmax"] == pytest.approx(hi_2d)
    assert (calls["vmin"], calls["vmax"]) == (win.signals.color_min, win.signals.color_max)

    area._view3d_cb.setChecked(False)
    assert area._stack.currentIndex() == 0  # back to the 2D canvas
    win.close()


def test_run_summary_written_to_log(qapp, scene):
    # F3.1: finishing a run writes a validity summary into the log console.
    win = _loaded_window(scene)
    win.controller.run()
    win._right._on_done()
    text = win._right._console.toPlainText()
    assert "Frame-1 stereo match:" in text
    assert "Analysis complete —" in text and "median validity" in text
    assert "Stopped early" not in text  # complete run: no partial-run banner
    win.close()


def test_run_summary_reports_stopped_early(qapp, scene):
    # R2 (engine 0.7 partial results): a cancelled-but-kept run logs ONE honest
    # line saying how many frames survived, instead of discarding silently.
    win = _loaded_window(scene)
    win.controller.run()
    win.controller.state.result.meta.update(
        stopped_early=True, stopped_at_frame=2, stop_reason="Computation cancelled by user."
    )
    win._right._on_done()
    text = win._right._console.toPlainText()
    assert "Stopped early at frame 2/3" in text
    assert "kept 2 computed frames" in text
    assert "Stopped early" in win._right._progress_lbl.text()
    win.close()


def test_empty_result_logs_error_and_shows_canvas_notice(qapp, scene):
    # F3.1 empty-result guard: all-NaN reconstruction -> explicit error line
    # in the log + a visible notice on the canvas, never silent nothing.
    from dataclasses import replace

    win = _loaded_window(scene)
    win.controller.run()
    result = win.controller.state.result
    rec = result.reconstruction
    nan_pts = np.full_like(rec.points, np.nan)
    empty_rec = replace(
        rec,
        points=nan_pts,
        displacement=np.full_like(rec.displacement, np.nan),
        reproj_error=np.full_like(rec.reproj_error, np.nan),
    )
    win.controller.state.result = replace(result, reconstruction=empty_rec)

    win._right._on_done()  # summary path sees the empty reconstruction
    text = win._right._console.toPlainText()
    assert "No valid points in ANY frame" in text

    win._canvas_area.render()
    assert win._canvas_area._result_empty
    assert win._canvas_area._empty_notice.isVisible()
    win.close()


def test_run_worker_failure_reports_exception_type(qapp, scene):
    # F3.1: a worker crash surfaces the exception TYPE + message to the UI.
    from al_dic_3d.gui.panels.right_sidebar import RunWorker

    win = _loaded_window(scene)

    class Boom:
        def run(self, progress=None, stop=None):  # noqa: ARG002
            raise ValueError("boom: bad calibration matrix")

    worker = RunWorker(Boom())
    got: list[str] = []
    worker.failed.connect(got.append)
    worker.run()  # synchronous call (no thread needed for the error path)
    assert got == ["ValueError: boom: bad calibration matrix"]
    win.close()
