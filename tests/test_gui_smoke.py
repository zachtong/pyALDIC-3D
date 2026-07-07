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


def test_roi_draw_updates_draft(qapp, scene):
    win = _loaded_window(scene)
    win._canvas_area.canvas.roi_changed.emit((10, 150, 20, 160))
    assert win.controller.state.draft.roi == (10, 150, 20, 160)
    # drawing releases the toggle (2D deactivate idiom)
    assert not win._left.roi_draw_button.isChecked()
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
