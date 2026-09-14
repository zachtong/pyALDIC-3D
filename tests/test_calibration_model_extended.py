"""Full OpenCV distortion model, skew-consistent undistortion, OpenCV 4.x support.

Fix batch V (readiness audit, calibration findings):

- ``CameraIntrinsics`` used to truncate every calibration to ``[k1, k2, p1, p2, k3]``;
  rational (k4-k6), thin-prism (s1-s4) and tilt (tau_x, tau_y) terms were dropped
  silently by every importer.
- ``project_points`` applied the skew term while ``cv2.undistortPoints`` ignores
  ``K[0, 1]``, so a calibration with skew did not round-trip.
- ``undistort_points`` passed ``criteria=`` to ``cv2.undistortPoints``, which only
  OpenCV 5 accepts; on OpenCV 4.x every reconstruction raised.
- The DICe importer ignored ``LENS_DISTORTION_MODEL`` and the extended terms.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pytest

from al_dic_3d.calibration import (
    CameraIntrinsics,
    StereoRig,
    from_dice_xml,
    from_opencv_yaml,
    project_points,
    undistort_points,
)
from al_dic_3d.calibration import geometry as geometry_mod
from al_dic_3d.calibration.importers import _K_matrix_to_intrinsics
from al_dic_3d.calibration.report import to_opencv_yaml


def _points(n: int = 300, seed: int = 3) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return np.column_stack(
        [rng.uniform(-150, 150, n), rng.uniform(-120, 120, n), rng.uniform(800, 1200, n)]
    )


def _normalized_truth(X: np.ndarray) -> np.ndarray:
    return X[:, :2] / X[:, 2:3]


EXTENDED = dict(
    k1=-0.12,
    k2=0.03,
    p1=8e-4,
    p2=-5e-4,
    k3=0.002,
    k4=0.01,
    k5=-0.004,
    k6=0.0015,
    s1=1e-3,
    s2=-5e-4,
    s3=8e-4,
    s4=-3e-4,
)


# --------------------------------------------------------------------------- #
# model
# --------------------------------------------------------------------------- #


def test_dist_coeffs_stay_five_terms_without_extended_distortion():
    intr = CameraIntrinsics(fx=1000, fy=1000, cx=640, cy=480, k1=-0.1, k3=0.01)
    assert intr.dist_coeffs.shape == (5,)
    assert not intr.has_extended_distortion


def test_dist_coeffs_expand_to_fourteen_terms_in_opencv_order():
    intr = CameraIntrinsics(fx=1000, fy=1000, cx=640, cy=480, tau_x=0.01, tau_y=-0.02, **EXTENDED)
    d = intr.dist_coeffs
    assert d.shape == (14,)
    expected = [
        EXTENDED["k1"], EXTENDED["k2"], EXTENDED["p1"], EXTENDED["p2"], EXTENDED["k3"],
        EXTENDED["k4"], EXTENDED["k5"], EXTENDED["k6"],
        EXTENDED["s1"], EXTENDED["s2"], EXTENDED["s3"], EXTENDED["s4"],
        0.01, -0.02,
    ]  # fmt: skip
    assert np.allclose(d, expected)
    assert intr.has_extended_distortion


# --------------------------------------------------------------------------- #
# geometry
# --------------------------------------------------------------------------- #


def test_skew_round_trips_through_project_and_undistort():
    intr = CameraIntrinsics(
        fx=1200, fy=1205, cx=639.5, cy=511.5, skew=5.0, k1=-0.18, k2=0.05, p1=1e-3, p2=-8e-4
    )
    X = _points()
    uv = project_points(X, intr, np.eye(3), np.zeros(3))
    xn = undistort_points(uv, intr)
    # Before the fix the skew was ignored on the way back: ~5e-5 normalized error.
    assert np.max(np.abs(xn - _normalized_truth(X))) < 1e-9


def test_extended_distortion_round_trips():
    intr = CameraIntrinsics(fx=1200, fy=1205, cx=639.5, cy=511.5, skew=2.0, **EXTENDED)
    X = _points()
    uv = project_points(X, intr, np.eye(3), np.zeros(3))
    xn = undistort_points(uv, intr)
    assert np.max(np.abs(xn - _normalized_truth(X))) < 1e-8


def test_extended_projection_matches_opencv_model():
    import cv2

    intr = CameraIntrinsics(
        fx=1200, fy=1205, cx=639.5, cy=511.5, tau_x=0.02, tau_y=-0.01, **EXTENDED
    )
    X = _points()
    uv = project_points(X, intr, np.eye(3), np.zeros(3))
    ref, _ = cv2.projectPoints(X, np.zeros(3), np.zeros(3), intr.K, intr.dist_coeffs)
    assert np.max(np.abs(uv - ref.reshape(-1, 2))) < 1e-8


def test_five_term_projection_path_is_unchanged():
    """Calibrations without extended terms keep the original closed-form model."""
    intr = CameraIntrinsics(fx=1200, fy=1205, cx=639.5, cy=511.5, k1=-0.18, k2=0.05, k3=-0.01)
    X = _points()
    uv = project_points(X, intr, np.eye(3), np.zeros(3))
    x, y = X[:, 0] / X[:, 2], X[:, 1] / X[:, 2]
    r2 = x * x + y * y
    radial = 1 + intr.k1 * r2 + intr.k2 * r2**2 + intr.k3 * r2**3
    assert np.array_equal(uv[:, 0], intr.fx * (x * radial) + intr.cx)


def _opencv_major() -> int:
    import cv2

    return int(cv2.__version__.split(".")[0])


@pytest.mark.skipif(
    _opencv_major() < 5, reason="on OpenCV 4.x the real fallback path runs in every other test"
)
def test_undistort_falls_back_to_iterative_api_on_opencv4(monkeypatch):
    """OpenCV 4.x: undistortPoints has no ``criteria``; undistortPointsIter has."""
    import cv2

    real = cv2.undistortPoints
    calls = {"iter": 0}

    def undistort_v4(src, cameraMatrix, distCoeffs, dst=None, R=None, P=None, **kw):
        if "criteria" in kw:
            raise TypeError("'criteria' is an invalid keyword argument for undistortPoints()")
        return real(src, cameraMatrix, distCoeffs, R=R, P=P)

    def undistort_iter_v4(src, cameraMatrix, distCoeffs, R, P, criteria):
        calls["iter"] += 1
        return real(src, cameraMatrix, distCoeffs, R=R, P=P, criteria=criteria)

    monkeypatch.setattr(cv2, "undistortPoints", undistort_v4)
    monkeypatch.setattr(cv2, "undistortPointsIter", undistort_iter_v4, raising=False)
    monkeypatch.setattr(geometry_mod, "_CRITERIA_API", None)

    intr = CameraIntrinsics(fx=1200, fy=1205, cx=639.5, cy=511.5, k1=-0.18, k2=0.05, p1=1e-3)
    X = _points()
    uv = project_points(X, intr, np.eye(3), np.zeros(3))
    xn = undistort_points(uv, intr)
    assert calls["iter"] >= 1
    assert np.max(np.abs(xn - _normalized_truth(X))) < 1e-9


# --------------------------------------------------------------------------- #
# importers / YAML writer
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("n", [4, 5, 8, 12, 14])
def test_K_matrix_import_keeps_every_opencv_coefficient(n):
    full = np.array(
        [-0.1, 0.02, 1e-3, -2e-3, 0.004, 0.01, -0.02, 0.03, 1e-4, 2e-4, 3e-4, 4e-4, 0.01, 0.02]
    )
    K = np.array([[1000.0, 0.0, 640.0], [0.0, 1001.0, 480.0], [0.0, 0.0, 1.0]])
    intr = _K_matrix_to_intrinsics(K, full[:n])
    got = np.concatenate([intr.dist_coeffs, np.zeros(14)])[:14]
    want = np.concatenate([full[:n], np.zeros(14)])[:14]
    assert np.allclose(got, want)


def test_opencv_yaml_round_trips_extended_distortion(tmp_path: Path):
    left = CameraIntrinsics(fx=1200, fy=1205, cx=640, cy=512, **EXTENDED)
    right = CameraIntrinsics(fx=1180, fy=1185, cx=650, cy=505, k1=-0.1)
    rig = StereoRig(
        cameras={"L": left, "R": right},
        extrinsics={("L", "R"): (np.eye(3), np.array([-120.0, 0.0, 0.0]))},
    )
    path = tmp_path / "rig.yml"
    to_opencv_yaml(rig, path)
    back = from_opencv_yaml(path)
    assert np.allclose(back.cameras["L"].dist_coeffs, left.dist_coeffs)
    assert back.cameras["R"].dist_coeffs.shape == (5,)


_DICE_EXT = """<?xml version="1.0"?>
<ParameterList>
  <ParameterList name="CAMERA 0">
    <Parameter name="FX" type="double" value="1200.0"/>
    <Parameter name="FY" type="double" value="1205.0"/>
    <Parameter name="CX" type="double" value="640.0"/>
    <Parameter name="CY" type="double" value="512.0"/>
    <Parameter name="FS" type="double" value="{fs}"/>
    <Parameter name="K1" type="double" value="-0.12"/>
    <Parameter name="K4" type="double" value="0.01"/>
    <Parameter name="K5" type="double" value="-0.004"/>
    <Parameter name="K6" type="double" value="0.0015"/>
    <Parameter name="S1" type="double" value="0.001"/>
    <Parameter name="S4" type="double" value="-0.0003"/>
    <Parameter name="T1" type="double" value="0.02"/>
    <Parameter name="T2" type="double" value="-0.01"/>
    <Parameter name="LENS_DISTORTION_MODEL" type="string" value="{model}"/>
  </ParameterList>
  <ParameterList name="CAMERA 1">
    <Parameter name="FX" type="double" value="1180.0"/>
    <Parameter name="FY" type="double" value="1185.0"/>
    <Parameter name="CX" type="double" value="650.0"/>
    <Parameter name="CY" type="double" value="505.0"/>
    <Parameter name="TX" type="double" value="-120.0"/>
    <Parameter name="LENS_DISTORTION_MODEL" type="string" value="{model}"/>
    <ParameterList name="rotation_3x3_matrix">
      <Parameter name="ROW 0" type="string" value="{{ 1.0, 0.0, 0.0 }}"/>
      <Parameter name="ROW 1" type="string" value="{{ 0.0, 1.0, 0.0 }}"/>
      <Parameter name="ROW 2" type="string" value="{{ 0.0, 0.0, 1.0 }}"/>
    </ParameterList>
  </ParameterList>
