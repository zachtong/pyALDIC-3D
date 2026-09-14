"""The 3D export uses the interactive 3D view's current camera (fix batch V, H7)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

from types import SimpleNamespace

import pytest

pytest.importorskip("PySide6")

from al_dic_3d.gui.app import create_app  # noqa: E402
from al_dic_3d.gui.main_window import MainWindow3D  # noqa: E402
from al_dic_3d.gui.widgets.view3d import View3D  # noqa: E402

CAMERA = ((1.0, 2.0, 3.0), (0.0, 0.0, 0.5), (0.0, 0.0, 1.0))


class _Cam:
    """The attributes of pyvista's CameraPosition the widget reads."""

    position = CAMERA[0]
    focal_point = CAMERA[1]
    viewup = CAMERA[2]


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


def _show_surface(view: View3D) -> None:
    view._plotter = SimpleNamespace(camera_position=_Cam())
    view._surf = object()
    view._reset_camera_pending = False


def _drop_stub(view: View3D) -> None:
    view._plotter = view._surf = None  # never tear the stub down as a plotter


def test_no_camera_until_a_surface_is_shown(qapp):
    view = View3D()
    assert view.camera_position() is None  # no plotter yet
    view._plotter = SimpleNamespace(camera_position=_Cam())
    assert view.camera_position() is None  # a plotter, but nothing rendered
    _drop_stub(view)


def test_camera_is_plain_float_tuples(qapp):
    view = View3D()
    _show_surface(view)
    assert view.camera_position() == CAMERA
    _drop_stub(view)


def test_no_camera_while_new_results_wait_to_be_framed(qapp):
    view = View3D()
    _show_surface(view)
    view.request_camera_reset()  # the next render re-frames: this view is stale
    assert view.camera_position() is None
    _drop_stub(view)


def test_export_dialog_reads_the_live_3d_camera(qapp):
    win = MainWindow3D()
    provider = win._right._view3d_camera_provider
    assert provider is not None
    assert provider() is None  # nothing rendered: the export uses its isometric view
    view = win._canvas_area._view3d
    _show_surface(view)
    assert provider() == CAMERA
    _drop_stub(view)
    win.close()
