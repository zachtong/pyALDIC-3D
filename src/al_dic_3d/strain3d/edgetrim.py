"""Explicit strain edge-trim (Q4) — drop low-confidence VSG fits near voids.

3D adaptation of the 2D plane-fit edge trim (``al_dic.strain.comp_def_grad.
edge_valid_mask``): there the criterion is the pixel distance to the ROI/hole
BOUNDARY; here the mesh only exists inside the ROI, so the boundary evidence is
the set of INVALID/missing nodes (NaN displacement or reconstruction). A node
whose distance — in pixels, on the reference 2D grid — to the nearest invalid
node is smaller than ``alpha * vsg_radius`` has a one-sided, boundary-crossing
VSG window: its plane fit is biased, and its strain is trimmed to ``NaN``
(displacement is never touched). ``alpha = 0`` disables trimming; ``alpha = 1``
trims any node whose window can reach an invalid node. Qt-free.
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
    if alpha <= 0.0 or finite.all() or not finite.any():
        return trim  # nothing to trim against (or trimming disabled)

    key = (finite.tobytes(), round(float(alpha), 9)) if cache is not None else None
    if cache is not None and key in cache:
        return cache[key]

    from scipy.spatial import cKDTree

    ref_2d = np.asarray(ref_2d, dtype=np.float64).reshape(-1, 2)
    invalid = ~finite
    # Invalid nodes without usable 2D coords carry no boundary evidence.
    invalid &= np.isfinite(ref_2d).all(axis=1)
    if invalid.any():
        dist, _ = cKDTree(ref_2d[invalid]).query(ref_2d[finite])
        trim[np.where(finite)[0]] = dist < float(alpha) * float(vsg_radius)

    if cache is not None:
        cache[key] = trim
        while len(cache) > _TRIM_CACHE_CAPACITY:
            cache.pop(next(iter(cache)))
    return trim
