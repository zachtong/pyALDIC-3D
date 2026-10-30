"""The drawn ROI layer: left frame-1 image only, off once a run finishes, toggleable.

It used to stay on top of every view — tinting the results blue, sitting at its
frame-1 place on deformed frames and on the right camera — with no way to hide
it short of deleting the ROI.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import pytest

pytest.importorskip("PySide6")
pytest.importorskip("cv2")

from al_dic_3d.gui.app import create_app  # noqa: E402
from tests.test_session_fidelity_gui import (  # noqa: E402 - shared scene helpers
    IMG,
    _loaded_window,
    _paint_brush,
    _paint_shaped_roi,
)


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


@pytest.fixture(scope="module")
def scene(tmp_path_factory):
    from tests import synth_parity

    d = tmp_path_factory.mktemp("roi_toggle_scene")
    return synth_parity.build_parity_scene(d, img=IMG, n_frames=3, seed=7)


def _shown(area) -> bool:
    canvas = area.canvas
    roi, brush = canvas._roi_mask_item.isVisible(), canvas._brush_item.isVisible()
    assert roi == brush  # one switch for both mask layers
    return roi


def test_the_roi_shows_on_the_left_frame_one_image_only(qapp, scene):
    win = _loaded_window(scene)
    area = win._canvas_area
    _paint_shaped_roi(area)
    area.render()
    assert _shown(area)

    win.signals.current_camera = "R"
    area.render()
    assert not _shown(area)  # the left mask does not belong on the right image

    win.signals.current_camera = "L"
    win.signals.current_frame = 1
    area.render()
    assert not _shown(area)  # frame-2 background: the frame-1 outline would be misplaced

    win.signals.current_frame = 0
    area.render()
    assert _shown(area)
    win.close()


def test_a_finished_run_hides_it_and_the_tools_bring_it_back(qapp, scene):
    win = _loaded_window(scene)
    area = win._canvas_area
    _paint_shaped_roi(area)
    area.render()

    win.signals.run_state_changed.emit("done")
    assert not area._roi_cb.isChecked() and not _shown(area)
    assert not area.canvas._roi_mask_item.pixmap().isNull()  # hidden, not erased

    area.start_shape_tool("rect", "add")
    assert area._roi_cb.isChecked() and _shown(area)
    area.canvas.set_tool("select")

    area._roi_cb.setChecked(False)
    _paint_brush(area)  # arming the refinement brush shows the mask layers too
    assert area._roi_cb.isChecked()
    win.close()


def test_reference_geometry_keeps_it_on_later_frames_with_results(qapp, scene):
    win = _loaded_window(scene)
    area = win._canvas_area
    _paint_shaped_roi(area)
    win.signals.current_frame = 2
    win.controller.state.result = object()  # only its presence matters here

    win.signals.show_deformed = True
    area._apply_mask_layer_visibility()
    assert not _shown(area)  # deformed frame-3 background
    win.signals.show_deformed = False
    area._apply_mask_layer_visibility()
    assert _shown(area)  # reference geometry: the frame-1 image is what is shown

    win.controller.state.result = None
    win.close()
