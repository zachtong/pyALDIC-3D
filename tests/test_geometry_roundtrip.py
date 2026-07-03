"""Round-trip test enforcing the COORDINATES.md contract (Phase 1, step 2).

synthetic 3D -> project through both cameras -> undistort -> triangulate ->
recover. Exact (<1e-9) with zero distortion; ~1e-6 with distortion (bounded by
cv2.undistortPoints' iterative inverse). If this fails, a coordinate convention
drifted — fix the code, not the test.
"""

from __future__ import annotations

import numpy as np
import pytest

from al_dic_3d.calibration import (
    CameraIntrinsics,
    StereoRig,
    project_points,
    undistort_points,
)
from al_dic_3d.reconstruct import reprojection_error, triangulate_dlt


def _rotation_y(deg: float) -> np.ndarray:
    a = np.deg2rad(deg)
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]], dtype=np.float64)


def _make_rig(distortion: bool) -> StereoRig:
    d = dict(k1=-0.18, k2=0.05, p1=1e-3, p2=-8e-4, k3=-0.01) if distortion else {}
    left = CameraIntrinsics(fx=1200.0, fy=1205.0, cx=639.5, cy=511.5, width=1280, height=1024, **d)
    right = CameraIntrinsics(fx=1185.0, fy=1190.0, cx=650.0, cy=505.0, width=1280, height=1024, **d)
    # Right camera: ~15 deg toe-in, 120 mm baseline along -x in the right frame.
    R = _rotation_y(-15.0)
    T = np.array([-120.0, 0.0, 0.0], dtype=np.float64)
    return StereoRig(cameras={"L": left, "R": right}, extrinsics={("L", "R"): (R, T)})


def _synthetic_points(n: int = 200, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    x = rng.uniform(-150.0, 150.0, n)
    y = rng.uniform(-120.0, 120.0, n)
    z = rng.uniform(800.0, 1200.0, n)  # in front of both cameras (mm)
    return np.column_stack([x, y, z])


def _roundtrip(rig: StereoRig, X: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    RL, TL = rig.pose("L")
    RR, TR = rig.pose("R")
    uvL = project_points(X, rig.cameras["L"], RL, TL)
    uvR = project_points(X, rig.cameras["R"], RR, TR)
    xnL = undistort_points(uvL, rig.cameras["L"])
    xnR = undistort_points(uvR, rig.cameras["R"])
    X_rec = triangulate_dlt(xnL, xnR, RR, TR)
    return X_rec, xnL, xnR


def test_roundtrip_no_distortion_recovers_to_1e9():
    rig = _make_rig(distortion=False)
    X = _synthetic_points()
    X_rec, _, _ = _roundtrip(rig, X)
    assert np.isfinite(X_rec).all()
    assert np.max(np.abs(X_rec - X)) < 1e-9


def test_roundtrip_with_distortion_recovers_to_micron():
    rig = _make_rig(distortion=True)
    X = _synthetic_points()
    X_rec, _, _ = _roundtrip(rig, X)
    assert np.isfinite(X_rec).all()
    # World units are mm; 1e-6 mm = 1 nm — far below any real DIC resolution.
    assert np.max(np.abs(X_rec - X)) < 1e-6


def test_reprojection_error_near_zero_for_true_points():
    rig = _make_rig(distortion=True)
    X = _synthetic_points()
    X_rec, xnL, xnR = _roundtrip(rig, X)
    RR, TR = rig.pose("R")
    err = reprojection_error(X_rec, xnL, xnR, RR, TR)
    assert np.isfinite(err).all()
    assert np.max(err) < 1e-6


def test_nan_propagates_through_pipeline():
    rig = _make_rig(distortion=False)
    X = _synthetic_points(n=10)
    RL, TL = rig.pose("L")
    RR, TR = rig.pose("R")
    uvL = project_points(X, rig.cameras["L"], RL, TL)
    uvR = project_points(X, rig.cameras["R"], RR, TR)
    uvL[3] = np.nan  # drop one observation
    xnL = undistort_points(uvL, rig.cameras["L"])
    xnR = undistort_points(uvR, rig.cameras["R"])
    X_rec = triangulate_dlt(xnL, xnR, RR, TR)
    assert np.isnan(X_rec[3]).all()
    assert np.isfinite(X_rec[np.arange(10) != 3]).all()


def test_point_behind_camera_is_nan():
    rig = _make_rig(distortion=False)
    X = np.array([[0.0, 0.0, 1000.0], [0.0, 0.0, -500.0]])  # 2nd is behind
    uv = project_points(X, rig.cameras["L"], *rig.pose("L"))
    assert np.isfinite(uv[0]).all()
    assert np.isnan(uv[1]).all()


def test_projection_matrix_left_is_K_identity():
    rig = _make_rig(distortion=False)
    P = rig.projection_matrix("L")
    expected = np.hstack([rig.cameras["L"].K, np.zeros((3, 1))])
    assert np.allclose(P, expected)


def test_unknown_camera_raises():
    rig = _make_rig(distortion=False)
    with pytest.raises(KeyError):
        rig.pose("Z")
