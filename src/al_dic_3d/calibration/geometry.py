"""Projection and undistortion primitives (Qt-free; see docs/COORDINATES.md).

- :func:`project_points` — world 3D -> distorted pixel ``(u, v)`` (forward model).
- :func:`undistort_points` — distorted pixel ``(u, v)`` -> normalized undistorted
  ``(x, y)`` via ``cv2.undistortPoints`` (the ``funUndistortPoints`` equivalent).

``NaN`` propagates: non-finite / behind-camera inputs map to ``NaN`` outputs.
``cv2`` is imported lazily so importing this module only needs numpy.

The two functions are exact inverses for every supported model: the 5-term
Brown-Conrady form keeps its closed-form forward model, the extended OpenCV
terms (rational, thin prism, tilt) go through ``cv2.projectPoints``, and the
skew term ``K[0, 1]`` — which OpenCV's distortion functions ignore — is applied
and inverted here on both sides.
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

        if intr.has_extended_distortion:
            x_d, y_d = _distort_opencv(x, y, intr)
        else:
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


def _distort_opencv(
    x: NDArray[np.float64], y: NDArray[np.float64], intr: CameraIntrinsics
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Distort normalized coordinates with OpenCV's full 14-term model.

    ``cv2.projectPoints`` with an identity camera matrix returns the distorted
    normalized coordinates exactly as OpenCV models them (tilt included), so the
    forward model can never drift from the ``cv2.undistortPoints`` inverse.
    """
    import cv2

    x_d = np.full_like(x, np.nan)
    y_d = np.full_like(y, np.nan)
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.any():
        pts = np.column_stack([x[ok], y[ok], np.ones(int(ok.sum()))])
        out, _ = cv2.projectPoints(
            np.ascontiguousarray(pts), np.zeros(3), np.zeros(3), np.eye(3), intr.dist_coeffs
        )
        out = out.reshape(-1, 2)
        x_d[ok] = out[:, 0]
        y_d[ok] = out[:, 1]
    return x_d, y_d


# Which OpenCV API takes the iteration criteria: ``"undistortPoints"`` (OpenCV 5)
# or ``"undistortPointsIter"`` (OpenCV 4.x, whose undistortPoints has no
# ``criteria``). Probed on first use; tests reset it to None.
_CRITERIA_API: str | None = None


def _undistort_cv(
    pts: NDArray[np.float64], K: NDArray[np.float64], dist: NDArray[np.float64], criteria
) -> NDArray[np.float64]:
    """``cv2.undistortPoints`` with explicit criteria on OpenCV 4.x and 5.x."""
    global _CRITERIA_API
    import cv2

    if _CRITERIA_API in (None, "undistortPoints"):
        try:
            out = cv2.undistortPoints(pts, K, dist, R=None, P=None, criteria=criteria)
            _CRITERIA_API = "undistortPoints"
            return out
        except (TypeError, cv2.error) as exc:
            # OpenCV 4.x rejects the keyword (cv2.error "Overload resolution
            # failed: 'criteria' is an invalid keyword argument"). Anything else
            # is a genuine error and must surface unchanged.
            if "criteria" not in str(exc) or not hasattr(cv2, "undistortPointsIter"):
                raise
            _CRITERIA_API = "undistortPointsIter"
    return cv2.undistortPointsIter(pts, K, dist, None, None, criteria)


def undistort_points(
    uv: NDArray[np.float64],
    intr: CameraIntrinsics,
) -> NDArray[np.float64]:
    """Undistort pixel coordinates to normalized coordinates ``(x, y)``.

    Wraps ``cv2.undistortPoints`` (no ``P``), so the result is in normalized
    (pinhole) coordinates ready for :func:`reconstruct.triangulate_dlt`. This is
    the ``funUndistortPoints`` step of ``stereoReconstruction_quadtree.m``.

    OpenCV reads only ``fx, fy, cx, cy`` from the camera matrix, so a non-zero
    skew is removed here first (the exact inverse of :func:`project_points`) and
    the distortion is then inverted in normalized coordinates.

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
        if intr.skew != 0.0:
            p = pts.reshape(-1, 2)
            y_d = (p[:, 1] - intr.cy) / intr.fy
            x_d = (p[:, 0] - intr.cx - intr.skew * y_d) / intr.fx
            pts = np.column_stack([x_d, y_d]).reshape(-1, 1, 2)
            K = np.eye(3)
        else:
            K = intr.K
        normalized = _undistort_cv(pts, K, intr.dist_coeffs, criteria)
        out[finite] = normalized.reshape(-1, 2)
    return out
