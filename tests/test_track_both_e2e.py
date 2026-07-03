"""End-to-end validation of the track_both strategy through 3D reconstruction.

A textured plane at depth ``Z0`` undergoes a KNOWN in-plane affine motion; two
calibrated cameras (zero distortion) view it. Because the surface is planar, both
the L<->R stereo map and each camera's temporal motion are exact homographies, so
the whole image sequence is generated from one speckle image by
``cv2.warpPerspective`` with NO modeling error, and every material point's true
pixel track and 3D position are analytic.

The test drives the full pipeline: ``TrackBothStrategy.compute`` ->
``CorrespondenceSet`` -> ``undistort_points`` -> ``triangulate_dlt`` -> 3D
displacement, and asserts the recovered image tracks and 3D displacement match
ground truth. This is the Phase-1 headless-MVP integration proof (short of the
deferred MATLAB-parity gate).
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.ndimage import gaussian_filter

from al_dic_3d.calibration import CameraIntrinsics, StereoRig, undistort_points
from al_dic_3d.matching import get_strategy
from al_dic_3d.matching.contracts import TRACKED, CorrespondenceConfig
from al_dic_3d.matching.primitives import make_local_dicpara
from al_dic_3d.matching.temporal import build_grid_mesh
from al_dic_3d.reconstruct import triangulate_dlt
from al_dic_3d.sequence import ArrayFrameProvider, StereoSequence

cv2 = pytest.importorskip("cv2")

# --- scene constants ---------------------------------------------------------
IMG = 260
FX = FY = 1400.0
CX = CY = 130.0
Z0 = 800.0  # plane depth (world mm)
N_FRAMES = 4


def _speckle(seed: int = 5) -> np.ndarray:
    rng = np.random.default_rng(seed)
    f = gaussian_filter(rng.standard_normal((IMG, IMG)), sigma=2.2, mode="nearest")
    f -= f.min()
    f /= f.max()
    return 20.0 + 215.0 * f


def _K() -> np.ndarray:
    return np.array([[FX, 0, CX], [0, FY, CY], [0, 0, 1]], dtype=np.float64)


def _rig() -> tuple[StereoRig, np.ndarray, np.ndarray]:
    """Left = world; right = a realistic 18 deg converging stereo view.

    The right camera is yawed 18 deg about Y and translated so its optical axis
    meets the left's at the plane center (a standard converging DIC rig): the
    disparity is ~0 at the image center (good NCC coverage) while the wide stereo
    angle keeps depth triangulation well-conditioned.
    """
    th = np.deg2rad(18.0)
    R = np.array(
        [[np.cos(th), 0, np.sin(th)], [0, 1, 0], [-np.sin(th), 0, np.cos(th)]],
        dtype=np.float64,
    )
    T = np.array([-Z0 * np.sin(th), 0.0, Z0 * (1.0 - np.cos(th))], dtype=np.float64)
    intr = CameraIntrinsics(fx=FX, fy=FY, cx=CX, cy=CY, width=IMG, height=IMG)
    rig = StereoRig(
        cameras={"L": intr, "R": intr},
        extrinsics={("L", "R"): (R, T)},
        world_cam="L",
    )
    return rig, R, T


def _homographies(R: np.ndarray, T: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Plane (Z=Z0) -> pixel homographies for both cameras, over (X, Y, 1)."""
    K = _K()
    h_wl = K @ np.diag([1.0, 1.0, Z0])
    h_wr = K @ np.column_stack([R[:, 0], R[:, 1], Z0 * R[:, 2] + T])
    return h_wl, h_wr


def _affine_k(k: int) -> np.ndarray:
    """Cumulative in-plane world affine at frame k (identity at k=0)."""
    a = 1.0 + 0.0006 * k
    tx, ty = 0.30 * k, 0.15 * k  # world mm
    return np.array([[a, 0, tx], [0, a, ty], [0, 0, 1]], dtype=np.float64)


def _apply(M: np.ndarray, pts: np.ndarray) -> np.ndarray:
    ph = np.column_stack([pts, np.ones(len(pts))])
    q = ph @ M.T
    return q[:, :2] / q[:, 2:3]


def _warp(img: np.ndarray, M: np.ndarray) -> np.ndarray:
    return cv2.warpPerspective(
        img, M, (IMG, IMG), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT
    )


def _build_scene():
    l1 = _speckle()
    rig, R, T = _rig()
    h_wl, h_wr = _homographies(R, T)
    h_wl_inv = np.linalg.inv(h_wl)

    left_frames, right_frames = [], []
    for k in range(N_FRAMES):
        m = _affine_k(k)
        left_frames.append(_warp(l1, h_wl @ m @ h_wl_inv))
        right_frames.append(_warp(l1, h_wr @ m @ h_wl_inv))
    return l1, rig, R, T, h_wl, h_wr, left_frames, right_frames


