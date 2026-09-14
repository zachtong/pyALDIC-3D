"""Viewer performance batch V-view: dense renderer reuse, bounds, correctness.

* deformed mode builds ONE triangulation per node set (never per frame/field)
  and ONE barycentric table per frame, reused by every field of that frame;
* the warped ROI knockout is computed once per (frame, ROI) and reused;
* caches are bounded by bytes and store float32 grids + 1D axes only;
* the node step and the ROI/crack CONTENT are part of the cache identity
  (a step or ROI edit can never resurface stale grids / crack blanks);
* renders are thread-safe and a clear during a compute plants nothing stale.
"""

from __future__ import annotations

import threading

import numpy as np
import pytest

from al_dic_3d.viz3d import fieldmap as fm
from al_dic_3d.viz3d import raster
from al_dic_3d.viz3d.fieldmap import FieldmapRenderer

IMG = (220, 260)
STEP = 16


def _lattice(nx=12, ny=10, step=16.0, origin=30.0):
    xs, ys = np.meshgrid(origin + step * np.arange(nx), origin + step * np.arange(ny))
    return np.column_stack([xs.ravel(), ys.ravel()]).astype(np.float64)


def _frames(ref, n=4):
    """Rigid-ish motion + a smooth stretch per frame."""
    out = []
    for k in range(n):
        d = np.column_stack([2.0 * k + 0.01 * k * ref[:, 0], -1.5 * k + 0.0 * ref[:, 1]])
        out.append(ref + d)
    return out


def _count_calls(monkeypatch):
    counts = {"topology": 0, "raster": 0}
    real_build = raster.MeshTopology.build.__func__
    real_raster = fm.rasterize_mesh

    def build(cls, ref_pts):
        counts["topology"] += 1
        return real_build(cls, ref_pts)

    def rast(*a, **k):
        counts["raster"] += 1
        return real_raster(*a, **k)

    monkeypatch.setattr(raster.MeshTopology, "build", classmethod(build))
    monkeypatch.setattr(fm, "rasterize_mesh", rast)
    return counts


def _render(r, k, field, pos, ref, vals, **kw):
    d = pos - ref
    return r.render_field_rgba(
        k,
        field,
        pos,
        vals,
        IMG,
        STEP,
        vmin=0.0,
        vmax=300.0,
        deformed=k > 0,
        ref_uv=(d[:, 0], d[:, 1]) if k > 0 else None,
        ref_pts=ref,
        **kw,
    )


def test_deformed_mode_triangulates_once_and_rasterizes_once_per_frame(monkeypatch):
    counts = _count_calls(monkeypatch)
    ref = _lattice()
    frames = _frames(ref)
    r = FieldmapRenderer()
    roi = np.ones(IMG, dtype=bool)
    for k in range(1, 4):
        for field in ("L:U", "L:V", "L:W"):
            rgba, *_ = _render(r, k, field, frames[k], ref, ref[:, 0], roi_mask=roi)
            assert rgba is not None
    assert counts["topology"] == 1  # the reference Delaunay, reused for every frame
    assert counts["raster"] == 3  # one table per frame, shared by all three fields
    # the warped ROI knockout is shared by the fields of a frame too
    assert len(r._warp_cache) == 3


def test_field_switch_at_a_frame_is_a_gather_not_a_rebuild(monkeypatch):
    ref = _lattice()
    frames = _frames(ref)
    r = FieldmapRenderer()
    _render(r, 2, "L:U", frames[2], ref, ref[:, 0])
    counts = _count_calls(monkeypatch)
    _render(r, 2, "L:V", frames[2], ref, ref[:, 1])
    assert counts == {"topology": 0, "raster": 0}


def test_caches_store_float32_grids_and_stay_within_byte_budget(monkeypatch):
    monkeypatch.setattr(fm, "INTERP_CACHE_BYTES", 10_000)
    ref = _lattice()
    frames = _frames(ref)
    r = FieldmapRenderer()
    for k in range(1, 4):
        _render(r, k, "L:U", frames[k], ref, ref[:, 0])
    data, _sig = next(iter(r._interp_cache.values()))
    assert data.dtype == np.float32
    assert r._interp_cache.total_bytes <= 10_000
    _, xg, yg, _ = _render(r, 3, "L:U", frames[3], ref, ref[:, 0])
    assert xg.strides[0] == 0 and yg.strides[1] == 0  # views of 1D axes


def test_node_step_is_part_of_the_cache_identity():
    ref = _lattice()
    r = FieldmapRenderer()
    a, *_, step_a = r.render_field_rgba(0, "L:U", ref, ref[:, 0], IMG, 16, vmin=0, vmax=300)
    b, *_, step_b = r.render_field_rgba(0, "L:U", ref, ref[:, 0], IMG, 8, vmin=0, vmax=300)
    assert (step_a, step_b) == (4, 2)
    assert a.shape != b.shape  # a stale step-16 grid is never served for step 8


