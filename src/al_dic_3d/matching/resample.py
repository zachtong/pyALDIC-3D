"""Scattered-node resampling for the right-camera assembly (Qt-free).

Moved out of :mod:`al_dic_3d.matching.temporal` (fix batch V, file-size rule);
``temporal`` re-exports every public name, so existing imports keep working.
"""

from __future__ import annotations

from collections import OrderedDict

import numpy as np
from numpy.typing import NDArray


class _ResampleGeometryCache:
    """Bounded, thread-safe cache of resampling geometry (P3.4).

    :func:`resample_to_points` is called once per frame from the strategy
    assembly loops, but the FINITE source-node set (and therefore the Delaunay
    triangulation and the nearest-fill KD-tree) rarely changes between frames.
    Entries are keyed by the exact source-point bytes — the coordinates fully
    determine both structures — so a hit is always geometrically identical to
    a rebuild. ``LinearNDInterpolator(tri, values)`` then reuses the cached
    triangulation with the per-frame values.

    ``delaunay_builds`` / ``kdtree_builds`` count actual constructions
    (observability + tests). The lock only guards the map; a rare concurrent
    double-build is idempotent.
    """

    def __init__(self, capacity: int = 4) -> None:
        import threading

        self._capacity = max(1, int(capacity))
        self._lock = threading.Lock()
        self._entries: OrderedDict[bytes, list] = OrderedDict()  # key -> [tri, tree]
        self.delaunay_builds = 0
        self.kdtree_builds = 0

    def _slot(self, key: bytes, idx: int):
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None:
                self._entries.move_to_end(key)
                return entry[idx]
        return None

    def _store(self, key: bytes, idx: int, obj) -> None:
        with self._lock:
            entry = self._entries.setdefault(key, [None, None])
            entry[idx] = obj
            self._entries.move_to_end(key)
            while len(self._entries) > self._capacity:
                self._entries.popitem(last=False)

    def triangulation(self, src: NDArray[np.float64]):
        """Delaunay of ``src`` — cached by the exact point bytes."""
        key = src.tobytes()
        tri = self._slot(key, 0)
        if tri is None:
            from scipy.spatial import Delaunay

            tri = Delaunay(src)
            self.delaunay_builds += 1
            self._store(key, 0, tri)
        return tri

    def kdtree(self, src: NDArray[np.float64]):
        """cKDTree of ``src`` — cached by the exact point bytes (nearest fill)."""
        key = src.tobytes()
        tree = self._slot(key, 1)
        if tree is None:
            from scipy.spatial import cKDTree

            tree = cKDTree(src)
            self.kdtree_builds += 1
            self._store(key, 1, tree)
        return tree

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
            self.delaunay_builds = 0
            self.kdtree_builds = 0


#: Module-level cache shared by every strategy's per-frame resampling calls.
_RESAMPLE_CACHE = _ResampleGeometryCache()


