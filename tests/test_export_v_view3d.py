"""3D-view export matches the interactive 3D view (fix batch V, M4 / H5).

* colour range: the interactive view uses a per-frame 2nd-98th percentile over
  the nodes inside the ROI (or the user's fixed range); the sequence export used
  min/max over ALL frames and the turntable one frame's min/max;
* the exported surface honours the drawn ROI (``build_surface`` passed None);
* the camera comes from the user's view when one is supplied, else the 3D
  View's first framing (from the left camera, on the surface bounds) — the old
  isometric default looked at the specimen from behind;
* values/labels follow the display unit (``value_scale`` / ``field_label``);
* a writer that cannot open raises; a cancelled animation is deleted.

Export parity with the reworked 3D View: lit smooth shading and the fitted
scalar bar, the deformation magnification, and a sequence rebuild that never
calls ``plotter.clear()`` (it removed the light kit: unlit frames).
"""

from __future__ import annotations

import itertools
import threading
from types import SimpleNamespace

import numpy as np
import pytest

pv = pytest.importorskip("pyvista")

from al_dic_3d.export import render3d  # noqa: E402
from al_dic_3d.export.tables import display_field_frame  # noqa: E402
from al_dic_3d.viz3d.fieldmap import auto_range, visible_values  # noqa: E402
from al_dic_3d.viz3d.view_setup import scalar_bar_args, tick_format  # noqa: E402
from tests.synth_export import grid_result  # noqa: E402

CAMERA = ((10.0, -40.0, 900.0), (0.0, 0.0, 800.0), (0.0, 1.0, 0.0))


class _Mapper:
    def __init__(self, clim):
        self.scalar_range = clim
        self.lookup_table = SimpleNamespace(scalar_range=clim)


class _Bar:
    """A vtkScalarBarActor's tick format."""

    def __init__(self, fmt):
        self.fmt = fmt

    def SetLabelFormat(self, fmt):  # noqa: N802 - the VTK method name
        self.fmt = fmt


class _ScalarBars(dict):
    """pyvista's ``plotter.scalar_bars``: title -> bar actor; clears counted."""

    def __init__(self):
        super().__init__()
        self.clears = 0

    def clear(self):
        self.clears += 1
        super().clear()


class _FakePlotter:
    def __init__(self):
        self.camera_position = None
        self.camera_sets: list = []
        self.meshes: list = []
        self.mesh_kwargs: list[dict] = []
        self.actors: list = []
        self.removed: list = []
        self.resets: list[dict] = []
        self.texts: list[tuple] = []
        self.clims: list = []
        self.iso = 0
        self.clears = 0
        self.actor = None
        self.camera = SimpleNamespace(Azimuth=lambda deg: None)
        self.scalar_bars = _ScalarBars()

    def __setattr__(self, name, value):
        if name == "camera_position" and value is not None:
            self.__dict__.setdefault("camera_sets", []).append(value)
        super().__setattr__(name, value)

    def clear(self):
        self.clears += 1  # would also remove the light kit

    def add_mesh(self, mesh, **kw):
        self.meshes.append(mesh)
        self.mesh_kwargs.append(kw)
        self.clims.append(tuple(kw["clim"]))
        bar_args = kw.get("scalar_bar_args", {})
        self.titles = bar_args.get("title")
        self.scalar_bars[self.titles] = _Bar(bar_args.get("fmt"))
        self.actor = SimpleNamespace(mapper=_Mapper(tuple(kw["clim"])))
        self.actors.append(self.actor)
        return self.actor

    def remove_actor(self, actor, render=True):
        self.removed.append(actor)

    def add_text(self, text, **kw):
        self.texts.append((text, kw))

    def reset_camera(self, render=True, bounds=None):
        self.resets.append({"bounds": bounds, "camera": self.camera_position})

    def view_isometric(self):
        self.iso += 1

    def render(self):
        pass

    def close(self):
        pass


@pytest.fixture()
def fake(monkeypatch):
    made: list[_FakePlotter] = []
    shots: list[tuple] = []
    points: list[np.ndarray] = []
    fmts: list[str] = []

    def make(window_size, background):
        p = _FakePlotter()
        made.append(p)
        return p

    def shot(pl):
        # Record the colour range, the bar's tick format and the drawn
        # geometry live at screenshot time (in-place updates too).
        shots.append(tuple(pl.actor.mapper.lookup_table.scalar_range))
        fmts.append(pl.scalar_bars[pl.titles].fmt)
        points.append(np.array(pl.meshes[-1].points))
        return np.zeros((24, 32, 3), np.uint8)

    monkeypatch.setattr(render3d, "_make_plotter", make)
    monkeypatch.setattr(render3d, "_screenshot_bgr", shot)
    return SimpleNamespace(made=made, shots=shots, points=points, fmts=fmts)


