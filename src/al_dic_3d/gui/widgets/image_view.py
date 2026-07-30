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
erase), whose buffers and painting live in
:class:`~al_dic_3d.gui.widgets.image_view_brush.BrushToolMixin` (mixed in here;
split out for the 800-line file cap). Zoom: Fit / 100% / +/- and mouse wheel
(anchor under mouse), clamped to [5 %, 4000 %]; pan with the right or middle
mouse button, or hold Space for a hand-drag pan mode (G2.4). Qt view layer; no
user-facing strings.

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

from al_dic_3d.gui.widgets.image_view_brush import BrushToolMixin

if TYPE_CHECKING:
    from al_dic_3d.gui.controllers.roi_controller import ROIController

# Drawing preview pens (cosmetic: constant screen width at any zoom).
_PEN_ADD = QPen(QColor(59, 130, 246, 200), 2)  # accent blue
_PEN_ADD.setCosmetic(True)
_PEN_CUT = QPen(QColor(239, 68, 68, 200), 2)  # red #ef4444
_PEN_CUT.setCosmetic(True)

_ROI_OVERLAY_RGBA = (59, 130, 246, 80)  # blue semi-transparent mask fill

_SHAPE_TOOLS = ("rect", "polygon", "circle", "circle3")

# Zoom clamp (G2.4): 5 % .. 4000 % — wheel/buttons can never zoom into a
# useless single-pixel blowup or an invisible speck.
ZOOM_MIN = 0.05
ZOOM_MAX = 40.0


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


def gray_to_qimage(arr: np.ndarray) -> QImage:
    """Min/max-normalize a 2D array to an 8-bit grayscale QImage.

    Thread-safe (QImage, unlike QPixmap, may be built off the GUI thread) —
    the frame prefetcher decodes through this in its worker (P2.2); the GUI
    thread then only pays the cheap ``QPixmap.fromImage`` conversion.
    """
    arr = np.asarray(arr, dtype=np.float64)
    lo, hi = float(np.nanmin(arr)), float(np.nanmax(arr))
    norm = (arr - lo) / (hi - lo) * 255.0 if hi > lo else np.zeros_like(arr)
    buf = np.ascontiguousarray(np.clip(norm, 0, 255).astype(np.uint8))
    h, w = buf.shape
    image = QImage(buf.data, w, h, w, QImage.Format.Format_Grayscale8)
    return image.copy()  # deep copy: the QImage owns its pixels past `buf`


def gray_to_qpixmap(arr: np.ndarray) -> QPixmap:
    """Min/max-normalize a 2D array to an 8-bit grayscale QPixmap."""
    return QPixmap.fromImage(gray_to_qimage(arr))


