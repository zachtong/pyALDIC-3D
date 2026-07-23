"""Dense full-field visualization controller (port of the 2D ``VizController``).

The compute core (scatter -> dense grid -> mask -> RGBA, with the 2D cache
scheme) lives in the Qt-free :class:`al_dic_3d.viz3d.fieldmap.FieldmapRenderer`
so the image exporter renders EXACTLY what the canvas shows. This class adds
only the Qt edge: the Tier-2 colored ``QPixmap`` cache and the
``numpy -> QImage -> QPixmap`` conversion.

Cache tiers (same scheme as 2D):

Tier 1 (interp cache, in the base class): ``scatter_to_grid`` output arrays.
    Key: ``(frame_idx, field_name, deformed)`` — ``field_name`` is
    caller-namespaced (``"L:U"`` / ``"R:W"`` / ``"strain_window:exx"``).
    Invalidated: when results change. Survives colormap/range changes.
Tier 2 (pixmap cache, here): colored ``QPixmap`` ready for display.
    Key adds ``(cmap, vmin, vmax, has_mask)``.
Warp/support/ref-interp caches: see :mod:`al_dic_3d.viz3d.fieldmap`.

``apply_colormap`` / ``visible_values`` / ``valid_node_support_mask`` are
re-exported for the existing GUI/test import sites.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from PySide6.QtGui import QImage, QPixmap

from al_dic_3d.viz3d.fieldmap import (  # noqa: F401 - re-exported compute API
    FieldmapRenderer,
    apply_colormap,
    auto_range,
    valid_node_support_mask,
    visible_values,
)
from al_dic_3d.viz3d.lru import LRUCache

# Tier-2 cap (P2.1): pixmaps are recolored from the Tier-1 grids on miss.
PIXMAP_CACHE_SIZE = 48


class VizController3D(FieldmapRenderer):
    """The Qt-free renderer plus the Tier-2 ``QPixmap`` cache."""

    def __init__(self) -> None:
        super().__init__()
        # Tier 2: colored pixmaps {(frame, field, cmap, vmin, vmax, has_mask, deformed)}
        self._pixmap_cache: LRUCache[tuple, QPixmap] = LRUCache(PIXMAP_CACHE_SIZE)

    def clear_all(self) -> None:
        """Clear every cache tier (results changed)."""
        super().clear_all()
        self._pixmap_cache.clear()

    def clear_pixmap_cache(self) -> None:
        """Clear Tier 2 only (colormap/range changed)."""
        self._pixmap_cache.clear()

    def invalidate_masks(self) -> None:
        """Clear caches that depend on ROI mask content (pixmap + warp + support)."""
        super().invalidate_masks()
        self._pixmap_cache.clear()

    # ------------------------------------------------------------------
    # Qt edge
    # ------------------------------------------------------------------

    def render_field(
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
        barrier_mask: NDArray[np.float64] | None = None,
    ) -> tuple[QPixmap | None, NDArray | None, NDArray | None, int]:
        """Render a field to a QPixmap overlay (Tier-2 cached).

        Returns ``(pixmap, x_grid, y_grid, output_step)``: position the pixmap
        item at ``(x_grid.min(), y_grid.min())`` and scale it by
        ``output_step`` to land on image pixels. ``pixmap`` is None when the
        node set is degenerate.
        """
        interp_key = (frame_idx, field_name, deformed)
        pixmap_key = (
            frame_idx,
            field_name,
            cmap,
            round(vmin, 6),
            round(vmax, 6),
            roi_mask is not None,
            deformed,
            barrier_mask is not None,
        )

        cached_interp = self._interp_cache.get(interp_key)
        if pixmap_key in self._pixmap_cache and cached_interp is not None:
            # render_field_rgba caches (grid_data, xg, yg, out_step, crack_grid).
            _, xg, yg, out_step = cached_interp[:4]
            return self._pixmap_cache[pixmap_key], xg, yg, out_step

        rgba, xg, yg, out_step = self.render_field_rgba(
            frame_idx,
            field_name,
            nodes,
            values,
            img_shape,
            mesh_step,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            roi_mask=roi_mask,
            deformed=deformed,
            ref_uv=ref_uv,
            ref_pts=ref_pts,
            barrier_mask=barrier_mask,
        )
        if rgba is None:
            return None, None, None, 1

        h, w = rgba.shape[:2]
        rgba_contiguous = np.ascontiguousarray(rgba)
        qimg = QImage(rgba_contiguous.data, w, h, w * 4, QImage.Format.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimg.copy())  # .copy() detaches from numpy

        self._pixmap_cache[pixmap_key] = pixmap
        return pixmap, xg, yg, out_step
