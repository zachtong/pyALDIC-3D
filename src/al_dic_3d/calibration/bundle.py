"""Joint stereo bundle adjustment with a robust per-point loss (Qt-free, C3).

Refines BOTH cameras' intrinsics, the stereo extrinsics, and every board pose
in ONE scipy ``least_squares`` problem. What this adds over the OpenCV
``stereoCalibrate`` pipeline in :mod:`al_dic_3d.calibration.solve`:

- a robust per-POINT loss (``soft_l1``): individual bad corners are
  down-weighted instead of poisoning the solve or costing a whole view;
- views seen by only ONE camera still contribute (their mono reprojection
  residuals constrain that camera's intrinsics), whereas ``stereoCalibrate``
  can only consume common views.

Concept follows aniposelib's ``CameraGroup.bundle_adjust_iter`` (BSD-2) and
multical's joint optimization — used as design references only; this is an
original implementation on scipy/OpenCV.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.calibration.detect import BoardDetection
from al_dic_3d.calibration.model import CameraIntrinsics, StereoRig

if TYPE_CHECKING:
    from al_dic_3d.calibration.solve import StereoResult

_BASE_KEYS = ("fx", "fy", "cx", "cy", "k1", "k2")


def _free_keys(*, zero_tangent: bool, fix_k3: bool) -> tuple[str, ...]:
    keys = list(_BASE_KEYS)
    if not zero_tangent:
        keys += ["p1", "p2"]
    if not fix_k3:
        keys += ["k3"]
    return tuple(keys)


def _intr_vector(intr: CameraIntrinsics, keys: tuple[str, ...]) -> NDArray[np.float64]:
    return np.array([getattr(intr, k) for k in keys], dtype=np.float64)


def _intr_from(base: CameraIntrinsics, keys: tuple[str, ...], vals: NDArray) -> CameraIntrinsics:
    from dataclasses import replace

    return replace(base, **{k: float(v) for k, v in zip(keys, vals, strict=True)})


def _init_poses(
    left: Sequence[BoardDetection],
    right: Sequence[BoardDetection],
    views: list[int],
    rig: StereoRig,
    min_points: int,
) -> NDArray[np.float64]:
    """Per-view board pose seeds (world = left frame), ``(n_views, 6)`` rvec|tvec."""
    import cv2

    r_s, t_s = rig.pose("R")
    intr_l, intr_r = rig.cameras["L"], rig.cameras["R"]
    poses = np.zeros((len(views), 6), dtype=np.float64)
    for k, i in enumerate(views):
        if left[i].ok and left[i].n_points >= min_points:
            _ok, rvec, tvec = cv2.solvePnP(
                left[i].object_points, left[i].image_points, intr_l.K, intr_l.dist_coeffs
            )
            poses[k, :3] = np.asarray(rvec, np.float64).ravel()
            poses[k, 3:] = np.asarray(tvec, np.float64).ravel()
        else:  # right-only view: bring the cam-R board pose into the world frame
            _ok, rvec, tvec = cv2.solvePnP(
                right[i].object_points, right[i].image_points, intr_r.K, intr_r.dist_coeffs
            )
            r_b, _ = cv2.Rodrigues(np.asarray(rvec, np.float64))
            t_b = np.asarray(tvec, np.float64).ravel()
            r_w = r_s.T @ r_b
            poses[k, :3] = cv2.Rodrigues(r_w)[0].ravel()
            poses[k, 3:] = r_s.T @ (t_b - t_s)
    return poses


def bundle_refine(
    left: Sequence[BoardDetection],
    right: Sequence[BoardDetection],
    base: StereoResult,
    *,
    zero_tangent: bool = True,
    fix_k3: bool = False,
    loss: str = "soft_l1",
    f_scale: float = 1.0,
    min_points: int = 6,
    max_nfev: int = 200,
) -> tuple[StereoRig, dict[str, float]]:
    """Jointly refine ``base.rig`` on ALL usable views; returns (rig, info).

    ``left[i]``/``right[i]`` are index-paired captures (same convention as
    :func:`~al_dic_3d.calibration.solve.calibrate_stereo`). ``info`` carries
    ``rms_before``/``rms_after`` (plain px RMS over all residuals),
    ``n_views``/``n_mono_views``, and ``nfev``.
    """
    import cv2
    from scipy.optimize import least_squares
    from scipy.sparse import lil_matrix

    if len(left) != len(right):
        raise ValueError(f"left/right view counts differ: {len(left)} vs {len(right)}")

    def usable(d: BoardDetection) -> bool:
        return d.ok and d.n_points >= min_points

    views = [i for i in range(len(left)) if usable(left[i]) or usable(right[i])]
    if len(views) < 3:
        raise ValueError(f"need >= 3 usable views for bundle adjustment, got {len(views)}")
    n_mono = sum(1 for i in views if usable(left[i]) != usable(right[i]))

    keys = _free_keys(zero_tangent=zero_tangent, fix_k3=fix_k3)
    n_cam = len(keys)
    base_l, base_r = base.rig.cameras["L"], base.rig.cameras["R"]
    r_s0, t_s0 = base.rig.pose("R")
    poses0 = _init_poses(left, right, views, base.rig, min_points)

    x0 = np.concatenate(
        [
            _intr_vector(base_l, keys),
            _intr_vector(base_r, keys),
            cv2.Rodrigues(r_s0)[0].ravel(),
            np.asarray(t_s0, np.float64),
            poses0.ravel(),
        ]
    )
    pose_off = 2 * n_cam + 6

    def unpack(x: NDArray):
        intr_l = _intr_from(base_l, keys, x[:n_cam])
        intr_r = _intr_from(base_r, keys, x[n_cam : 2 * n_cam])
        r_s, _ = cv2.Rodrigues(x[2 * n_cam : 2 * n_cam + 3])
        t_s = x[2 * n_cam + 3 : 2 * n_cam + 6]
        poses = x[pose_off:].reshape(-1, 6)
        return intr_l, intr_r, r_s, t_s, poses

    def residuals(x: NDArray) -> NDArray:
        intr_l, intr_r, r_s, t_s, poses = unpack(x)
        k_l, d_l = intr_l.K, intr_l.dist_coeffs
        k_r, d_r = intr_r.K, intr_r.dist_coeffs
        out: list[NDArray] = []
        for k, i in enumerate(views):
            rvec, tvec = poses[k, :3], poses[k, 3:]
            if usable(left[i]):
                proj, _ = cv2.projectPoints(left[i].object_points, rvec, tvec, k_l, d_l)
                out.append((proj.reshape(-1, 2) - left[i].image_points).ravel())
            if usable(right[i]):
                r_w, _ = cv2.Rodrigues(rvec)
                r_c = r_s @ r_w
                t_c = r_s @ tvec + t_s
                rvec_c, _ = cv2.Rodrigues(r_c)
                proj, _ = cv2.projectPoints(right[i].object_points, rvec_c, t_c, k_r, d_r)
                out.append((proj.reshape(-1, 2) - right[i].image_points).ravel())
        return np.concatenate(out)

    # Sparsity: each view's residual block sees the shared camera/stereo params
    # plus ONLY its own pose block — the structure scipy needs for sparse
    # finite differences to stay tractable.
    n_res = sum(
        (left[i].n_points * 2 if usable(left[i]) else 0)
        + (right[i].n_points * 2 if usable(right[i]) else 0)
        for i in views
    )
    sparsity = lil_matrix((n_res, x0.size), dtype=bool)
    row = 0
    for k, i in enumerate(views):
        pose_cols = slice(pose_off + 6 * k, pose_off + 6 * (k + 1))
        if usable(left[i]):
            block = slice(row, row + 2 * left[i].n_points)
            sparsity[block, 0:n_cam] = True
            sparsity[block, pose_cols] = True
            row = block.stop
        if usable(right[i]):
            block = slice(row, row + 2 * right[i].n_points)
            sparsity[block, n_cam : 2 * n_cam] = True
            sparsity[block, 2 * n_cam : 2 * n_cam + 6] = True
            sparsity[block, pose_cols] = True
            row = block.stop

    res0 = residuals(x0)
    fit = least_squares(
        residuals,
        x0,
        jac_sparsity=sparsity,
        method="trf",
        loss=loss,
        f_scale=f_scale,
        x_scale="jac",
        max_nfev=max_nfev,
    )
    intr_l, intr_r, r_s, t_s, _poses = unpack(fit.x)
    rig = StereoRig(
        cameras={"L": intr_l, "R": intr_r},
        extrinsics={("L", "R"): (np.asarray(r_s, np.float64), np.asarray(t_s, np.float64))},
    )
    info = {
        "rms_before": float(np.sqrt(np.mean(res0**2))),
        "rms_after": float(np.sqrt(np.mean(fit.fun**2))),
        "n_views": float(len(views)),
        "n_mono_views": float(n_mono),
        "nfev": float(fit.nfev),
    }
    return rig, info
