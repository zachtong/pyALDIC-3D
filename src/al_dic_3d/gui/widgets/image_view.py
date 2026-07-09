"""``ImageCanvas3D`` — zoomable, layered image canvas (2D ``ImageCanvas`` idiom).

Layers: background image (z0), semi-transparent field overlay (z1), refinement
brush overlay (z1.5, cyan), ROI mask overlay (z1.8, blue — the mask fill IS the
ROI display). Scene coordinates are 1:1 with image pixels, so drawn shapes are
directly in pixel coordinates.

Interaction is a tool-mode state machine ported from the 2D canvas:
``set_tool(shape, mode)`` arms a one-shot rect / polygon / circle / circle3
drawing tool (add = accent preview, cut = red preview) that rasterizes through
the attached :class:`ROIController` on commit and auto-resets to select;
``set_brush_tool(mode, radius)`` arms the freehand refinement brush (paint /
erase). Zoom: Fit / 100% / +/- and mouse wheel (anchor under mouse); pan with
the middle mouse button. Qt view layer; no user-facing strings.

``ImageView`` is kept as a thin alias for backward compatibility.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
from al_dic.gui.theme import COLORS
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
)

if TYPE_CHECKING:
    from al_dic_3d.gui.controllers.roi_controller import ROIController

# Drawing preview pens (cosmetic: constant screen width at any zoom).
_PEN_ADD = QPen(QColor(59, 130, 246, 200), 2)  # accent blue
_PEN_ADD.setCosmetic(True)
_PEN_CUT = QPen(QColor(239, 68, 68, 200), 2)  # red #ef4444
_PEN_CUT.setCosmetic(True)

_ROI_OVERLAY_RGBA = (59, 130, 246, 80)  # blue semi-transparent mask fill
_BRUSH_OVERLAY_RGBA = (20, 220, 200, 110)  # cyan semi-transparent brush fill

_SHAPE_TOOLS = ("rect", "polygon", "circle", "circle3")


def _circumcircle(
    p1: tuple[float, float], p2: tuple[float, float], p3: tuple[float, float]
) -> tuple[float, float, float] | None:
    """Circle through three points: ``(cx, cy, radius)``, or None if collinear.

    Near-collinear points yield a valid but very large circle; callers should
    sanity-cap the radius against the scene size before rasterizing.
    """
    (ax, ay), (bx, by), (cx, cy) = p1, p2, p3
    d = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-9:
        return None  # collinear -> circumcenter at infinity
    a2 = ax * ax + ay * ay
    b2 = bx * bx + by * by
    c2 = cx * cx + cy * cy
    ux = (a2 * (by - cy) + b2 * (cy - ay) + c2 * (ay - by)) / d
    uy = (a2 * (cx - bx) + b2 * (ax - cx) + c2 * (bx - ax)) / d
    return (ux, uy, math.hypot(ax - ux, ay - uy))


def load_gray_image(path) -> np.ndarray:
    """Read any-bit-depth image as a ``(H, W)`` float64 grayscale array."""
    import cv2

    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"cannot read image: {path}")
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.shape[2] == 3 else img[..., 0]
    return img.astype(np.float64)


def gray_to_qpixmap(arr: np.ndarray) -> QPixmap:
    """Min/max-normalize a 2D array to an 8-bit grayscale QPixmap."""
    arr = np.asarray(arr, dtype=np.float64)
    lo, hi = float(np.nanmin(arr)), float(np.nanmax(arr))
    norm = (arr - lo) / (hi - lo) * 255.0 if hi > lo else np.zeros_like(arr)
    buf = np.ascontiguousarray(np.clip(norm, 0, 255).astype(np.uint8))
    h, w = buf.shape
    image = QImage(buf.data, w, h, w, QImage.Format.Format_Grayscale8)
    return QPixmap.fromImage(image.copy())


def _mask_to_rgba_pixmap(mask: np.ndarray, rgba: tuple[int, int, int, int]) -> QPixmap:
    """Full-image RGBA8888 pixmap with ``rgba`` where ``mask`` is truthy."""
    m = np.asarray(mask) > 0
    h, w = m.shape
    buf = np.zeros((h, w, 4), dtype=np.uint8)
    buf[m, :] = rgba
    buf = np.ascontiguousarray(buf)
    img = QImage(buf.data, w, h, 4 * w, QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(img.copy())  # deep copy: pixmap owns the pixels


class ImageCanvas3D(QGraphicsView):
    """Layered, zoomable canvas: image + overlays + ROI toolbox drawing tools."""

    roi_mask_edited = Signal()  # a shape/brush op changed the ROI controller mask
    drawing_finished = Signal()  # one-shot tool committed/cancelled (toolbar resets)
    notice = Signal(str, str)  # (message, level) forwarded to the app log
    brush_changed = Signal()  # a refinement brush stroke finished (read brush_mask())
    view_changed = Signal()  # zoom / pan / resize (overlays reposition on this)
    scene_hover = Signal(float, float)  # mouse at scene (x, y), no drag tool active
    hover_left = Signal()  # mouse left the canvas

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._bg_item = QGraphicsPixmapItem()
        self._bg_item.setZValue(0)
        self._scene.addItem(self._bg_item)

        self._overlay_item = QGraphicsPixmapItem()
        self._overlay_item.setZValue(1)
        self._overlay_item.setOpacity(0.85)
        self._scene.addItem(self._overlay_item)

        # Brush layer (z1.5): refinement-mask strokes over frame 1 (cyan).
        self._brush_item = QGraphicsPixmapItem()
        self._brush_item.setZValue(1.5)
        self._scene.addItem(self._brush_item)
        self._brush_radius = 16
        self._brush_mode = "paint"  # "paint" or "erase"
        self._brush_mask: np.ndarray | None = None  # (H, W) uint8, 255 = refine
        self._brush_rgba: np.ndarray | None = None  # premixed display buffer
        self._brush_last: tuple[int, int] | None = None

        # ROI mask layer (z1.8): blue semi-transparent boolean mask fill —
        # the only ROI display (the bbox rectangle was removed, review F1.4).
        self._roi_mask_item = QGraphicsPixmapItem()
        self._roi_mask_item.setZValue(1.8)
        self._scene.addItem(self._roi_mask_item)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(COLORS.BG_CANVAS)))
        self.setFrameShape(self.Shape.NoFrame)
        self.setMouseTracking(True)  # hover subset window needs move events

        # Tool state machine
        self._tool: str = "select"  # select | rect | polygon | circle | circle3 | brush
        self._draw_mode: str = "add"  # add | cut (shape tools)
        self._draw_state: dict | None = None  # in-progress drawing data
        self._preview_items: list = []  # temp graphics items while drawing
        self._roi_ctrl: ROIController | None = None

        self._panning = False
        self._pan_anchor = QPointF()
        self._zoom_level = 1.0
        self._fitted = True  # auto-refit on resize until the user zooms
        self._loaded_path: str | None = None

    # --- image ---------------------------------------------------------------

    @property
    def has_image(self) -> bool:
        return not self._bg_item.pixmap().isNull()

    def set_image_file(self, path) -> None:
        """Load + show an image file; a no-op if the same path is already shown."""
        key = str(path)
        if key == self._loaded_path:
            return
        self._loaded_path = key
        self.set_image_gray(load_gray_image(path))

    def set_image_gray(self, arr: np.ndarray) -> None:
        pixmap = gray_to_qpixmap(arr)
        first = self._bg_item.pixmap().isNull() or self._bg_item.pixmap().size() != pixmap.size()
        self._bg_item.setPixmap(pixmap)
        self._scene.setSceneRect(QRectF(pixmap.rect()))
        if first or self._fitted:
            self.fit_to_view()

    def clear_image(self) -> None:
        self._bg_item.setPixmap(QPixmap())
        self.set_overlay_pixmap(None)
        self._roi_mask_item.setPixmap(QPixmap())
        self._loaded_path = None

    # --- field overlay ---------------------------------------------------------

    def set_overlay_pixmap(self, pixmap: QPixmap | None) -> None:
        if pixmap is None:
            self._overlay_item.setPixmap(QPixmap())
            self.set_overlay_geometry(1.0, 0.0, 0.0)  # drop any stale transform
        else:
            self._overlay_item.setPixmap(pixmap)

    def set_overlay_geometry(self, scale: float, x: float, y: float) -> None:
        """Place the overlay pixmap: dense renders are grid-resolution images
        positioned at the grid origin and scaled by the output step."""
        self._overlay_item.setScale(scale)
        self._overlay_item.setPos(x, y)

    def set_overlay_opacity(self, alpha: float) -> None:
        self._overlay_item.setOpacity(max(0.0, min(1.0, alpha)))

    # --- ROI toolbox -------------------------------------------------------------

    def set_roi_controller(self, ctrl: ROIController | None) -> None:
        """Attach the mask engine the shape tools rasterize into."""
        self._roi_ctrl = ctrl

    def set_tool(self, shape: str, mode: str = "add") -> None:
        """Arm a one-shot shape tool ("rect"/"polygon"/"circle"/"circle3").

        ``shape="select"`` disarms every tool (including the brush).
        """
        self._cancel_drawing(emit=False)
        self._brush_last = None
        if shape in _SHAPE_TOOLS:
            self._tool = shape
            self._draw_mode = "cut" if mode == "cut" else "add"
            self.setCursor(Qt.CursorShape.CrossCursor)
            self.setFocus(Qt.FocusReason.OtherFocusReason)  # Escape cancels
        else:
            self._tool = "select"
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def update_roi_overlay(self) -> None:
        """Refresh the blue mask overlay from the attached ROI controller."""
        mask = self._roi_ctrl.mask if self._roi_ctrl is not None else None
        if mask is None or not mask.any():
            self._roi_mask_item.setPixmap(QPixmap())
            return
        self._roi_mask_item.setPixmap(_mask_to_rgba_pixmap(mask, _ROI_OVERLAY_RGBA))
        self._roi_mask_item.setPos(0, 0)

    # --- refinement brush -------------------------------------------------------

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
        h, w = self._brush_mask.shape
        img = QImage(self._brush_rgba.data, w, h, 4 * w, QImage.Format.Format_RGBA8888)
        self._brush_item.setPixmap(QPixmap.fromImage(img.copy()))

    # --- zoom / pan ------------------------------------------------------------

    def fit_to_view(self) -> None:
        if not self.has_image:
            return
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom_level = self.transform().m11()
        self._fitted = True
        self.view_changed.emit()

    def zoom_to_100(self) -> None:
        self.resetTransform()
        self._zoom_level = 1.0
        self._fitted = False
        self.view_changed.emit()

    def zoom_in(self) -> None:
        self._apply_zoom(1.25)

    def zoom_out(self) -> None:
        self._apply_zoom(0.8)

    def _apply_zoom(self, factor: float) -> None:
        self._zoom_level *= factor
        self.scale(factor, factor)
        self._fitted = False
        self.view_changed.emit()

    def wheelEvent(self, event) -> None:  # noqa: N802 (Qt override)
        self._apply_zoom(1.25 if event.angleDelta().y() > 0 else 0.8)

    def scrollContentsBy(self, dx: int, dy: int) -> None:  # noqa: N802 (Qt override)
        super().scrollContentsBy(dx, dy)
        self.view_changed.emit()

    # --- events ----------------------------------------------------------------

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_anchor = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return
        if event.button() == Qt.MouseButton.LeftButton and self._tool in _SHAPE_TOOLS:
            self._handle_draw_press(self.mapToScene(event.position().toPoint()))
            return
        if event.button() == Qt.MouseButton.LeftButton and self._tool == "brush":
            if self._ensure_brush_buffers():
                self._brush_last = None
                self._brush_stroke_to(self.mapToScene(event.position().toPoint()))
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if self._panning:
            delta = event.position() - self._pan_anchor
            self._pan_anchor = event.position()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - int(delta.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - int(delta.y()))
            self.view_changed.emit()
            return
        if self._draw_state is not None:
            self._handle_draw_move(self.mapToScene(event.position().toPoint()))
            return
        if (
            self._tool == "brush"
            and (event.buttons() & Qt.MouseButton.LeftButton)
            and self._brush_last is not None
        ):
            self._brush_stroke_to(self.mapToScene(event.position().toPoint()))
            return
        sp = self.mapToScene(event.position().toPoint())
        self.scene_hover.emit(sp.x(), sp.y())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if self._panning and event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            crosshair = self._tool in _SHAPE_TOOLS or self._tool == "brush"
            self.setCursor(Qt.CursorShape.CrossCursor if crosshair else Qt.CursorShape.ArrowCursor)
            return
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._draw_state is not None
            and self._tool in ("rect", "circle")
        ):
            self._handle_draw_release(self.mapToScene(event.position().toPoint()))
            return
        if event.button() == Qt.MouseButton.LeftButton and self._tool == "brush":
            if self._brush_last is not None:
                self._brush_last = None
                self.brush_changed.emit()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._tool == "polygon"
            and self._draw_state is not None
        ):
            self._finalize_polygon()
            return
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if event.key() == Qt.Key.Key_Escape and self._tool in _SHAPE_TOOLS:
            self._cancel_drawing(emit=True)
            return
        super().keyPressEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802 (Qt override)
        self.hover_left.emit()
        super().leaveEvent(event)

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        super().resizeEvent(event)
        if self.has_image and self._fitted:
            self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.view_changed.emit()

    # --- shape drawing logic -----------------------------------------------------

    def _pen(self) -> QPen:
        return _PEN_CUT if self._draw_mode == "cut" else _PEN_ADD

    def _handle_draw_press(self, pos: QPointF) -> None:
        pen = self._pen()

        if self._tool == "rect":
            self._draw_state = {"start": pos}
            rect_item = QGraphicsRectItem(QRectF(pos, pos))
            rect_item.setPen(pen)
            rect_item.setZValue(10)
            self._scene.addItem(rect_item)
            self._preview_items = [rect_item]

        elif self._tool == "circle":
            self._draw_state = {"center": pos}
            ellipse = QGraphicsEllipseItem(QRectF(pos, pos))
            ellipse.setPen(pen)
            ellipse.setZValue(10)
            self._scene.addItem(ellipse)
            self._preview_items = [ellipse]

        elif self._tool == "polygon":
            if self._draw_state is None:
                self._draw_state = {"points": [pos]}
                self._preview_items = []
            else:
                self._draw_state["points"].append(pos)
            # Add a new line segment preview between the last two vertices.
            pts = self._draw_state["points"]
            if len(pts) >= 2:
                line = QGraphicsLineItem(pts[-2].x(), pts[-2].y(), pts[-1].x(), pts[-1].y())
                line.setPen(pen)
                line.setZValue(10)
                self._scene.addItem(line)
                self._preview_items.append(line)

        elif self._tool == "circle3":
            # Three-point circle: collect exactly 3 points on the circle's
            # edge, then commit the circumcircle automatically on the 3rd click.
            if self._draw_state is None:
                self._draw_state = {"points": [pos]}
                self._preview_items = []
            else:
                self._draw_state["points"].append(pos)
            dot = QGraphicsEllipseItem(QRectF(pos.x() - 2, pos.y() - 2, 4, 4))
            dot.setPen(pen)
            dot.setZValue(11)
            self._scene.addItem(dot)
            self._preview_items.append(dot)
            if len(self._draw_state["points"]) >= 3:
                self._finalize_circle3()

    def _handle_draw_move(self, pos: QPointF) -> None:
        if self._tool == "rect" and self._preview_items:
            self._preview_items[0].setRect(QRectF(self._draw_state["start"], pos).normalized())

        elif self._tool == "circle" and self._preview_items:
            center = self._draw_state["center"]
            radius = math.hypot(pos.x() - center.x(), pos.y() - center.y())
            self._preview_items[0].setRect(
                QRectF(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius)
            )

        elif self._tool == "circle3" and self._draw_state is not None:
            # Live circumcircle preview through the 2 placed points + cursor.
            pts = self._draw_state.get("points", [])
            if len(pts) >= 2:
                res = _circumcircle(
                    (pts[0].x(), pts[0].y()), (pts[1].x(), pts[1].y()), (pos.x(), pos.y())
                )
                circ = self._draw_state.get("preview_circle")
                sr = self._scene.sceneRect()
                max_r = 5.0 * math.hypot(sr.width(), sr.height())
                if res is not None and 0 < res[2] <= max_r:
                    cx, cy, r = res
                    if circ is None:
                        circ = QGraphicsEllipseItem()
                        circ.setPen(self._pen())
                        circ.setZValue(10)
                        self._scene.addItem(circ)
                        self._draw_state["preview_circle"] = circ
                        self._preview_items.append(circ)
                    circ.setRect(QRectF(cx - r, cy - r, 2 * r, 2 * r))
                    circ.setVisible(True)
                elif circ is not None:
                    circ.setVisible(False)

    def _handle_draw_release(self, pos: QPointF) -> None:
        if self._roi_ctrl is None:
            self._cancel_drawing(emit=True)
            return
        if self._tool == "rect":
            start = self._draw_state["start"]
            self._roi_ctrl.add_rectangle(
                int(min(start.x(), pos.x())),
                int(min(start.y(), pos.y())),
                int(max(start.x(), pos.x())),
                int(max(start.y(), pos.y())),
                self._draw_mode,
            )
            self._finish_drawing()
        elif self._tool == "circle":
            center = self._draw_state["center"]
            radius = int(math.hypot(pos.x() - center.x(), pos.y() - center.y()))
            self._roi_ctrl.add_circle(int(center.x()), int(center.y()), radius, self._draw_mode)
            self._finish_drawing()

    def _finalize_polygon(self) -> None:
        pts = (self._draw_state or {}).get("points", [])
        if self._roi_ctrl is None or len(pts) < 3:
            self._cancel_drawing(emit=True)
            return
        self._roi_ctrl.add_polygon([(int(p.x()), int(p.y())) for p in pts], self._draw_mode)
        self._finish_drawing()

    def _finalize_circle3(self) -> None:
        """Commit a three-point circle (circumcircle of the 3 clicks).

        Aborts gracefully when the points are (nearly) collinear, which would
        otherwise produce a garbage radius.
        """
        pts = (self._draw_state or {}).get("points", [])
        if self._roi_ctrl is None or len(pts) < 3:
            self._cancel_drawing(emit=True)
            return
        res = _circumcircle(
            (pts[0].x(), pts[0].y()), (pts[1].x(), pts[1].y()), (pts[2].x(), pts[2].y())
        )
        sr = self._scene.sceneRect()
        max_r = 5.0 * math.hypot(sr.width(), sr.height())
        if res is None or not (0 < res[2] <= max_r):
            self.notice.emit(
                "the three points are nearly collinear — pick points spread "
                "around the circle's edge",
                "warning",
            )
            self._cancel_drawing(emit=True)
            return
        cx, cy, r = res
        self._roi_ctrl.add_circle(int(round(cx)), int(round(cy)), int(round(r)), self._draw_mode)
        self._finish_drawing()

    def _finish_drawing(self) -> None:
        """One-shot commit: refresh the overlay, reset to select, notify."""
        self._remove_preview_items()
        self._draw_state = None
        self._tool = "select"
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update_roi_overlay()
        self.roi_mask_edited.emit()
        self.drawing_finished.emit()

    def _cancel_drawing(self, emit: bool) -> None:
        """Abort in-progress drawing; optionally notify (toolbar highlight reset)."""
        was_active = self._draw_state is not None or self._tool in _SHAPE_TOOLS
        self._remove_preview_items()
        self._draw_state = None
        if self._tool in _SHAPE_TOOLS:
            self._tool = "select"
            self.setCursor(Qt.CursorShape.ArrowCursor)
        if emit and was_active:
            self.drawing_finished.emit()

    def _remove_preview_items(self) -> None:
        for item in self._preview_items:
            self._scene.removeItem(item)
        self._preview_items = []


# Backward-compatible alias (earlier pages referenced ImageView).
ImageView = ImageCanvas3D
