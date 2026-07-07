"""Tests for the six calibration-file importers (Phase 1, step 1).

Each format is exercised with a self-contained synthetic file (CI-portable). The
DICe importer is additionally validated against the real sample in the read-only
MATLAB reference repo, skipped when that repo is absent (mirrors the 2D repo's
MATLAB-checkpoint pattern).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from al_dic_3d.calibration import (
    StereoRig,
    from_dice_xml,
    from_matchid_caldat,
    from_matlabcv_mat,
    from_mmc_mat,
    from_opencorr_csv,
    from_opencv_yaml,
    load_calibration,
)
from al_dic_3d.calibration.importers import _euler_zyx_deg

# Reference DICe sample (read-only sibling repo; skip when unavailable, e.g. CI).
_DICE_SAMPLE = (
    Path(__file__).resolve().parents[2]
    / "3D-Stereo-ALDIC"
    / "examples"
    / "Stereo_DIC_Challenge_1.0_S3"
    / "calibration_DICe.xml"
)


def _assert_left_is_world(rig: StereoRig) -> None:
    RL, TL = rig.pose("L")
    assert np.allclose(RL, np.eye(3)) and np.allclose(TL, 0.0)
    R, T = rig.extrinsics[("L", "R")]
    assert R.shape == (3, 3) and T.shape == (3,)
    assert np.allclose(R @ R.T, np.eye(3), atol=1e-9)  # orthonormal
    assert np.isclose(np.linalg.det(R), 1.0, atol=1e-9)


# --------------------------------------------------------------------------- #
# DICe
# --------------------------------------------------------------------------- #

_DICE_SYNTH = """<?xml version="1.0"?>
<ParameterList>
  <Parameter name="system_type_3D" type="string" value="OPENCV"/>
  <ParameterList name="CAMERA 0">
    <Parameter name="FX" type="double" value="1200.0"/>
    <Parameter name="FY" type="double" value="1205.0"/>
    <Parameter name="CX" type="double" value="640.0"/>
    <Parameter name="CY" type="double" value="512.0"/>
    <Parameter name="K1" type="double" value="-0.12"/>
    <Parameter name="K2" type="double" value="0.03"/>
    <Parameter name="K3" type="double" value="0.001"/>
    <ParameterList name="rotation_3x3_matrix">
      <Parameter name="ROW 0" type="string" value="{ 1.0, 0.0, 0.0 }"/>
      <Parameter name="ROW 1" type="string" value="{ 0.0, 1.0, 0.0 }"/>
      <Parameter name="ROW 2" type="string" value="{ 0.0, 0.0, 1.0 }"/>
    </ParameterList>
  </ParameterList>
  <ParameterList name="CAMERA 1">
    <Parameter name="FX" type="double" value="1180.0"/>
    <Parameter name="FY" type="double" value="1185.0"/>
    <Parameter name="CX" type="double" value="650.0"/>
    <Parameter name="CY" type="double" value="505.0"/>
    <Parameter name="K1" type="double" value="-0.10"/>
    <Parameter name="TX" type="double" value="-120.0"/>
    <Parameter name="TY" type="double" value="1.5"/>
    <Parameter name="TZ" type="double" value="20.0"/>
    <ParameterList name="rotation_3x3_matrix">
      <Parameter name="ROW 0" type="string" value="{ 0.8, 0.0, 0.6 }"/>
      <Parameter name="ROW 1" type="string" value="{ 0.0, 1.0, 0.0 }"/>
      <Parameter name="ROW 2" type="string" value="{ -0.6, 0.0, 0.8 }"/>
    </ParameterList>
  </ParameterList>