def _roi(shape=(200, 200)) -> np.ndarray:
    roi = np.zeros(shape, bool)
    roi[:, :120] = True
    return roi


def test_sequence_uses_the_per_frame_percentile_inside_the_roi(tmp_path, fake):
    result = grid_result(n_frames=4)
    roi = _roi()
    out = render3d.export_view3d_frames(
        tmp_path,
        "v",
        "20260913000000",
        result,
        "U",
        write_frames=True,
        roi_mask=roi,
        value_scale=1000.0,
    )
    assert len(out) == 4 and not out.cancelled
    want = []
    for k in range(4):
        vals = display_field_frame(result, "U", k, deformed=True) * 1000.0
        lo, hi = auto_range(visible_values(vals, result.ref_coords, roi))
        want.append((lo, hi))
    got = fake.shots
    assert len(got) == 4
    for (glo, ghi), (wlo, whi) in zip(got[1:], want[1:], strict=True):
        assert glo == pytest.approx(wlo) and ghi == pytest.approx(whi)
    # Not the old all-frame min/max: frame 1's range differs from frame 3's.
    assert got[1] != pytest.approx(got[3])


def test_sequence_honours_fixed_range_roi_camera_and_label(tmp_path, fake):
    result = grid_result(n_frames=3)
    roi = _roi()
    render3d.export_view3d_frames(
        tmp_path,
        "v",
        "20260913000001",
        result,
        "W",
        write_frames=True,
        roi_mask=roi,
        auto_range=False,
        vmin=-5.0,
        vmax=7.0,
        camera=CAMERA,
        field_label="W (µm)",
    )
    pl = fake.made[0]
    assert all(c == (-5.0, 7.0) for c in fake.shots)
    assert pl.camera_sets and all(c == CAMERA for c in pl.camera_sets)
    assert pl.iso == 0 and not pl.resets  # the user's camera as is, never re-framed
    assert pl.titles == "W (µm)"
    full = render3d.build_surface(
        result.reconstruction.points[0],
        np.ones(result.reconstruction.n_pts),
        "W",
        result.ref_coords,
    )
    assert pl.meshes[0].n_cells < full.n_cells  # the ROI removed the right-hand cells


def test_turntable_uses_the_user_camera_and_frame_percentile(tmp_path, fake):
    result = grid_result(n_frames=3)
    roi = _roi()
    out = render3d.export_view3d_turntable(
        tmp_path,
        "t",
        "20260913000002",
        result,
        "V",
        frame_k=2,
        n_orbit=4,
        roi_mask=roi,
        camera=CAMERA,
        animation_format="gif",
    )
    assert len(out) == 1 and out[0].suffix == ".gif"
    pl = fake.made[0]
    assert pl.camera_sets[0] == CAMERA and pl.iso == 0
    vals = display_field_frame(result, "V", 2, deformed=True)
    lo, hi = auto_range(visible_values(vals, result.ref_coords, roi))
    assert pl.clims[0] == (pytest.approx(lo), pytest.approx(hi))


def test_sequence_animation_writer_failure_raises(tmp_path, fake, monkeypatch):
    from al_dic_3d.export import animation

    class Closed:
        def __init__(self, *a, **k):
            pass

        def isOpened(self):  # noqa: N802
            return False

        def release(self):
            pass

    monkeypatch.setattr(animation.cv2, "VideoWriter", Closed)
    result = grid_result(n_frames=2)
    with pytest.raises(OSError):
        render3d.export_view3d_frames(
            tmp_path,
            "v",
            "20260913000003",
            result,
            "U",
            write_frames=False,
            animation_format="mp4",
        )
    with pytest.raises(OSError):
        render3d.export_view3d_turntable(
            tmp_path, "t", "20260913000004", result, "U", n_orbit=4, animation_format="mp4"
        )


def test_cancelled_turntable_is_deleted(tmp_path, fake):
    result = grid_result(n_frames=2)
    stop = threading.Event()
    out = render3d.export_view3d_turntable(
        tmp_path,
        "t",
        "20260913000005",
        result,
        "U",
        n_orbit=6,
        animation_format="gif",
        stop_event=stop,
        progress_cb=lambda d, t, s: stop.set(),
    )
    assert out == [] and out.cancelled
    assert not list(tmp_path.rglob("*.gif"))