def test_track_both_end_to_end_reconstruction():
    l1, rig, R, T, h_wl, h_wr, left_frames, right_frames = _build_scene()

    seq = StereoSequence(
        providers={
            "L": ArrayFrameProvider(left_frames),
            "R": ArrayFrameProvider(right_frames),
        }
    )
    seq.validate()

    # Reference mesh (left, frame 1) — kept clear of the right edge so the stereo
    # search window stays on-image despite the ~17 px disparity.
    para = make_local_dicpara(img_size=(IMG, IMG), roi=(45, 175, 45, 215), winsize=32)
    mesh_L = build_grid_mesh(para, IMG, IMG)
    coords_L = np.asarray(mesh_L.coordinates_fem, dtype=np.float64)

    strategy = get_strategy("track_both")()
    cs = strategy.compute(seq, rig, mesh_L, CorrespondenceConfig(strategy="track_both"))

    assert cs.strategy == "track_both"
    assert cs.n_frames == N_FRAMES and cs.n_pts == coords_L.shape[0]

    # Ground-truth pixel tracks and 3D positions for each material point.
    h_wl_inv = np.linalg.inv(h_wl)
    world_xy = _apply(h_wl_inv, coords_L)  # (n, 2) plane coords of each node

    Rp, Tp = rig.pose("R")
    disp_errs, inplane_errs, xl_errs, xr_errs, tracked_frac = [], [], [], [], []
    for k in range(N_FRAMES):
        moved = _apply(_affine_k(k), world_xy)  # (n, 2) world (X', Y')
        xL_gt = _apply(h_wl, moved)
        xR_gt = _apply(h_wr, moved)

        tracked = cs.source[k] == TRACKED
        tracked_frac.append(tracked.mean())
        if not tracked.any():
            continue

        xl_errs.append(np.linalg.norm(cs.xL[k][tracked] - xL_gt[tracked], axis=1))
        xr_errs.append(np.linalg.norm(cs.xR[k][tracked] - xR_gt[tracked], axis=1))

        # Triangulate the RECOVERED correspondence -> 3D, compare displacement.
        xnL = undistort_points(cs.xL[k][tracked], rig.cameras["L"])
        xnR = undistort_points(cs.xR[k][tracked], rig.cameras["R"])
        P_rec = triangulate_dlt(xnL, xnR, Rp, Tp)
        P_gt = np.column_stack([moved[tracked], np.full(tracked.sum(), Z0)])
        if k == 0:
            P_rec0, P_gt0, mask0 = P_rec, P_gt, tracked
            continue
        # Displacement uses the frame-0 baseline for the SAME points.
        common = tracked & mask0
        if not common.any():
            continue
        d_rec = P_rec[common[tracked]] - P_rec0[common[mask0]]
        d_gt = P_gt[common[tracked]] - P_gt0[common[mask0]]
        disp_errs.append(np.linalg.norm(d_rec - d_gt, axis=1))
        inplane_errs.append(np.linalg.norm(d_rec[:, :2] - d_gt[:, :2], axis=1))

    xl_all = np.concatenate(xl_errs)
    xr_all = np.concatenate(xr_errs)
    disp_all = np.concatenate(disp_errs)
    inplane_all = np.concatenate(inplane_errs)

    # Coverage: (nearly) every node tracked on every frame for this converging rig.
    assert min(tracked_frac) > 0.95, f"low coverage: {[f'{x:.0%}' for x in tracked_frac]}"
    # Image-plane correspondence accuracy (sub-pixel).
    assert np.median(xl_all) < 0.1, f"xL median err {np.median(xl_all):.3f}px"
    assert np.median(xr_all) < 0.15, f"xR median err {np.median(xr_all):.3f}px"
    assert np.percentile(xl_all, 90) < 0.25
    # In-plane 3D displacement (well-conditioned) — tight.
    assert np.median(inplane_all) < 0.03, f"in-plane disp median {np.median(inplane_all):.4f}mm"
    # Full 3D displacement (includes the depth component) — realistic for an 18 deg rig.
    assert np.median(disp_all) < 0.05, f"3D disp median err {np.median(disp_all):.4f}mm"
    assert np.percentile(disp_all, 90) < 0.12, f"3D disp p90 {np.percentile(disp_all, 90):.4f}mm"


def test_track_both_zero_motion_is_recovered_as_zero():
    """A static scene: every frame's correspondence equals frame 1's."""
    l1 = _speckle(seed=9)
    rig, R, T = _rig()
    h_wl, h_wr = _homographies(R, T)
    h_wl_inv = np.linalg.inv(h_wl)
    r1 = _warp(l1, h_wr @ h_wl_inv)

    seq = StereoSequence(
        providers={
            "L": ArrayFrameProvider([l1, l1.copy(), l1.copy()]),
            "R": ArrayFrameProvider([r1, r1.copy(), r1.copy()]),
        }
    )
    para = make_local_dicpara(img_size=(IMG, IMG), roi=(45, 175, 45, 215), winsize=32)
    mesh_L = build_grid_mesh(para, IMG, IMG)

    strategy = get_strategy("track_both")()
    cs = strategy.compute(seq, rig, mesh_L, CorrespondenceConfig())

    for k in range(1, cs.n_frames):
        tracked = cs.source[k] == TRACKED
        dL = np.linalg.norm(cs.xL[k][tracked] - cs.xL[0][tracked], axis=1)
        dR = np.linalg.norm(cs.xR[k][tracked] - cs.xR[0][tracked], axis=1)
        assert np.nanmedian(dL) < 0.02
        assert np.nanmedian(dR) < 0.05
