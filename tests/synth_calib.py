"""Synthetic stereo calibration-image generator (D12 parity gate).

Renders views of a planar calibration board (any ``BoardSpec``) through two
distorted, converging cameras with EXACT ground truth: the board texture is
sampled by back-projecting each output pixel through the true camera model
(undistort -> ray -> plane intersection -> board mm -> texture px), so detected
control points can be compared against analytic projections of the true object
lattice, and the solver against the true rig.

NOT collected by pytest (no ``test_`` prefix).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from scipy.ndimage import map_coordinates

from al_dic_3d.calibration import CameraIntrinsics, StereoRig, project_points

IMG_W, IMG_H = 640, 512
Z0 = 500.0  # nominal board distance (mm)


def make_rig(tangential: bool = False) -> StereoRig:
    """Converging stereo rig (12 deg) with distinct mild Brown-Conrady distortion.

    Resolution/focal are sized so a 12 mm board square spans ~37 px — high-tilt
    views keep enough pixels per square for clean sub-pixel corner detection.
    ``tangential=False`` matches the solver's zero-tangent default model (the
    tangential variant exercises ``zero_tangent=False`` recovery).
    """
    common = dict(
        fx=1540.0, fy=1550.0, cx=(IMG_W - 1) / 2.0, cy=(IMG_H - 1) / 2.0, width=IMG_W, height=IMG_H
    )
    p_l = dict(p1=5e-4, p2=-4e-4) if tangential else {}
    p_r = dict(p1=-3e-4, p2=6e-4) if tangential else {}
    left = CameraIntrinsics(**common, k1=-0.08, k2=0.02, k3=0.0, **p_l)
    right = CameraIntrinsics(**common, k1=-0.06, k2=0.015, k3=0.0, **p_r)
    th = np.deg2rad(12.0)
    R = np.array(
        [[np.cos(th), 0, np.sin(th)], [0, 1, 0], [-np.sin(th), 0, np.cos(th)]],
        dtype=np.float64,
    )
    T = np.array([-Z0 * np.sin(th), 0.0, Z0 * (1.0 - np.cos(th))], dtype=np.float64)
    return StereoRig(cameras={"L": left, "R": right}, extrinsics={("L", "R"): (R, T)})


def board_poses(extent_mm: tuple[float, float], n: int = 12) -> list[tuple[NDArray, NDArray]]:
    """Deterministic diverse poses (board frame -> world = left camera frame).

    Tilts to ~+/-25 deg on both axes, roll, depth variation, and lateral offsets
    sweeping the field of view; the board center is placed near the optical axis
    shifted by the offsets, so both converging cameras keep it in frame.
    """
    ex, ey = extent_mm
    # (rot_x, rot_y, rot_z, z_scale, offset_x, offset_y): corners/edges of the
    # FOV get low-tilt poses (stay visible), center poses carry the big tilts
    # (to +/-32 deg), depths span 0.82-1.10. Reaching the sensor borders is what
    # constrains cx/cy and k1; strong tilts are what decouple cx from T and
    # fx from Z — a 0.05 px corner noise already costs ~2.5 px of cx with weak
    # (<25 deg) tilt diversity (measured with analytic corners).
    specs = [
        (0.0, 0.0, 0.0, 1.00, 0.0, 0.0),
        (0.0, 0.0, 15.0, 0.82, 0.0, 0.0),
        (4.0, 4.0, 0.0, 1.02, -44.0, -34.0),
        (-4.0, 4.0, 0.0, 1.02, 44.0, -34.0),
        (4.0, -4.0, 0.0, 1.02, -44.0, 34.0),
        (-4.0, -4.0, 0.0, 1.02, 44.0, 34.0),
        (0.0, 12.0, 5.0, 0.95, -42.0, 0.0),
        (0.0, -12.0, -5.0, 0.95, 42.0, 0.0),
        (12.0, 0.0, 5.0, 0.95, 0.0, -34.0),
        (-12.0, 0.0, -5.0, 0.95, 0.0, 34.0),
        (30.0, 0.0, 8.0, 0.92, 0.0, -10.0),
        (-30.0, 0.0, -8.0, 0.98, 0.0, 10.0),
        (0.0, 32.0, -10.0, 0.95, -10.0, 0.0),
        (0.0, -32.0, 10.0, 1.00, 10.0, 0.0),
        (20.0, 20.0, 15.0, 1.06, 10.0, 8.0),
        (-20.0, -20.0, -15.0, 1.10, -10.0, -8.0),
        (25.0, -15.0, 0.0, 0.85, -15.0, 10.0),
        (-25.0, 15.0, 0.0, 0.85, 15.0, -10.0),
    ]
    poses = []
    for rx, ry, rz, zs, ox, oy in specs[:n]:
        a, b, c = np.deg2rad([rx, ry, rz])
        rot_x = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
        rot_y = np.array([[np.cos(b), 0, np.sin(b)], [0, 1, 0], [-np.sin(b), 0, np.cos(b)]])
        rot_z = np.array([[np.cos(c), -np.sin(c), 0], [np.sin(c), np.cos(c), 0], [0, 0, 1]])
        R_b = (rot_z @ rot_y @ rot_x).astype(np.float64)
        # Center the board's mm extent on the (offset) axis point at depth zs*Z0.
        t_b = np.array([ox, oy, zs * Z0]) - R_b @ np.array([ex / 2.0, ey / 2.0, 0.0])
        poses.append((R_b, t_b.astype(np.float64)))
    return poses


def _undistorted_rays(intr: CameraIntrinsics) -> NDArray[np.float64]:
    """Per-pixel normalized ray directions (H*W, 3) — pose-independent, cached."""
    import cv2

    uu, vv = np.meshgrid(np.arange(IMG_W, dtype=np.float64), np.arange(IMG_H, dtype=np.float64))
    pts = np.column_stack([uu.ravel(), vv.ravel()]).reshape(-1, 1, 2)
    crit = (cv2.TERM_CRITERIA_COUNT | cv2.TERM_CRITERIA_EPS, 40, 1e-12)
    xn = cv2.undistortPoints(pts, intr.K, intr.dist_coeffs, R=None, P=None, criteria=crit)
    xn = xn.reshape(-1, 2)
    return np.column_stack([xn, np.ones(len(xn))])


def render_view(
    texture: NDArray,
    origin_px: tuple[float, float],
    px_per_mm: float,
    pose: tuple[NDArray, NDArray],
    rays: NDArray[np.float64],
    R_cam: NDArray,
    T_cam: NDArray,
) -> NDArray[np.float64]:
    """Render one camera view of the posed board (float64 image, white bg)."""
    R_b, t_b = pose
    cam_center = -R_cam.T @ T_cam  # world coords
    dirs = rays @ R_cam  # row-wise R_cam.T @ ray
    normal = R_b[:, 2]
    denom = dirs @ normal
    tt = np.where(np.abs(denom) > 1e-12, ((t_b - cam_center) @ normal) / denom, np.nan)
    pts = cam_center[None, :] + tt[:, None] * dirs
    board_xy = (pts - t_b) @ R_b  # row-wise R_b.T @ (X - t_b)
    tex_x = board_xy[:, 0] * px_per_mm + origin_px[0]
    tex_y = board_xy[:, 1] * px_per_mm + origin_px[1]
    vals = map_coordinates(
        texture.astype(np.float64), [tex_y, tex_x], order=1, mode="constant", cval=255.0
    )
    vals[~np.isfinite(tt) | (tt <= 0)] = 255.0
    return vals.reshape(IMG_H, IMG_W)


def render_stereo_set(spec, rig: StereoRig, poses, px_per_mm: float = 8.0, sigma: float = 3.0):
    """Render all poses through both cameras -> (left_images, right_images).

    The board texture is Gaussian band-limited before projective sampling; the
    warp scale is ~0.3 image px per texture px here, so ``sigma`` (texture px)
    is sized to spread edges over ~1 IMAGE pixel — hard or under-smoothed
    edges alias and add ~0.2 px random error to sub-pixel corner localization.
    """
    from scipy.ndimage import gaussian_filter

    texture = gaussian_filter(spec.render(px_per_mm).astype(np.float64), sigma=sigma)
    origin = spec.origin_px(px_per_mm)
    R_r, T_r = rig.pose("R")
    rays_l = _undistorted_rays(rig.cameras["L"])
    rays_r = _undistorted_rays(rig.cameras["R"])
    eye, zero = np.eye(3), np.zeros(3)
    lefts, rights = [], []
    for pose in poses:
        lefts.append(render_view(texture, origin, px_per_mm, pose, rays_l, eye, zero))
        rights.append(render_view(texture, origin, px_per_mm, pose, rays_r, R_r, T_r))
    return lefts, rights


def gt_pixels(spec, pose: tuple[NDArray, NDArray], rig: StereoRig, cam: str) -> NDArray[np.float64]:
    """Analytic projections of the board's object lattice into camera ``cam``."""
    R_b, t_b = pose
    obj = spec.object_points()
    world = obj @ R_b.T + t_b
    R, T = rig.pose(cam)
    return project_points(world, rig.cameras[cam], R, T)
