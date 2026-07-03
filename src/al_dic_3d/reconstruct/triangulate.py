"""DLT triangulation and reprojection error (Qt-free).

Mirrors ``stereoReconstruction_quadtree.m``: undistort points first, then linear
triangulation with the left camera as the world frame. Inputs are **normalized
undistorted** coordinates (from :func:`calibration.geometry.undistort_points`),
so the recovered points are directly in world metric units.

``NaN`` propagates: a point missing in either view triangulates to ``NaN``.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def triangulate_dlt(
    xn_left: NDArray[np.float64],
    xn_right: NDArray[np.float64],
    R: NDArray[np.float64],
    T: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Triangulate world points from a normalized stereo correspondence.

    Uses ``P_L = [I | 0]`` (left = world) and ``P_R = [R | T]`` and solves the
    homogeneous DLT system per point via a batched SVD.

    Args:
        xn_left: ``(N, 2)`` normalized undistorted coords in the left/world camera.
        xn_right: ``(N, 2)`` normalized undistorted coords in the right camera.
        R, T: world -> right-camera pose (``X_right = R @ X_world + T``).

    Returns:
        ``(N, 3)`` world points; rows non-finite in either view are ``NaN``.
    """
    xnL = np.asarray(xn_left, dtype=np.float64).reshape(-1, 2)
    xnR = np.asarray(xn_right, dtype=np.float64).reshape(-1, 2)
    if xnL.shape != xnR.shape:
        raise ValueError(f"shape mismatch: {xnL.shape} vs {xnR.shape}")

    n = xnL.shape[0]
    PL = np.hstack([np.eye(3), np.zeros((3, 1))])  # (3, 4)
    PR = np.hstack([np.asarray(R, dtype=np.float64), np.asarray(T, dtype=np.float64).reshape(3, 1)])

    X = np.full((n, 3), np.nan, dtype=np.float64)
    valid = np.isfinite(xnL).all(axis=1) & np.isfinite(xnR).all(axis=1)
    if not valid.any():
        return X

    uvL = xnL[valid]
    uvR = xnR[valid]
    m = uvL.shape[0]

    # Homogeneous system A (m, 4, 4): each row is x*P[2] - P[k].
    A = np.empty((m, 4, 4), dtype=np.float64)
    A[:, 0, :] = uvL[:, 0:1] * PL[2] - PL[0]
    A[:, 1, :] = uvL[:, 1:2] * PL[2] - PL[1]
    A[:, 2, :] = uvR[:, 0:1] * PR[2] - PR[0]
    A[:, 3, :] = uvR[:, 1:2] * PR[2] - PR[1]

    # Solution = right-singular vector of the smallest singular value.
    _, _, Vt = np.linalg.svd(A)
    Xh = Vt[:, -1, :]  # (m, 4)
    X[valid] = Xh[:, :3] / Xh[:, 3:4]
    return X


def reprojection_error(
    points_world: NDArray[np.float64],
    xn_left: NDArray[np.float64],
    xn_right: NDArray[np.float64],
    R: NDArray[np.float64],
    T: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Per-point reprojection error in normalized units (left+right RMS).

    Projects each world point back to both normalized image planes and compares
    with the observed normalized coordinates. ``NaN`` where the point or an
    observation is invalid.

    Returns:
        ``(N,)`` RMS error over the four normalized residual components.
    """
    X = np.asarray(points_world, dtype=np.float64).reshape(-1, 3)
    xnL = np.asarray(xn_left, dtype=np.float64).reshape(-1, 2)
    xnR = np.asarray(xn_right, dtype=np.float64).reshape(-1, 2)
    R = np.asarray(R, dtype=np.float64)
    T = np.asarray(T, dtype=np.float64).reshape(3)

    with np.errstate(invalid="ignore", divide="ignore"):
        projL = X[:, :2] / X[:, 2:3]  # left = world: [I|0]
        Xr = X @ R.T + T
        projR = Xr[:, :2] / Xr[:, 2:3]
        resid = np.concatenate([projL - xnL, projR - xnR], axis=1)  # (N, 4)
        err = np.sqrt(np.mean(resid * resid, axis=1))
    return err
