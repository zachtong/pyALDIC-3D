"""Mono + stereo calibration solve with quality control (Qt-free, D12).

Pipeline (mirrors OpenCV/stereo-DIC best practice from the D12 research):

1. per-camera intrinsics on ALL views that camera sees
   (``calibrateCameraExtended``; optional release-object method for imprecise
   printed boards) — 5-coefficient Brown-Conrady only, matching
   :class:`CameraIntrinsics` and the MATLAB-parity contract (no rational model);
2. stereo extrinsics on the common-id subset of synchronized pairs
   (``stereoCalibrateExtended`` with ``CALIB_FIX_INTRINSIC`` by default;
   ``joint_refine=True`` switches to ``CALIB_USE_INTRINSIC_GUESS``);
3. automatic worst-pair rejection loop (``rms > max(abs, k*median)``) with a
   floor on the number of surviving pairs — every drop is recorded;
4. epipolar-distance validation (undistort -> ``computeCorrespondEpilines``).

Errors raise ``ValueError`` with English messages (the GUI translates).
Convention out: ``X_R = R @ X_L + T``, left camera = world — exactly
``cv2.stereoCalibrate``'s output, so the rig is assembled with NO transform.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.calibration.detect import BoardDetection
from al_dic_3d.calibration.model import CameraIntrinsics, StereoRig

# Verified live against the wheel: stdDeviationsIntrinsics ordering is
# (fx, fy, cx, cy, k1, k2, p1, p2, k3, k4, k5, k6, s1..s4, taux, tauy).
_STD_KEYS = ("fx", "fy", "cx", "cy", "k1", "k2", "p1", "p2", "k3")


@dataclass(frozen=True)
class MonoCalibration:
    """One camera's intrinsics solve + its QC outputs."""

    intrinsics: CameraIntrinsics
    rms: float
    per_view_rms: NDArray[np.float64]  # (n_used,)
    view_indices: NDArray[np.int64]  # indices into the input detection list
    std_devs: dict[str, float]  # parameter std deviations (fx..k3)
    method: str  # "standard" | "release_object"
    board_rvecs: NDArray[np.float64]  # (n_used, 3) board pose per used view
    board_tvecs: NDArray[np.float64]  # (n_used, 3)


@dataclass(frozen=True)
class PairQC:
    """Per-stereo-pair quality record (kept for GUI bars, even when rejected)."""

    index: int  # pair index in the input sequences
    rms_left: float
    rms_right: float
    n_common: int
    used: bool
    tilt_deg: float = float("nan")  # board tilt vs left optical axis
    distance: float = float("nan")  # |tvec| board distance (calibration units)
    note: str = ""


@dataclass(frozen=True)
class StereoResult:
    """Everything the GUI / report / YAML writer needs from one stereo solve."""

    rig: StereoRig
    rms: float  # stereo RMS over the used pairs
    epipolar_rms: float  # mean epipolar distance (px) over used pairs
    pairs: tuple[PairQC, ...]
    mono: dict[str, MonoCalibration]  # keys "L", "R"
    joint_refined: bool
    warnings: tuple[str, ...]

    @property
    def n_pairs_used(self) -> int:
        return sum(1 for p in self.pairs if p.used)

    @property
    def baseline(self) -> float:
        _r, t = self.rig.pose("R")
        return float(np.linalg.norm(t))


def _mono_flags(*, fix_k3: bool, zero_tangent: bool, fix_aspect: bool) -> int:
    import cv2

    flags = 0
    if fix_k3:
        flags |= cv2.CALIB_FIX_K3
    if zero_tangent:
        flags |= cv2.CALIB_ZERO_TANGENT_DIST
    if fix_aspect:
        flags |= cv2.CALIB_FIX_ASPECT_RATIO
    return flags


def _intrinsics_from(K: NDArray, dist: NDArray, image_size: tuple[int, int]) -> CameraIntrinsics:
    K = np.asarray(K, np.float64)
    d = np.concatenate([np.asarray(dist, np.float64).ravel(), np.zeros(5)])[:5]
    return CameraIntrinsics(
        fx=float(K[0, 0]),
        fy=float(K[1, 1]),
        cx=float(K[0, 2]),
        cy=float(K[1, 2]),
        skew=float(K[0, 1]),
        k1=float(d[0]),
        k2=float(d[1]),
        p1=float(d[2]),
        p2=float(d[3]),
        k3=float(d[4]),
        width=int(image_size[0]),
        height=int(image_size[1]),
    )


