"""Camera-image backgrounds exactly as the canvas shows them (Qt-free).

The canvas reads frames at their native bit depth
(``gui.widgets.image_view.load_gray_image``: ``IMREAD_UNCHANGED``, colour ->
gray) and min/max-stretches them to 8 bits (``gray_to_qimage``). The exporters
used ``IMREAD_GRAYSCALE``, which squeezes 16-bit files to 8 bits by dividing by
256: 12-bit data in 16-bit files peaked at 15 (a black background), and 8-bit
frames lost the canvas's contrast stretch (fix batch V, M6).

:func:`load_display_gray` reproduces the canvas pipeline bit for bit — the
same ``(v - lo) / (hi - lo) * 255`` float64 formula, clipped and truncated —
through a lookup table for integer images (identical values, ~10x faster at
12 Mpx than the float64 image). It is shared by every export path and the
export Preview so all of them match the canvas.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from numpy.typing import NDArray


def _to_gray(img: NDArray) -> NDArray:
    """Colour -> single channel exactly like the canvas loader."""
    import cv2

    if img.ndim == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.shape[2] == 3 else img[..., 0]
    return img


def stretch_to_u8(gray: NDArray) -> NDArray[np.uint8]:
    """Min/max-normalize a 2D array to uint8 (the canvas ``gray_to_qimage`` rule)."""
    arr = np.asarray(gray)
    if arr.size == 0:
        return np.zeros(arr.shape, np.uint8)
    lo = float(np.nanmin(arr))
    hi = float(np.nanmax(arr))
    if arr.dtype in (np.uint8, np.uint16) and hi > lo:
        # One float64 evaluation per possible value — bit-identical to the
        # per-pixel float64 formula below, without a float64 copy of the image.
        values = np.arange(int(hi) + 1, dtype=np.float64)
        lut = np.clip((values - lo) / (hi - lo) * 255.0, 0, 255).astype(np.uint8)
        return lut[arr]
    arr = arr.astype(np.float64)
    norm = (arr - lo) / (hi - lo) * 255.0 if hi > lo else np.zeros_like(arr)
    return np.clip(norm, 0, 255).astype(np.uint8)


def load_display_gray(path: str | Path) -> NDArray[np.uint8] | None:
    """Read any-bit-depth image -> canvas-identical ``(H, W)`` uint8; None on failure.

    Unicode-safe (``pathsafe.imread_unicode``).
    """
    from al_dic_3d.pathsafe import imread_unicode

    img = imread_unicode(path)
    if img is None:
        return None
    return stretch_to_u8(_to_gray(img))


def image_shape(path: str | Path) -> tuple[int, int] | None:
    """``(H, W)`` of an image file from its header only (no pixel decode)."""
    try:
        from PIL import Image

        with Image.open(Path(path)) as im:
            w, h = im.size
        return int(h), int(w)
    except Exception:  # noqa: BLE001 - unknown format / missing file -> caller falls back
        return None
