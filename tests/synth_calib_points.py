"""Point-level synthetic calibration data: exact projections plus seeded noise.

No rendering. Each board view becomes a :class:`BoardDetection` whose image
points are the analytic projections of the board lattice through a known
camera, optionally moved by an extra field the lens model cannot represent,
plus Gaussian noise. Fast and deterministic, so it suits tests of the solver's
QC logic. It uses pyALDIC-3D's own projection model, so it is NOT independent
ground truth (that is the stereo_gt project's job).

NOT collected by pytest (no ``test_`` prefix).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.calibration import BoardDetection, CameraIntrinsics, StereoRig, project_points

Field = Callable[[NDArray[np.float64], CameraIntrinsics], NDArray[np.float64]]


def rotation(rx_deg: float, ry_deg: float, rz_deg: float) -> NDArray[np.float64]:
    """``Rz @ Ry @ Rx`` from degrees."""
    a, b, c = np.deg2rad([rx_deg, ry_deg, rz_deg])
    rot_x = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
    rot_y = np.array([[np.cos(b), 0, np.sin(b)], [0, 1, 0], [-np.sin(b), 0, np.cos(b)]])
    rot_z = np.array([[np.cos(c), -np.sin(c), 0], [np.sin(c), np.cos(c), 0], [0, 0, 1]])
    return (rot_z @ rot_y @ rot_x).astype(np.float64)


def pose_at(
    extent_mm: tuple[float, float],
    centre_mm: tuple[float, float, float],
    angles_deg: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Board pose (board frame -> world = left camera) with the board centred at ``centre_mm``."""
    rot = rotation(*angles_deg)
    ex, ey = extent_mm
    t = np.asarray(centre_mm, np.float64) - rot @ np.array([ex / 2.0, ey / 2.0, 0.0])
    return rot, t


def detections(
    spec,
    rig: StereoRig,
    poses: Sequence[tuple[NDArray[np.float64], NDArray[np.float64]]],
    cam: str,
    *,
    noise_px: float = 0.0,
    seed: int = 0,
    extra_field: Field | None = None,
    margin_px: float = 2.0,
    method: str = "sb",
) -> list[BoardDetection]:
    """One detection per pose; points outside the image (less ``margin_px``) are dropped."""
    rng = np.random.default_rng(seed)
    obj = spec.object_points()
    intr = rig.cameras[cam]
    rot_c, t_c = rig.pose(cam)
    width, height = intr.width, intr.height
    out: list[BoardDetection] = []
    for rot_b, t_b in poses:
        uv = project_points(obj @ rot_b.T + t_b, intr, rot_c, t_c)
        if extra_field is not None:
            uv = uv + extra_field(uv, intr)
        uv = uv + rng.normal(scale=noise_px, size=uv.shape)
        keep = np.isfinite(uv).all(axis=1)
        keep &= (uv[:, 0] >= margin_px) & (uv[:, 0] <= width - 1 - margin_px)
        keep &= (uv[:, 1] >= margin_px) & (uv[:, 1] <= height - 1 - margin_px)
        if int(keep.sum()) < 6:
            out.append(BoardDetection(ok=False, method=method, reason="board out of view"))
            continue
        out.append(
            BoardDetection(
                ok=True,
                image_points=uv[keep],
                object_points=obj[keep],
                ids=np.flatnonzero(keep).astype(np.int64),
                method=method,
            )
        )
    return out


def cubic_mismatch_field(amplitude_px: float) -> Field:
    """Non-radial cubic field ``(x*y^2, x^2*y)`` in normalised coordinates.

    Scaled so the displacement is ``amplitude_px`` at the normalised image
    corner. The 5-coefficient Brown-Conrady model cannot represent it (the
    stereo_gt ``mismatch`` preset has the same shape).
    """

    def field(uv: NDArray[np.float64], intr: CameraIntrinsics) -> NDArray[np.float64]:
        x = (uv[:, 0] - intr.cx) / intr.fx
        y = (uv[:, 1] - intr.cy) / intr.fy
        xc = max(intr.cx, (intr.width or 0) - 1 - intr.cx) / intr.fx
        yc = max(intr.cy, (intr.height or 0) - 1 - intr.cy) / intr.fy
        scale = amplitude_px / np.hypot(xc * yc**2, xc**2 * yc)
        return scale * np.column_stack([x * y**2, x**2 * y])

    return field
