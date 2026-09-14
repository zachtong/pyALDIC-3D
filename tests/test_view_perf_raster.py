"""Viewer performance batch V-view: the Lagrangian mesh rasterizer (Qt-free).

The dense overlay no longer rebuilds a Delaunay per (frame, field): the
REFERENCE triangulation is rasterized once per frame at the frame's node
positions into a barycentric table, and every field of that frame is a cheap
gather. These tests pin the table against scipy's LinearNDInterpolator, the
NaN semantics (a triangle with an invalid vertex is transparent inside, its
valid neighbours stay drawn up to the shared edge), the warp (reference
positions of deformed grid points), the scatter_to_grid-identical grid, and the
exact, vectorised crack-barrier edge test.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.interpolate import LinearNDInterpolator
from scipy.spatial import Delaunay

from al_dic_3d.viz3d.raster import (
    GridSpec,
    MeshTopology,
    cells_cross_barrier,
    edges_cross_barrier,
    rasterize_mesh,
)


def _lattice(nx=9, ny=7, step=16.0, origin=40.0, jitter=0.0, seed=0):
    xs, ys = np.meshgrid(origin + step * np.arange(nx), origin + step * np.arange(ny))
    pts = np.column_stack([xs.ravel(), ys.ravel()]).astype(np.float64)
    if jitter:
        pts += np.random.default_rng(seed).uniform(-jitter, jitter, pts.shape)
    return pts


@pytest.mark.parametrize(
    ("img_shape", "step", "jitter"),
    [((200, 260), 16, 0.0), ((180, 190), 10, 2.5), ((64, 70), 7, 0.0), ((300, 300), 3, 0.7)],
)
def test_grid_spec_matches_scatter_to_grid(img_shape, step, jitter):
    from al_dic.utils.interpolation import scatter_to_grid

    pts = _lattice(step=float(max(step, 4)), jitter=jitter)
    _, info = scatter_to_grid(pts, pts[:, 0], img_shape=img_shape, mesh_step=step)
    grid = GridSpec.for_nodes(pts, img_shape, step)
    xg, yg = grid.views()
    np.testing.assert_array_equal(xg, info["x_grid"])
    np.testing.assert_array_equal(yg, info["y_grid"])
    assert grid.step == info["output_step"]
    assert grid.shape == info["x_grid"].shape
    # compact: the 2D views are broadcasts of 1D axes, no per-point storage
    assert xg.strides[0] == 0 and yg.strides[1] == 0


def test_reference_table_matches_linear_interpolation():
    ref = _lattice(jitter=3.0, seed=3)
    topo = MeshTopology.build(ref)
    grid = GridSpec.for_nodes(ref, (200, 260), 16)
    table = rasterize_mesh(ref, topo.simplices, grid)
    vals = np.sin(ref[:, 0] / 30.0) + ref[:, 1] / 50.0
    got = table.interpolate(vals)
    xg, yg = grid.views()
    want = LinearNDInterpolator(Delaunay(ref), vals)(xg, yg)
    both = np.isfinite(want) & np.isfinite(got)
    # identical coverage (same triangulation) and float32-level agreement
    np.testing.assert_array_equal(np.isfinite(got), np.isfinite(want))
    np.testing.assert_allclose(got[both], want[both], rtol=0, atol=2e-5)
    assert got.dtype == np.float32


def test_nan_vertex_blanks_its_triangles_but_keeps_shared_edges():
    ref = _lattice()
    topo = MeshTopology.build(ref)
    grid = GridSpec.for_nodes(ref, (200, 260), 16)
    table = rasterize_mesh(ref, topo.simplices, grid)
    vals = ref[:, 0].copy()
    hole = 3 * 9 + 4  # interior node at (104, 88)
    vals[hole] = np.nan
    got = table.interpolate(vals)
    xs, ys = grid.xs(), grid.ys()

    def at(x, y):
        return got[int(np.searchsorted(ys, y)), int(np.searchsorted(xs, x))]

    assert np.isnan(at(104, 88))  # the invalid node itself
    assert np.isnan(at(108, 92))  # inside a triangle touching it
    assert np.isfinite(at(104 + 32, 88))  # two steps away: drawn
    # the ring of edges opposite the hole belongs to valid triangles too
    assert np.isfinite(at(120, 88)) and at(120, 88) == pytest.approx(120.0)


def test_deformed_positions_reuse_reference_connectivity_and_warp_back():
    ref = _lattice()
    topo = MeshTopology.build(ref)
    shift = np.array([6.0, -4.0])
    pos = ref + shift
    grid = GridSpec.for_nodes(pos, (200, 260), 16)
    table = rasterize_mesh(pos, topo.simplices, grid)
    vals = ref[:, 1] * 2.0
    got = table.interpolate(vals)
    # a material point keeps its value after the rigid shift
    xs, ys = grid.xs(), grid.ys()
    r = int(np.searchsorted(ys, 88 + shift[1]))
    c = int(np.searchsorted(xs, 104 + shift[0]))
    assert got[r, c] == pytest.approx(88 * 2.0, abs=1e-4)
    # the warp returns the reference position of every covered grid point
    back = table.blend(ref)
    gp = table.grid_points()
    np.testing.assert_allclose(back, gp - shift, atol=1e-3)


def test_triangles_with_nan_positions_are_skipped():
    ref = _lattice()
    topo = MeshTopology.build(ref)
    pos = ref.copy()
    lost = 2 * 9 + 2
    pos[lost] = np.nan
    grid = GridSpec.for_nodes(pos[np.isfinite(pos).all(axis=1)], (200, 260), 16)
    table = rasterize_mesh(pos, topo.simplices, grid)
    got = table.interpolate(np.ones(len(ref)))
    xs, ys = grid.xs(), grid.ys()
    x, y = ref[lost]
    assert np.isnan(got[int(np.searchsorted(ys, y)), int(np.searchsorted(xs, x))])
    assert np.isfinite(got).any()


def test_topology_needs_three_non_collinear_nodes():
    assert MeshTopology.build(np.array([[0.0, 0.0], [1.0, 1.0], [np.nan, 0.0]])) is None
    assert MeshTopology.build(np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]])) is None


def test_edge_cap_drops_long_reference_triangles():
    ref = _lattice()
    ref = ref[~((ref[:, 0] > 60) & (ref[:, 0] < 150) & (ref[:, 1] > 60) & (ref[:, 1] < 120))]
    topo = MeshTopology.build(ref)
    capped = topo.drawable(max_edge=2.5 * 16)
    assert 0 < len(capped) < len(topo.simplices)
    pts = ref[capped]
    edges = np.linalg.norm(pts - np.roll(pts, 1, axis=1), axis=2)
    assert edges.max() <= 40.0 + 1e-9
    np.testing.assert_array_equal(topo.drawable(None), topo.simplices)


def _scalar_edge_cross(p0, p1, barrier):
    from al_dic.utils.crack_barrier import segment_crosses_barrier

    h, w = barrier.shape

    def inside(x, y):
        xi = min(max(int(round(x)), 0), w - 1)
        yi = min(max(int(round(y)), 0), h - 1)
        return bool(barrier[yi, xi] >= 0.5)

    return (
        inside(*p0)
        and inside(*p1)
        and segment_crosses_barrier(float(p0[0]), float(p0[1]), float(p1[0]), float(p1[1]), barrier)
    )


def test_edges_cross_barrier_matches_scalar_reference_exactly():
    rng = np.random.default_rng(11)
    barrier = np.ones((120, 150), dtype=np.float64)
    barrier[:, 70:73] = 0.0  # vertical crack
    barrier[30:33, 20:60] = 0.2  # horizontal slit (still < 0.5)
    p0 = rng.uniform(-5, 155, size=(600, 2))
    p1 = p0 + rng.normal(0, 25, size=(600, 2))
    p1[:40] = p0[:40] + rng.uniform(-400, 400, size=(40, 2))  # a few very long edges
    got = edges_cross_barrier(p0, p1, barrier)
    want = np.array([_scalar_edge_cross(a, b, barrier) for a, b in zip(p0, p1, strict=True)])
    np.testing.assert_array_equal(got, want)
    assert want.any() and not want.all()
    # a bool mask gives the same answer as its float image (no float copy needed)
    np.testing.assert_array_equal(edges_cross_barrier(p0, p1, barrier >= 0.5), want)


def test_cells_cross_barrier_quads_and_tris():
    ref = _lattice(nx=13, ny=13)
    barrier = np.ones((300, 300), dtype=bool)
    xc = 40 + 6 * 16 + 8
    barrier[:, xc - 1 : xc + 2] = False
    topo = MeshTopology.build(ref)
    flags = cells_cross_barrier(topo.simplices, ref, barrier)
    cx = ref[topo.simplices, 0]
    straddle = (cx.min(axis=1) < xc) & (cx.max(axis=1) > xc)
    np.testing.assert_array_equal(flags, straddle)
    assert not cells_cross_barrier(topo.simplices, ref, np.ones((300, 300), bool)).any()


def test_chunked_rasterization_and_barrier_scan_match_single_chunk(monkeypatch):
    from al_dic_3d.viz3d import raster

    ref = _lattice(nx=15, ny=12, jitter=2.0, seed=9)
    topo = MeshTopology.build(ref)
    pos = ref + np.array([3.0, -2.0])
    grid = GridSpec.for_nodes(pos, (260, 300), 16)
    rng = np.random.default_rng(4)
    p0 = rng.uniform(0, 280, size=(400, 2))
    p1 = p0 + rng.normal(0, 40, size=(400, 2))
    barrier = np.ones((260, 300), dtype=bool)
    barrier[:, 140:143] = False
    whole = rasterize_mesh(pos, topo.simplices, grid)
    whole_cross = edges_cross_barrier(p0, p1, barrier)
    monkeypatch.setattr(raster, "_RASTER_CHUNK_CANDIDATES", 97)
    monkeypatch.setattr(raster, "_BARRIER_CHUNK_SAMPLES", 53)
    chunked = rasterize_mesh(pos, topo.simplices, grid)
    vals = ref[:, 0] + 0.5 * ref[:, 1]
    np.testing.assert_array_equal(chunked.interpolate(vals), whole.interpolate(vals))
    np.testing.assert_array_equal(edges_cross_barrier(p0, p1, barrier), whole_cross)
