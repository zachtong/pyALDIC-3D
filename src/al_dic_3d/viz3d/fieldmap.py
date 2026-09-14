"""Dense full-field compute core — Qt-free (extracted from ``VizController3D``).

Scattered nodal values become a dense image-space RGBA overlay: the nodes are
interpolated (piecewise linear) onto a regular grid over the node bounding box
at ``mesh_step // 4`` resolution (``scatter_to_grid``'s "auto" grid), pixels
outside the reference-frame ROI mask are knocked out, and a matplotlib colormap
turns the grid into RGBA with NaN -> alpha 0.

This module holds everything that does NOT touch Qt so that BOTH the GUI
(:class:`al_dic_3d.gui.controllers.viz_controller.VizController3D`, which adds
only the ``QPixmap`` edge) and the Qt-free image exporter
(:mod:`al_dic_3d.export.render`) share one renderer — the exported frames are
pixel-for-pixel the compute the canvas shows (WYSIWYG).

Geometry (V-view performance batch): ONE Delaunay of a camera's frame-1 node
positions (:class:`~al_dic_3d.viz3d.raster.MeshTopology`) is reused for every
frame — the material mesh is drawn at frame k's node positions
(:func:`~al_dic_3d.viz3d.raster.rasterize_mesh`) into a barycentric table, so a
deformed-mode frame costs one vectorised rasterization instead of a fresh
Delaunay per (frame, field) plus two extra interpolations for the mask warp,
and every further field of that frame is a gather. The table's blend of the
reference positions is the exact inverse map, so the reference ROI warps with
the material (holes travel). NaN semantics: a triangle with an invalid vertex
is transparent inside (see :mod:`al_dic_3d.viz3d.raster`) — the valid-node
support rule, now identical with or without a drawn ROI and in both modes.

Cache tiers (all bounded by entries AND bytes; recompute-on-miss):

Tier 1 (``_interp_cache``): the float32 field grid per
    ``(frame_idx, field_name, deformed)`` — ``field_name`` caller-namespaced
    (``"L:U"`` / ``"strain_window:exx"``) — valid only for the geometry it was
    built on (node sets, node step, image shape, edge-cap config).
``_ref_interp_cache``: reference topologies per node-set digest (L / R / strain).
``_support_cache``: drawable triangles per (topology, edge cap).
``_table_cache``: barycentric tables per (topology, cap, frame positions, grid).
``_warp_cache``: ROI knockout grids per (table, ROI content) — the warped mask.
``_crack_cache``: crack-blank grids per (table, barrier content).

Every cache is guarded by one lock held only for dictionary operations (never
during compute), and writes are fenced by an epoch so a worker thread still
computing after :meth:`FieldmapRenderer.clear_all` can never plant stale data.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any

import numpy as np
from matplotlib import colormaps
from numpy.typing import NDArray
from scipy.spatial import Delaunay

from al_dic_3d.viz3d.lru import LRUCache
from al_dic_3d.viz3d.raster import (
    BaryTable,
    GridSpec,
    MeshTopology,
    cells_cross_barrier,
    rasterize_mesh,
)
from al_dic_3d.viz3d.sized_cache import DigestMemo, SizedLRUCache, array_digest, mask_digest
from al_dic_3d.viz3d.surface import MAX_EDGE_FACTOR, median_nn_spacing

_MB = 1024 * 1024
# Entry caps (P2.1 contracts) — scrubbing recomputes on miss, eviction is safe.
INTERP_CACHE_SIZE = 32
WARP_CACHE_SIZE = 32
SUPPORT_CACHE_SIZE = 32
REF_INTERP_CACHE_SIZE = 4  # node-sets (L / R / strain window), not frames
TABLE_CACHE_SIZE = 16
CRACK_CACHE_SIZE = 32
# Byte budgets per renderer (V-view): a 12 Mpx frame at node step 16 is ~1.8 MB
# of float32 grid and ~9 MB of table; at step <= 7 the grid is full-resolution.
# Tables only serve a NEW field at a recently visited frame (Tier-1 grids and
# ROI knockouts are cached on their own), so their budget is the smaller one.
INTERP_CACHE_BYTES = 192 * _MB
TABLE_CACHE_BYTES = 128 * _MB
WARP_CACHE_BYTES = 64 * _MB
SUPPORT_CACHE_BYTES = 64 * _MB
CRACK_CACHE_BYTES = 64 * _MB


def apply_colormap(
    data: NDArray[np.floating],
    vmin: float,
    vmax: float,
    cmap: str = "turbo",
) -> NDArray[np.uint8]:
    """Apply a matplotlib colormap to a 2D float array -> RGBA uint8.

    NaN pixels get alpha=0 (transparent) — invalid propagates to the screen.
    """
    if vmax <= vmin:
        vmax = vmin + 1e-10

    normalized = np.clip((data - vmin) / (vmax - vmin), 0, 1)
    rgba = colormaps[cmap](normalized, bytes=True)  # == (cm(x) * 255).astype(uint8)
    rgba[np.isnan(data)] = 0
    return rgba


def visible_values(
    values: NDArray[np.float64],
    nodes: NDArray[np.float64],
    mask: NDArray[np.bool_] | None,
) -> NDArray[np.float64]:
    """Return *values* with entries outside *mask* set to NaN (2D port).

    Used so the auto colorbar range is computed only from nodes that are
    actually rendered (inside the reference ROI mask), not from nodes clipped
    by the mask. Falls back to the original array when *mask* is None or when
    the intersection is empty (avoids a degenerate all-NaN range).
    """
    if mask is None or len(values) == 0:
        return values
    h, w = mask.shape
    xy = np.nan_to_num(nodes, nan=-1.0)
    ix = np.round(xy[:, 0]).astype(int)
    iy = np.round(xy[:, 1]).astype(int)
    in_bounds = (ix >= 0) & (ix < w) & (iy >= 0) & (iy < h)
    vis = np.zeros(len(values), dtype=bool)
    vis[in_bounds] = mask[iy[in_bounds], ix[in_bounds]]
    if not np.any(vis):
        return values  # fallback: no node hit the mask
    out = values.copy()
    out[~vis] = np.nan
    return out


def auto_range(values: NDArray[np.float64]) -> tuple[float, float]:
    """2–98 percentile color range of the finite entries (2D-app parity, G2.3).

    The 2D app's auto mode clips the range to the 2nd/98th percentile so a
    handful of outlier nodes cannot stretch the colormap; the colorbar end
    labels show these clipped bounds (exactly like 2D). Returns ``(0.0, 1.0)``
    when nothing is finite.
    """
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return 0.0, 1.0
    lo, hi = np.nanpercentile(finite, [2.0, 98.0])
    return float(lo), float(hi)


def valid_node_support_mask(
    nodes: NDArray[np.float64],
    values: NDArray[np.float64],
    img_shape: tuple[int, int],
    mesh_step: float | None = None,
) -> NDArray[np.bool_]:
    """Boolean ``(H, W)`` support: Delaunay triangles whose 3 vertices are valid.

    The full-resolution form of the renderer's fallback support (kept as a
    public helper): it covers the point cloud like the 2D convex-hull
    behavior, but triangles touching an invalid node (NaN value or NaN
    position) are dropped, so holes from invalid nodes stay transparent.

    Triangles whose longest edge exceeds ``2.5 x`` the node step are dropped
    too: Delaunay spans node-free ROI holes (right camera / maskless runs)
    with long triangles that would otherwise fill the hole. ``mesh_step`` is
    the nominal node spacing; when absent it defaults to the median
    nearest-neighbor spacing of the finite nodes.
    """
    import cv2

    h, w = img_shape
    mask = np.zeros((h, w), dtype=np.uint8)
    finite = np.isfinite(nodes).all(axis=1)
    pts = nodes[finite]
    if pts.shape[0] < 3:
        return mask.astype(bool)
    ok = np.isfinite(np.asarray(values, dtype=np.float64))[finite]
    try:
        tri = Delaunay(pts)
    except Exception:  # degenerate (collinear) node sets have no support
        return mask.astype(bool)
    good = ok[tri.simplices].all(axis=1)
    step = float(mesh_step) if mesh_step else median_nn_spacing(pts)
    if step > 0.0:
        tri_pts = pts[tri.simplices]  # (n_tri, 3, 2)
        edges = tri_pts - np.roll(tri_pts, 1, axis=1)
        longest = np.sqrt((edges**2).sum(axis=2)).max(axis=1)
        good &= longest <= MAX_EDGE_FACTOR * step
    if np.any(good):
        polys = np.round(pts[tri.simplices[good]]).astype(np.int32)
        cv2.fillPoly(mask, list(polys), 1)
    return mask.astype(bool)


def lookup_outside(
    mask: NDArray,
    x: NDArray[np.float64],
    y: NDArray[np.float64],
) -> NDArray[np.bool_]:
    """True where the (x, y) points fall OUTSIDE *mask* (nearest pixel, clipped).

    Non-bool masks are read as ``> 0`` (inside).
    """
    xi = np.clip(np.round(x).astype(int), 0, mask.shape[1] - 1)
    yi = np.clip(np.round(y).astype(int), 0, mask.shape[0] - 1)
    inside = mask[yi, xi]
    if inside.dtype != np.bool_:
        inside = inside > 0
    return ~inside


@dataclass(frozen=True)
class _GeomKeys:
    """Everything that identifies one render geometry (cheap to compute)."""

    pos: NDArray[np.float64]  # this render's node positions
    ref: NDArray[np.float64]  # frame-1 positions (the triangulation lives there)
    grid: GridSpec
    topo_key: bytes
    pos_key: bytes
    max_edge: float | None

    @property
    def table_key(self) -> tuple:
        return (self.topo_key, self.max_edge, self.pos_key, self.grid)

    @property
    def is_reference(self) -> bool:
        return self.pos_key == self.topo_key


class FieldmapRenderer:
    """Dense field rendering with bounded, thread-safe caches (Qt-free)."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._epoch = 0
        self._interp_cache: SizedLRUCache[tuple, tuple] = SizedLRUCache(
            INTERP_CACHE_SIZE, INTERP_CACHE_BYTES
        )
        self._warp_cache: SizedLRUCache[tuple, NDArray[np.bool_]] = SizedLRUCache(
            WARP_CACHE_SIZE, WARP_CACHE_BYTES
        )
        self._support_cache: SizedLRUCache[tuple, NDArray[np.int32]] = SizedLRUCache(
            SUPPORT_CACHE_SIZE, SUPPORT_CACHE_BYTES
        )
        self._table_cache: SizedLRUCache[tuple, BaryTable] = SizedLRUCache(
            TABLE_CACHE_SIZE, TABLE_CACHE_BYTES
        )
        self._crack_cache: SizedLRUCache[tuple, tuple] = SizedLRUCache(
            CRACK_CACHE_SIZE, CRACK_CACHE_BYTES
        )
        self._ref_interp_cache: LRUCache[bytes, tuple] = LRUCache(REF_INTERP_CACHE_SIZE)
        # Identity memos in front of the content digests used as cache keys.
        self._pts_digest = DigestMemo(array_digest)
        self._roi_digest = DigestMemo(mask_digest)
        self._barrier_digest = DigestMemo(lambda m: mask_digest(m, barrier=True))

    # ------------------------------------------------------------------
    # Invalidation
    # ------------------------------------------------------------------

    def _caches(self) -> tuple[LRUCache, ...]:
        return (
            self._interp_cache,
            self._warp_cache,
            self._support_cache,
            self._table_cache,
            self._crack_cache,
            self._ref_interp_cache,
        )

    def clear_all(self) -> None:
        """Clear every cache tier (results or images changed)."""
        with self._lock:
            self._epoch += 1
            for cache in self._caches():
                cache.clear()

    def invalidate_masks(self) -> None:
        """Clear everything that depends on ROI / crack-mask content.

        The ROI knockout (warp) grids and the crack blanks — both are keyed by
        mask content as well, so a stale entry could never be hit, but an ROI
        edit must not leave dead grids occupying the budget either.
        """
        with self._lock:
            self._epoch += 1
            self._warp_cache.clear()
            self._crack_cache.clear()

    def clear_frame_caches(self) -> None:
        """Drop per-frame products, KEEP the reference geometry.

        Batch exporters render each (frame, field) exactly once, so the Tier-1
        grids, per-frame tables and masks provide no reuse — only memory growth
        over hundreds of frames. The reference topology / table DO repeat
        across frames and stay cached.
        """
        with self._lock:
            self._epoch += 1
            self._interp_cache.clear()
            self._warp_cache.clear()
            self._crack_cache.clear()
            for key in [k for k in self._table_cache if k[0] != k[2]]:
                del self._table_cache[key]

    # ------------------------------------------------------------------
    # Thread-safe cache access (lock held for dict operations only)
    # ------------------------------------------------------------------

    def _cget(self, cache: LRUCache, key: Any) -> Any:
        with self._lock:
            return cache.get(key)

    def _cput(self, epoch: int, cache: LRUCache, key: Any, value: Any) -> None:
        with self._lock:
            if epoch == self._epoch:  # a clear happened mid-compute: drop the write
                cache[key] = value

    # ------------------------------------------------------------------
    # Compute core (numpy/scipy/matplotlib only — no Qt)
    # ------------------------------------------------------------------

    def render_field_rgba(
        self,
        frame_idx: int,
        field_name: str,
        nodes: NDArray[np.float64],
        values: NDArray[np.float64],
        img_shape: tuple[int, int],
        mesh_step: int,
        cmap: str = "turbo",
        vmin: float = 0.0,
        vmax: float = 1.0,
        roi_mask: NDArray[np.bool_] | None = None,
        deformed: bool = False,
        ref_uv: tuple[NDArray[np.float64], NDArray[np.float64]] | None = None,
        ref_pts: NDArray[np.float64] | None = None,
        barrier_mask: NDArray | None = None,
    ) -> tuple[NDArray[np.uint8] | None, NDArray | None, NDArray | None, int]:
        """Render a field to a dense RGBA array (cached compute).

        Args:
            frame_idx / field_name: Tier-1 identity. ``field_name`` must be
                namespaced by the caller ("L:U", "strain_window:exx", ...).
            nodes: (n, 2) image-plane node positions for THIS render (frame-1
                positions in reference mode, frame-k in deformed mode). NaN
                rows (nodes lost at this frame) draw no triangle.
            values: (n,) field values; NaN = invalid.
            img_shape: (H, W) of the camera image.
            mesh_step: the RUN's node spacing in px (grid density, edge cap).
            roi_mask: reference-frame boolean ROI mask, or None for the
                valid-node support fallback (edge-capped triangles).
            deformed: nodes are frame-k positions; the reference ROI is warped
                through the mesh's exact inverse map.
            ref_uv: (u, v) per-node ``x_k - x_1``; only used to recover the
                reference positions when ``ref_pts`` is not given.
            ref_pts: (n, 2) frame-1 positions of ALL nodes — the triangulation
                is built there once per node set.
            barrier_mask: (H, W) crack mask in REFERENCE coordinates
                (``< 0.5`` = barrier, bool or float — never copied). Triangles
                with an edge crossing it are BLANKED (Batch C item 4); None
                (default) leaves the render bit-exact.

        Returns:
            (rgba, x_grid, y_grid, output_step): ``x_grid`` / ``y_grid`` are
            zero-copy ``(ny, nx)`` broadcast views of the grid axes; rgba is
            None when the node set is degenerate or off-image.
        """
        epoch = self._epoch
        g = self._geometry_keys(nodes, img_shape, mesh_step, deformed, ref_uv, ref_pts, roi_mask)
        if g is None:
            return None, None, None, 1
        table: list[BaryTable | None] = [None]

        def need_table() -> BaryTable | None:
            if table[0] is None:
                table[0] = self._table(epoch, g)
            return table[0]

        data = self._field_grid(
            epoch, (frame_idx, field_name, deformed), g, values, mesh_step, img_shape, need_table
        )
        if data is None:
            return None, None, None, 1
        blank = self._outside_grid(epoch, g, roi_mask, need_table)
        crack = self._crack_grid(epoch, g, barrier_mask, need_table)
        if crack is not None:
            blank = crack if blank is None else (blank | crack)

        render = data
        if blank is not None and blank.any():
            render = data.copy()
            render[blank] = np.nan
        xg, yg = g.grid.views()
        return apply_colormap(render, vmin, vmax, cmap), xg, yg, g.grid.step

    def _geometry_keys(
        self,
        nodes: NDArray[np.float64],
        img_shape: tuple[int, int],
        mesh_step: int,
        deformed: bool,
        ref_uv: tuple[NDArray[np.float64], NDArray[np.float64]] | None,
        ref_pts: NDArray[np.float64] | None,
        roi_mask: NDArray | None,
    ) -> _GeomKeys | None:
        pos = np.asarray(nodes, dtype=np.float64).reshape(-1, 2)
        finite = np.isfinite(pos).all(axis=1)
        if int(finite.sum()) < 3:
            return None
        if ref_pts is not None:
            ref = np.asarray(ref_pts, dtype=np.float64).reshape(-1, 2)
        elif deformed and ref_uv is not None:
            ref = pos - np.column_stack(ref_uv)
        else:
            ref = pos
        if ref.shape != pos.shape:
            raise ValueError(f"ref_pts {ref.shape} must match nodes {pos.shape}")
        grid = GridSpec.for_nodes(pos[finite], img_shape, mesh_step)
        if grid.size == 0:
            return None  # nodes entirely outside img_shape (e.g. no image yet)
        max_edge = None
        if roi_mask is None:  # support fallback: node-free holes stay open (F1.5)
            ref_ok = ref[np.isfinite(ref).all(axis=1)]
            step = float(mesh_step) if mesh_step else median_nn_spacing(ref_ok)
            max_edge = MAX_EDGE_FACTOR * step if step > 0.0 else None
        topo_key = self._pts_digest(ref)
        pos_key = topo_key if pos is ref else self._pts_digest(pos)
        return _GeomKeys(pos, ref, grid, topo_key, pos_key, max_edge)

    def _topology(self, epoch: int, g: _GeomKeys) -> MeshTopology | None:
        hit = self._cget(self._ref_interp_cache, g.topo_key)
        if hit is not None:
            return hit[0]
        topo = MeshTopology.build(g.ref)
        self._cput(epoch, self._ref_interp_cache, g.topo_key, (topo,))
        return topo

    def _drawable(self, epoch: int, g: _GeomKeys, topo: MeshTopology) -> NDArray[np.int32]:
        key = (g.topo_key, g.max_edge)
        hit = self._cget(self._support_cache, key)
        if hit is not None:
            return hit
        drawable = topo.drawable(g.max_edge)
        self._cput(epoch, self._support_cache, key, drawable)
        return drawable

    def _table(self, epoch: int, g: _GeomKeys) -> BaryTable | None:
        key = g.table_key
        hit = self._cget(self._table_cache, key)
        if hit is not None:
            return hit
        topo = self._topology(epoch, g)
        if topo is None:
            return None
        table = rasterize_mesh(g.pos, self._drawable(epoch, g, topo), g.grid)
        self._cput(epoch, self._table_cache, key, table)
        return table

    def _field_grid(
        self,
        epoch: int,
        key: tuple,
        g: _GeomKeys,
        values: NDArray[np.float64],
        mesh_step: int,
        img_shape: tuple[int, int],
        need_table,
    ) -> NDArray[np.float32] | None:
        """Tier 1: the interpolated field, valid only for the same geometry."""
        signature = (g.table_key, int(mesh_step or 0), tuple(int(v) for v in img_shape))
        hit = self._cget(self._interp_cache, key)
        if hit is not None and hit[1] == signature:
            return hit[0]
        table = need_table()
        if table is None:
            return None
        data = table.interpolate(values)
        self._cput(epoch, self._interp_cache, key, (data, signature))
        return data

    def _outside_grid(
        self, epoch: int, g: _GeomKeys, roi_mask: NDArray | None, need_table
    ) -> NDArray[np.bool_] | None:
        """ROI knockout on the grid: the reference mask looked up where each
        grid point came from (the warped mask in deformed mode)."""
        if roi_mask is None:
            return None
        key = (g.table_key, self._roi_digest(roi_mask))
        hit = self._cget(self._warp_cache, key)
        if hit is not None:
            return hit
        table = need_table()
        if table is None:
            return None
        where = table.grid_points() if g.is_reference else table.blend(g.ref)
        outside = table.full_mask(lookup_outside(np.asarray(roi_mask), where[:, 0], where[:, 1]))
        self._cput(epoch, self._warp_cache, key, outside)
        return outside

    def _crack_grid(
        self, epoch: int, g: _GeomKeys, barrier_mask: NDArray | None, need_table
    ) -> NDArray[np.bool_] | None:
        """Crack blank: grid points inside a triangle bridging the barrier.

        The crossing test runs in REFERENCE coordinates once per (topology,
        barrier) and travels with the material. Keyed by barrier CONTENT, so an
        ROI edit can never keep blanking from the old ROI.
        """
        if barrier_mask is None:
            return None
        bkey = self._barrier_digest(barrier_mask)
        key = (g.table_key, bkey)
        hit = self._cget(self._crack_cache, key)
        if hit is not None:
            return hit[0]
        flags_key = ("flags", g.topo_key, g.max_edge, bkey)
        flags_hit = self._cget(self._crack_cache, flags_key)
        if flags_hit is None:
            topo = self._topology(epoch, g)
            if topo is None:
                return None
            drawable = self._drawable(epoch, g, topo)
            flags = cells_cross_barrier(drawable, topo.ref, np.asarray(barrier_mask))
            self._cput(epoch, self._crack_cache, flags_key, (flags,))
        else:
            flags = flags_hit[0]
        grid_mask = None
        if flags.any():
            table = need_table()
            if table is not None:
                cov = flags[table.tri]
                grid_mask = table.full_mask(cov) if cov.any() else None
        self._cput(epoch, self._crack_cache, key, (grid_mask,))
        return grid_mask
