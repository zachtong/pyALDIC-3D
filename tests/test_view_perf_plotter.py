"""Viewer performance batch V-view — 3D view robustness and first-open cost.

No real OpenGL: the plotter is faked (the degradation-test idiom), so these run
headless on every CI runner.

* the first open is visibly busy (wait cursor + message painted first);
* the interactor is created without pyvistaqt's 5 Hz auto-render timer and a
  scene rebuild renders once, not once per ``add_mesh``;
* a failure in a LATER render, or a VTK OpenGL/context error reported by the
  FIRST render, degrades to the translated message instead of propagating.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import sys
import types
from contextlib import contextmanager
from types import SimpleNamespace

import numpy as np
import pytest

pytest.importorskip("PySide6")
pv = pytest.importorskip("pyvista")

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication, QWidget  # noqa: E402

from al_dic_3d.gui.app import create_app  # noqa: E402
from al_dic_3d.gui.widgets.view3d import View3D  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


def _grid():
    xs, ys = np.meshgrid(100.0 + 16.0 * np.arange(5), 50.0 + 16.0 * np.arange(4))
    ref = np.column_stack([xs.ravel(), ys.ravel()])
    pts = np.column_stack([ref * 0.1, np.full(len(ref), 800.0)])
    return pts, pts[:, 0], ref


class _Plotter:
    """Records calls; ``fail_on`` names a method that raises."""

    def __init__(self, fail_on: str | None = None):
        self.calls: list[tuple] = []
        self.camera_position = ("c",)
        self.fail_on = fail_on
        self.interactor = QWidget()

    def _hit(self, name, **kw):
        self.calls.append((name, kw))
        if self.fail_on == name:
            raise RuntimeError(f"{name} exploded")

    def set_background(self, *_a):
        self._hit("set_background")

    def clear(self):
        self._hit("clear")

    def add_mesh(self, mesh, **kw):
        self._hit("add_mesh", render=kw.get("render", True))
        return SimpleNamespace(
            mapper=SimpleNamespace(
                scalar_range=(0, 1), lookup_table=SimpleNamespace(scalar_range=(0, 1))
            )
        )

    def reset_camera(self):
        self._hit("reset_camera")

    def render(self):
        self._hit("render")

    def close(self):
        self._hit("close")


def _install_fake_pyvistaqt(monkeypatch, plotter, seen):
    fake = types.ModuleType("pyvistaqt")

    def factory(parent=None, **kwargs):
        seen["kwargs"] = kwargs
        seen["cursor"] = QApplication.overrideCursor()
        seen["cursor_shape"] = None if seen["cursor"] is None else seen["cursor"].shape()
        seen["text"] = parent._placeholder.text()
        return plotter

    fake.QtInteractor = factory
    monkeypatch.setitem(sys.modules, "pyvistaqt", fake)


def test_first_open_is_busy_and_creates_no_auto_render_timer(qapp, monkeypatch):
    plotter = _Plotter()
    seen: dict = {}
    _install_fake_pyvistaqt(monkeypatch, plotter, seen)
    view = View3D()
    view.show()
    pts, vals, ref = _grid()
    view.update_view(pts, vals, field_label="U", cmap="turbo", vmin=0, vmax=1, ref_coords=ref)
    assert seen["kwargs"].get("auto_update") is False
    assert seen["cursor_shape"] == Qt.CursorShape.WaitCursor  # busy while starting
    assert seen["text"] == view.tr("Starting the 3D view…")
    assert QApplication.overrideCursor() is None  # restored afterwards
    assert not view._placeholder.isVisible()  # the scene replaced the message
    view.close()


def test_scene_rebuild_renders_once(qapp):
    view = View3D()
    plotter = _Plotter()
    view._plotter = plotter
    rig = SimpleNamespace(pose=lambda cam: (np.eye(3), np.zeros(3)))
    pts, vals, ref = _grid()
    view.update_view(
        pts, vals, field_label="U", cmap="turbo", vmin=0, vmax=1, rig=rig, ref_coords=ref
    )
    adds = [kw for name, kw in plotter.calls if name == "add_mesh"]
    assert len(adds) == 3  # surface + two frusta ...
    assert all(kw["render"] is False for kw in adds)  # ... none rendering on its own
    view.close()


def test_failure_in_a_later_render_degrades_to_message(qapp):
    view = View3D()
    plotter = _Plotter()
    view._plotter = plotter
    pts, vals, ref = _grid()
    view.update_view(pts, vals, field_label="U", cmap="turbo", vmin=0, vmax=1, ref_coords=ref)
    plotter.fail_on = "render"  # e.g. the GL context died (display change, RDP)
    pts2 = pts.copy()
    pts2[:, 2] += 1.0
    view.update_view(pts2, vals, field_label="U", cmap="turbo", vmin=0, vmax=1, ref_coords=ref)
    assert view._failed and view._plotter is None
    prefix = view.tr("3D view unavailable: {0}").split("{0}")[0]
    assert view._placeholder.text().startswith(prefix)
    assert "render exploded" in view._placeholder.text()
    # no retry storm: later updates short-circuit quietly
    view.update_view(pts2, vals, field_label="U", cmap="turbo", vmin=0, vmax=1, ref_coords=ref)
    assert view._plotter is None
    view.close()


def test_gl_error_reported_by_first_render_degrades(qapp, monkeypatch):
    class _Catcher:
        def __init__(self, **_kw):
            self.error_events = []

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            self.error_events.append(
                SimpleNamespace(alert="Unable to find a valid OpenGL 3.2 or later implementation.")
            )
            return False

    monkeypatch.setattr(pv, "VtkErrorCatcher", _Catcher)
    view = View3D()
    view._plotter = _Plotter()
    pts, vals, ref = _grid()
    view.update_view(pts, vals, field_label="U", cmap="turbo", vmin=0, vmax=1, ref_coords=ref)
    assert view._failed
    assert "OpenGL 3.2" in view._placeholder.text()
    view.close()


def test_non_gl_vtk_errors_do_not_disable_the_view(qapp, monkeypatch):
    @contextmanager
    def catcher(**_kw):
        ns = SimpleNamespace(error_events=[SimpleNamespace(alert="vtkPolyData: bad scalars")])
        yield ns

    monkeypatch.setattr(pv, "VtkErrorCatcher", catcher)
    view = View3D()
    view._plotter = _Plotter()
    pts, vals, ref = _grid()
    view.update_view(pts, vals, field_label="U", cmap="turbo", vmin=0, vmax=1, ref_coords=ref)
    assert not view._failed and view._rendered_once
    view.close()


def test_surface_build_error_shows_message_without_disabling(qapp, monkeypatch):
    from al_dic_3d.gui.widgets import view3d as v3d

    view = View3D()
    view._plotter = _Plotter()
    pts, vals, ref = _grid()
    real = v3d.build_surface_mesh

    def boom(*a, **k):
        raise ValueError("bad frame data")

    monkeypatch.setattr(v3d, "build_surface_mesh", boom)
    view.update_view(pts, vals, field_label="U", cmap="turbo", vmin=0, vmax=1, ref_coords=ref)
    assert not view._failed  # a data problem is not a missing OpenGL
    assert "bad frame data" in view._placeholder.text()
    monkeypatch.setattr(v3d, "build_surface_mesh", real)
    view.update_view(pts, vals, field_label="U", cmap="turbo", vmin=0, vmax=1, ref_coords=ref)
    assert not view._placeholder.isVisibleTo(view) and view._rendered_once
    view.close()
