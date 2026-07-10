"""Dense full-field compute core — Qt-free (extracted from ``VizController3D``).

Scattered nodal values become a dense image-space RGBA overlay exactly like the
2D app: ``scatter_to_grid`` (Delaunay + CloughTocher, NaN outside the hull)
builds a regular grid over the node bounding box at ``mesh_step // 4``
resolution, a reference-frame ROI mask (or the valid-node support fallback)
knocks out pixels outside the region of interest, and a matplotlib colormap
turns the masked grid into RGBA with NaN -> alpha 0.

This module holds everything that does NOT touch Qt so that BOTH the GUI
(:class:`al_dic_3d.gui.controllers.viz_controller.VizController3D`, which adds
only the ``QPixmap`` edge) and the Qt-free image exporter
(:mod:`al_dic_3d.export.render`) share one renderer — the exported frames are
pixel-for-pixel the compute the canvas shows (WYSIWYG).

Cache tiers (the 2D scheme, minus the Qt pixmap tier):

Tier 1 (interp cache): ``scatter_to_grid`` output arrays.
    Key: ``(frame_idx, field_name, deformed)`` — ``field_name`` is
    caller-namespaced (``"L:U"`` / ``"R:W"`` / ``"strain_window:exx"``).
    Invalidated when results change; survives colormap/range changes.
Warp cache: deformed-coordinate outside-masks per Tier-1 key (computed during
    full compute via the inverse-displacement lookup, reused across repaints).
Support cache: fallback valid-node support masks per ``(frame, field)``.
Ref-interp cache: reference-frame ``FieldInterpolator`` per node-set bytes
    (one renderer may serve the LEFT and RIGHT node clouds).
"""

from __future__ import annotations

import numpy as np
from al_dic.utils.interpolation import FieldInterpolator, scatter_to_grid
from matplotlib import colormaps
from numpy.typing import NDArray
from scipy.spatial import Delaunay

from al_dic_3d.viz3d.lru import LRUCache
from al_dic_3d.viz3d.surface import MAX_EDGE_FACTOR, median_nn_spacing

# Cache caps (P2.1): scrubbing recomputes on miss, so eviction is safe; the
# caps bound memory to ~a few dozen dense grids / masks per renderer.
INTERP_CACHE_SIZE = 32
WARP_CACHE_SIZE = 32
SUPPORT_CACHE_SIZE = 32
REF_INTERP_CACHE_SIZE = 4  # node-sets (L / R / strain window), not frames


def apply_colormap(
    data: NDArray[np.float64],
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
    rgba = (colormaps[cmap](normalized) * 255).astype(np.uint8)
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

    The fallback "ROI" when no drawn mask exists (e.g. the RIGHT camera): it
    covers the point cloud like the 2D convex-hull behavior, but triangles
    touching an invalid node (NaN value or NaN position) are dropped, so holes
    from invalid nodes stay transparent instead of being interpolated across.

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
    mask: NDArray[np.bool_],
    x: NDArray[np.float64],
    y: NDArray[np.float64],
) -> NDArray[np.bool_]:
    """True where the (x, y) grid points fall OUTSIDE *mask* (nearest pixel)."""
    xi = np.clip(np.round(x).astype(int), 0, mask.shape[1] - 1)
    yi = np.clip(np.round(y).astype(int), 0, mask.shape[0] - 1)
    return ~mask[yi, xi]