def calibrate_mono(
    detections: Sequence[BoardDetection],
    image_size: tuple[int, int],
    *,
    fix_k3: bool = False,
    zero_tangent: bool = True,
    fix_aspect: bool = False,
    release_object: bool = False,
    min_points: int = 6,
    reject_view_rms: float = 1.0,
    reject_view_factor: float = 3.0,
    max_reject_rounds: int = 3,
) -> MonoCalibration:
    """Solve one camera's intrinsics from its usable board detections.

    Views whose per-view reprojection RMS exceeds
    ``max(reject_view_rms, reject_view_factor * median)`` are dropped and the
    solve repeats (up to ``max_reject_rounds`` rounds, never below 3 views):
    one catastrophically misdetected view otherwise biases fx by percents
    while the pooled RMS still looks merely mediocre.

    ``image_size`` is ``(width, height)``. ``zero_tangent`` defaults to True:
    on planar targets the principal point and the decentering (tangential)
    terms are nearly indistinguishable — freeing p1/p2 amplifies corner noise
    into ~3x larger cx/cy errors (measured on analytic corners), while real
    machine-vision lenses have negligible tangential distortion. This matches
    the MATLAB calibrator's default that DIC users know. ``release_object=True``
    enables the Strobl-Hirzinger RO method (better for imprecise printed
    boards); it requires the identical full point set in every view and
    silently falls back to the standard solve (recorded in ``method``) when
    views are partial.
    """
    import cv2

    usable = [i for i, d in enumerate(detections) if d.ok and d.n_points >= min_points]
    if len(usable) < 3:
        raise ValueError(f"need >= 3 usable views to calibrate, got {len(usable)}")

    flags = _mono_flags(fix_k3=fix_k3, zero_tangent=zero_tangent, fix_aspect=fix_aspect)
    size = (int(image_size[0]), int(image_size[1]))

    method = "standard"
    if release_object:
        ids0 = detections[usable[0]].ids
        identical = all(np.array_equal(detections[i].ids, ids0) for i in usable[1:])
        if identical:
            method = "release_object"
        # else: partial/mismatched views — RO is undefined, use the standard solve.

    def _solve(view_ids: list[int]):
        obj = [np.float32(detections[i].object_points).reshape(-1, 1, 3) for i in view_ids]
        img = [np.float32(detections[i].image_points).reshape(-1, 1, 2) for i in view_ids]
        if method == "release_object":
            # Recommended fixed point = last point of the first board row; the
            # row length derives from the object lattice (non-square safe).
            obj0 = detections[view_ids[0]].object_points
            row_len = int(np.sum(np.isclose(obj0[:, 1], obj0[0, 1])))
            ret = cv2.calibrateCameraROExtended(
                obj, img, size, max(1, row_len - 1), None, None, flags=flags
            )
            rms, K, dist, rvecs, tvecs, _new_obj, std_i, _std_e, _std_o, per_view = ret
        else:
            rms, K, dist, rvecs, tvecs, std_i, _std_e, per_view = cv2.calibrateCameraExtended(
                obj, img, size, None, None, flags=flags
            )
        return rms, K, dist, rvecs, tvecs, std_i, np.asarray(per_view, np.float64).ravel()

    rms, K, dist, rvecs, tvecs, std_i, per_view = _solve(usable)
    for _round in range(max_reject_rounds):
        if len(usable) <= 3:
            break
        cut = max(reject_view_rms, reject_view_factor * float(np.median(per_view)))
        keep = per_view <= cut
        if keep.all():
            break
        usable = [i for i, k in zip(usable, keep, strict=True) if k]
        rms, K, dist, rvecs, tvecs, std_i, per_view = _solve(usable)

    std = np.asarray(std_i, np.float64).ravel()
    std_devs = {k: float(std[j]) if j < std.size else 0.0 for j, k in enumerate(_STD_KEYS)}
    return MonoCalibration(
        intrinsics=_intrinsics_from(K, dist, size),
        rms=float(rms),
        per_view_rms=per_view,
        view_indices=np.asarray(usable, dtype=np.int64),
        std_devs=std_devs,
        method=method,
        board_rvecs=np.asarray(rvecs, np.float64).reshape(-1, 3),
        board_tvecs=np.asarray(tvecs, np.float64).reshape(-1, 3),
    )


