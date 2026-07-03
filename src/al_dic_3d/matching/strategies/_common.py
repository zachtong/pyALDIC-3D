"""Shared helpers for concrete correspondence strategies (Qt-free)."""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray


def bbox_roi(
    points: NDArray[np.float64],
    img_h: int,
    img_w: int,
    margin: int,
) -> tuple[int, int, int, int]:
    """Axis-aligned pixel ROI ``(xmin, xmax, ymin, ymax)`` around finite points."""
    p = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    p = p[np.isfinite(p).all(axis=1)]
    if p.size == 0:
        raise ValueError("no finite points to bound an ROI")
    xmin = max(0, int(math.floor(p[:, 0].min())) - margin)
    xmax = min(img_w - 1, int(math.ceil(p[:, 0].max())) + margin)
    ymin = max(0, int(math.floor(p[:, 1].min())) - margin)
    ymax = min(img_h - 1, int(math.ceil(p[:, 1].max())) + margin)
    return xmin, xmax, ymin, ymax
