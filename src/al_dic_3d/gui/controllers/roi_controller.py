"""ROI mask controller — boolean add/cut operations using OpenCV.

Ported from the 2D app (``al_dic.gui.controllers.roi_controller``) and owned
here so the 3D toolbox controls its own mask engine (the 2D repo is a pinned,
read-only library). Manages a 2-D boolean mask and exposes ``add_rectangle``,
``add_polygon``, ``add_circle``, ``stroke_segment``, ``import_mask``, and
``clear``/``invert``/``save_mask`` operations. Each shape can be applied in
"add" (union) or "cut" (subtract) mode. Pure numpy + cv2; Qt-free.
"""

from __future__ import annotations

import cv2
import numpy as np
from numpy.typing import NDArray


def read_mask_as_bool(path: str, target_shape: tuple[int, int] | None = None) -> NDArray[np.bool_]:
    """Read a mask image as a boolean array (any bit depth, unicode-safe).

    Pixels brighter than 50% of the image maximum become ``True``; this
    auto-detects 0/1 vs 0/255 vs 16-bit encodings. The image is resized
    (nearest-neighbour) when ``target_shape`` differs.

    Raises:
        IOError: If the file cannot be read or decoded as an image.
    """
    try:
        buf = np.fromfile(str(path), dtype=np.uint8)  # unicode-safe on Windows
    except OSError as exc:
        raise OSError(f"cannot read mask file: {path}") from exc
    img = cv2.imdecode(buf, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise OSError(f"cannot decode mask image: {path}")
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.shape[2] == 3 else img[..., 0]
    arr = img.astype(np.float64)
    if target_shape is not None and arr.shape[:2] != tuple(target_shape):
        arr = cv2.resize(arr, (target_shape[1], target_shape[0]), interpolation=cv2.INTER_NEAREST)
    max_val = float(arr.max()) if arr.size else 0.0
    if max_val <= 0.0:
        return np.zeros(arr.shape, dtype=bool)
    return arr > (max_val / 2.0)


class ROIController:
    """Boolean ROI mask with add/cut shape operations."""

    def __init__(self, img_shape: tuple[int, int]) -> None:
        """Initialize an empty mask.

        Args:
            img_shape: (height, width) of the image.
        """
        if len(img_shape) != 2 or img_shape[0] <= 0 or img_shape[1] <= 0:
            raise ValueError(f"img_shape must be (H, W) with positive dimensions, got {img_shape}")
        self._shape = img_shape
        self.mask: NDArray[np.bool_] = np.zeros(img_shape, dtype=bool)

    @property
    def shape(self) -> tuple[int, int]:
        """Return (height, width) of the mask."""
        return self._shape

    def add_rectangle(self, x1: int, y1: int, x2: int, y2: int, mode: str = "add") -> None:
        """Add or cut a filled rectangle.

        Args:
            x1, y1: Top-left corner (column, row).
            x2, y2: Bottom-right corner (column, row).
            mode: "add" to union, "cut" to subtract.
        """
        canvas = np.zeros(self._shape, dtype=np.uint8)
        cv2.rectangle(canvas, (x1, y1), (x2, y2), 255, thickness=-1)
        self._apply(canvas, mode)

    def add_polygon(self, points: list[tuple[int, int]], mode: str = "add") -> None:
        """Add or cut a filled polygon.

        Args:
            points: List of (x, y) vertices.
            mode: "add" to union, "cut" to subtract.
        """
        if len(points) < 3:
            return
        canvas = np.zeros(self._shape, dtype=np.uint8)
        pts = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
        cv2.fillPoly(canvas, [pts], 255)
        self._apply(canvas, mode)

    def add_circle(self, cx: int, cy: int, radius: int, mode: str = "add") -> None:
        """Add or cut a filled circle.

        Args:
            cx, cy: Center (column, row).
            radius: Circle radius in pixels.
            mode: "add" to union, "cut" to subtract.
        """
        if radius <= 0:
            return
        canvas = np.zeros(self._shape, dtype=np.uint8)
        cv2.circle(canvas, (cx, cy), radius, 255, thickness=-1)
        self._apply(canvas, mode)

    def stroke_segment(
        self, x1: int, y1: int, x2: int, y2: int, radius: int, mode: str = "add"
    ) -> None:
        """Paint or erase a thick line segment (freehand brush stroke).

        Each call rasterizes a single segment between consecutive mouse
        positions; a click (start == end) degenerates to a filled disc.

        Args:
            x1, y1: Start of the segment (column, row).
            x2, y2: End of the segment (column, row).
            radius: Brush radius in pixels (>= 1).
            mode: ``"add"`` to union into the mask, ``"cut"`` to subtract.
        """
        if radius <= 0:
            return
        canvas = np.zeros(self._shape, dtype=np.uint8)
        if x1 == x2 and y1 == y2:
            cv2.circle(canvas, (x1, y1), radius, 255, thickness=-1)
        else:
            cv2.line(canvas, (x1, y1), (x2, y2), 255, thickness=2 * radius, lineType=cv2.LINE_8)
        self._apply(canvas, mode)

    def import_mask(self, path: str) -> None:
        """Import an external mask image (resized to fit when needed).

        Args:
            path: Filesystem path to the mask image.

        Raises:
            IOError: If the file cannot be read as an image.
        """
        self.mask = read_mask_as_bool(path, target_shape=self._shape)

    def clear(self) -> None:
        """Reset the mask to all False."""
        self.mask = np.zeros(self._shape, dtype=bool)

    def invert(self) -> None:
        """Invert the mask (True <-> False)."""
        self.mask = ~self.mask

    def save_mask(self, path: str) -> None:
        """Save the current mask as a grayscale PNG (255=True, 0=False).

        Args:
            path: Filesystem path to write the image.
        """
        img = (self.mask.astype(np.uint8)) * 255
        success, buf = cv2.imencode(".png", img)
        if not success:
            raise OSError(f"Failed to encode mask to PNG: {path}")
        buf.tofile(path)

    def _apply(self, canvas: NDArray[np.uint8], mode: str) -> None:
        """Apply a rasterized shape to the mask.

        Args:
            canvas: uint8 image with 255 inside the shape.
            mode: "add" or "cut".
        """
        region = canvas > 0
        if mode == "add":
            self.mask = self.mask | region
        elif mode == "cut":
            self.mask = self.mask & ~region
        else:
            raise ValueError(f"Unknown mode: {mode!r}. Expected 'add' or 'cut'.")