def _disc_centroid_offsets(
    obj_pts: NDArray,
    radius_mm: float,
    rvec: NDArray,
    tvec: NDArray,
    intr: CameraIntrinsics,
    n_samples: int = 32,
) -> NDArray[np.float64]:
    """Eccentricity bias of each dot: projected-disc centroid minus projected center.

    A circle images as a distorted ellipse whose intensity centroid is NOT the
    projection of the circle center (perspective + lens distortion — opencv
    issue #7312). Model it exactly: project ``n_samples`` boundary points of
    each dot through the CURRENT camera model and take the polygon area
    centroid. Returns ``(n, 2)`` px offsets to SUBTRACT from measured centroids.
    """
    import cv2

    ang = np.linspace(0.0, 2.0 * np.pi, n_samples, endpoint=False)
    ring = radius_mm * np.column_stack([np.cos(ang), np.sin(ang), np.zeros(n_samples)])
    n = obj_pts.shape[0]
    boundary = (obj_pts[:, None, :] + ring[None, :, :]).reshape(-1, 3)
    all_pts = np.vstack([boundary, obj_pts])
    proj, _ = cv2.projectPoints(
        np.float64(all_pts), np.float64(rvec), np.float64(tvec), intr.K, intr.dist_coeffs
    )
    proj = proj.reshape(-1, 2)
    poly = proj[: n * n_samples].reshape(n, n_samples, 2)
    centers = proj[n * n_samples :]
    # Shoelace area centroid of each closed projected boundary polygon.
    x, y = poly[..., 0], poly[..., 1]
    xn, yn = np.roll(x, -1, axis=1), np.roll(y, -1, axis=1)
    cross = x * yn - xn * y
    area = cross.sum(axis=1) / 2.0
    cx = ((x + xn) * cross).sum(axis=1) / (6.0 * area)
    cy = ((y + yn) * cross).sum(axis=1) / (6.0 * area)
    return np.column_stack([cx, cy]) - centers


def _correct_eccentricity(
    detections: list[BoardDetection],
    mono: MonoCalibration,
    radius_mm: float,
) -> list[BoardDetection]:
    """Subtract the modeled disc-centroid bias from each used view's points."""
    corrected = list(detections)
    for k, i in enumerate(mono.view_indices):
        det = detections[int(i)]
        offsets = _disc_centroid_offsets(
            det.object_points,
            radius_mm,
            mono.board_rvecs[k],
            mono.board_tvecs[k],
            mono.intrinsics,
        )
        corrected[int(i)] = replace(det, image_points=det.image_points - offsets)
    return corrected


def _common_points(
    left: BoardDetection, right: BoardDetection
) -> tuple[NDArray, NDArray, NDArray] | None:
    """Intersect the two views' point ids -> (obj (n,3), img_l (n,2), img_r (n,2))."""
    _ids, il, ir = np.intersect1d(left.ids, right.ids, return_indices=True)
    if il.size < 6:
        return None
    return left.object_points[il], left.image_points[il], right.image_points[ir]


def _board_pose_stats(rvec: NDArray, tvec: NDArray) -> tuple[float, float]:
    """(tilt of the board normal vs the left optical axis in deg, |tvec|)."""
    import cv2

    R, _ = cv2.Rodrigues(np.asarray(rvec, np.float64))
    tilt = float(np.degrees(np.arccos(np.clip(abs(R[2, 2]), 0.0, 1.0))))
    return tilt, float(np.linalg.norm(tvec))