def test_sequence_frame_without_surface_keeps_animation_timing(tmp_path, fake):
    result = grid_result(n_frames=3)
    result.reconstruction.points[1] = np.nan  # nothing to draw at frame 2
    out = render3d.export_view3d_frames(
        tmp_path,
        "v",
        "20260913000006",
        result,
        "U",
        write_frames=True,
        animation_format="gif",
    )
    gifs = [p for p in out if p.suffix == ".gif"]
    assert len(gifs) == 1
    from PIL import Image

    im = Image.open(gifs[0])
    assert getattr(im, "n_frames", 1) == 3  # a blank frame holds the slot
    assert len([p for p in out if p.suffix == ".png"]) == 2
    assert len(out.skipped) == 1


# ---------------------------------------------------------------------------
# Export parity with the reworked 3D View
# ---------------------------------------------------------------------------


_STAMPS = itertools.count(20260913000100)


def _export(mode: str, tmp_path, result, **kw):
    """Run one of the three 3D exports of field U, labelled "U (mm)" (fake plotter)."""
    rec = result.reconstruction
    ts = str(next(_STAMPS))
    if mode == "frame":
        return render3d.render_view3d_frame(
            rec.points[0],
            display_field_frame(result, "U", 0, deformed=True),
            field_label="U (mm)",
            ref_coords=result.ref_coords,
            ref_points=rec.points[0],
            **kw,
        )
    if mode == "sequence":
        return render3d.export_view3d_frames(
            tmp_path, "v", ts, result, "U", write_frames=True, field_label="U (mm)", **kw
        )
    return render3d.export_view3d_turntable(
        tmp_path,
        "t",
        ts,
        result,
        "U",
        n_orbit=2,
        animation_format="gif",
        field_label="U (mm)",
        **kw,
    )


@pytest.mark.parametrize("mode", ["frame", "sequence", "turntable"])
def test_default_framing_looks_from_the_left_camera_at_the_surface(tmp_path, fake, mode):
    result = grid_result(n_frames=3)
    _export(mode, tmp_path, result)
    pl = fake.made[0]
    assert pl.iso == 0  # never the isometric view from behind
    assert len(pl.resets) == 1  # framed once (a sequence never jumps)
    pts = result.reconstruction.points[0]  # the first drawn surface
    want = np.column_stack([pts.min(axis=0), pts.max(axis=0)]).ravel()
    np.testing.assert_allclose(pl.resets[0]["bounds"], want)  # the surface bounds only
    position, focal, up = pl.resets[0]["camera"]
    assert position[2] < focal[2]  # the eye sits on the camera side (toward z = 0)
    assert up[1] < -0.9  # image-up (world -y) is up on screen


@pytest.mark.parametrize("mode", ["frame", "sequence", "turntable"])
def test_surface_is_lit_like_the_view_with_its_fitted_scalar_bar(tmp_path, fake, mode):
    result = grid_result(n_frames=2)
    _export(mode, tmp_path, result)
    kw = fake.made[0].mesh_kwargs[0]
    assert kw["lighting"] is True and kw["smooth_shading"] is True
    assert (kw["ambient"], kw["diffuse"], kw["specular"]) == (0.3, 0.7, 0.1)
    lo, hi = kw["clim"]
    assert kw["scalar_bar_args"] == scalar_bar_args("U (mm)", "black", lo, hi)

    _export(mode, tmp_path, result, shading=False)
    kw = fake.made[1].mesh_kwargs[0]
    assert kw["lighting"] is False and kw["smooth_shading"] is False
    assert "ambient" not in kw  # shading off: the exact colormap colours


def test_sequence_swaps_the_surface_without_clearing_the_scene(tmp_path, fake):
    result = grid_result(n_frames=4)
    result.reconstruction.points[2, 0] = np.nan  # frame 3 changes the topology
    out = render3d.export_view3d_frames(
        tmp_path, "v", "20260913000012", result, "U", write_frames=True
    )
    assert len(out) == 4
    pl = fake.made[0]
    assert pl.clears == 0  # clear() would drop the light kit -> unlit frames
    # Frame 2 updates in place; frames 3 and 4 change the topology: each
    # rebuild removes exactly the previous surface actor (its bar goes with it).
    assert len(pl.actors) == 3
    assert pl.removed == pl.actors[:2]
    assert pl.scalar_bars.clears == 2
    assert len(pl.resets) == 1 and pl.iso == 0  # the camera is kept through rebuilds


