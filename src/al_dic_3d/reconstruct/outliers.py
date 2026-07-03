"""3D robustness: reprojection gate + statistical outlier removal (Qt-free).

Post-reconstruction filters that demote bad points to ``INVALID`` (NaN 3D, NaN
reproj, ``INVALID`` source). Both are pure: a new :class:`Reconstruction3D` is
returned with the displacement recomputed so ``D = P - P[0]`` stays consistent
after any demotion.

``remove_3d_outliers`` ports the *idea* of ``funRemoveOutliers3D`` (not its code):
a per-frame universal-outlier test (Westerweel & Scarano) on the displacement
field — a point whose displacement deviates from its spatial-neighbour median by
more than ``threshold * (neighbour MAD + eps)`` in any component is an outlier.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.matching.contracts import INVALID
from al_dic_3d.reconstruct.reconstruction import Reconstruction3D


def _rebuilt(
    points: NDArray[np.float64],
    reproj: NDArray[np.float64],
    source: NDArray[np.uint8],
) -> Reconstruction3D:
    """Reassemble a Reconstruction3D, recomputing ``D = P - P[0]`` (NaN-consistent)."""
    displacement = points - points[0][None, :, :]
    return Reconstruction3D(
        points=points, displacement=displacement, reproj_error=reproj, source=source
    )


def apply_reproj_gate(rec: Reconstruction3D, max_reproj: float) -> Reconstruction3D:
    """Demote points whose reprojection error exceeds ``max_reproj`` (native units).

    ``reproj_error`` is in normalized coordinates (see ``reconstruct.triangulate``),
    so a caller with a pixel threshold should divide by the focal length first.
    """
    bad = np.isfinite(rec.reproj_error) & (rec.reproj_error > float(max_reproj))
    if not bad.any():
        return rec
    points = rec.points.copy()
    reproj = rec.reproj_error.copy()
    source = rec.source.copy()
    points[bad] = np.nan
    reproj[bad] = np.nan
    source[bad] = INVALID
    return _rebuilt(points, reproj, source)


def remove_3d_outliers(
    rec: Reconstruction3D,
    ref_coords: NDArray[np.float64],
    *,
    k_neighbors: int = 8,
    threshold: float = 3.0,
    eps: float = 0.02,
) -> Reconstruction3D:
    """Universal-outlier test on each frame's displacement field.

    Args:
        rec: the reconstruction to clean.
        ref_coords: ``(n_pts, 2)`` reference (frame-1) node coordinates — the
            spatial topology for the neighbourhood (always finite for a mesh).
        k_neighbors: neighbours per point for the local median/MAD.
        threshold: reject if the normalized residual exceeds this in any component.
        eps: MAD floor (in displacement units, mm) so a smooth field is not
            over-sensitive where the local MAD collapses to ~0.

    Returns:
        A new :class:`Reconstruction3D` with outliers demoted to ``INVALID``.
    """
    from scipy.spatial import cKDTree

    ref = np.asarray(ref_coords, dtype=np.float64).reshape(-1, 2)
    n_frames, n_pts = rec.n_frames, rec.n_pts
    if n_pts < 3:
        return rec

    kq = min(k_neighbors + 1, n_pts)  # +1 because the nearest is the point itself
    tree = cKDTree(ref)
    _, idx = tree.query(ref, k=kq)
    nbr = idx[:, 1:] if kq > 1 else idx  # drop self

    points = rec.points.copy()
    reproj = rec.reproj_error.copy()
    source = rec.source.copy()

    with np.errstate(invalid="ignore"):
        for k in range(n_frames):
            d = rec.displacement[k]  # (n_pts, 3)
            d_nbr = d[nbr]  # (n_pts, k, 3), NaN where a neighbour is invalid
            if np.isnan(d_nbr).all():
                continue
            med = np.nanmedian(d_nbr, axis=1)  # (n_pts, 3)
            mad = np.nanmedian(np.abs(d_nbr - med[:, None, :]), axis=1)  # (n_pts, 3)
            resid = np.abs(d - med) / (mad + eps)
            outlier = np.isfinite(d).all(axis=1) & (resid > threshold).any(axis=1)
            points[k, outlier] = np.nan
            reproj[k, outlier] = np.nan
            source[k, outlier] = INVALID

    return _rebuilt(points, reproj, source)