def calibrate_stereo(
    left: Sequence[BoardDetection],
    right: Sequence[BoardDetection],
    image_size: tuple[int, int],
    *,
    joint_refine: bool = False,
    fix_k3: bool = False,
    zero_tangent: bool = True,
    fix_aspect: bool = False,
    release_object: bool = False,
    reject_rms: float = 1.0,
    reject_factor: float = 2.5,
    max_reject_rounds: int = 5,
    min_pairs: int = 6,
    dot_radius_mm: float | None = None,
) -> StereoResult:
    """Full stereo calibration from per-camera detection lists (index-paired).

    ``left[i]`` and ``right[i]`` must come from the same synchronized capture.
    ``dot_radius_mm`` enables the eccentricity correction for circle/dot
    targets (pass the physical dot radius): two rounds of mono-solve ->
    subtract the modeled disc-centroid bias — without it, large/tilted dots
    bias the solve (k1 can even flip sign). Returns a :class:`StereoResult`
    whose rig maps ``X_R = R @ X_L + T`` with the left camera as world — ready
    for ``to_opencv_yaml`` and the pipeline.
    """
    import cv2

    if len(left) != len(right):
        raise ValueError(f"left/right view counts differ: {len(left)} vs {len(right)}")

    mono_kwargs = dict(
        fix_k3=fix_k3,
        zero_tangent=zero_tangent,
        fix_aspect=fix_aspect,
        release_object=release_object,
    )
    left = list(left)
    right = list(right)
    mono_l = calibrate_mono(left, image_size, **mono_kwargs)
    mono_r = calibrate_mono(right, image_size, **mono_kwargs)
    if dot_radius_mm is not None and dot_radius_mm > 0:
        # Fixed-point: always correct the ORIGINAL measurements with the latest
        # model (correcting corrected points would accumulate the offsets).
        orig_l, orig_r = left, right
        for _iteration in range(2):
            left = _correct_eccentricity(orig_l, mono_l, dot_radius_mm)
            right = _correct_eccentricity(orig_r, mono_r, dot_radius_mm)
            mono_l = calibrate_mono(left, image_size, **mono_kwargs)
            mono_r = calibrate_mono(right, image_size, **mono_kwargs)

    # Candidate pairs: both views detected and sharing >= 6 point ids.
    pairs: dict[int, PairQC] = {}
    data: dict[int, tuple[NDArray, NDArray, NDArray]] = {}
    for i, (dl, dr) in enumerate(zip(left, right, strict=True)):
        if not (dl.ok and dr.ok):
            which = [] if dl.ok else ["left"]
            which += [] if dr.ok else ["right"]
            note = "no detection ({}): {}".format(
                "+".join(which), (dl.reason or dr.reason or "").strip()
            )
            pairs[i] = PairQC(i, np.nan, np.nan, 0, used=False, note=note)
            continue
        common = _common_points(dl, dr)
        if common is None:
            pairs[i] = PairQC(i, np.nan, np.nan, 0, used=False, note="< 6 common point ids")
            continue
        data[i] = common
        pairs[i] = PairQC(i, np.nan, np.nan, common[0].shape[0], used=True)

    used = sorted(data)
    if len(used) < min_pairs:
        raise ValueError(f"only {len(used)} usable stereo pairs (need >= {min_pairs})")

    K1, d1 = mono_l.intrinsics.K, mono_l.intrinsics.dist_coeffs
    K2, d2 = mono_r.intrinsics.K, mono_r.intrinsics.dist_coeffs
    flags = cv2.CALIB_USE_INTRINSIC_GUESS if joint_refine else cv2.CALIB_FIX_INTRINSIC
    criteria = (cv2.TERM_CRITERIA_COUNT | cv2.TERM_CRITERIA_EPS, 200, 1e-9)
    size = (int(image_size[0]), int(image_size[1]))

    def solve(indices: list[int]):
        obj = [np.float32(data[i][0]).reshape(-1, 1, 3) for i in indices]
        i1 = [np.float32(data[i][1]).reshape(-1, 1, 2) for i in indices]
        i2 = [np.float32(data[i][2]).reshape(-1, 1, 2) for i in indices]
        return cv2.stereoCalibrateExtended(
            obj,
            i1,
            i2,
            K1.copy(),
            d1.copy(),
            K2.copy(),
            d2.copy(),
            size,
            np.eye(3),
            np.zeros(3),
            flags=flags,
            criteria=criteria,
        )

    # Rejection loop: drop pairs whose worst-camera RMS exceeds
    # max(reject_rms, reject_factor * median), never sinking below min_pairs.
    # The absolute floor keeps uniformly-good sets intact (k*median alone would
    # amputate healthy geometry and weaken the solve).
    result = solve(used)
    for _round in range(max_reject_rounds):
        per_view = np.asarray(result[11], np.float64)  # (n, 2) RMS per pair per camera
        worst = per_view.max(axis=1)
        threshold = max(reject_rms, reject_factor * float(np.median(worst)))
        bad = [k for k in range(len(used)) if worst[k] > threshold]
        if not bad or len(used) - len(bad) < min_pairs:
            break
        for k in bad:
            i = used[k]
            pairs[i] = replace(
                pairs[i],
                used=False,
                rms_left=float(per_view[k, 0]),
                rms_right=float(per_view[k, 1]),
                note=f"rejected: rms {worst[k]:.3f}px > {threshold:.3f}px",
            )
        used = [i for k, i in enumerate(used) if k not in set(bad)]
        result = solve(used)

    rms, K1o, d1o, K2o, d2o, R, T, _e, F, rvecs, tvecs, per_view = result
    per_view = np.asarray(per_view, np.float64)
    for k, i in enumerate(used):
        tilt, dist = _board_pose_stats(rvecs[k], tvecs[k])
        pairs[i] = replace(
            pairs[i],
            rms_left=float(per_view[k, 0]),
            rms_right=float(per_view[k, 1]),
            tilt_deg=tilt,
            distance=dist,
        )

    intr_l = _intrinsics_from(K1o, d1o, size) if joint_refine else mono_l.intrinsics
    intr_r = _intrinsics_from(K2o, d2o, size) if joint_refine else mono_r.intrinsics
    rig = StereoRig(
        cameras={"L": intr_l, "R": intr_r},
        extrinsics={
            ("L", "R"): (
                np.asarray(R, np.float64).reshape(3, 3),
                np.asarray(T, np.float64).reshape(3),
            )
        },
    )

    epi = _epipolar_rms([data[i][1] for i in used], [data[i][2] for i in used], intr_l, intr_r, F)

    warnings: list[str] = []
    methods = {left[i].method for i in used} | {right[i].method for i in used}
    if "sb" in methods and "classic" in methods:
        warnings.append(
            "mixed chessboard detectors (SB + classic fallback) in one calibration set; "
            "their sub-pixel corners differ slightly — consider retaking the fallback images"
        )
    if release_object and "release_object" not in (mono_l.method, mono_r.method):
        warnings.append("release-object method unavailable (partial board views); used standard")

    return StereoResult(
        rig=rig,
        rms=float(rms),
        epipolar_rms=epi,
        pairs=tuple(pairs[i] for i in sorted(pairs)),
        mono={"L": mono_l, "R": mono_r},
        joint_refined=joint_refine,
        warnings=tuple(warnings),
    )


