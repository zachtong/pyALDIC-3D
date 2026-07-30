"""Freehand refinement-brush layer of :class:`~al_dic_3d.gui.widgets.image_view.ImageCanvas3D`.

Split out of ``image_view.py`` (which mixes this in) to keep that file under the
800-line cap — same arrangement as ``CanvasToolsMixin`` for ``CanvasArea3D``.
Behaviour is unchanged: the canvas owns a ``(H, W)`` uint8 stroke buffer
(255 = refine here) plus a premixed RGBA display buffer, painted with OpenCV
line segments and blitted into the cyan brush layer.

The buffer is the brush's EDITING state, so it must be kept in step with
``ProjectDraft.refinement_mask_array`` in BOTH directions: strokes flow out
through ``brush_changed``, and a restored session flows back in through
:meth:`BrushToolMixin.set_brush_mask` (batch Z) — without that, the first stroke
after reopening a project would start from an empty buffer and silently replace
the painted zones the session was saved with.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap

if TYPE_CHECKING:  # attributes/signals owned by ImageCanvas3D
    from PySide6.QtCore import QPointF, SignalInstance
    from PySide6.QtWidgets import QGraphicsPixmapItem

_BRUSH_OVERLAY_RGBA = (20, 220, 200, 110)  # cyan semi-transparent brush fill


class BrushToolMixin:
    """Refinement-brush state, painting and buffer synchronisation.

    The host (``ImageCanvas3D``) owns the buffers declared below plus the
    ``has_image`` property and ``_cancel_drawing`` used here.
    """

    if TYPE_CHECKING:  # attributes/signals owned by ImageCanvas3D
        _bg_item: QGraphicsPixmapItem
        _brush_item: QGraphicsPixmapItem
        _brush_mask: np.ndarray | None
        _brush_rgba: np.ndarray | None
        _brush_radius: int
        _brush_mode: str
        _brush_last: tuple[int, int] | None
        _tool: str
        brush_changed: SignalInstance

    def set_brush_tool(self, mode: str, radius: int | None = None) -> None:
        """Arm the freehand refinement brush ('paint' adds, 'erase' removes)."""
        self._cancel_drawing(emit=False)
        self._tool = "brush"
        self._brush_mode = "erase" if mode == "erase" else "paint"
        if radius is not None:
            self._brush_radius = max(2, int(radius))
        self._brush_last = None
        self.setCursor(Qt.CursorShape.CrossCursor)

    def set_brush_radius(self, radius: int) -> None:
        """Live radius update from the toolbar spinbox."""
        self._brush_radius = max(2, int(radius))

    def brush_mask(self) -> np.ndarray | None:
        """The painted ``(H, W)`` uint8 mask (255 = refine here), or None."""
        return self._brush_mask

    def set_brush_mask(self, mask: np.ndarray | None) -> None:
        """Adopt an existing mask as the paint buffer (session restore, Z1).

        Deliberately emits no ``brush_changed``: the draft is already the source
        of this data, and a project just opened is not dirty. A mask whose shape
        does not match the current image (or no image yet) clears the buffer
        rather than leaving a half-restored one behind.
        """
        m = None if mask is None else np.asarray(mask) > 0
        if m is None or not self._ensure_brush_buffers() or m.shape != self._brush_mask.shape:
            self._brush_mask = None
            self._brush_rgba = None
            self._brush_item.setPixmap(QPixmap())
            return
        self._brush_mask[:] = m * 255
        self._brush_rgba[:] = 0
        self._brush_rgba[m] = _BRUSH_OVERLAY_RGBA
        self._brush_last = None  # a new stroke must not connect to a stale point
        self._blit_brush()

    def clear_brush(self) -> None:
        self._brush_mask = None
        self._brush_rgba = None
        self._brush_item.setPixmap(QPixmap())
        self.brush_changed.emit()

    def _ensure_brush_buffers(self) -> bool:
        if not self.has_image:
            return False
        size = self._bg_item.pixmap().size()
        h, w = size.height(), size.width()
        if self._brush_mask is None or self._brush_mask.shape != (h, w):
            self._brush_mask = np.zeros((h, w), dtype=np.uint8)
            self._brush_rgba = np.zeros((h, w, 4), dtype=np.uint8)
        return True

    def _brush_stroke_to(self, scene_pos: QPointF) -> None:
        import cv2

        pt = (int(round(scene_pos.x())), int(round(scene_pos.y())))
        p0 = self._brush_last or pt
        thickness = 2 * self._brush_radius
        erase = self._brush_mode == "erase"
        cv2.line(self._brush_mask, p0, pt, 0 if erase else 255, thickness=thickness)
        fill = (0, 0, 0, 0) if erase else _BRUSH_OVERLAY_RGBA
        cv2.line(self._brush_rgba, p0, pt, fill, thickness=thickness)
        self._brush_last = pt
        self._blit_brush()

    def _blit_brush(self) -> None:
        """Push the premixed RGBA buffer into the brush layer's pixmap."""
        h, w = self._brush_mask.shape
        img = QImage(self._brush_rgba.data, w, h, 4 * w, QImage.Format.Format_RGBA8888)
        self._brush_item.setPixmap(QPixmap.fromImage(img.copy()))
