"""3D-view export matches the interactive 3D view (fix batch V, M4 / H5).

* colour range: the interactive view uses a per-frame 2nd-98th percentile over
  the nodes inside the ROI (or the user's fixed range); the sequence export used
  min/max over ALL frames and the turntable one frame's min/max;
* the exported surface honours the drawn ROI (``build_surface`` passed None);
* the camera comes from the user's view when one is supplied (was always
  isometric);
* values/labels follow the display unit (``value_scale`` / ``field_label``);
* a writer that cannot open raises; a cancelled animation is deleted.
"""

from __future__ import annotations

import threading
from types import SimpleNamespace

import numpy as np
import pytest

pv = pytest.importorskip("pyvista")

from al_dic_3d.export import render3d  # noqa: E402
from al_dic_3d.export.tables import display_field_frame  # noqa: E402
from al_dic_3d.viz3d.fieldmap import auto_range, visible_values  # noqa: E402
from tests.synth_export import grid_result  # noqa: E402

CAMERA = ((10.0, -40.0, 900.0), (0.0, 0.0, 800.0), (0.0, 1.0, 0.0))


class _Mapper:
    def __init__(self, clim):
        self.scalar_range = clim
        self.lookup_table = SimpleNamespace(scalar_range=clim)


class _FakePlotter:
    def __init__(self):
        self.camera_position = None
        self.camera_sets: list = []
        self.meshes: list = []
        self.clims: list = []
        self.iso = 0
        self.actor = None
        self.camera = SimpleNamespace(Azimuth=lambda deg: None)

    def __setattr__(self, name, value):
        if name == "camera_position" and value is not None:
            self.__dict__.setdefault("camera_sets", []).append(value)
        super().__setattr__(name, value)

    def clear(self):
        pass

    def add_mesh(self, mesh, **kw):
        self.meshes.append(mesh)
        self.clims.append(tuple(kw["clim"]))
        self.titles = kw.get("scalar_bar_args", {}).get("title")
        self.actor = SimpleNamespace(mapper=_Mapper(tuple(kw["clim"])))
        return self.actor

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

    def make(window_size, background):
        p = _FakePlotter()
        made.append(p)
        return p

    def shot(pl):
        # Record the colour range live at screenshot time (in-place updates too).
        shots.append(tuple(pl.actor.mapper.lookup_table.scalar_range))
        return np.zeros((24, 32, 3), np.uint8)

    monkeypatch.setattr(render3d, "_make_plotter", make)
    monkeypatch.setattr(render3d, "_screenshot_bgr", shot)
    return SimpleNamespace(made=made, shots=shots)


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
    assert pl.iso == 0  # the user's camera, never the isometric default
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