def resample_to_points(
    ref_coords: NDArray[np.float64],
    values: NDArray[np.float64],
    query: NDArray[np.float64],
    *,
    fill_nearest: bool = True,
    reuse_geometry: bool = True,
    max_edge: float | None = None,
    max_fill_dist: float | None = None,
) -> NDArray[np.float64]:
    """Interpolate a scattered vector field onto arbitrary query points (NaN-aware).

    Builds a Delaunay-based linear interpolant from the FINITE rows of ``values``
    (so NaN/invalid nodes never contaminate a neighborhood) and evaluates it at
    ``query``. Points outside the convex hull are ``NaN`` from the linear pass; if
    ``fill_nearest`` they are back-filled with the nearest finite node (a mild,
    clearly-bounded extrapolation for corr points that drift just past the hull).

    Args:
        ref_coords: ``(n, 2)`` field node coordinates ``[x, y]``.
        values: ``(n, 2)`` field values ``[u, v]`` (rows may be ``NaN``).
        query: ``(m, 2)`` points to sample at.
        fill_nearest: back-fill finite out-of-hull queries from the nearest node.
        reuse_geometry: serve the Delaunay/KD-tree from the module cache when
            the finite source-point set repeats across frames (P3.4). The cache
            key is the exact source bytes, so results are identical either way;
            disable only to benchmark or to avoid retaining the geometry.
        max_edge: reject interpolation inside any Delaunay triangle with an edge
            longer than this (pixels). Invalid (NaN) source nodes are left out of
            the triangulation, so a triangle that jumps across a gated region
            has long edges; without the cap its interior was filled from
            distant, unrelated nodes (fix batch V). ``None`` = no cap.
        max_fill_dist: only nearest-fill a query whose nearest finite node is
            within this distance (pixels). ``None`` = unlimited (the old
            behaviour: ANY point, however far, got the nearest node's value).

    Returns:
        ``(m, 2)`` interpolated values; ``NaN`` rows where no estimate exists.
    """
    from scipy.interpolate import LinearNDInterpolator

    ref = np.asarray(ref_coords, dtype=np.float64).reshape(-1, 2)
    val = np.asarray(values, dtype=np.float64).reshape(-1, 2)
    q = np.asarray(query, dtype=np.float64).reshape(-1, 2)

    finite = np.isfinite(val).all(axis=1) & np.isfinite(ref).all(axis=1)
    out = np.full((q.shape[0], 2), np.nan, dtype=np.float64)
    if finite.sum() < 3:
        return out  # Delaunay needs >=3 non-collinear points

    src = np.ascontiguousarray(ref[finite])
    dst = val[finite]
    from scipy.spatial import QhullError

    try:
        if reuse_geometry:
            # LinearNDInterpolator(points, ...) builds Delaunay(points) internally;
            # passing the cached triangulation is the documented equivalent path.
            lin = LinearNDInterpolator(_RESAMPLE_CACHE.triangulation(src), dst)
        else:
            lin = LinearNDInterpolator(src, dst)
    except (QhullError, ValueError):
        # Too few / collinear surviving nodes to triangulate (e.g. a camera the
        # honesty gate almost entirely rejected): no linear estimate anywhere;
        # only the capped nearest fill below may still reach adjacent queries.
        lin = None
    if lin is not None:
        out[:] = lin(q)

    if max_edge is not None and lin is not None:
        tri = lin.tri
        long_tri = _long_simplices(tri, float(max_edge))
        if long_tri.any():
            qf = np.isfinite(q).all(axis=1)
            simplex = np.full(q.shape[0], -1, dtype=np.int64)
            simplex[qf] = tri.find_simplex(q[qf])
            bridged = (simplex >= 0) & long_tri[np.maximum(simplex, 0)]
            out[bridged] = np.nan

    if fill_nearest:
        # Only fill FINITE queries with no linear estimate (outside the hull, or
        # inside a rejected long triangle); a non-finite query row has no
        # estimate and must stay NaN (documented contract) — never feed it to
        # the KD-tree (scipy raises on non-finite query points).
        missing = (~np.isfinite(out).all(axis=1)) & np.isfinite(q).all(axis=1)
        if missing.any():
            rows = np.flatnonzero(missing)
            tree = _RESAMPLE_CACHE.kdtree(src) if reuse_geometry else None
            if tree is None:
                from scipy.spatial import cKDTree

                tree = cKDTree(src)
            dist, nearest_idx = tree.query(q[rows])
            if max_fill_dist is not None:
                keep = dist <= float(max_fill_dist)
                rows, nearest_idx = rows[keep], nearest_idx[keep]
            out[rows] = dst[nearest_idx]
    return out


def _long_simplices(tri, max_edge: float) -> NDArray[np.bool_]:
    """Per-simplex flag: any edge longer than ``max_edge``."""
    pts = tri.points[tri.simplices]  # (n_tri, 3, 2)
    e = np.stack(
        [
            np.linalg.norm(pts[:, 0] - pts[:, 1], axis=1),
            np.linalg.norm(pts[:, 1] - pts[:, 2], axis=1),
            np.linalg.norm(pts[:, 2] - pts[:, 0], axis=1),
        ],
        axis=1,
    )
    return e.max(axis=1) > max_edge


def node_spacing(coords: NDArray[np.float64]) -> float:
    """Median nearest-neighbour distance of finite nodes (the mesh step, px)."""
    from scipy.spatial import cKDTree

    c = np.asarray(coords, dtype=np.float64).reshape(-1, 2)
    c = c[np.isfinite(c).all(axis=1)]
    if c.shape[0] < 2:
        return float("nan")
    d, _ = cKDTree(c).query(c, k=2)
    return float(np.median(d[:, 1]))