class FieldmapRenderer:
    """Dense field rendering with the 2D caching scheme (Qt-free compute)."""

    def __init__(self) -> None:
        # Bounded LRUs (P2.1): all tiers recompute on miss, so eviction is safe.
        # Tier 1: interpolation results {(frame, field, deformed) -> (data, xg, yg, out_step)}
        self._interp_cache: LRUCache[tuple, tuple] = LRUCache(INTERP_CACHE_SIZE)
        # Deformed-mode warped outside-masks, keyed like Tier 1.
        self._warp_cache: LRUCache[tuple, NDArray[np.bool_]] = LRUCache(WARP_CACHE_SIZE)
        # Fallback valid-node support masks {(frame, field) -> bool mask}.
        self._support_cache: LRUCache[tuple, NDArray[np.bool_]] = LRUCache(SUPPORT_CACHE_SIZE)
        # Reference interpolators per node set (L / R / strain window share us).
        self._ref_interp_cache: LRUCache[bytes, FieldInterpolator] = LRUCache(REF_INTERP_CACHE_SIZE)

    def clear_all(self) -> None:
        """Clear every cache tier (results changed)."""
        self._interp_cache.clear()
        self._warp_cache.clear()
        self._support_cache.clear()
        self._ref_interp_cache.clear()

    def invalidate_masks(self) -> None:
        """Clear caches that depend on ROI mask content (warp + support)."""
        self._warp_cache.clear()
        self._support_cache.clear()

    def clear_frame_caches(self) -> None:
        """Drop per-frame products, KEEP the reference interpolators.

        Batch exporters render each (frame, field) exactly once, so the Tier-1
        grids and masks provide no reuse — only memory growth over hundreds of
        frames. The reference-frame Delaunay interpolators DO repeat across
        frames and stay cached.
        """
        self._interp_cache.clear()
        self._warp_cache.clear()
        self._support_cache.clear()

    # ------------------------------------------------------------------
    # Compute core (numpy/scipy/cv2/matplotlib only — no Qt)
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
    ) -> tuple[NDArray[np.uint8] | None, NDArray | None, NDArray | None, int]:
        """Render a field to a dense RGBA array (Tier-1 cached compute).

        Args:
            frame_idx / field_name: cache identity. ``field_name`` must be
                namespaced by the caller ("L:U", "strain_window:exx", ...).
            nodes: (n, 2) image-plane node positions for THIS render (frame-1
                positions in reference mode, frame-k in deformed mode). NaN
                rows (invalid nodes) are filtered before triangulation.
            values: (n,) field values; NaN = invalid.
            img_shape: (H, W) of the camera image.
            mesh_step: node spacing in px (drives the output grid density).
            roi_mask: reference-frame boolean ROI mask, or None to fall back
                to the valid-node Delaunay support of ``ref_pts``.
            deformed: nodes are frame-k positions; the reference support is
                warped by the inverse of ``ref_uv``.
            ref_uv: (u, v) per-node displacements ``x_k - x_1`` (required to
                warp the reference support when ``deformed`` is True).
            ref_pts: (n, 2) frame-1 positions of ALL nodes, used to build the
                fallback support (invalid frame-k nodes keep finite reference
                positions here, so their holes are located correctly).

        Returns:
            (rgba, x_grid, y_grid, output_step); rgba is None when the node
            set is degenerate (fewer than 3 finite nodes).
        """
        interp_key = (frame_idx, field_name, deformed)

        interpolator = None  # set on the compute path; reused by the warp mask
        cached = self._interp_cache.get(interp_key)
        if cached is not None:
            grid_data, xg, yg, out_step = cached
        else:
            finite = np.isfinite(nodes).all(axis=1)
            pts = nodes[finite]
            vals = np.asarray(values, dtype=np.float64)[finite]
            if pts.shape[0] < 3:
                return None, None, None, 1
            # Deformed positions change every frame — fresh triangulation.
            # Reference node sets are stable; cache per node-set bytes so one
            # renderer serves the L and R clouds without cross-talk.
            if deformed:
                interpolator = FieldInterpolator(pts)
            else:
                key = pts.tobytes()
                interpolator = self._ref_interp_cache.get(key)
                if interpolator is None:
                    interpolator = FieldInterpolator(pts)
                    self._ref_interp_cache[key] = interpolator
            grid_data, info = scatter_to_grid(
                pts,
                vals,
                img_shape=img_shape,
                mesh_step=mesh_step,
                output_mode="auto",
                oversample=4,
                interpolator=interpolator,
            )
            xg = info["x_grid"]
            yg = info["y_grid"]
            out_step = int(info.get("output_step", 1))
            if grid_data.size == 0:
                # Nodes lie entirely outside img_shape (e.g. no background
                # image yet) — nothing to draw; do not cache the empty grid.
                return None, None, None, 1
            self._interp_cache[interp_key] = (grid_data, xg, yg, out_step)

        # --- masking: warped mask (deformed) or direct reference lookup ---
        # The warp mask lives in its own bounded LRU; when it was evicted while
        # the interpolation entry survived, it is RECOMPUTED here (never fall
        # back to the wrong reference-coordinate lookup on a deformed grid).
        mask_to_use = None
        if deformed and ref_uv is not None:
            mask_to_use = self._warp_outside_mask(
                interp_key,
                nodes,
                values,
                img_shape,
                roi_mask,
                ref_uv,
                ref_pts,
                mesh_step,
                xg,
                yg,
                interpolator=interpolator,
            )
        if mask_to_use is None:
            eff = self._effective_mask(
                frame_idx,
                field_name,
                values,
                img_shape,
                roi_mask,
                ref_uv,
                ref_pts,
                nodes,
                mesh_step,
            )
            if eff is not None and xg is not None:
                mask_to_use = lookup_outside(eff, xg, yg)

        render_data = grid_data
        if mask_to_use is not None and np.any(mask_to_use):
            render_data = grid_data.copy()
            render_data[mask_to_use] = np.nan

        return apply_colormap(render_data, vmin, vmax, cmap), xg, yg, out_step

    def _warp_outside_mask(
        self,
        interp_key: tuple,
        nodes: NDArray[np.float64],
        values: NDArray[np.float64],
        img_shape: tuple[int, int],
        roi_mask: NDArray[np.bool_] | None,
        ref_uv: tuple[NDArray[np.float64], NDArray[np.float64]],
        ref_pts: NDArray[np.float64] | None,
        mesh_step: float | None,
        xg: NDArray,
        yg: NDArray,
        interpolator: FieldInterpolator | None = None,
    ) -> NDArray[np.bool_] | None:
        """Deformed-coordinate outside-mask (cached; recomputed after eviction).

        Warps the reference support into deformed coordinates via the inverse-
        displacement lookup (2D ``ref_uv`` contract) — internal holes survive
        instead of being interpolated across. ``interpolator`` is the fresh
        deformed-node interpolator when the caller just built one; on a warp
        cache miss WITHOUT one (LRU eviction), it is rebuilt from ``nodes``.
        """
        cached = self._warp_cache.get(interp_key)
        if cached is not None:
            return cached
        frame_idx, field_name, _deformed = interp_key
        eff = self._effective_mask(
            frame_idx, field_name, values, img_shape, roi_mask, ref_uv, ref_pts, nodes, mesh_step
        )
        if eff is None:
            return None
        finite = np.isfinite(nodes).all(axis=1)
        if interpolator is None:
            interpolator = FieldInterpolator(nodes[finite])
        u_grid = interpolator.interpolate(ref_uv[0][finite], xg, yg)
        v_grid = interpolator.interpolate(ref_uv[1][finite], xg, yg)
        xr = xg - u_grid
        yr = yg - v_grid
        nan_warp = np.isnan(xr) | np.isnan(yr)
        outside = lookup_outside(eff, np.nan_to_num(xr, nan=0.0), np.nan_to_num(yr, nan=0.0))
        result = outside | nan_warp
        self._warp_cache[interp_key] = result
        return result

    def _effective_mask(
        self,
        frame_idx: int,
        field_name: str,
        values: NDArray[np.float64],
        img_shape: tuple[int, int],
        roi_mask: NDArray[np.bool_] | None,
        ref_uv: tuple[NDArray[np.float64], NDArray[np.float64]] | None,
        ref_pts: NDArray[np.float64] | None,
        nodes: NDArray[np.float64],
        mesh_step: float | None = None,
    ) -> NDArray[np.bool_] | None:
        """The reference-frame support: the drawn ROI mask or the hull fallback.

        The fallback is built in REFERENCE coordinates with frame-k validity,
        so invalid-node holes appear in both plot modes (the deformed path
        warps this same mask). ``mesh_step`` feeds the edge-length cap that
        keeps node-free holes transparent. Cached per (frame, field).
        """
        if roi_mask is not None:
            return roi_mask
        skey = (frame_idx, field_name)
        support = self._support_cache.get(skey)
        if support is None:
            base = ref_pts
            if base is None:
                if ref_uv is not None:
                    base = nodes - np.column_stack(ref_uv)
                else:
                    base = nodes
            support = valid_node_support_mask(base, values, img_shape, mesh_step=mesh_step)
            self._support_cache[skey] = support
        return support