</ParameterList>
"""


def _dice_file(tmp_path: Path, model: str = "OPENCV_LENS_DISTORTION", fs: float = 0.0) -> Path:
    f = tmp_path / "dice.xml"
    f.write_text(_DICE_EXT.format(model=model, fs=fs), encoding="utf-8")
    return f


def test_dice_imports_rational_thin_prism_and_tilt_terms(tmp_path: Path):
    rig = from_dice_xml(_dice_file(tmp_path))
    c = rig.cameras["L"]
    assert (c.k4, c.k5, c.k6) == (0.01, -0.004, 0.0015)
    assert (c.s1, c.s4) == (0.001, -0.0003)
    assert (c.tau_x, c.tau_y) == (0.02, -0.01)
    assert rig.cameras["R"].dist_coeffs.shape == (5,)


@pytest.mark.parametrize("model", ["NONE", "NO_LENS_DISTORTION"])
def test_dice_no_distortion_model_zeroes_the_coefficients(tmp_path: Path, model: str):
    rig = from_dice_xml(_dice_file(tmp_path, model=model))
    assert np.allclose(rig.cameras["L"].dist_coeffs, 0.0)


@pytest.mark.parametrize(
    "model", ["VIC3D_LENS_DISTORTION", "VIC3D_DIS", "K1R1_K2R2_K3R3", "K1R2_K2R4_K3R6", "WHATEVER"]
)
def test_dice_unsupported_distortion_model_raises(tmp_path: Path, model: str):
    with pytest.raises(ValueError, match="LENS_DISTORTION_MODEL"):
        from_dice_xml(_dice_file(tmp_path, model=model))


def test_dice_nonzero_skew_warns_about_its_unit(tmp_path: Path):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        rig = from_dice_xml(_dice_file(tmp_path, fs=0.5))
    assert rig.cameras["L"].skew == 0.5
    assert any("FS" in str(w.message) for w in caught)
