"""Shared helpers for concrete correspondence strategies (Qt-free)."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from al_dic_3d.sequence import StereoSequence


def mask_stream(seq: StereoSequence, cam: str) -> list[NDArray[np.float64]] | None:
    """Per-frame masks for ``cam`` as float64 arrays, or None when absent.

    Strategies MUST forward these into :func:`temporal_track`: tracking a
    background-heavy bounding-box mesh without masks lets textureless nodes
    poison the FFT seed search (escalating search zones break even the good
    nodes) — the failure mode found on the Stereo DIC Challenge S3 dataset,
    where the 2D engine then silently zero-filled an all-NaN field.
    """
    if seq.masks.get(cam) is None:
        return None
    return [np.asarray(seq.mask(cam, k), dtype=np.float64) for k in range(seq.n_frames)]


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
