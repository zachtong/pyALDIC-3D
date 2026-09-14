"""Camera intrinsics and stereo-rig data model (frozen dataclasses, 01 §E).

Conventions are fixed in ``docs/COORDINATES.md``: pixel coords ``(u, v)`` = (col,
row); intrinsic matrix ``K = [[fx, skew, cx], [0, fy, cy], [0, 0, 1]]``; distortion in
OpenCV order ``[k1, k2, p1, p2, k3(, k4, k5, k6, s1, s2, s3, s4, tau_x, tau_y)]``
(Brown-Conrady + rational + thin-prism + tilt); world frame = left camera
(``R = I``, ``T = 0``); a camera pose ``(R, T)`` maps world -> camera.

The layout is N-camera-ready (``StereoRig.cameras`` is a ``dict``); v1 uses the
two keys ``"L"`` and ``"R"``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class CameraIntrinsics:
    """Pinhole intrinsics + OpenCV lens distortion for one camera.

    Constructed format-agnostically: the six calibration-file importers (Phase 1)
    all normalize into this type. Lengths are in pixels; distortion is
    dimensionless. The rational (``k4-k6``), thin-prism (``s1-s4``) and tilt
    (``tau_x``, ``tau_y``) terms default to zero; they used to be truncated away by
    every importer (fix batch V), which silently changed calibrations that use
    OpenCV's full model.
    """

    fx: float
    fy: float
    cx: float
    cy: float
    skew: float = 0.0
    k1: float = 0.0
    k2: float = 0.0
    p1: float = 0.0
    p2: float = 0.0
    k3: float = 0.0
    width: int | None = None
    height: int | None = None
    k4: float = 0.0
    k5: float = 0.0
    k6: float = 0.0
    s1: float = 0.0
    s2: float = 0.0
    s3: float = 0.0
    s4: float = 0.0
    tau_x: float = 0.0
    tau_y: float = 0.0

    @property
    def extended_coeffs(self) -> tuple[float, ...]:
        """``(k4, k5, k6, s1, s2, s3, s4, tau_x, tau_y)`` in OpenCV order."""
        return (
            self.k4, self.k5, self.k6,
            self.s1, self.s2, self.s3, self.s4,
            self.tau_x, self.tau_y,
        )  # fmt: skip

    @property
    def has_extended_distortion(self) -> bool:
        """True when any term beyond ``[k1, k2, p1, p2, k3]`` is non-zero."""
        return any(v != 0.0 for v in self.extended_coeffs)

    @property
    def K(self) -> NDArray[np.float64]:
        """The ``3x3`` intrinsic matrix (see docs/COORDINATES.md §3)."""
        return np.array(
            [[self.fx, self.skew, self.cx], [0.0, self.fy, self.cy], [0.0, 0.0, 1.0]],
            dtype=np.float64,
        )

    @property
    def dist_coeffs(self) -> NDArray[np.float64]:
        """Distortion vector in OpenCV order.

        ``[k1, k2, p1, p2, k3]`` (5 terms) when no extended term is set — the form
        every existing calibration file and code path uses — otherwise the full
        14-term vector ``[..., k4, k5, k6, s1, s2, s3, s4, tau_x, tau_y]``.
        """
        base = [self.k1, self.k2, self.p1, self.p2, self.k3]
        if self.has_extended_distortion:
            base.extend(self.extended_coeffs)
        return np.array(base, dtype=np.float64)


@dataclass(frozen=True)
class StereoRig:
    """A set of cameras plus their pairwise extrinsics.

    ``cameras`` maps a camera key (e.g. ``"L"``, ``"R"``) to its intrinsics.
    ``extrinsics`` maps an ordered pair ``(a, b)`` to ``(R, T)`` such that
    ``X_b = R @ X_a + T`` (world/camera-``a`` -> camera-``b``). ``world_cam`` is the
    camera whose optical frame IS the world frame (identity pose).
    """

    cameras: dict[str, CameraIntrinsics]
    extrinsics: dict[tuple[str, str], tuple[NDArray[np.float64], NDArray[np.float64]]]
    world_cam: str = "L"

    def pose(self, cam: str) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Return the world -> ``cam`` pose ``(R (3,3), T (3,))``.

        The world camera has identity pose. Any other camera reads its pose from
        ``extrinsics[(world_cam, cam)]``.
        """
        if cam not in self.cameras:
            raise KeyError(f"unknown camera {cam!r}; have {sorted(self.cameras)}")
        if cam == self.world_cam:
            return np.eye(3, dtype=np.float64), np.zeros(3, dtype=np.float64)
        key = (self.world_cam, cam)
        if key not in self.extrinsics:
            raise KeyError(f"no extrinsics {key!r}; have {sorted(self.extrinsics)}")
        R, T = self.extrinsics[key]
        return np.asarray(R, dtype=np.float64), np.asarray(T, dtype=np.float64).reshape(3)

    def projection_matrix(self, cam: str) -> NDArray[np.float64]:
        """The ``3x4`` pixel projection matrix ``P = K @ [R | T]`` for ``cam``.

        (For triangulation from *normalized* coords use :meth:`pose` and ``[R|T]``
        without ``K`` — see docs/COORDINATES.md §5.)
        """
        R, T = self.pose(cam)
        return self.cameras[cam].K @ np.hstack([R, T.reshape(3, 1)])
