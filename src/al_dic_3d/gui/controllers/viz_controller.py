"""Dense full-field visualization controller (port of the 2D ``VizController``).

The compute core (scatter -> dense grid -> mask -> RGBA, with bounded caches)
lives in the Qt-free :class:`al_dic_3d.viz3d.fieldmap.FieldmapRenderer` so the
image exporter renders EXACTLY what the canvas shows. This class adds only the
Qt edge: the Tier-2 colored ``QPixmap`` cache and the
``numpy -> QImage -> QPixmap`` conversion.

Tier 2 (pixmap cache, here): colored ``QPixmap`` + its placement, keyed by
    ``(frame, field, cmap, vmin, vmax, roi content, deformed, barrier content,
    step)``; bounded by entries AND bytes. GUI thread only.

The Tier-2 API is split so the canvas can run the heavy compute on a worker
(V-view): :meth:`pixmap_key` / :meth:`cached_pixmap` on the GUI thread,
:meth:`FieldmapRenderer.render_field_rgba` on the worker (thread-safe), and
:meth:`adopt_rgba` back on the GUI thread (``QPixmap`` must be created there).
:meth:`render_field` is the synchronous composition of the three.

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
from al_dic_3d.viz3d.sized_cache import SizedLRUCache

# Tier-2 caps (P2.1 + V-view): pixmaps are recolored from Tier-1 on miss.
PIXMAP_CACHE_SIZE = 48
PIXMAP_CACHE_BYTES = 256 * 1024 * 1024


def _pixmap_entry_bytes(entry: tuple) -> int:
    pixmap = entry[0]
    return int(pixmap.width()) * int(pixmap.height()) * 4


class VizController3D(FieldmapRenderer):
    """The Qt-free renderer plus the Tier-2 ``QPixmap`` cache."""

    def __init__(self) -> None:
        super().__init__()
        # Tier 2: {pixmap_key -> (pixmap, x_grid, y_grid, output_step)}
        self._pixmap_cache: SizedLRUCache[tuple, tuple] = SizedLRUCache(
            PIXMAP_CACHE_SIZE, PIXMAP_CACHE_BYTES, sizer=_pixmap_entry_bytes
        )

    def clear_all(self) -> None:
        """Clear every cache tier (results changed)."""
        super().clear_all()
        self._pixmap_cache.clear()

    def clear_pixmap_cache(self) -> None:
        """Clear Tier 2 only (colormap/range changed)."""
        self._pixmap_cache.clear()

    def invalidate_masks(self) -> None:
        """Clear caches that depend on ROI mask content (pixmap + warp + crack)."""
        super().invalidate_masks()
        self._pixmap_cache.clear()

    # ------------------------------------------------------------------
    # Qt edge
    # ------------------------------------------------------------------

    def _mask_identity(self, mask, *, barrier: bool = False):
        """Content identity of a mask for Tier-2 keys (memoised digest).

        A non-array stand-in (a mask a worker will derive) keys as "pending".
        """
        if mask is None:
            return None
        if not isinstance(mask, np.ndarray):
            return "pending"
        return self._barrier_digest(mask) if barrier else self._roi_digest(mask)

    def pixmap_key(
        self,
        frame_idx: int,
        field_name: str,
        cmap: str,
        vmin: float,
        vmax: float,
        roi_mask: NDArray | None,
        deformed: bool,
        barrier_mask: NDArray | None,
        mesh_step: int,
    ) -> tuple:
        """Tier-2 identity of one colored overlay.

        The ROI / barrier enter by CONTENT (digest, memoised per mask object),
        so an edited mask can never resurface a pixmap drawn with the old one,
        whether or not the owner remembered to call :meth:`invalidate_masks`.
        """
        return (
            frame_idx,
            field_name,
            cmap,
            round(float(vmin), 6),
            round(float(vmax), 6),
            self._mask_identity(roi_mask),
            bool(deformed),
            self._mask_identity(barrier_mask, barrier=True),
            int(mesh_step or 0),
        )

    def cached_pixmap(self, key: tuple) -> tuple[QPixmap, NDArray, NDArray, int] | None:
        """Exact Tier-2 hit ``(pixmap, x_grid, y_grid, output_step)`` or None."""
        return self._pixmap_cache.get(key)

    def adopt_rgba(
        self,
        key: tuple,
        rgba: NDArray[np.uint8] | None,
        xg: NDArray | None,
        yg: NDArray | None,
        out_step: int,
    ) -> tuple[QPixmap | None, NDArray | None, NDArray | None, int]:
        """GUI thread: wrap a computed RGBA grid as a ``QPixmap`` and cache it."""
        if rgba is None:
            return None, None, None, 1
        h, w = rgba.shape[:2]
        rgba_contiguous = np.ascontiguousarray(rgba)
        qimg = QImage(rgba_contiguous.data, w, h, w * 4, QImage.Format.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimg.copy())  # .copy() detaches from numpy
        entry = (pixmap, xg, yg, int(out_step))
        self._pixmap_cache[key] = entry
        return entry

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
        barrier_mask: NDArray | None = None,
    ) -> tuple[QPixmap | None, NDArray | None, NDArray | None, int]:
        """Render a field to a QPixmap overlay synchronously (Tier-2 cached).

        Returns ``(pixmap, x_grid, y_grid, output_step)``: position the pixmap
        item at ``(x_grid.min(), y_grid.min())`` and scale it by
        ``output_step`` to land on image pixels. ``pixmap`` is None when the
        node set is degenerate.
        """
        key = self.pixmap_key(
            frame_idx, field_name, cmap, vmin, vmax, roi_mask, deformed, barrier_mask, mesh_step
        )
        hit = self.cached_pixmap(key)
        if hit is not None:
            return hit
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
        return self.adopt_rgba(key, rgba, xg, yg, out_step)
