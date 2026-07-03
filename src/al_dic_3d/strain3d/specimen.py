"""Optional specimen-frame transform (``GetRTMatrix.m`` equivalent, Qt-free).

Build an orthonormal specimen frame ``(R, T)`` from three user base points
``(O, X, Y)`` given in reference 2D image coords: their 3D positions are
interpolated from the reconstructed reference surface, then a right-handed frame
is built by Gram-Schmidt. Feeds ``compute_surface_strain(coordinate="specific",
specimen_R=R)`` so strain is reported in the specimen frame.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def specimen_frame(
    ref_2d: NDArray[np.float64],
    ref_3d: NDArray[np.float64],
    base_points_2d: NDArray[np.float64],
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return ``(R (3,3), T (3,))`` for the specimen frame from 3 base points.

    Args:
        ref_2d: ``(n, 2)`` reference node image coords.
        ref_3d: ``(n, 3)`` reference node 3D world coords.
        base_points_2d: ``(3, 2)`` image coords of the O, X, Y base points.

    ``x_hat = (X-O)/|.|``; ``z_hat = normalize(x_hat x (Y-O)/|.|)``;
    ``y_hat = z_hat x x_hat``. ``R`` columns are the specimen basis; ``T = O_3d``.
    """
    from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator

    ref_2d = np.asarray(ref_2d, dtype=np.float64).reshape(-1, 2)
    ref_3d = np.asarray(ref_3d, dtype=np.float64).reshape(-1, 3)
    base = np.asarray(base_points_2d, dtype=np.float64).reshape(-1, 2)
    if base.shape[0] != 3:
        raise ValueError(f"need exactly 3 base points, got {base.shape[0]}")

    finite = np.isfinite(ref_2d).all(1) & np.isfinite(ref_3d).all(1)
    src, dst = ref_2d[finite], ref_3d[finite]
    base_3d = LinearNDInterpolator(src, dst)(base)  # (3, 3); NaN outside the hull
    # MATLAB scatteredInterpolant('linear') extrapolates by default, so a base point
    # just outside the node hull (common near a specimen edge) still yields a finite
    # frame; nearest-fill those to match GetRTMatrix.m rather than aborting.
    outside = ~np.isfinite(base_3d).all(axis=1)
    if outside.any():
        base_3d[outside] = NearestNDInterpolator(src, dst)(base[outside])

    o, xp, yp = base_3d
    x_hat = xp - o
    x_hat /= np.linalg.norm(x_hat)
    y_raw = yp - o
    y_raw /= np.linalg.norm(y_raw)
    z_hat = np.cross(x_hat, y_raw)
    z_hat /= np.linalg.norm(z_hat)
    y_hat = np.cross(z_hat, x_hat)
    r = np.column_stack([x_hat, y_hat, z_hat])
    return r, o