class ImageCanvas3D(BrushToolMixin, QGraphicsView):
    """Layered, zoomable canvas: image + overlays + ROI toolbox drawing tools."""

    roi_mask_edited = Signal()  # a shape/brush op changed the ROI controller mask
    drawing_finished = Signal()  # one-shot tool committed/cancelled (toolbar resets)
    seed_clicked = Signal(float, float)  # seed tool: scene (x, y) of a placed point
    seed_remove_requested = Signal(float, float)  # seed tool: right-click to remove nearest
    notice = Signal(str, str)  # (message, level) forwarded to the app log
    brush_changed = Signal()  # a refinement brush stroke finished (read brush_mask())
    view_changed = Signal()  # zoom / pan / resize (overlays reposition on this)
    scene_hover = Signal(float, float)  # mouse at scene (x, y), no drag tool active
    hover_left = Signal()  # mouse left the canvas
    context_menu_requested = Signal(object)  # plain right-CLICK (no drag): global QPoint (G3.1b)

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
        self._roi_rgba_buf: np.ndarray | None = None  # reused fill buffer (P2.6)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(COLORS.BG_CANVAS)))
        self.setFrameShape(self.Shape.NoFrame)
        self.setMouseTracking(True)  # hover subset window needs move events

        # Tool state machine
        self._tool: str = "select"  # select | rect | polygon | circle | circle3 | brush | seed
        self._draw_mode: str = "add"  # add | cut (shape tools)
        self._draw_state: dict | None = None  # in-progress drawing data
        self._preview_items: list = []  # temp graphics items while drawing
        self._roi_ctrl: ROIController | None = None
        self._seed_markers: list = []  # QGraphicsItemGroups at the placed seed points

        self._panning = False
        self._pan_button: Qt.MouseButton | None = None  # which button drives the pan
        self._pan_anchor = QPointF()
        self._pan_travel = 0.0  # accumulated drag distance of the active pan
        self._space_pan = False  # Space held: left-drag pans (hand cursor)
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

    def set_image_pixmap(self, path, pixmap: QPixmap) -> None:
        """Show a pre-decoded frame (the prefetcher hot path, P2.2).

        Same contract as :meth:`set_image_file` — records the path (no-op when
        already shown) and updates the scene rect — but skips the 100–300 ms
        decode+normalize because the worker already produced the pixmap.
        """
        key = str(path)
        if key == self._loaded_path:
            return
        self._loaded_path = key
        self._set_background(pixmap)

    def set_image_gray(self, arr: np.ndarray) -> None:
        self._set_background(gray_to_qpixmap(arr))

    def background_pixmap(self) -> QPixmap:
        """The currently shown background frame (fed back to the prefetcher)."""
        return self._bg_item.pixmap()

    def _set_background(self, pixmap: QPixmap) -> None:
        first = self._bg_item.pixmap().isNull() or self._bg_item.pixmap().size() != pixmap.size()
        self._bg_item.setPixmap(pixmap)
        self._scene.setSceneRect(QRectF(pixmap.rect()))
        if first or self._fitted:
            self.fit_to_view()

    def clear_image(self) -> None:
        self._bg_item.setPixmap(QPixmap())
        self.set_overlay_pixmap(None)
        self._roi_mask_item.setPixmap(QPixmap())
        self.set_seed_markers([])
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
        self._roi_mask_item.setPixmap(self._mask_overlay_pixmap(mask, _ROI_OVERLAY_RGBA))
        self._roi_mask_item.setPos(0, 0)

    def _mask_overlay_pixmap(self, mask: np.ndarray, rgba: tuple[int, int, int, int]) -> QPixmap:
        """RGBA fill pixmap through a REUSED buffer (P2.6: no per-call alloc).

        The (H, W, 4) fill buffer is kept between calls (same-shape masks are
        the common case); the ``QImage.copy()`` is still required so the
        pixmap owns its pixels independently of the buffer's next reuse.
        """
        m = np.asarray(mask) > 0
        h, w = m.shape
        if self._roi_rgba_buf is None or self._roi_rgba_buf.shape[:2] != (h, w):
            self._roi_rgba_buf = np.zeros((h, w, 4), dtype=np.uint8)
        buf = self._roi_rgba_buf
        buf[:] = 0
        buf[m, :] = rgba
        img = QImage(buf.data, w, h, 4 * w, QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(img.copy())  # deep copy: pixmap owns the pixels

    # --- seed point (F2) ----------------------------------------------------------

    def set_seed_tool(self, active: bool) -> None:
        """Arm / disarm the multi-seed click tool.

        Stays armed across clicks (left-click ADDS a Starting Point, right-click
        REMOVES the nearest); Esc or toggling off exits. Batch S.
        """
        self._cancel_drawing(emit=False)
        self._brush_last = None
        if active:
            self._tool = "seed"
            self.setCursor(Qt.CursorShape.CrossCursor)
            self.setFocus(Qt.FocusReason.OtherFocusReason)  # Escape cancels
        elif self._tool == "seed":
            self._tool = "select"
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def set_seed_markers(self, points) -> None:
        """Show numbered accent markers at each placed Starting Point (Batch S).

        ``points`` is an iterable of ``(x, y)`` scene coords; an empty iterable
        clears all markers. Each marker is a constant-screen-size crosshair with
        its 1-based index — legible even with many overlapping seeds.
        """
        for group in self._seed_markers:
            self._scene.removeItem(group)
        self._seed_markers = []
        from PySide6.QtGui import QFont
        from PySide6.QtWidgets import QGraphicsItemGroup, QGraphicsSimpleTextItem

        accent = QColor(COLORS.ACCENT)
        pen = QPen(accent, 1.5)
        r = 4.0
        for i, xy in enumerate(points, start=1):
            x, y = float(xy[0]), float(xy[1])
            group = QGraphicsItemGroup()
            # ItemIgnoresTransformations: constant screen size at any zoom level.
            group.setFlag(group.GraphicsItemFlag.ItemIgnoresTransformations, True)
            group.setZValue(2.5)
            circle = QGraphicsEllipseItem(-r, -r, 2 * r, 2 * r)
            circle.setPen(pen)
            circle.setBrush(QBrush(QColor(accent.red(), accent.green(), accent.blue(), 70)))
            group.addToGroup(circle)
            for x1, y1, x2, y2 in (
                (-10.0, 0.0, -r, 0.0),
                (r, 0.0, 10.0, 0.0),
                (0.0, -10.0, 0.0, -r),
                (0.0, r, 0.0, 10.0),
            ):
                line = QGraphicsLineItem(x1, y1, x2, y2)
                line.setPen(pen)
                group.addToGroup(line)
            label = QGraphicsSimpleTextItem(str(i))
            label.setBrush(QBrush(accent))
            label.setFont(QFont("", 8))
            label.setPos(8.0, 6.0)
            group.addToGroup(label)
            group.setPos(x, y)
            self._scene.addItem(group)
            self._seed_markers.append(group)

    def set_seed_marker(self, xy: tuple[float, float] | None) -> None:
        """Back-compat single-seed marker (delegates to :meth:`set_seed_markers`)."""
        self.set_seed_markers([] if xy is None else [xy])

    def _commit_seed_click(self, pos: QPointF) -> None:
        """Add a Starting Point: clamp to the image, emit, STAY armed (Batch S)."""
        rect = self._scene.sceneRect()
        x = float(min(max(pos.x(), rect.left()), rect.right() - 1))
        y = float(min(max(pos.y(), rect.top()), rect.bottom() - 1))
        self.seed_clicked.emit(x, y)  # tool stays "seed" for the next placement

    # --- refinement brush: see BrushToolMixin (image_view_brush.py) ---------------

    # --- zoom / pan ------------------------------------------------------------

    @property
    def zoom_level(self) -> float:
        """Current zoom factor (1.0 = 100 %); drives the toolbar readout (G2.4)."""
        return self._zoom_level

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
        # G2.4 clamp: adjust the factor so the resulting level stays in range.
        target = max(ZOOM_MIN, min(ZOOM_MAX, self._zoom_level * factor))
        factor = target / self._zoom_level
        if abs(factor - 1.0) < 1e-9:
            return
        self._zoom_level = target
        self.scale(factor, factor)
        self._fitted = False
        self.view_changed.emit()

    def wheelEvent(self, event) -> None:  # noqa: N802 (Qt override)
        self._apply_zoom(1.25 if event.angleDelta().y() > 0 else 0.8)

    def scrollContentsBy(self, dx: int, dy: int) -> None:  # noqa: N802 (Qt override)
        super().scrollContentsBy(dx, dy)
        self.view_changed.emit()

    # --- events ----------------------------------------------------------------

    def _begin_pan(self, button: Qt.MouseButton, pos: QPointF) -> None:
        self._panning = True
        self._pan_button = button
        self._pan_anchor = pos
        self._pan_travel = 0.0  # G3.1b: distinguishes a right-CLICK from a drag
        self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def _end_pan(self) -> None:
        self._panning = False
        self._pan_button = None
        self._restore_cursor()

    def _restore_cursor(self) -> None:
        """Cursor for the current mode: hand (Space pan) / cross (tools) / arrow."""
        if self._space_pan:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        elif self._tool in _SHAPE_TOOLS or self._tool in ("brush", "seed"):
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        # Pan starts on middle OR right drag (G2.4), or left drag in Space mode.
        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton):
            self._begin_pan(event.button(), event.position())
            return
        if event.button() == Qt.MouseButton.LeftButton and self._space_pan:
            self._begin_pan(Qt.MouseButton.LeftButton, event.position())
            return
        if event.button() == Qt.MouseButton.LeftButton and self._tool in _SHAPE_TOOLS:
            self._handle_draw_press(self.mapToScene(event.position().toPoint()))
            return
        if event.button() == Qt.MouseButton.LeftButton and self._tool == "brush":
            if self._ensure_brush_buffers():
                self._brush_last = None
                self._brush_stroke_to(self.mapToScene(event.position().toPoint()))
            return
        if event.button() == Qt.MouseButton.LeftButton and self._tool == "seed":
            self._commit_seed_click(self.mapToScene(event.position().toPoint()))
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if self._panning:
            delta = event.position() - self._pan_anchor
            self._pan_travel += abs(delta.x()) + abs(delta.y())
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
        if self._panning and event.button() == self._pan_button:
            was_click = self._pan_travel <= 4.0  # G3.1b: press+release, no drag
            self._end_pan()
            if (
                was_click
                and event.button() == Qt.MouseButton.RightButton
                and self._tool == "select"  # no draw/brush/seed tool armed
                and self.has_image
            ):
                self.context_menu_requested.emit(event.globalPosition().toPoint())
            elif (
                was_click
                and event.button() == Qt.MouseButton.RightButton
                and self._tool == "seed"  # Batch S: right-click removes nearest seed
                and self.has_image
            ):
                sp = self.mapToScene(event.position().toPoint())
                self.seed_remove_requested.emit(sp.x(), sp.y())
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
        if event.key() == Qt.Key.Key_Escape and self._tool == "seed":
            self.set_seed_tool(False)
            self.drawing_finished.emit()
            return
        # G2.4: holding Space switches to hand-drag pan mode (open-hand cursor;
        # left-drag pans while held). Consumed here so the main window's Space
        # play/pause never fires while the canvas has focus.
        if event.key() == Qt.Key.Key_Space:
            if not event.isAutoRepeat() and not self._space_pan:
                self._space_pan = True
                if not self._panning:
                    self.setCursor(Qt.CursorShape.OpenHandCursor)
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._space_pan = False
            if not self._panning:
                self._restore_cursor()
            return
        super().keyReleaseEvent(event)

    def focusOutEvent(self, event) -> None:  # noqa: N802 (Qt override)
        # A missed Space release (focus stolen mid-hold) must not stick pan mode.
        if self._space_pan:
            self._space_pan = False
            if not self._panning:
                self._restore_cursor()
        super().focusOutEvent(event)

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