def test_crack_blank_follows_the_current_barrier_content():
    """fieldmap ~187-190 kept blanking from the old ROI after an ROI edit."""
    ref = _lattice()
    vals = ref[:, 0] * 1e-3
    r = FieldmapRenderer()

    def blank_cols(xc):
        barrier = np.ones(IMG, dtype=bool)
        barrier[:, xc - 1 : xc + 2] = False
        plain = r.render_field_rgba(0, "L:f", ref, vals, IMG, STEP, vmin=0, vmax=0.3)[0]
        rgba, xg, _yg, _ = r.render_field_rgba(
            0, "L:f", ref, vals, IMG, STEP, vmin=0, vmax=0.3, barrier_mask=barrier
        )
        new_blank = (plain[..., 3] > 0) & (rgba[..., 3] == 0)
        return np.unique(np.asarray(xg)[new_blank])

    first = blank_cols(30 + 3 * 16 + 8)
    second = blank_cols(30 + 8 * 16 + 8)  # the crack moved: no invalidate call
    assert first.size and second.size
    assert first.max() < second.min()  # old blanking did not survive the edit


def test_deformed_crack_travels_with_the_material():
    ref = _lattice()
    shift = np.array([10.0, 0.0])
    pos = ref + shift
    vals = np.ones(len(ref))
    xc = 30 + 5 * 16 + 8
    barrier = np.ones(IMG, dtype=bool)
    barrier[:, xc - 1 : xc + 2] = False
    rgba, xg, yg, _ = FieldmapRenderer().render_field_rgba(
        1,
        "L:f",
        pos,
        vals,
        IMG,
        STEP,
        vmin=0,
        vmax=2,
        deformed=True,
        ref_pts=ref,
        barrier_mask=barrier,
    )
    blank_x = np.asarray(xg)[rgba[..., 3] == 0]
    blank_y = np.asarray(yg)[rgba[..., 3] == 0]
    inner = (blank_y > 60) & (blank_y < 150)
    assert np.any(np.abs(blank_x[inner] - (xc + shift[0])) < 12)


def test_invalid_node_is_a_hole_with_or_without_roi():
    """NaN = invalid end to end: the drawn-ROI path no longer interpolates
    across an invalid node (it matches the valid-node support and 3D view)."""
    ref = _lattice()
    vals = ref[:, 0].copy()
    hole = 4 * 12 + 5
    vals[hole] = np.nan
    x, y = ref[hole]
    roi = np.ones(IMG, dtype=bool)
    for mask in (None, roi):
        rgba, xg, yg, st = FieldmapRenderer().render_field_rgba(
            0, "L:U", ref, vals, IMG, STEP, vmin=0, vmax=300, roi_mask=mask
        )
        c = int(round((x - float(xg.min())) / st))
        rr = int(round((y - float(yg.min())) / st))
        assert rgba[rr, c, 3] == 0
        assert rgba[rr, c + 8, 3] == 255  # two node steps away: drawn


def test_concurrent_renders_and_clear_all_are_safe():
    ref = _lattice()
    frames = _frames(ref, n=6)
    r = FieldmapRenderer()
    errors: list[BaseException] = []

    def worker(offset):
        try:
            for rep in range(3):
                for k in range(1, 6):
                    _render(r, k, f"L:{offset}", frames[k], ref, ref[:, 0] + rep)
        except BaseException as exc:  # noqa: BLE001 - surfaced by the assert below
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
    for t in threads:
        t.start()
    for _ in range(20):
        r.clear_all()
    for t in threads:
        t.join()
    assert not errors


def test_clear_during_compute_plants_no_stale_entry(monkeypatch):
    ref = _lattice()
    r = FieldmapRenderer()
    real = fm.rasterize_mesh

    def clearing(*a, **k):
        out = real(*a, **k)
        r.clear_all()  # results changed while the worker was computing
        return out

    monkeypatch.setattr(fm, "rasterize_mesh", clearing)
    rgba, *_ = r.render_field_rgba(0, "L:U", ref, ref[:, 0], IMG, STEP, vmin=0, vmax=300)
    assert rgba is not None  # the in-flight render still completes ...
    assert len(r._interp_cache) == 0 and len(r._table_cache) == 0  # ... but caches nothing


def test_clear_frame_caches_keeps_reference_geometry():
    ref = _lattice()
    frames = _frames(ref)
    r = FieldmapRenderer()
    _render(r, 0, "L:U", frames[0], ref, ref[:, 0])
    _render(r, 2, "L:U", frames[2], ref, ref[:, 0])
    assert len(r._table_cache) == 2
    r.clear_frame_caches()
    assert len(r._table_cache) == 1 and len(r._ref_interp_cache) == 1
    assert len(r._interp_cache) == 0


@pytest.mark.parametrize("deformed", [False, True])
def test_render_is_deterministic_across_renderers(deformed):
    ref = _lattice()
    pos = _frames(ref)[2] if deformed else ref
    roi = np.zeros(IMG, dtype=bool)
    roi[20:200, 20:240] = True
    roi[80:110, 90:130] = False
    a = _render(FieldmapRenderer(), 2 if deformed else 0, "L:U", pos, ref, ref[:, 1], roi_mask=roi)
    b = _render(FieldmapRenderer(), 2 if deformed else 0, "L:U", pos, ref, ref[:, 1], roi_mask=roi)
    np.testing.assert_array_equal(a[0], b[0])