</ParameterList>
"""


def test_dice_synthetic(tmp_path: Path):
    f = tmp_path / "calib_DICe.xml"
    f.write_text(_DICE_SYNTH, encoding="utf-8")
    rig = from_dice_xml(f)
    assert rig.cameras["L"].fx == 1200.0
    assert rig.cameras["L"].cx == 640.0
    assert rig.cameras["L"].k3 == 0.001
    assert rig.cameras["R"].p1 == 0.0  # omitted -> 0
    R, T = rig.extrinsics[("L", "R")]
    assert np.allclose(T, [-120.0, 1.5, 20.0])
    # Exact orthonormal Ry (cos=0.8, sin=0.6); row-major, no transpose.
    assert np.isclose(R[0, 2], 0.6) and np.isclose(R[2, 0], -0.6)
    _assert_left_is_world(rig)
    assert load_calibration(f, "dice").cameras["L"].fy == 1205.0


@pytest.mark.skipif(not _DICE_SAMPLE.exists(), reason="3D-Stereo-ALDIC reference repo not present")
def test_dice_real_sample():
    rig = from_dice_xml(_DICE_SAMPLE)
    # Sanity values from the extraction of the real Challenge 1.0 S3 calibration.
    assert np.isclose(rig.cameras["L"].fx, 6638.574743420, rtol=0, atol=1e-6)
    assert np.isclose(rig.cameras["L"].cx, 981.5068955210, atol=1e-6)
    assert np.allclose(
        [rig.cameras["L"].k1, rig.cameras["L"].k2, rig.cameras["L"].k3],
        [0.08894459783258, -2.841976089948, 55.92468005109],
    )
    assert np.isclose(rig.cameras["R"].fx, 6644.744254670, atol=1e-6)
    R, T = rig.extrinsics[("L", "R")]
    assert np.allclose(T, [121.4047696045, 0.5744273552224, 23.19261669936], atol=1e-6)
    assert np.isclose(R[0, 0], 0.9461706699489, atol=1e-9)
    assert np.isclose(R[0, 2], -0.3236443991035, atol=1e-9)
    _assert_left_is_world(rig)


# --------------------------------------------------------------------------- #
# MatchID
# --------------------------------------------------------------------------- #

_MATCHID = """Cam0_Fx\t1200.0
Cam0_Fy\t1205.0
Cam0_Fs\t0.0
Cam0_Cx\t640.0
Cam0_Cy\t512.0
Cam0_Kappa1\t-0.12
Cam0_Kappa2\t0.03
Cam0_Kappa 3\t0.001
Cam0_P1\t0.0005
Cam0_P2\t-0.0003
Cam1_Fx\t1180.0
Cam1_Fy\t1185.0
Cam1_Fs\t0.0
Cam1_Cx\t650.0
Cam1_Cy\t505.0
Cam1_Kappa1\t-0.10
Cam1_Kappa2\t0.02
Cam1_Kappa3\t0.0
Cam1_P1\t0.0
Cam1_P2\t0.0
Tx\t-120.0
Ty\t1.5
Tz\t20.0
Theta\t0.0
Phi\t15.0
Psi\t0.0
"""


def test_matchid_synthetic(tmp_path: Path):
    f = tmp_path / "cal.caldat"
    f.write_text(_MATCHID, encoding="utf-8")
    rig = from_matchid_caldat(f)
    assert rig.cameras["L"].fx == 1200.0
    assert rig.cameras["L"].k1 == -0.12
    assert rig.cameras["L"].k3 == 0.001  # 'Kappa 3' (space) normalized
    assert rig.cameras["L"].p1 == 0.0005
    assert rig.cameras["R"].fx == 1180.0
    R, T = rig.extrinsics[("L", "R")]
    assert np.allclose(T, [-120.0, 1.5, 20.0])
    # Phi=15deg about y -> R == Ry(15)
    assert np.allclose(R, _euler_zyx_deg(0.0, 15.0, 0.0))
    _assert_left_is_world(rig)


# --------------------------------------------------------------------------- #
# OpenCorr
# --------------------------------------------------------------------------- #

_OPENCORR = """name,left,right
Fx,1200.0,1180.0
Fy,1205.0,1185.0
Fs,0.0,0.0
Cx,640.0,650.0
Cy,512.0,505.0
K1,-0.12,-0.10
K2,0.03,0.02
K3,0.001,0.0
K4,0.0,0.0
K5,0.0,0.0
K6,0.0,0.0
P1,0.0005,0.0
P2,-0.0003,0.0
Tx,0.0,-120.0
Ty,0.0,1.5
Tz,0.0,20.0
Rx,0.0,0.0
Ry,0.0,15.0
Rz,0.0,0.0
"""


def test_opencorr_synthetic(tmp_path: Path):
    f = tmp_path / "cal.csv"
    f.write_text(_OPENCORR, encoding="utf-8")
    rig = from_opencorr_csv(f)
    assert rig.cameras["L"].fx == 1200.0
    assert rig.cameras["R"].cx == 650.0
    assert rig.cameras["L"].p2 == -0.0003
    R, T = rig.extrinsics[("L", "R")]
    assert np.allclose(T, [-120.0, 1.5, 20.0])  # right column only
    assert np.allclose(R, _euler_zyx_deg(0.0, 15.0, 0.0))
    _assert_left_is_world(rig)


# --------------------------------------------------------------------------- #
# MMC and MatlabCV (.mat via scipy)
# --------------------------------------------------------------------------- #


def _K(fx, fy, cx, cy, skew=0.0):
    return np.array([[fx, skew, cx], [0.0, fy, cy], [0.0, 0.0, 1.0]])


def test_mmc_synthetic(tmp_path: Path):
    from scipy.io import savemat

    R = _euler_zyx_deg(0.0, 15.0, 0.0)
    savemat(
        str(tmp_path / "mmc.mat"),
        {
            "Camera_0001_Group_0001_IntrinsicMatrix": _K(1200, 1205, 640, 512),
            "Camera_0001_Group_0001_RadialDistortion": np.array(
                [-0.12, 0.03, 0.001, 0.0, 0.0]
            ),  # k4..k6 dropped
            "Camera_0001_Group_0001_TangentialDistortion": np.array([0.0005, -0.0003]),
            "Camera_0002_Group_0001_IntrinsicMatrix": _K(1180, 1185, 650, 505),
            "Camera_0002_Group_0001_RadialDistortion": np.array([-0.10, 0.02, 0.0]),
            "Camera_0002_Group_0001_TangentialDistortion": np.array([0.0, 0.0]),
            "Camera_0002_Group_0001_R": R,
            "Camera_0002_Group_0001_T": np.array([-120.0, 1.5, 20.0]),
        },
    )
    rig = from_mmc_mat(tmp_path / "mmc.mat")
    assert rig.cameras["L"].fx == 1200.0
    assert rig.cameras["L"].k3 == 0.001  # third radial kept; ZERO k4..k6 tolerated
    assert rig.cameras["L"].p1 == 0.0005
    assert np.allclose(rig.extrinsics[("L", "R")][1], [-120.0, 1.5, 20.0])
    _assert_left_is_world(rig)


def test_mmc_discovers_slots_and_groups(tmp_path: Path):
    # MMC camera digits = GUI slot index (1..36), group = combobox value; a rig
    # loaded in slots 3/4 of group 2 must import without hardcoded assumptions.
    from scipy.io import savemat

    R = _euler_zyx_deg(0.0, 15.0, 0.0)
    savemat(
        str(tmp_path / "mmc_slots.mat"),
        {
            "Camera_0003_Group_0002_IntrinsicMatrix": _K(1200, 1205, 640, 512),
            "Camera_0003_Group_0002_RadialDistortion": np.array([-0.12, 0.03, 0.001]),
            "Camera_0003_Group_0002_TangentialDistortion": np.array([0.0005, -0.0003]),
            "Camera_0003_Group_0002_ThinPrismDistortion": np.zeros(4),  # zero: OK
            "Camera_0004_Group_0002_IntrinsicMatrix": _K(1180, 1185, 650, 505),
            "Camera_0004_Group_0002_RadialDistortion": np.array([-0.10, 0.02, 0.0]),
            "Camera_0004_Group_0002_TangentialDistortion": np.array([0.0, 0.0]),
            "Camera_0004_Group_0002_R": R,
            "Camera_0004_Group_0002_T": np.array([-120.0, 1.5, 20.0]),
        },
    )
    rig = from_mmc_mat(tmp_path / "mmc_slots.mat")
    assert rig.cameras["L"].fx == 1200.0  # lowest slot = left/world
    assert rig.cameras["R"].fx == 1180.0
    assert np.allclose(rig.extrinsics[("L", "R")][1], [-120.0, 1.5, 20.0])
    _assert_left_is_world(rig)


def test_mmc_rejects_unrepresentable_distortion(tmp_path: Path):
    # Nonzero rational k4..k6 or thin-prism cannot fit the 5-coeff model and
    # must die loudly at import instead of silently mis-modeling distortion.
    import pytest
    from scipy.io import savemat

    base = {
        "Camera_0001_Group_0001_IntrinsicMatrix": _K(1200, 1205, 640, 512),
        "Camera_0001_Group_0001_TangentialDistortion": np.zeros(2),
        "Camera_0002_Group_0001_IntrinsicMatrix": _K(1180, 1185, 650, 505),
        "Camera_0002_Group_0001_RadialDistortion": np.array([-0.10, 0.02, 0.0]),
        "Camera_0002_Group_0001_TangentialDistortion": np.zeros(2),
        "Camera_0002_Group_0001_R": np.eye(3),
        "Camera_0002_Group_0001_T": np.array([-120.0, 0.0, 0.0]),
    }
    savemat(
        str(tmp_path / "rational.mat"),
        {**base, "Camera_0001_Group_0001_RadialDistortion": np.array([-0.1, 0.02, 0, 0.05, 0, 0])},
    )
    with pytest.raises(ValueError, match="k4..k6"):
        from_mmc_mat(tmp_path / "rational.mat")

    savemat(
        str(tmp_path / "prism.mat"),
        {
            **base,
            "Camera_0001_Group_0001_RadialDistortion": np.array([-0.1, 0.02, 0.0]),
            "Camera_0001_Group_0001_ThinPrismDistortion": np.array([1e-4, 0, 0, 0]),
        },
    )
    with pytest.raises(ValueError, match="ThinPrism"):
        from_mmc_mat(tmp_path / "prism.mat")


def test_matlabcv_synthetic(tmp_path: Path):
    from scipy.io import savemat

    R = _euler_zyx_deg(0.0, 15.0, 0.0)
    savemat(
        str(tmp_path / "cv.mat"),
        {
            "K_left": _K(1200, 1205, 640, 512),
            "dist_left": np.array([-0.12, 0.03, 0.0005, -0.0003, 0.001]),
            "K_right": _K(1180, 1185, 650, 505),
            "dist_right": np.array([-0.10, 0.02, 0.0, 0.0, 0.0]),
            "R": R,
            "T": np.array([-120.0, 1.5, 20.0]),
        },
    )
    rig = from_matlabcv_mat(tmp_path / "cv.mat")
    assert rig.cameras["L"].fx == 1200.0
    assert rig.cameras["L"].p1 == 0.0005
    assert np.allclose(rig.extrinsics[("L", "R")][0], R)
    _assert_left_is_world(rig)


def test_matlabcv_missing_fields_raises(tmp_path: Path):
    from scipy.io import savemat

    savemat(str(tmp_path / "bad.mat"), {"K_left": _K(1200, 1205, 640, 512)})
    with pytest.raises(ValueError, match="missing raw fields"):
        from_matlabcv_mat(tmp_path / "bad.mat")


# --------------------------------------------------------------------------- #
# OpenCV YAML
# --------------------------------------------------------------------------- #


def test_opencv_yaml_synthetic(tmp_path: Path):
    import cv2

    R = _euler_zyx_deg(0.0, 15.0, 0.0)
    f = str(tmp_path / "stereo.yml")
    fs = cv2.FileStorage(f, cv2.FILE_STORAGE_WRITE)
    fs.write("cameraMatrix1", _K(1200, 1205, 640, 512))
    fs.write("distCoeffs1", np.array([-0.12, 0.03, 0.0005, -0.0003, 0.001]))
    fs.write("cameraMatrix2", _K(1180, 1185, 650, 505))
    fs.write("distCoeffs2", np.array([-0.10, 0.02, 0.0, 0.0, 0.0]))
    fs.write("R", R)
    fs.write("T", np.array([[-120.0], [1.5], [20.0]]))
    fs.release()
    rig = from_opencv_yaml(f)
    assert rig.cameras["L"].fx == 1200.0
    assert rig.cameras["L"].k3 == 0.001
    assert np.allclose(rig.extrinsics[("L", "R")][1], [-120.0, 1.5, 20.0])
    _assert_left_is_world(rig)


# --------------------------------------------------------------------------- #
# Cross-format consistency + dispatch
# --------------------------------------------------------------------------- #


def test_all_formats_agree(tmp_path: Path):
    """DICe, MatchID, OpenCorr, MMC, MatlabCV, OpenCV-YAML built from the SAME
    parameters must yield equal CameraIntrinsics and extrinsics."""
    import cv2
    from scipy.io import savemat

    # Shared truth (no skew; Phi=15deg toe-in; 120mm baseline).
    KL, KR = _K(1200, 1205, 640, 512), _K(1180, 1185, 650, 505)
    dL = np.array([-0.12, 0.03, 0.0005, -0.0003, 0.001])
    dR = np.array([-0.10, 0.02, 0.0, 0.0, 0.0])
    R = _euler_zyx_deg(0.0, 15.0, 0.0)
    T = np.array([-120.0, 1.5, 20.0])

    (tmp_path / "d.xml").write_text(_DICE_SYNTH, encoding="utf-8")
    (tmp_path / "m.caldat").write_text(_MATCHID, encoding="utf-8")
    (tmp_path / "o.csv").write_text(_OPENCORR, encoding="utf-8")
    savemat(
        str(tmp_path / "mmc.mat"),
        {
            "Camera_0001_Group_0001_IntrinsicMatrix": KL,
            "Camera_0001_Group_0001_RadialDistortion": np.array([dL[0], dL[1], dL[4]]),
            "Camera_0001_Group_0001_TangentialDistortion": dL[2:4],
            "Camera_0002_Group_0001_IntrinsicMatrix": KR,
            "Camera_0002_Group_0001_RadialDistortion": np.array([dR[0], dR[1], dR[4]]),
            "Camera_0002_Group_0001_TangentialDistortion": dR[2:4],
            "Camera_0002_Group_0001_R": R,
            "Camera_0002_Group_0001_T": T,
        },
    )
    savemat(
        str(tmp_path / "cv.mat"),
        {
            "K_left": KL,
            "dist_left": dL,
            "K_right": KR,
            "dist_right": dR,
            "R": R,
            "T": T,
        },
    )
    yf = str(tmp_path / "s.yml")
    fs = cv2.FileStorage(yf, cv2.FILE_STORAGE_WRITE)
    for k, v in (
        ("cameraMatrix1", KL),
        ("distCoeffs1", dL),
        ("cameraMatrix2", KR),
        ("distCoeffs2", dR),
        ("R", R),
        ("T", T.reshape(3, 1)),
    ):
        fs.write(k, v)
    fs.release()

    rigs = {
        "mmc": from_mmc_mat(tmp_path / "mmc.mat"),
        "matlabcv": from_matlabcv_mat(tmp_path / "cv.mat"),
        "opencv_yaml": from_opencv_yaml(yf),
        "matchid": from_matchid_caldat(tmp_path / "m.caldat"),
        "opencorr": from_opencorr_csv(tmp_path / "o.csv"),
    }
    ref = rigs["mmc"]
    for name, rig in rigs.items():
        for cam in ("L", "R"):
            a, b = ref.cameras[cam], rig.cameras[cam]
            assert np.allclose(a.K, b.K), f"{name} K[{cam}]"
            assert np.allclose(a.dist_coeffs, b.dist_coeffs), f"{name} dist[{cam}]"
        assert np.allclose(ref.extrinsics[("L", "R")][0], rig.extrinsics[("L", "R")][0]), (
            f"{name} R"
        )
        assert np.allclose(ref.extrinsics[("L", "R")][1], rig.extrinsics[("L", "R")][1]), (
            f"{name} T"
        )


def test_unknown_format_raises():
    with pytest.raises(ValueError, match="unknown calibration format"):
        load_calibration("x", "nope")
