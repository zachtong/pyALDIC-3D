"""``ImageCanvas3D`` — zoomable, layered image canvas (2D ``ImageCanvas`` idiom).

Layers: background image (z0), semi-transparent field overlay (z1), ROI rectangle
(z2). Scene coordinates are 1:1 with image pixels, so a drawn ROI is directly in
pixel coordinates. Zoom: Fit / 100% / +/- buttons and mouse wheel (anchor under
mouse); pan with the middle mouse button. Qt view layer; no user-facing strings.

``ImageView`` is kept as a thin alias for backward compatibility.
"""

from __future__ import annotations

import numpy as np
from al_dic.gui.theme import COLORS
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView


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


class ImageCanvas3D(QGraphicsView):
    """Layered, zoomable canvas: image + field overlay + drawable ROI."""

    roi_changed = Signal(tuple)  # (xmin, xmax, ymin, ymax) in image pixels
    view_changed = Signal()  # zoom / pan / resize (overlays reposition on this)

    def __init__(self, *, editable_roi: bool = False, parent=None) -> None:
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

        self._roi_item = None  # created lazily (z2, cosmetic red pen)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(COLORS.BG_CANVAS)))
        self.setFrameShape(self.Shape.NoFrame)

        self._editable = editable_roi
        self._drag_start: QPointF | None = None
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
        self._overlay_item.setPixmap(QPixmap())
        if self._roi_item is not None:
            self._roi_item.setRect(0, 0, 0, 0)
        self._loaded_path = None

    # --- field overlay ---------------------------------------------------------

    def set_overlay_pixmap(self, pixmap: QPixmap | None) -> None:
        self._overlay_item.setPixmap(pixmap if pixmap is not None else QPixmap())

    def set_overlay_opacity(self, alpha: float) -> None:
        self._overlay_item.setOpacity(max(0.0, min(1.0, alpha)))

    # --- ROI -----------------------------------------------------------------

    def set_roi_editable(self, editable: bool) -> None:
        self._editable = editable
        self.setCursor(Qt.CursorShape.CrossCursor if editable else Qt.CursorShape.ArrowCursor)

    def set_roi(self, roi: tuple[int, int, int, int] | None) -> None:
        if roi is None:
            if self._roi_item is not None:
                self._roi_item.setRect(0, 0, 0, 0)
            return
        xmin, xmax, ymin, ymax = roi
        self._ensure_roi_item()
        self._roi_item.setRect(xmin, ymin, xmax - xmin, ymax - ymin)

    def _ensure_roi_item(self) -> None:
        if self._roi_item is None:
            pen = QPen(QColor(COLORS.ACCENT))
            pen.setWidth(2)
            pen.setCosmetic(True)
            self._roi_item = self._scene.addRect(0, 0, 0, 0, pen)
            self._roi_item.setZValue(2)

    def _emit_roi(self) -> None:
        rect = self._roi_item.rect().normalized()
        img = self._scene.sceneRect()
        xmin = max(0, int(round(rect.left())))
        ymin = max(0, int(round(rect.top())))
        xmax = min(int(img.width()), int(round(rect.right())))
        ymax = min(int(img.height()), int(round(rect.bottom())))
        if xmax > xmin and ymax > ymin:
            self.roi_changed.emit((xmin, xmax, ymin, ymax))

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

    # --- events ----------------------------------------------------------------

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_anchor = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return
        if self._editable and self.has_image and event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = self.mapToScene(event.position().toPoint())
            self._ensure_roi_item()
            self._roi_item.setRect(QRectF(self._drag_start, self._drag_start))
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
        if self._editable and self._drag_start is not None:
            current = self.mapToScene(event.position().toPoint())
            self._roi_item.setRect(QRectF(self._drag_start, current).normalized())
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if self._panning and event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(
                Qt.CursorShape.CrossCursor if self._editable else Qt.CursorShape.ArrowCursor
            )
            return
        if self._editable and self._drag_start is not None:
            self._drag_start = None
            self._emit_roi()
            return
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        super().resizeEvent(event)
        if self.has_image and self._fitted:
            self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.view_changed.emit()


# Backward-compatible alias (earlier pages referenced ImageView).
ImageView = ImageCanvas3D
