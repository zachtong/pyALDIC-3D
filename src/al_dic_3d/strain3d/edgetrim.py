"""Explicit strain edge-trim (Q4) — drop low-confidence VSG fits near voids.

3D adaptation of the 2D plane-fit edge trim (``al_dic.strain.comp_def_grad.
edge_valid_mask``). The 2D criterion trims a node whose distance to the ROI/hole
BOUNDARY *or* the outer image border is below ``alpha * rad`` — the OUTER ROI
edge is itself a barrier. strain3d has no pixel mask, but the node cloud has two
kinds of boundary evidence, and a node is trimmed when it is within
``alpha * vsg_radius`` (pixels, on the reference 2D grid) of EITHER:

  * an INVALID/missing node (NaN displacement or reconstruction) — an interior
    hole/crack/dropout; or
  * the node-grid OUTER boundary — a node that lacks a full 8-neighbour ring on
    the reference lattice sits on the specimen's outer edge and has a one-sided,
    biased VSG plane fit (audit A6-1). Without this a clean rectangular specimen
    trimmed NOTHING and showed its biased outer ring to the user.

The strain of a trimmed node is set to ``NaN`` (displacement is never touched).
``alpha = 0`` disables trimming. Qt-free.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

# Trim masks cached per (validity pattern, alpha); consecutive frames almost
# always share one — same rationale/bound as the neighbour-table cache.
_TRIM_CACHE_CAPACITY = 8


def edge_trim_mask(
    ref_2d: NDArray[np.float64],
    finite: NDArray[np.bool_],
    vsg_radius: float,
    alpha: float,
    cache: dict | None = None,
) -> NDArray[np.bool_]:
    """Boolean per-node mask — ``True`` = trim this node's strain to NaN.

    Args:
        ref_2d: ``(n, 2)`` reference node coords in the left image (px).
        finite: ``(n,)`` validity of this frame's fit inputs (finite ref_2d,
            ref_3d and displacement) — exactly the mask ``fit_gradients`` uses.
        vsg_radius: the VSG Chebyshev radius in pixels (``0.5*strain_length``).
        alpha: trim coefficient in ``[0, 1]``; a valid node closer than
            ``alpha * vsg_radius`` to any invalid node is trimmed. ``<= 0``
            disables (all-False mask).
        cache: optional dict reused across frames of one run (keyed by the
            validity-pattern bytes + alpha) so the KD-tree query runs once per
            distinct pattern.

    Returns:
        ``(n,)`` bool; always ``False`` at already-invalid nodes (their strain
        is NaN regardless — the count reflects TRIMMED valid nodes only).
    """
    finite = np.asarray(finite, dtype=bool)
    n = finite.shape[0]
    trim = np.zeros(n, dtype=bool)
    # NOTE: unlike the pre-A6-1 version, an all-valid grid is NOT short-circuited
    # — its outer boundary ring still needs trimming.
    if alpha <= 0.0 or not finite.any():
        return trim  # trimming disabled, or nothing valid to trim

    key = (finite.tobytes(), round(float(alpha), 9)) if cache is not None else None
    if cache is not None and key in cache:
        return cache[key]

    from scipy.spatial import cKDTree

    ref_2d = np.asarray(ref_2d, dtype=np.float64).reshape(-1, 2)
    has_coord = np.isfinite(ref_2d).all(axis=1)
    finite_idx = np.where(finite)[0]
    valid_pts = ref_2d[finite]
    radius = float(alpha) * float(vsg_radius)

    dist = np.full(finite_idx.shape[0], np.inf, dtype=np.float64)

    # (1) Distance to interior invalid nodes (holes / cracks / dropouts).
    invalid = (~finite) & has_coord
    if invalid.any():
        d_inv, _ = cKDTree(ref_2d[invalid]).query(valid_pts)
        dist = np.minimum(dist, d_inv)

    # (2) Distance to the node-grid OUTER boundary (A6-1): the 2D edge trim
    # treats the outer ROI edge as a barrier; here that edge is the perimeter of
    # the reference node lattice. Nodes missing a full 8-neighbour ring lie on it
    # (or a coord hole's rim), and holes are already covered by (1), so this
    # reduces to the invalid-node behaviour around holes.
    boundary = _boundary_nodes(ref_2d, has_coord)
    if boundary.any():
        d_bnd, _ = cKDTree(ref_2d[boundary]).query(valid_pts)
        dist = np.minimum(dist, d_bnd)

    trim[finite_idx] = dist < radius

    if cache is not None:
        cache[key] = trim
        while len(cache) > _TRIM_CACHE_CAPACITY:
            cache.pop(next(iter(cache)))
    return trim


def _boundary_nodes(
    ref_2d: NDArray[np.float64],
    has_coord: NDArray[np.bool_],
) -> NDArray[np.bool_]:
    """Nodes on the OUTER edge of the reference node lattice.

    A structured node grid's interior node has all 8 grid-neighbours (4 axis at
    the node step, 4 diagonal at ``step*sqrt2``); a node missing any of them lies
    on the lattice perimeter. Detected geometrically (no grid indices needed) by
    counting lattice neighbours within ``1.5 * step`` — which straddles the
    diagonal (``1.414*step``) but excludes the next axis node (``2*step``):
    interior => 8 neighbours + self, boundary => fewer. Holes keep their finite
    ``ref_2d`` coordinates (only the per-frame validity drops), so they stay in
    the lattice and do NOT create outer-boundary flags — interior holes are
    fenced by the invalid-node distance instead.
    """
    from scipy.spatial import cKDTree

    out = np.zeros(ref_2d.shape[0], dtype=bool)
    idx = np.where(has_coord)[0]
    pts = ref_2d[idx]
    m = pts.shape[0]
    if m < 2:
        out[idx] = True  # degenerate lattice: every present node is a boundary
        return out

    tree = cKDTree(pts)
    # Grid step = median nearest-neighbour distance (robust on a regular lattice
    # to both boundary nodes and the occasional gap).
    nn, _ = tree.query(pts, k=2)
    step = float(np.median(nn[:, 1]))
    if not np.isfinite(step) or step <= 0.0:
        out[idx] = True
        return out

    counts = np.asarray(tree.query_ball_point(pts, r=1.5 * step, return_length=True))
    out[idx] = counts < 9  # fewer than 8 grid-neighbours (+ self) => perimeter
    return out
