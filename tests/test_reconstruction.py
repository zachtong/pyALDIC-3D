"""Validate reconstruct_correspondence: CorrespondenceSet -> Reconstruction3D.

Known 3D points undergo a known displacement; both are projected (WITH lens
distortion) through a calibrated stereo rig to build a CorrespondenceSet. The
reconstructor must recover the points and the displacement D = P - P[0], report
near-zero reprojection error, and propagate NaN for invalid correspondences.
"""

from __future__ import annotations

import numpy as np
import pytest

from al_dic_3d.calibration import CameraIntrinsics, StereoRig, project_points
from al_dic_3d.matching.contracts import INVALID, TRACKED, CorrespondenceSet
from al_dic_3d.reconstruct import Reconstruction3D, reconstruct_correspondence

pytest.importorskip("cv2")


def _rig() -> tuple[StereoRig, np.ndarray, np.ndarray]:
    th = np.deg2rad(20.0)
    R = np.array(
        [[np.cos(th), 0, np.sin(th)], [0, 1, 0], [-np.sin(th), 0, np.cos(th)]],
        dtype=np.float64,
    )
    T = np.array([-250.0, 0.0, 30.0], dtype=np.float64)
    left = CameraIntrinsics(fx=1500, fy=1500, cx=320, cy=240, k1=-0.12, k2=0.03)
    right = CameraIntrinsics(fx=1500, fy=1500, cx=320, cy=240, k1=-0.10, k2=0.02)
    return StereoRig(cameras={"L": left, "R": right}, extrinsics={("L", "R"): (R, T)}), R, T


def _known_surface(n: int = 40, seed: int = 1) -> np.ndarray:
    rng = np.random.default_rng(seed)
    xy = rng.uniform(-60, 60, size=(n, 2))
    z = 800.0 + rng.uniform(-20, 20, size=n)  # mild relief around the plane
    return np.column_stack([xy, z])


def _corr_from_points(points_per_frame, rig, R, T) -> CorrespondenceSet:
    """Project a list of (n,3) world frames to pixels -> a TRACKED CorrespondenceSet."""
    nf = len(points_per_frame)
    n = points_per_frame[0].shape[0]
    xL = np.empty((nf, n, 2))
    xR = np.empty((nf, n, 2))
    for k, P in enumerate(points_per_frame):
        xL[k] = project_points(P, rig.cameras["L"], np.eye(3), np.zeros(3))
        xR[k] = project_points(P, rig.cameras["R"], R, T)
    return CorrespondenceSet(
        strategy="synthetic",
        xL=xL,
        xR=xR,
        quality=np.zeros((nf, n)),
        source=np.full((nf, n), TRACKED, np.uint8),
    )


def test_reconstruct_recovers_points_and_displacement():
    rig, R, T = _rig()
    P1 = _known_surface()
    n = P1.shape[0]
    deltas = [
        np.zeros((n, 3)),
        np.tile([0.5, -0.3, 0.2], (n, 1)),
        np.column_stack([0.01 * P1[:, 0], np.zeros(n), np.full(n, -0.4)]),  # non-rigid
    ]
    frames = [P1 + d for d in deltas]
    cs = _corr_from_points(frames, rig, R, T)

    rec = reconstruct_correspondence(cs, rig)

    assert isinstance(rec, Reconstruction3D)
    assert rec.n_frames == 3 and rec.n_pts == n
    assert np.allclose(rec.points[0], P1, atol=1e-6)
    for k, d in enumerate(deltas):
        assert np.allclose(rec.points[k], P1 + d, atol=1e-6), f"frame {k} points"
        assert np.allclose(rec.displacement[k], d, atol=1e-6), f"frame {k} disp"
    assert np.nanmax(rec.reproj_error) < 1e-8  # exact projection -> ~0 reproj


def test_reconstruct_propagates_nan_for_invalid():
    rig, R, T = _rig()
    P1 = _known_surface(n=12)
    cs = _corr_from_points([P1, P1 + 0.5], rig, R, T)

    # Invalidate point 3 in frame 1, and point 5 at the reference frame 0.
    xL = cs.xL.copy()
    xR = cs.xR.copy()
    source = cs.source.copy()
    xL[1, 3] = np.nan
    source[1, 3] = INVALID
    xR[0, 5] = np.nan
    source[0, 5] = INVALID
    cs2 = CorrespondenceSet("synthetic", xL, xR, cs.quality, source)

    rec = reconstruct_correspondence(cs2, rig)
    assert np.isnan(rec.points[1, 3]).all()  # invalid observation -> NaN point
    assert np.isnan(rec.points[0, 5]).all()
    # Displacement needs BOTH the frame and its reference anchor: point 5 has a
    # NaN anchor (frame 0), so its displacement is NaN on every frame.
    assert np.isnan(rec.displacement[1, 5]).all()
    assert np.isnan(rec.displacement[1, 3]).all()
    # A point valid on both frames keeps a finite displacement.
    assert np.isfinite(rec.displacement[1, 0]).all()
    assert np.array_equal(rec.source, source)
