"""Projection and undistortion primitives (Qt-free; see docs/COORDINATES.md).

- :func:`project_points` — world 3D -> distorted pixel ``(u, v)`` (forward model).
- :func:`undistort_points` — distorted pixel ``(u, v)`` -> normalized undistorted
  ``(x, y)`` via ``cv2.undistortPoints`` (the ``funUndistortPoints`` equivalent).

``NaN`` propagates: non-finite / behind-camera inputs map to ``NaN`` outputs.
``cv2`` is imported lazily so importing this module only needs numpy.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.calibration.model import CameraIntrinsics


def project_points(
    points_world: NDArray[np.float64],
    intr: CameraIntrinsics,
    R: NDArray[np.float64],
    T: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Project world points to distorted pixel coordinates ``(u, v)``.

    Args:
        points_world: ``(N, 3)`` points in the world frame.
        intr: camera intrinsics + distortion.
        R, T: world -> camera pose (``X_cam = R @ X_world + T``).

    Returns:
        ``(N, 2)`` pixels ``(u, v)``; rows with ``Z <= 0`` or non-finite input
        are ``NaN`` (a point behind the camera has no valid projection).
    """
    X = np.asarray(points_world, dtype=np.float64)
    R = np.asarray(R, dtype=np.float64)
    T = np.asarray(T, dtype=np.float64).reshape(3)

    Xc = X @ R.T + T  # (N, 3) camera-frame coordinates
    Z = Xc[:, 2]
    with np.errstate(invalid="ignore", divide="ignore"):
        x = Xc[:, 0] / Z
        y = Xc[:, 1] / Z

        r2 = x * x + y * y
        radial = 1.0 + intr.k1 * r2 + intr.k2 * r2 * r2 + intr.k3 * r2 * r2 * r2
        x_d = x * radial + 2.0 * intr.p1 * x * y + intr.p2 * (r2 + 2.0 * x * x)
        y_d = y * radial + intr.p1 * (r2 + 2.0 * y * y) + 2.0 * intr.p2 * x * y

        u = intr.fx * x_d + intr.skew * y_d + intr.cx
        v = intr.fy * y_d + intr.cy

    uv = np.column_stack([u, v])
    invalid = ~np.isfinite(Z) | (Z <= 0.0) | ~np.isfinite(X).all(axis=1)
    uv[invalid] = np.nan
    return uv


def undistort_points(
    uv: NDArray[np.float64],
    intr: CameraIntrinsics,
) -> NDArray[np.float64]:
    """Undistort pixel coordinates to normalized coordinates ``(x, y)``.

    Wraps ``cv2.undistortPoints`` (no ``P``), so the result is in normalized
    (pinhole) coordinates ready for :func:`reconstruct.triangulate_dlt`. This is
    the ``funUndistortPoints`` step of ``stereoReconstruction_quadtree.m``.

    Args:
        uv: ``(N, 2)`` distorted pixels ``(u, v)``.
        intr: camera intrinsics + distortion.

    Returns:
        ``(N, 2)`` normalized undistorted coords; ``NaN`` rows pass through as
        ``NaN`` (``cv2`` is not called on them).
    """
    import cv2

    xy = np.asarray(uv, dtype=np.float64)
    out = np.full_like(xy, np.nan)
    finite = np.isfinite(xy).all(axis=1)
    if finite.any():
        pts = np.ascontiguousarray(xy[finite]).reshape(-1, 1, 2)
        # Pass a tight termination criteria to the iterative inverse. Without it,
        # cv2.undistortPoints defaults to only 5 fixed iterations with no
        # convergence test, leaving ~1e-4 normalized error (micron-scale 3D error
        # at metre depth) for edge points under real distortion. Undistortion
        # accuracy caps 3D reconstruction accuracy, so this is not optional polish.
        criteria = (cv2.TERM_CRITERIA_COUNT | cv2.TERM_CRITERIA_EPS, 40, 1e-12)
        normalized = cv2.undistortPoints(
            pts, intr.K, intr.dist_coeffs, R=None, P=None, criteria=criteria
        )
        out[finite] = normalized.reshape(-1, 2)
    return out
