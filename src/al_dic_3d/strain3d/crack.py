"""Crack / barrier geometry for surface-strain (Qt-free port of the 2D rule).

The reference ROI mask can carry a **thin crack barrier** — a continuous band of
masked (``mask < 0.5``) pixels narrower than the node spacing, so no node falls
inside it, yet a VSG plane fit spanning it would blend the two crack faces. These
helpers reproduce the 2D line-of-sight rule
(:func:`al_dic.strain.comp_def_grad._segment_hits_mask` +
:func:`~al_dic.strain.comp_def_grad.node_boundary_distance`) so the strain layer
can drop cross-crack neighbours and trim the crack band.

Ported (not imported) to keep :mod:`al_dic_3d.strain3d` pure numpy/scipy with no
``al_dic`` coupling. The conventions MATCH the 2D source exactly:

* coordinates are ``(x, y)`` with ``x`` = image column, ``y`` = image row;
* mask lookups round-half-to-even then clip to ``[0, dim-1]``;
* a segment is sampled on its OPEN interior at ~1 px, ``n = int(hypot(dx, dy))``
  samples, ``n < 2`` never blocks (adjacent nodes can never be excluded);
* "barrier" = any interior sample with ``mask < 0.5``.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def node_boundary_distance(
    coordinates: NDArray[np.float64],
    mask: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Distance from each node's pixel to the nearest INTERIOR barrier pixel.

    Port of ``al_dic.strain.comp_def_grad.node_boundary_distance``: equal to
    ``distance_transform_edt(mask > 0.5)`` sampled at the nodes' clipped-rounded
    pixels, computed in ``O(n_nodes + n_boundary)`` via an 8-connected boundary
    KD-tree. The image border is NOT counted here. A node whose own pixel is
    background sits on the barrier and gets ``0``; a mask with no background at
    all returns ``+inf`` everywhere.
    """
    from scipy.ndimage import binary_dilation
    from scipy.spatial import cKDTree

    mask = np.asarray(mask, dtype=np.float64)
    coordinates = np.asarray(coordinates, dtype=np.float64).reshape(-1, 2)
    h, w = mask.shape
    fg = mask > 0.5
    cc = np.clip(np.round(coordinates[:, 0]).astype(np.int64), 0, w - 1)
    rc = np.clip(np.round(coordinates[:, 1]).astype(np.int64), 0, h - 1)

    boundary = (~fg) & binary_dilation(fg, structure=np.ones((3, 3), bool))
    ys, xs = np.where(boundary)
    if len(ys) == 0:
        d = np.full(coordinates.shape[0], np.inf, dtype=np.float64)
    else:
        tree = cKDTree(np.column_stack([xs, ys]).astype(np.float64))
        d, _ = tree.query(np.column_stack([cc, rc]).astype(np.float64))
    # A node on a background pixel is ON the barrier -> distance 0.
    return np.where(fg[rc, cc], d, 0.0)


def segment_hits_barrier(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    mask: NDArray[np.float64],
) -> bool:
    """True if the open segment ``(x0,y0)->(x1,y1)`` passes through ``mask < 0.5``.

    Port of ``al_dic.strain.comp_def_grad._segment_hits_mask``: both endpoints
    (mesh nodes inside the ROI) are excluded; the interior is sampled at ~1 px,
    ``n = int(hypot(dx, dy))`` (int truncation), ``n < 2`` never blocks.
    """
    n = int(np.hypot(x1 - x0, y1 - y0))
    if n < 2:
        return False
    t = np.linspace(0.0, 1.0, n + 1)[1:-1]  # interior samples only
    xs = np.clip(np.round(x0 + t * (x1 - x0)).astype(np.int64), 0, mask.shape[1] - 1)
    ys = np.clip(np.round(y0 + t * (y1 - y0)).astype(np.int64), 0, mask.shape[0] - 1)
    return bool(np.any(mask[ys, xs] < 0.5))
