"""``ImageView`` — a fit-to-view image canvas with an optional drawable ROI.

A ``QGraphicsView`` whose scene is 1:1 with image pixels, so an ROI drawn on it is
directly in pixel coordinates ``(xmin, xmax, ymin, ymax)``. Used to preview the
imported frames and to draw the ROI on the left camera, frame 1. Qt view layer; no
user-facing strings.
"""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView


def load_gray_image(path) -> np.ndarray:
    """Read any-bit-depth image as a ``(H, W)`` float64 grayscale array."""
    import cv2

    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"cannot read image: {path}")
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.shape[2] == 3 else img[..., 0]
    return img.astype(np.float64)


class ImageView(QGraphicsView):
    """Displays a grayscale image; optionally lets the user rubber-band an ROI."""

    roi_changed = Signal(tuple)  # (xmin, xmax, ymin, ymax) in image pixels

    def __init__(self, *, editable_roi: bool = False, parent=None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setMinimumHeight(160)
        self._pix_item = None
        self._roi_item = None
        self._editable = editable_roi
        self._drag_start = None
        self._loaded_path: str | None = None

    @property
    def has_image(self) -> bool:
        return self._pix_item is not None

    # --- image ---------------------------------------------------------------

    def set_image_file(self, path) -> None:
        """Load + show an image file; a no-op if the same path is already shown."""
        key = str(path)
        if key == self._loaded_path:
            return
        self._loaded_path = key
        self.set_image_gray(load_gray_image(path))

    def set_image_gray(self, arr: np.ndarray) -> None:
        """Show a 2D array (any dtype), min/max-normalized to 8-bit for display."""
        arr = np.asarray(arr, dtype=np.float64)
        lo, hi = float(np.nanmin(arr)), float(np.nanmax(arr))
        norm = (arr - lo) / (hi - lo) * 255.0 if hi > lo else np.zeros_like(arr)
        buf = np.ascontiguousarray(np.clip(norm, 0, 255).astype(np.uint8))
        h, w = buf.shape
        image = QImage(buf.data, w, h, w, QImage.Format.Format_Grayscale8)
        self._set_pixmap(QPixmap.fromImage(image.copy()))

    def clear_image(self) -> None:
        self._scene.clear()
        self._pix_item = None
        self._roi_item = None
        self._loaded_path = None

    def _set_pixmap(self, pixmap: QPixmap) -> None:
        self._scene.clear()
        self._roi_item = None
        self._pix_item = self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(QRectF(pixmap.rect()))
        self.fitInView(self._pix_item, Qt.AspectRatioMode.KeepAspectRatio)

    # --- ROI -----------------------------------------------------------------

    def set_roi(self, roi: tuple[int, int, int, int] | None) -> None:
        if roi is None or self._pix_item is None:
            return
        xmin, xmax, ymin, ymax = roi
        self._ensure_roi_item()
        self._roi_item.setRect(xmin, ymin, xmax - xmin, ymax - ymin)

    def _ensure_roi_item(self) -> None:
        if self._roi_item is None:
            pen = QPen(QColor("#ff5252"))
            pen.setWidth(2)
            pen.setCosmetic(True)  # constant on-screen width regardless of zoom
            self._roi_item = self._scene.addRect(0, 0, 0, 0, pen)

    def _emit_roi(self) -> None:
        rect = self._roi_item.rect().normalized()
        img = self._scene.sceneRect()
        xmin = max(0, int(round(rect.left())))
        ymin = max(0, int(round(rect.top())))
        xmax = min(int(img.width()), int(round(rect.right())))
        ymax = min(int(img.height()), int(round(rect.bottom())))
        if xmax > xmin and ymax > ymin:
            self.roi_changed.emit((xmin, xmax, ymin, ymax))

    # --- events --------------------------------------------------------------

    def mousePressEvent(self, event) -> None:
        if self._editable and self._pix_item and event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = self.mapToScene(event.position().toPoint())
            self._ensure_roi_item()
            self._roi_item.setRect(QRectF(self._drag_start, self._drag_start))
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._editable and self._drag_start is not None:
            current = self.mapToScene(event.position().toPoint())
            self._roi_item.setRect(QRectF(self._drag_start, current).normalized())
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._editable and self._drag_start is not None:
            self._drag_start = None
            self._emit_roi()
        else:
            super().mouseReleaseEvent(event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._pix_item is not None:
            self.fitInView(self._pix_item, Qt.AspectRatioMode.KeepAspectRatio)
