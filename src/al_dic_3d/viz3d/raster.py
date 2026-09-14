"""Lagrangian mesh rasterizer for the dense field overlay (Qt-free, numpy-only).

The dense overlay interpolates scattered node values onto a regular output
grid. The old path rebuilt a scipy Delaunay per (frame, field) in deformed mode
and evaluated a ``LinearNDInterpolator`` (point location over ~0.5 M grid
points) for every field AND twice more for the mask warp: ~1 s per frame at
27k nodes / 12 Mpx. This module replaces that with:

* :class:`MeshTopology` — ONE Delaunay of a camera's frame-1 (reference) node
  positions, built once per node set;
* :func:`rasterize_mesh` — the reference triangles drawn at ANY frame's node
  positions (the material mesh moves with the specimen, connectivity kept) into
  a :class:`BaryTable`: per covered grid point, its triangle and barycentric
  weights. ~0.1 s per frame, vectorised numpy;
* :meth:`BaryTable.interpolate` — any field of that frame is then a gather and
  a 3-term weighted sum (a few ms), and :meth:`BaryTable.blend` of the
  reference positions is the exact inverse map used to warp the reference ROI.

NaN semantics (``NaN = invalid``, end to end): a grid point is transparent when
the triangle holding it has an invalid vertex with a POSITIVE weight, so a
triangle touching an invalid node is blank inside while points on edges shared
with valid triangles stay drawn — identical to the valid-node support mask and
the 3D surface, in every mode. Triangles with a non-finite vertex POSITION
(a node lost at this frame) are not drawn at all.

:class:`GridSpec` reproduces ``al_dic.utils.interpolation.scatter_to_grid``'s
"auto" grid exactly (same origin, step and extent) but stores only its 1D axes;
:meth:`GridSpec.views` hands out zero-copy 2D broadcast views for callers that
index ``x_grid[r, c]``.

:func:`edges_cross_barrier` is an exact vectorised port of the scalar crack test
(``al_dic.utils.crack_barrier.segment_crosses_barrier`` plus the both-endpoints-
inside gate) so the overlay and the 3D surface blank the same crack cells.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

# Barycentric weights below this are treated as exactly zero: grid points on a
# triangle edge then ignore the opposite vertex (so an invalid vertex across a
# shared edge never blanks the valid neighbour's edge points).
WEIGHT_EPS = 1e-9
# Candidate (triangle, grid point) pairs evaluated per vectorised chunk: ~150 B
# of temporaries per candidate, so 250k keeps the transient peak near 40 MB at
# unchanged speed (measured 157 MB -> 62 MB peak on a 12 Mpx frame).
_RASTER_CHUNK_CANDIDATES = 250_000
# Barrier samples evaluated per vectorised chunk (edges are length-bucketed).
_BARRIER_CHUNK_SAMPLES = 1_000_000


@dataclass(frozen=True)
class GridSpec:
    """A regular output grid ``x = x0 + i * step``, ``y = y0 + j * step``."""

    x0: int
    y0: int
    step: int
    nx: int
    ny: int

    @classmethod
    def for_nodes(
        cls, pts: NDArray[np.float64], img_shape: tuple[int, int], mesh_step: int
    ) -> GridSpec:
        """``scatter_to_grid(output_mode="auto", oversample=4)``'s grid for ``pts``.

        The grid spans the node bounding box plus half a node step, clipped to
        the image, at ``max(1, mesh_step // 4)`` pixel spacing.
        """
        h, w = int(img_shape[0]), int(img_shape[1])
        step = int(mesh_step)
        out = max(1, step // 4)
        margin = step // 2
        x_min = max(0, int(math.floor(np.nanmin(pts[:, 0]))) - margin)
        x_max = min(w, int(math.ceil(np.nanmax(pts[:, 0]))) + margin)
        y_min = max(0, int(math.floor(np.nanmin(pts[:, 1]))) - margin)
        y_max = min(h, int(math.ceil(np.nanmax(pts[:, 1]))) + margin)
        return cls(x_min, y_min, out, len(range(x_min, x_max, out)), len(range(y_min, y_max, out)))

    @property
    def shape(self) -> tuple[int, int]:
        return (self.ny, self.nx)

    @property
    def size(self) -> int:
        return self.nx * self.ny

    def xs(self) -> NDArray[np.float64]:
        return self.x0 + self.step * np.arange(self.nx, dtype=np.float64)

    def ys(self) -> NDArray[np.float64]:
        return self.y0 + self.step * np.arange(self.ny, dtype=np.float64)

    def views(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Zero-copy read-only ``(x_grid, y_grid)`` shaped like ``meshgrid(xs, ys)``."""
        return (
            np.broadcast_to(self.xs()[None, :], self.shape),
            np.broadcast_to(self.ys()[:, None], self.shape),
        )


def overlay_origin(xg: NDArray, yg: NDArray, out_step: float) -> tuple[float, float]:
    """Where a dense overlay's top-left corner goes, in canvas scene coordinates.

    Grid sample (i, j) was evaluated at image pixel (xg[j], yg[i]) and is drawn
    as an ``out_step``-pixel block centred on that pixel, so the corner lies
    (out_step - 1) / 2 before the first sample (scene pixel k spans [k, k + 1)).
    Fix batch V: the corner sat ON the first sample, which put every value that
    far right of and below its node; the exporter follows the same rule.
    """
    half = (float(out_step) - 1.0) / 2.0
    return float(np.min(xg)) - half, float(np.min(yg)) - half


@dataclass(frozen=True, eq=False)
class MeshTopology:
    """Delaunay connectivity of one camera's frame-1 node positions.

    ``simplices`` index ALL ``n`` nodes (rows with a non-finite reference
    position take part in no triangle); ``longest_edge`` is each triangle's
    longest REFERENCE edge, for the node-free-hole edge cap.
    """

    ref: NDArray[np.float64]
    simplices: NDArray[np.int32]
    longest_edge: NDArray[np.float64]

    @classmethod
    def build(cls, ref_pts: NDArray[np.float64]) -> MeshTopology | None:
        """Triangulate the finite reference nodes; ``None`` when degenerate."""
        from scipy.spatial import Delaunay, QhullError

        ref = np.array(ref_pts, dtype=np.float64).reshape(-1, 2)
        idx = np.flatnonzero(np.isfinite(ref).all(axis=1))
        if idx.size < 3:
            return None
        try:
            tri = Delaunay(ref[idx])
        except (QhullError, ValueError):
            return None  # collinear / duplicate-only node sets have no area
        if len(tri.simplices) == 0:
            return None
        simplices = idx[tri.simplices].astype(np.int32)
        corners = ref[simplices]
        longest = np.sqrt(((corners - np.roll(corners, 1, axis=1)) ** 2).sum(axis=2)).max(axis=1)
        return cls(ref, simplices, longest)

    @property
    def nbytes(self) -> int:
        return int(self.ref.nbytes + self.simplices.nbytes + self.longest_edge.nbytes)

    def drawable(self, max_edge: float | None) -> NDArray[np.int32]:
        """Triangles to draw: all, or those whose longest edge is ``<= max_edge``."""
        if max_edge is None or max_edge <= 0.0:
            return self.simplices
        return self.simplices[self.longest_edge <= float(max_edge)]


@dataclass(frozen=True, eq=False)
class BaryTable:
    """Per covered grid point: flat grid index, triangle, barycentric weights."""

    grid: GridSpec
    simplices: NDArray[np.int32]  # the (drawable) triangles that were rasterized
    cov_idx: NDArray[np.int32]  # (M,) flat indices into the grid
    tri: NDArray[np.int32]  # (M,) row of ``simplices`` holding each point
    weights: NDArray[np.float32]  # (M, 3) barycentric weights, tiny ones zeroed

    @property
    def nbytes(self) -> int:
        return int(self.cov_idx.nbytes + self.tri.nbytes + self.weights.nbytes)

    def _gather(self, values: NDArray[np.float64]) -> NDArray[np.float64]:
        """Weighted sum per covered point with the NaN semantics (see module doc)."""
        vv = np.asarray(values, dtype=np.float64)[self.simplices[self.tri]]  # (M, 3)
        w = self.weights
        nan = np.isnan(vv)
        if nan.any():
            bad = (nan & (w > 0.0)).any(axis=1)
            vv = np.where(nan, 0.0, vv)
            res = vv[:, 0] * w[:, 0] + vv[:, 1] * w[:, 1] + vv[:, 2] * w[:, 2]
            res[bad] = np.nan
            return res
        return vv[:, 0] * w[:, 0] + vv[:, 1] * w[:, 1] + vv[:, 2] * w[:, 2]

    def interpolate(self, values: NDArray[np.float64]) -> NDArray[np.float32]:
        """Dense ``(ny, nx)`` float32 field; NaN outside the drawn triangles."""
        out = np.full(self.grid.size, np.nan, dtype=np.float32)
        if self.cov_idx.size:
            out[self.cov_idx] = self._gather(values)
        return out.reshape(self.grid.shape)

    def blend(self, coords: NDArray[np.float64]) -> NDArray[np.float64]:
        """Barycentric blend of per-node ``(n, d)`` coordinates -> ``(M, d)``.

        With the reference positions this is the exact inverse map of the
        piecewise-linear deformation: where each deformed grid point came from.
        """
        c = np.asarray(coords, dtype=np.float64)
        verts = self.simplices[self.tri]
        w = self.weights.astype(np.float64)
        return c[verts[:, 0]] * w[:, 0:1] + c[verts[:, 1]] * w[:, 1:2] + c[verts[:, 2]] * w[:, 2:3]

    def grid_points(self) -> NDArray[np.float64]:
        """``(M, 2)`` image coordinates of the covered grid points."""
        g = self.grid
        cols = self.cov_idx % g.nx
        rows = self.cov_idx // g.nx
        return np.column_stack([g.x0 + g.step * cols, g.y0 + g.step * rows]).astype(np.float64)

    def full_mask(self, covered_flags: NDArray[np.bool_]) -> NDArray[np.bool_]:
        """Scatter per-covered-point flags into a full ``(ny, nx)`` bool grid."""
        out = np.zeros(self.grid.size, dtype=bool)
        out[self.cov_idx] = covered_flags
        return out.reshape(self.grid.shape)


def rasterize_mesh(
    pos: NDArray[np.float64], simplices: NDArray[np.int32], grid: GridSpec
) -> BaryTable:
    """Locate every grid point in the triangles ``simplices`` drawn at ``pos``.

    ``pos`` are this frame's node positions (reference positions in reference
    mode); triangles with a non-finite or collinear corner are skipped.
    Candidate grid points are enumerated per triangle bounding box and kept
    when all barycentric coordinates are >= -1e-9; a point on a shared edge is
    claimed by one of its triangles (the NaN semantics make the choice
    immaterial). Flipped (folded) triangles overlap their neighbours and the
    last write wins — acceptable for a display.
    """
    p = np.asarray(pos, dtype=np.float64).reshape(-1, 2)
    simplices = np.asarray(simplices, dtype=np.int32)
    tri_of = np.full(grid.size, -1, dtype=np.int32)
    weights = np.zeros((grid.size, 3), dtype=np.float32)
    if len(simplices) and grid.size:
        corners = p[simplices]  # (T, 3, 2)
        tids = np.flatnonzero(np.isfinite(corners).all(axis=(1, 2)))
        if tids.size:
            _rasterize_into(corners, tids, grid, tri_of, weights)
    cov = np.flatnonzero(tri_of >= 0).astype(np.int32)
    return BaryTable(grid, simplices, cov, tri_of[cov], weights[cov])


def _rasterize_into(
    corners: NDArray[np.float64],
    tids: NDArray[np.intp],
    grid: GridSpec,
    tri_of: NDArray[np.int32],
    weights: NDArray[np.float32],
) -> None:
    """Vectorised bounding-box scan of ``corners[tids]`` into the flat grid."""
    x0, y0, s, nx, ny = float(grid.x0), float(grid.y0), float(grid.step), grid.nx, grid.ny
    px = corners[tids, :, 0]
    py = corners[tids, :, 1]
    i0 = np.maximum(np.ceil((px.min(axis=1) - x0) / s), 0).astype(np.int64)
    i1 = np.minimum(np.floor((px.max(axis=1) - x0) / s), nx - 1).astype(np.int64)
    j0 = np.maximum(np.ceil((py.min(axis=1) - y0) / s), 0).astype(np.int64)
    j1 = np.minimum(np.floor((py.max(axis=1) - y0) / s), ny - 1).astype(np.int64)
    ni = np.maximum(i1 - i0 + 1, 0)
    nj = np.maximum(j1 - j0 + 1, 0)
    counts = ni * nj
    csum = np.cumsum(counts)
    if csum.size == 0 or csum[-1] == 0:
        return
    # Chunk triangles so the candidate arrays stay bounded (~100 MB transient).
    splits = np.searchsorted(
        csum, np.arange(_RASTER_CHUNK_CANDIDATES, int(csum[-1]), _RASTER_CHUNK_CANDIDATES)
    )
    bounds = np.unique(np.concatenate([[0], splits, [len(tids)]]).astype(np.int64))
    for a, b in zip(bounds[:-1], bounds[1:], strict=True):
        cnt = counts[a:b]
        total = int(cnt.sum())
        if total == 0:
            continue
        rep = np.repeat(np.arange(a, b), cnt)
        local = np.arange(total) - np.repeat(np.cumsum(cnt) - cnt, cnt)
        nir = ni[rep]
        gi = i0[rep] + local % nir
        gj = j0[rep] + local // nir
        qx = x0 + gi * s
        qy = y0 + gj * s
        ax, bx, cx = px[rep, 0], px[rep, 1], px[rep, 2]
        ay, by, cy = py[rep, 0], py[rep, 1], py[rep, 2]
        det = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        with np.errstate(divide="ignore", invalid="ignore"):
            l1 = ((by - cy) * (qx - cx) + (cx - bx) * (qy - cy)) / det
            l2 = ((cy - ay) * (qx - cx) + (ax - cx) * (qy - cy)) / det
        l3 = 1.0 - l1 - l2
        inside = (l1 >= -WEIGHT_EPS) & (l2 >= -WEIGHT_EPS) & (l3 >= -WEIGHT_EPS) & (det != 0.0)
        if not inside.any():
            continue
        flat = (gj * nx + gi)[inside]
        w = np.column_stack([l1[inside], l2[inside], l3[inside]])
        w[w < WEIGHT_EPS] = 0.0
        tri_of[flat] = tids[rep[inside]]
        weights[flat] = w


def _inside_barrier(pts: NDArray[np.float64], barrier: NDArray) -> NDArray[np.bool_]:
    """Nearest-pixel ``barrier >= 0.5`` test (clipped to the image)."""
    h, w = barrier.shape
    xi = np.clip(np.round(pts[:, 0]).astype(np.int64), 0, w - 1)
    yi = np.clip(np.round(pts[:, 1]).astype(np.int64), 0, h - 1)
    return barrier[yi, xi] >= 0.5


def edges_cross_barrier(
    p0: NDArray[np.float64], p1: NDArray[np.float64], barrier: NDArray
) -> NDArray[np.bool_]:
    """Per edge: both endpoints inside ``barrier >= 0.5`` and the open segment
    passes through ``barrier < 0.5`` (a thin crack / hole).

    Exact vectorised port of the scalar
    ``al_dic.utils.crack_barrier.segment_crosses_barrier`` (``n = int(length)``
    interior samples at ``t = i / n``, nearest pixel, clipped) gated by the
    both-endpoints-inside rule. ``barrier`` may be float or bool — no copy.
    """
    a = np.asarray(p0, dtype=np.float64).reshape(-1, 2)
    b = np.asarray(p1, dtype=np.float64).reshape(-1, 2)
    out = np.zeros(len(a), dtype=bool)
    if len(a) == 0:
        return out
    h, w = barrier.shape
    finite = np.isfinite(a).all(axis=1) & np.isfinite(b).all(axis=1)
    length = np.where(finite, np.hypot(b[:, 0] - a[:, 0], b[:, 1] - a[:, 1]), 0.0)
    n = length.astype(np.int64)  # int() truncation, as in the scalar test
    ok = finite & (n >= 2)
    ok[ok] = _inside_barrier(a[ok], barrier) & _inside_barrier(b[ok], barrier)
    cand = np.flatnonzero(ok)
    if cand.size == 0:
        return out
    cand = cand[np.argsort(n[cand], kind="stable")]  # length buckets bound the sample block
    ns = n[cand]
    start = 0
    while start < cand.size:
        # Largest chunk whose (count x longest n) sample block fits the budget.
        block = np.arange(1, cand.size - start + 1) * ns[start:]
        stop = start + max(1, int(np.searchsorted(block, _BARRIER_CHUNK_SAMPLES, side="right")))
        nmax = int(ns[stop - 1])
        idx = cand[start:stop]
        ne = n[idx].astype(np.float64)
        steps = np.arange(1, nmax, dtype=np.float64)  # sample i = 1 .. n-1
        t = steps[None, :] * (1.0 / ne)[:, None]  # == np.linspace(0, 1, n + 1)[i]
        valid = steps[None, :] < ne[:, None]
        ax, ay = a[idx, 0:1], a[idx, 1:2]
        xs = np.clip(np.round(ax + t * (b[idx, 0:1] - ax)).astype(np.int64), 0, w - 1)
        ys = np.clip(np.round(ay + t * (b[idx, 1:2] - ay)).astype(np.int64), 0, h - 1)
        out[idx] = ((barrier[ys, xs] < 0.5) & valid).any(axis=1)
        start = stop
    return out


def cells_cross_barrier(
    cells: NDArray[np.integer], coords: NDArray[np.float64], barrier: NDArray
) -> NDArray[np.bool_]:
    """Per cell (tri or quad): any edge ``(e, e+1 mod k)`` crosses the barrier.

    Shared edges are tested once (unique undirected edges).
    """
    cells = np.asarray(cells, dtype=np.int64)
    if cells.size == 0:
        return np.zeros(len(cells), dtype=bool)
    k = cells.shape[1]
    a = cells.reshape(-1)
    b = np.roll(cells, -1, axis=1).reshape(-1)
    lo, hi = np.minimum(a, b), np.maximum(a, b)
    keys = lo * (int(cells.max()) + 1) + hi
    uniq, inv = np.unique(keys, return_inverse=True)
    stride = int(cells.max()) + 1
    xy = np.asarray(coords, dtype=np.float64).reshape(-1, 2)
    crosses = edges_cross_barrier(xy[uniq // stride], xy[uniq % stride], barrier)
    return crosses[np.asarray(inv).reshape(-1)].reshape(len(cells), k).any(axis=1)