def _epipolar_rms(
    pts_l: list[NDArray],
    pts_r: list[NDArray],
    intr_l: CameraIntrinsics,
    intr_r: CameraIntrinsics,
    F: NDArray,
) -> float:
    """Mean symmetric epipolar distance (px) over all matched points."""
    import cv2

    F = np.asarray(F, np.float64)
    total, count = 0.0, 0
    for pl, pr in zip(pts_l, pts_r, strict=True):
        ul = cv2.undistortPoints(
            np.float64(pl).reshape(-1, 1, 2), intr_l.K, intr_l.dist_coeffs, P=intr_l.K
        ).reshape(-1, 2)
        ur = cv2.undistortPoints(
            np.float64(pr).reshape(-1, 1, 2), intr_r.K, intr_r.dist_coeffs, P=intr_r.K
        ).reshape(-1, 2)
        lines_r = cv2.computeCorrespondEpilines(ul.reshape(-1, 1, 2), 1, F).reshape(-1, 3)
        lines_l = cv2.computeCorrespondEpilines(ur.reshape(-1, 1, 2), 2, F).reshape(-1, 3)
        d_r = np.abs(np.sum(lines_r[:, :2] * ur, axis=1) + lines_r[:, 2])
        d_l = np.abs(np.sum(lines_l[:, :2] * ul, axis=1) + lines_l[:, 2])
        total += float(d_r.sum() + d_l.sum())
        count += d_r.size + d_l.size
    return total / count if count else float("nan")
