"""The reworked 3D View: framing, lighting, messages, magnification, toolbar options.

Mostly against a recording fake plotter (no OpenGL); one test renders through a
real off-screen pyvista plotter when this machine can, to prove the lights
survive a scene rebuild (``plotter.clear()`` used to remove them).
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import sys
import types
from types import SimpleNamespace

import numpy as np
import pytest

pytest.importorskip("PySide6")
pv = pytest.importorskip("pyvista")

from PySide6.QtWidgets import QWidget  # noqa: E402

from al_dic_3d.gui.app import create_app  # noqa: E402
from al_dic_3d.gui.widgets.view3d import View3D  # noqa: E402

Z0 = 245.0


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


class _Plotter:
    def __init__(self):
        self.calls: list[tuple] = []
        self.camera_position = ("start",)
        self.interactor = QWidget()
        self.scalar_bars = SimpleNamespace(clear=lambda: self.calls.append(("bars_clear", {})))

    def _hit(self, name, **kw):
        self.calls.append((name, kw))

    def names(self) -> list[str]:
        return [name for name, _ in self.calls]

    def set_background(self, *_a):
        self._hit("set_background")

    def clear(self):
        self._hit("clear")

    def add_mesh(self, mesh, **kw):
        self._hit("add_mesh", mesh=mesh, **kw)
        return SimpleNamespace(
            mapper=SimpleNamespace(
                scalar_range=(0, 1), lookup_table=SimpleNamespace(scalar_range=(0, 1))
            )
        )

    def add_text(self, text, **kw):
        self._hit("add_text", text=text)
        return object()

    def remove_actor(self, actor, render=True):
        self._hit("remove_actor")

    def reset_camera_clipping_range(self):
        self._hit("reset_camera_clipping_range")

    def reset_camera(self, render=True, bounds=None):
        self._hit("reset_camera", bounds=bounds, camera=self.camera_position)

    def render(self):
        self._hit("render")

    def clear_events_for_key(self, key):
        self._hit("clear_events_for_key", key=key)

    def add_axes(self, **_kw):
        self._hit("add_axes")

    def close(self):
        self._hit("close")


def _plate(n: int = 9):
    xs, ys = np.meshgrid(np.arange(n) * 16.0 + 40.0, np.arange(n) * 16.0 + 40.0)
    ref_coords = np.column_stack([xs.ravel(), ys.ravel()])
    x = (ref_coords[:, 0] - ref_coords[:, 0].mean()) * 0.01
    y = (ref_coords[:, 1] - ref_coords[:, 1].mean()) * 0.01
    ref = np.column_stack([x, y, np.full_like(x, Z0)])
    cur = ref.copy()
    cur[:, 2] -= 0.002 * (x**2 + y**2)  # a tiny bowl toward the camera
    return ref, cur, ref_coords


def _view_with_fake(qapp):
    view = View3D()
    view._plotter = _Plotter()
    return view, view._plotter


def _show(view, cur, ref_coords, ref=None, **kw):
    args = {"field_label": "W (mm)", "cmap": "turbo", "vmin": 0.0, "vmax": 1.0}
    args.update(kw)
    view.update_view(cur, cur[:, 2], ref_coords=ref_coords, ref_points=ref, **args)


def test_rebuilds_never_clear_the_lights_and_remove_only_our_actors(qapp):
    view, fp = _view_with_fake(qapp)
    ref, cur, rc = _plate()
    _show(view, cur, rc, ref)
    _show(view, cur, rc, ref, field_label="U (mm)")  # field change: a rebuild
    assert "clear" not in fp.names()
    assert fp.names().count("remove_actor") >= 1 and "bars_clear" in fp.names()
    view.close()


def test_first_framing_looks_from_the_camera_at_the_surface_only(qapp):
    view, fp = _view_with_fake(qapp)
    ref, cur, rc = _plate()
    _show(view, cur, rc, ref, rig=SimpleNamespace(pose=lambda cam: (np.eye(3), np.zeros(3))))
    resets = [kw for name, kw in fp.calls if name == "reset_camera"]
    assert len(resets) == 1
    bounds = resets[0]["bounds"]
    assert bounds is not None and bounds[5] - bounds[4] < 1.0  # the surface, not the frusta
    position, focal, up = resets[0]["camera"]
    assert position[2] < focal[2]  # the eye sits on the camera side (toward z = 0)
    assert up[1] < -0.9  # image-up (world -y) is up on screen
    adds = [kw for name, kw in fp.calls if name == "add_mesh"]
    assert len(adds) == 1  # camera frusta are off by default
    view.close()


def test_a_message_hides_the_scene_page(qapp):
    view, _fp = _view_with_fake(qapp)
    ref, cur, rc = _plate()
    _show(view, cur, rc, ref)
    assert view._stack.currentWidget() is view._scene_page
    view.show_message("Selected field is not available.")
    assert view._stack.currentWidget() is view._placeholder
    _show(view, cur, rc, ref)
    assert view._stack.currentWidget() is view._scene_page
    view.close()


def test_magnification_reference_shape_cameras_and_note(qapp):
    view, fp = _view_with_fake(qapp)
    ref, cur, rc = _plate()
    view._toolbar.set_magnification(100.0)
    view._toolbar._reference.setChecked(True)
    view._toolbar._cameras.setChecked(True)
    rig = SimpleNamespace(pose=lambda cam: (np.eye(3), np.zeros(3)))
    _show(view, cur, rc, ref, rig=rig, note="rigid motion removed (translation)")

    adds = [kw for name, kw in fp.calls if name == "add_mesh"]
    surface = adds[0]["mesh"]
    np.testing.assert_allclose(np.asarray(surface.points), ref + 100.0 * (cur - ref), atol=1e-9)
    assert any(kw.get("style") == "wireframe" for kw in adds)  # the reference shape
    assert len(adds) == 4  # surface + reference + two frusta
    texts = [kw["text"] for name, kw in fp.calls if name == "add_text"]
    assert texts == ["rigid motion removed (translation)"]
    view.close()


def test_changing_an_option_rerenders_from_the_last_frame(qapp):
    view, fp = _view_with_fake(qapp)
    ref, cur, rc = _plate()
    _show(view, cur, rc, ref)
    before = fp.names().count("add_mesh")
    view._toolbar._shading.setChecked(False)
    assert fp.names().count("add_mesh") == before + 1
    last = [kw for name, kw in fp.calls if name == "add_mesh"][-1]
    assert last["lighting"] is False  # shading off: the exact colormap colours
    view.close()


def test_scrubbing_refits_the_clipping_range(qapp):
    view, fp = _view_with_fake(qapp)
    ref, cur, rc = _plate()
    _show(view, cur, rc, ref)
    _show(view, cur + [0.0, 0.0, -0.5], rc, ref)  # same topology: the in-place path
    assert fp.names()[-2:] == ["reset_camera_clipping_range", "render"]
    view.close()


def test_an_all_zero_frame_still_gets_a_colour_range(qapp):
    view, fp = _view_with_fake(qapp)
    ref, _cur, rc = _plate()
    _show(view, ref, rc, ref, vmin=0.0, vmax=0.0)  # frame 1: zero displacement
    clim = [kw for name, kw in fp.calls if name == "add_mesh"][0]["clim"]
    assert clim[1] > clim[0]
    view.close()


def test_the_unsafe_pyvista_keys_are_removed(qapp, monkeypatch):
    plotter = _Plotter()
    fake = types.ModuleType("pyvistaqt")
    fake.QtInteractor = lambda parent=None, **_kw: plotter
    monkeypatch.setitem(sys.modules, "pyvistaqt", fake)
    view = View3D()
    ref, cur, rc = _plate()
    _show(view, cur, rc, ref)
    cleared = {kw["key"] for name, kw in plotter.calls if name == "clear_events_for_key"}
    assert {"q", "v"} <= cleared  # 'q' used to tear the embedded plotter down
    assert "add_axes" in plotter.names()  # the orientation triad
    view.close()


def test_auto_picks_a_visible_factor(qapp):
    view, _fp = _view_with_fake(qapp)
    ref, cur, rc = _plate()
    _show(view, cur, rc, ref)
    view._auto_magnification()
    assert view.options().magnification > 1.0
    view.close()


def test_lights_survive_a_rebuild_on_a_real_plotter(qapp):
    try:
        plotter = pv.Plotter(off_screen=True, window_size=[160, 120])
    except Exception as exc:  # pragma: no cover - no offscreen GL here
        pytest.skip(f"no off-screen OpenGL: {exc}")
    plotter._first_time = False  # what pyvistaqt's interactor sets
    view = View3D()
    view._plotter = plotter
    ref, cur, rc = _plate()
    try:
        _show(view, cur, rc, ref)
        lights_before = len(plotter.renderer.lights)
        _show(view, cur, rc, ref, field_label="U (mm)")  # a full rebuild
        assert lights_before > 0
        assert len(plotter.renderer.lights) == lights_before
    finally:
        view._plotter = None
        plotter.close()
        view.close()