def test_in_place_frames_relabel_the_scalar_bar_for_their_range(tmp_path, fake):
    result = grid_result(n_frames=4)  # one topology: every later frame is in place
    render3d.export_view3d_frames(tmp_path, "v", "20260913000016", result, "U")
    assert len(fake.made[0].actors) == 1
    want = [tick_format(lo, hi) for lo, hi in fake.shots]
    assert fake.fmts == want
    assert len(set(want)) > 1  # the decimals do change along this sequence


def test_magnification_reaches_the_exported_sequence_geometry(tmp_path, fake):
    result = grid_result(n_frames=3)
    pts = result.reconstruction.points
    render3d.export_view3d_frames(
        tmp_path,
        "v",
        "20260913000013",
        result,
        "W",
        write_frames=True,
        magnification=50.0,
        field_label="W (mm)",
    )
    assert len(fake.points) == 3
    for k, drawn in enumerate(fake.points):
        np.testing.assert_allclose(drawn, pts[0] + 50.0 * (pts[k] - pts[0]), atol=1e-9)
    # The colours stay the true values (the last frame, updated in place).
    true_w = display_field_frame(result, "W", 2, deformed=True)
    np.testing.assert_allclose(fake.made[0].meshes[-1]["W (mm)"], true_w)


def test_out_of_plane_only_magnification(tmp_path, fake):
    result = grid_result(n_frames=3)
    pts = result.reconstruction.points
    render3d.export_view3d_turntable(
        tmp_path,
        "t",
        "20260913000014",
        result,
        "U",
        frame_k=2,
        n_orbit=2,
        animation_format="gif",
        magnification=100.0,
        normal_only=True,
    )
    drawn = np.asarray(fake.made[0].meshes[0].points)
    # The grid plate faces the camera (normal = world z): only z is magnified.
    np.testing.assert_allclose(drawn[:, :2], pts[0][:, :2], atol=1e-9)
    np.testing.assert_allclose(
        drawn[:, 2], pts[0][:, 2] + 100.0 * (pts[2][:, 2] - pts[0][:, 2]), atol=1e-9
    )


def test_single_frame_magnification_needs_the_reference(fake):
    result = grid_result(n_frames=3)
    pts = result.reconstruction.points
    vals = display_field_frame(result, "U", 2, deformed=True)
    render3d.render_view3d_frame(
        pts[2], vals, field_label="U", ref_points=pts[0], magnification=20.0
    )
    drawn = np.asarray(fake.made[0].meshes[0].points)
    np.testing.assert_allclose(drawn, pts[0] + 20.0 * (pts[2] - pts[0]), atol=1e-9)
    with pytest.raises(ValueError, match="reference"):
        render3d.render_view3d_frame(pts[2], vals, field_label="U", magnification=20.0)


def test_sequence_keeps_the_lights_through_a_rebuild_on_a_real_plotter(tmp_path, monkeypatch):
    try:
        probe = pv.Plotter(off_screen=True, window_size=[32, 32])
        probe.close()
    except Exception as exc:  # pragma: no cover - no off-screen OpenGL here
        pytest.skip(f"no off-screen OpenGL: {exc}")
    lights: list[int] = []
    real_shot = render3d._screenshot_bgr

    def counting_shot(pl):
        lights.append(len(pl.renderer.lights))
        return real_shot(pl)

    monkeypatch.setattr(render3d, "_screenshot_bgr", counting_shot)
    result = grid_result(n_frames=3)
    result.reconstruction.points[1, 0] = np.nan  # frame 2 changes the topology: a rebuild
    out = render3d.export_view3d_frames(
        tmp_path, "v", "20260913000015", result, "U", window_size=(160, 120), write_frames=True
    )
    assert len(out) == 3
    assert len(lights) == 3 and lights[0] > 0
    assert lights == [lights[0]] * 3  # the rebuild kept every light (clear() dropped them all)


@pytest.mark.parametrize("mode", ["frame", "sequence", "turntable"])
def test_note_is_a_corner_text_like_the_view(tmp_path, fake, mode):
    result = grid_result(n_frames=4)
    result.reconstruction.points[2, 0] = np.nan  # the sequence rebuilds on frame 3
    _export(mode, tmp_path, result, note="rigid motion removed (translation)")
    texts = fake.made[0].texts
    assert [t for t, _kw in texts] == ["rigid motion removed (translation)"]  # once
    assert texts[0][1]["position"] == "upper_left"
    _export(mode, tmp_path, result)  # no note: no text
    assert fake.made[1].texts == []
