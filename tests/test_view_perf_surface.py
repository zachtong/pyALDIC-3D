"""Viewer performance batch V-view: 3D surface topology (Qt-free).

The crack-aware 3D view froze 4-12 s per frame: a pure-Python per-edge crack
loop ran on every frame although its result does not depend on the frame, plus
a 96 MB float copy of the mask per render. These tests pin:

* the vectorised crack filter against the original per-edge loop (exact);
* the vectorised quad lattice against the original dict loop (exact order);
* the frame-independent topology cache (reference coords, ROI, barrier), which
  follows ROI edits by CONTENT;
* bool masks are consumed without a float copy.
"""

from __future__ import annotations

import time

import numpy as np
import pytest

from al_dic_3d.viz3d import surface


def _loop_filter_cross_barrier(cells, ref, barrier):
    """The pre-V-view implementation (reference semantics)."""
    from al_dic.utils.crack_barrier import segment_crosses_barrier

    b = np.ascontiguousarray(barrier, dtype=np.float64)
    h, w = b.shape

    def inside(x, y):
        xi = min(max(int(round(x)), 0), w - 1)
        yi = min(max(int(round(y)), 0), h - 1)
        return bool(b[yi, xi] >= 0.5)

    k = cells.shape[1]
    keep = np.ones(len(cells), dtype=bool)
    for i, cell in enumerate(cells):
        for e in range(k):
            xa, ya = ref[cell[e]]
            xc, yc = ref[cell[(e + 1) % k]]
            if inside(xa, ya) and inside(xc, yc) and segment_crosses_barrier(xa, ya, xc, yc, b):
                keep[i] = False
                break
    return cells[keep]


def _loop_quads(ref_coords, tol=0.25):
    """The pre-V-view dict-loop quad builder (reference semantics)."""
    coords = np.asarray(ref_coords, dtype=np.float64).reshape(-1, 2)
    ix = surface._lattice_indices(coords[:, 0], tol)
    iy = surface._lattice_indices(coords[:, 1], tol)
    lattice: dict = {}
    for node in np.flatnonzero((ix >= 0) & (iy >= 0)):
        lattice.setdefault((int(ix[node]), int(iy[node])), int(node))
    quads = []
    for (i, j), n00 in lattice.items():
        n10, n11, n01 = (
            lattice.get((i + 1, j)),
            lattice.get((i + 1, j + 1)),
            lattice.get((i, j + 1)),
        )
        if n10 is not None and n11 is not None and n01 is not None:
            quads.append((n00, n10, n11, n01))
    return np.asarray(sorted(quads), dtype=np.int64).reshape(-1, 4)


def _lattice(nx=20, ny=15, step=16.0, origin=40.0):
    xs, ys = np.meshgrid(origin + step * np.arange(nx), origin + step * np.arange(ny))
    return np.column_stack([xs.ravel(), ys.ravel()]).astype(np.float64)


@pytest.fixture(autouse=True)
def _fresh_topology_cache():
    surface.clear_surface_cache()
    yield
    surface.clear_surface_cache()


def test_quad_connectivity_matches_the_dict_loop():
    rng = np.random.default_rng(5)
    ref = _lattice()
    keep = rng.uniform(size=len(ref)) > 0.12  # random holes
    ref = ref[keep]
    ref = np.vstack([ref, ref[:2] + 8.0, ref[3:5]])  # off-lattice + duplicate nodes
    got = surface.build_quad_connectivity(ref)
    np.testing.assert_array_equal(got, _loop_quads(ref))
    assert len(got) > 0


@pytest.mark.parametrize("dtype", [np.float64, np.bool_, np.uint8])
def test_vectorised_crack_filter_matches_the_loop(dtype):
    ref = _lattice()
    barrier = np.ones((320, 420), dtype=np.float64)
    barrier[:, 150:153] = 0.0
    barrier[100:103, 40:200] = 0.0
    quads = surface.build_quad_connectivity(ref)
    tris = surface.build_tri_connectivity(ref)
    b = barrier.astype(dtype)
    for cells in (quads, tris):
        got = surface.filter_cells_cross_barrier(cells, ref, b)
        np.testing.assert_array_equal(got, _loop_filter_cross_barrier(cells, ref, barrier))
        assert 0 < len(got) < len(cells)


def test_crack_filter_is_fast_at_scale():
    ref = _lattice(nx=180, ny=150)  # 27k nodes, ~27k quads
    barrier = np.ones((2600, 3000), dtype=bool)
    barrier[:, 1500:1503] = False
    cells = surface.build_quad_connectivity(ref)
    t = time.perf_counter()
    kept = surface.filter_cells_cross_barrier(cells, ref, barrier)
    assert time.perf_counter() - t < 1.0  # the old loop took several seconds
    assert len(kept) == len(cells) - 149  # one crossed column of quads


def test_surface_topology_cached_per_reference_roi_and_barrier(monkeypatch):
    ref = _lattice()
    roi = np.zeros((320, 420), dtype=bool)
    roi[30:280, 30:380] = True
    calls = {"quads": 0, "barrier": 0}
    real_quads = surface.build_quad_connectivity
    real_barrier = surface.filter_cells_cross_barrier

    def quads(*a, **k):
        calls["quads"] += 1
        return real_quads(*a, **k)

    def barrier_f(*a, **k):
        calls["barrier"] += 1
        return real_barrier(*a, **k)

    monkeypatch.setattr(surface, "build_quad_connectivity", quads)
    monkeypatch.setattr(surface, "filter_cells_cross_barrier", barrier_f)
    a = surface.surface_cells(ref, roi, roi)
    b = surface.surface_cells(ref.copy(), roi.copy(), roi.copy())  # same CONTENT
    np.testing.assert_array_equal(a, b)
    assert calls == {"quads": 1, "barrier": 1}
    edited = roi.copy()
    edited[:, 200:203] = False  # an ROI edit (new crack) recomputes
    c = surface.surface_cells(ref, edited, edited)
    assert calls["barrier"] == 2 and len(c) < len(a)


def test_build_surface_polydata_reuses_topology_across_frames(monkeypatch):
    pytest.importorskip("pyvista")
    ref = _lattice()
    roi = np.ones((320, 420), dtype=bool)
    roi[:, 150:153] = False
    pts = np.column_stack([ref * 0.1, np.full(len(ref), 800.0)])
    calls = {"n": 0}
    real = surface.filter_cells_cross_barrier

    def spy(*a, **k):
        calls["n"] += 1
        return real(*a, **k)

    monkeypatch.setattr(surface, "filter_cells_cross_barrier", spy)
    s1 = surface.build_surface_polydata(pts, pts[:, 0], "U", ref, roi, roi)
    pts2 = pts.copy()
    pts2[:, 2] += 3.0
    pts2[5] = np.nan  # per-frame invalid node: still filtered per frame
    s2 = surface.build_surface_polydata(pts2, pts2[:, 0], "U", ref, roi, roi)
    assert calls["n"] == 1
    assert s2.n_cells < s1.n_cells


def test_nodes_in_mask_accepts_bool_without_threshold_copy():
    ref = _lattice(nx=4, ny=3)
    mask = np.zeros((200, 200), dtype=bool)
    mask[:, :80] = True
    np.testing.assert_array_equal(
        surface.nodes_in_mask(ref, mask), surface.nodes_in_mask(ref, mask.astype(np.uint8))
    )
