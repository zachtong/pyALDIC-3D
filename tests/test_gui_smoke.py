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
    assert result is not None and result.strain is not None
    # field overlay rendered on the canvas + colorbar visible
    win.signals.set_current_frame(1, 3)
    win._canvas_area.render()
    assert not win._canvas_area.canvas._overlay_item.pixmap().isNull()
    assert win._canvas_area._colorbar.isVisible()

    # switching to a strain field re-renders without error
    win.signals.set_display_field("von_mises")
    win._canvas_area.render()
    assert not win._canvas_area.canvas._overlay_item.pixmap().isNull()

    # switching camera swaps the background image (right frame exists)
    win.signals.set_camera("R")
    win._canvas_area.render()
    assert win._canvas_area.canvas.has_image
    win.close()


def test_field_range_is_stable_across_frames(qapp, scene):
    win = _loaded_window(scene)
    win.controller.run()
    win._right._on_done()
    result = win.controller.state.result
    lo1, hi1 = win._canvas_area._field_range(result)
    win.signals.set_current_frame(2, 3)
    lo2, hi2 = win._canvas_area._field_range(result)
    assert (lo1, hi1) == (lo2, hi2)  # playback does not re-scale colors
    disp = result.reconstruction.displacement
    assert lo1 <= np.nanmin(disp[:, :, 0]) + 1e-9
    win.close()
