"""Calibration-file importers for six formats, normalizing into StereoRig.

Ported from the MATLAB ``cameraParamsFormatConvertFrom*.m`` converters (see the
extraction in the Phase 1 notes). All six formats converge on the SAME target
convention, so the per-format code is only a thin parser feeding one normalizer:

- intrinsics -> ``K = [[fx, skew, cx], [0, fy, cy], [0, 0, 1]]`` (standard, never
  the MATLAB-legacy transposed ``IntrinsicMatrix``);
- distortion -> OpenCV order ``[k1, k2, p1, p2, k3]`` (no sign flip, no p1/p2 swap);
- extrinsics -> ``X_R = R @ X_L + T`` with the LEFT camera as world (``R=I, T=0``);
  a DIRECT pass-through for every format (no transpose, no inversion);
- ``T`` is in the calibration length units (millimetres).

Qt-free; imports only numpy / scipy / cv2 / stdlib (no ``al_dic``).
"""

from __future__ import annotations

import csv
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.calibration.model import CameraIntrinsics, StereoRig


def _euler_zyx_deg(rx_deg: float, ry_deg: float, rz_deg: float) -> NDArray[np.float64]:
    """Build ``R = Rz(rz) @ Ry(ry) @ Rx(rx)`` from degrees (MatchID / OpenCorr).

    Matches the MATLAB ``rotation_matrix(Theta, Phi, Psi)`` helper (cosd/sind,
    intrinsic Z-Y-X composition) used by both Euler-angle formats.
    """
    rx, ry, rz = np.deg2rad([rx_deg, ry_deg, rz_deg])
    cx, sx = np.cos(rx), np.sin(rx)
    cy, sy = np.cos(ry), np.sin(ry)
    cz, sz = np.cos(rz), np.sin(rz)
    rot_x = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], dtype=np.float64)
    rot_y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=np.float64)
    rot_z = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], dtype=np.float64)
    return rot_z @ rot_y @ rot_x


def _rig(
    left: CameraIntrinsics,
    right: CameraIntrinsics,
    R: NDArray[np.float64],
    T: NDArray[np.float64],
) -> StereoRig:
    """Assemble the two-camera rig with the left camera as world."""
    return StereoRig(
        cameras={"L": left, "R": right},
        extrinsics={
            ("L", "R"): (
                np.asarray(R, np.float64).reshape(3, 3),
                np.asarray(T, np.float64).reshape(3),
            )
        },
    )


def _K_matrix_to_intrinsics(
    K: NDArray[np.float64],
    dist_ovcv: NDArray[np.float64],
    size: tuple[int | None, int | None] = (None, None),
) -> CameraIntrinsics:
    """Build ``CameraIntrinsics`` from a standard ``K`` and OpenCV distCoeffs.

    ``dist_ovcv`` is ``[k1, k2, p1, p2, k3(, ...)]``; extra coefficients are dropped.
    Guards against a transposed ``K`` (principal point in the bottom row).
    """
    K = np.asarray(K, np.float64).reshape(3, 3)
    if abs(K[2, 0]) > 1e-6 or abs(K[2, 1]) > 1e-6:  # cx,cy leaked into bottom row
        K = K.T
    d = np.asarray(dist_ovcv, np.float64).ravel()
    d = np.concatenate([d, np.zeros(5)])[:5]  # pad/truncate to [k1,k2,p1,p2,k3]
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
        width=size[0],
        height=size[1],
    )


# --------------------------------------------------------------------------- #
# DICe — OpenCV XML camera-system file (the format used by the sample datasets)
# --------------------------------------------------------------------------- #


def _dice_camera_dict(
    cam_list: ET.Element,
) -> tuple[dict[str, float], NDArray[np.float64] | None, NDArray[np.float64] | None]:
    scalars: dict[str, float] = {}
    for p in cam_list.iter("Parameter"):
        name = p.get("name", "")
        if name.startswith("ROW"):
            continue
        try:
            scalars[name] = float(p.get("value", ""))
        except ValueError:
            pass  # non-numeric (e.g. LENS_DISTORTION_MODEL) — ignore
    R = None
    for sub in cam_list.iter("ParameterList"):
        if sub.get("name") == "rotation_3x3_matrix":
            rows = {
                p.get("name"): _parse_brace_vec(p.get("value", "")) for p in sub.iter("Parameter")
            }
            if all(f"ROW {i}" in rows for i in range(3)):
                R = np.array([rows["ROW 0"], rows["ROW 1"], rows["ROW 2"]], dtype=np.float64)
            break
    T = None
    if any(k in scalars for k in ("TX", "TY", "TZ")):
        T = np.array(
            [scalars.get("TX", 0.0), scalars.get("TY", 0.0), scalars.get("TZ", 0.0)], np.float64
        )
    return scalars, R, T


def _parse_brace_vec(s: str) -> list[float]:
    """Parse a DICe ROW string ``"{ a, b, c }"`` -> ``[a, b, c]``."""
    return [float(x) for x in s.replace("{", "").replace("}", "").split(",") if x.strip()]


def _dice_intrinsics(s: dict[str, float]) -> CameraIntrinsics:
    K = np.array(
        [
            [s.get("FX", 0.0), s.get("FS", 0.0), s.get("CX", 0.0)],
            [0.0, s.get("FY", 0.0), s.get("CY", 0.0)],
            [0.0, 0.0, 1.0],
        ]
    )
    dist = [
        s.get("K1", 0.0),
        s.get("K2", 0.0),
        s.get("P1", 0.0),
        s.get("P2", 0.0),
        s.get("K3", 0.0),
    ]
    w, h = None, None
    return _K_matrix_to_intrinsics(K, np.array(dist), (w, h))


def from_dice_xml(path: str | Path) -> StereoRig:
    """Import a DICe (``system_type_3D="OPENCV"``) XML camera-system file."""
    root = ET.parse(str(path)).getroot()
    cams = {
        pl.get("name"): pl
        for pl in root.iter("ParameterList")
        if pl.get("name") in ("CAMERA 0", "CAMERA 1")
    }
    if "CAMERA 0" not in cams or "CAMERA 1" not in cams:
        raise ValueError("DICe file must contain 'CAMERA 0' and 'CAMERA 1' ParameterLists")
    sL, _, _ = _dice_camera_dict(cams["CAMERA 0"])
    sR, R, T = _dice_camera_dict(cams["CAMERA 1"])
    if R is None or T is None:
        raise ValueError("DICe 'CAMERA 1' is missing rotation_3x3_matrix or TX/TY/TZ")
    return _rig(_dice_intrinsics(sL), _dice_intrinsics(sR), R, T)


# --------------------------------------------------------------------------- #
# MatchID — flat ``*.caldat`` label/value table, Euler extrinsics (degrees)
# --------------------------------------------------------------------------- #

_NUM_RE = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def _matchid_table(path: str | Path) -> dict[str, float]:
    table: dict[str, float] = {}
    for raw in Path(path).read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line:
            continue
        nums = _NUM_RE.findall(line)
        if not nums:
            continue
        value = float(nums[-1])
        label = line[: line.rfind(nums[-1])]
        key = re.sub(r"\s+", "", label).strip("=:,;\t ")  # 'Cam0_Kappa 1' -> 'Cam0_Kappa1'
        if key:
            table[key] = value
    return table


def _matchid_camera(t: dict[str, float], prefix: str) -> CameraIntrinsics:
    def g(name: str) -> float:
        return t.get(f"{prefix}{name}", 0.0)

    K = np.array([[g("Fx"), g("Fs"), g("Cx")], [0.0, g("Fy"), g("Cy")], [0.0, 0.0, 1.0]])
    dist = [g("Kappa1"), g("Kappa2"), g("P1"), g("P2"), g("Kappa3")]
    return _K_matrix_to_intrinsics(K, np.array(dist))


def from_matchid_caldat(path: str | Path) -> StereoRig:
    """Import a MatchID ``*.caldat`` calibration export (Cam0=Left, Cam1=Right)."""
    t = _matchid_table(path)
    left = _matchid_camera(t, "Cam0_")
    right = _matchid_camera(t, "Cam1_")
    R = _euler_zyx_deg(t.get("Theta", 0.0), t.get("Phi", 0.0), t.get("Psi", 0.0))
    T = np.array([t.get("Tx", 0.0), t.get("Ty", 0.0), t.get("Tz", 0.0)], np.float64)
    return _rig(left, right, R, T)


# --------------------------------------------------------------------------- #
# OpenCorr — 3-column CSV (name, left, right), Euler extrinsics (degrees)
# --------------------------------------------------------------------------- #


def from_opencorr_csv(path: str | Path) -> StereoRig:
    """Import an OpenCorr calibration CSV (col2=Left/world, col3=Right)."""
    left_vals: dict[str, float] = {}
    right_vals: dict[str, float] = {}
    with Path(path).open(encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        rows = [r for r in reader if r and len(r) >= 3]
    # First row is a header (readtable consumes it); match by name, not position.
    for r in rows[1:]:
        name = r[0].strip()
        try:
            left_vals[name], right_vals[name] = float(r[1]), float(r[2])
        except ValueError:
            continue

    def cam(vals: dict[str, float]) -> CameraIntrinsics:
        K = np.array(
            [
                [vals.get("Fx", 0.0), vals.get("Fs", 0.0), vals.get("Cx", 0.0)],
                [0.0, vals.get("Fy", 0.0), vals.get("Cy", 0.0)],
                [0.0, 0.0, 1.0],
            ]
        )
        dist = [
            vals.get("K1", 0.0),
            vals.get("K2", 0.0),
            vals.get("P1", 0.0),
            vals.get("P2", 0.0),
            vals.get("K3", 0.0),
        ]
        return _K_matrix_to_intrinsics(K, np.array(dist))

    R = _euler_zyx_deg(
        right_vals.get("Rx", 0.0), right_vals.get("Ry", 0.0), right_vals.get("Rz", 0.0)
    )
    T = np.array(
        [right_vals.get("Tx", 0.0), right_vals.get("Ty", 0.0), right_vals.get("Tz", 0.0)],
        np.float64,
    )
    return _rig(cam(left_vals), cam(right_vals), R, T)


# --------------------------------------------------------------------------- #
# MMC — .mat with ``Camera_000N_Group_0001_*`` plain arrays
# --------------------------------------------------------------------------- #


def from_mmc_mat(path: str | Path) -> StereoRig:
    """Import an MMC (Multi_Camera_Calibration / MMCL, YIN Zhuoyi) ``.mat`` result.

    Verified against the MMC source (``save_CalibrationeResult_file_mat``):
    variables are ``Camera_XXXX_Group_YYYY_*`` where the camera digits are the
    tool's GUI *slot* index (1..36 — not necessarily 1/2) and the group digits
    come from the group combobox — so both are DISCOVERED by pattern, never
    hardcoded. The lowest group is used; its two lowest camera slots become
    L/R. The first camera is the world (MMC writes R=I, T=0 for it); the
    second carries the stereo ``_R``/``_T`` (premultiply, already our target
    convention). MMC can export up to six rational radial coefficients and a
    ``ThinPrismDistortion`` — both exceed our 5-coefficient Brown-Conrady
    model, so NONZERO higher-order terms raise (re-export from MMC with
    radial count 3 and thin-prism 0) instead of being silently dropped.
    """
    from scipy.io import loadmat

    mat = loadmat(str(path))
    prefixes: dict[tuple[int, int], str] = {}
    for key in mat:
        m = re.fullmatch(r"(Camera_(\d+)_Group_(\d+)_)IntrinsicMatrix", key)
        if m:
            prefixes[(int(m.group(3)), int(m.group(2)))] = m.group(1)
    if not prefixes:
        raise ValueError("MMC .mat has no Camera_*_Group_*_IntrinsicMatrix variables")
    group = min(g for g, _c in prefixes)
    cams = sorted(c for g, c in prefixes if g == group)
    if len(cams) < 2:
        raise ValueError(f"MMC .mat group {group} has {len(cams)} camera(s); need 2 for stereo")

    def cam(prefix: str) -> CameraIntrinsics:
        K = np.asarray(mat[prefix + "IntrinsicMatrix"], np.float64)
        rad = np.asarray(mat[prefix + "RadialDistortion"], np.float64).ravel()
        tan = np.asarray(mat[prefix + "TangentialDistortion"], np.float64).ravel()
        if rad.size > 3 and np.abs(rad[3:]).max() > 1e-12:
            raise ValueError(
                f"MMC export {prefix}RadialDistortion uses rational coefficients "
                f"k4..k6 = {rad[3:6].tolist()} — unsupported by the 5-coefficient "
                "Brown-Conrady model; re-export from MMC with radial count 3."
            )
        prism = mat.get(prefix + "ThinPrismDistortion")
        if prism is not None and np.abs(np.asarray(prism, np.float64)).max() > 1e-12:
            raise ValueError(
                f"MMC export {prefix}ThinPrismDistortion is nonzero — unsupported; "
                "re-export from MMC with thin-prism count 0."
            )
        dist = [rad[0], rad[1], tan[0], tan[1], rad[2] if rad.size >= 3 else 0.0]
        return _K_matrix_to_intrinsics(K, np.array(dist))

    p_left = prefixes[(group, cams[0])]
    p_right = prefixes[(group, cams[1])]
    R = np.asarray(mat[p_right + "R"], np.float64).reshape(3, 3)
    T = np.asarray(mat[p_right + "T"], np.float64).ravel()
    return _rig(cam(p_left), cam(p_right), R, T)


# --------------------------------------------------------------------------- #
# MatlabCV — .mat with raw-exported stereoParameters fields
# --------------------------------------------------------------------------- #


def from_matlabcv_mat(path: str | Path) -> StereoRig:
    """Import a MATLAB-CV stereo calibration ``.mat``.

    MATLAB ``stereoParameters`` are OOP objects that scipy cannot deserialize, so
    this expects the raw fields pre-exported to plain arrays (the practical path):
    ``K_left, dist_left, K_right, dist_right, R, T`` (``dist_*`` in OpenCV order
    ``[k1,k2,p1,p2,k3]`` or ``[k1,k2,k3]`` radial + separate is not supported here).
    ``R, T`` follow the R2022b+ ``PoseCamera2`` premultiply convention (X_R=R@X_L+T).
    """
    from scipy.io import loadmat

    mat = loadmat(str(path))
    missing = [
        k for k in ("K_left", "dist_left", "K_right", "dist_right", "R", "T") if k not in mat
    ]
    if missing:
        raise ValueError(
            f"MatlabCV .mat missing raw fields {missing}; export stereoParameters to plain "
            "arrays K_left/dist_left/K_right/dist_right/R/T (scipy cannot read the OOP object)."
        )
    left = _K_matrix_to_intrinsics(mat["K_left"], mat["dist_left"])
    right = _K_matrix_to_intrinsics(mat["K_right"], mat["dist_right"])
    return _rig(left, right, np.asarray(mat["R"], np.float64), np.asarray(mat["T"], np.float64))


# --------------------------------------------------------------------------- #
# OpenCV YAML — cv2.FileStorage (the sixth, non-MATLAB format)
# --------------------------------------------------------------------------- #


def from_opencv_yaml(path: str | Path) -> StereoRig:
    """Import an OpenCV stereo calibration YAML/XML (cv2.FileStorage).

    Expected nodes: ``cameraMatrix1``, ``distCoeffs1``, ``cameraMatrix2``,
    ``distCoeffs2``, ``R``, ``T`` — the ``cv2.stereoCalibrate`` output convention
    (``X_2 = R @ X_1 + T``), which already matches the target (cam1 = left = world).
    """
    import cv2

    fs = cv2.FileStorage(str(path), cv2.FILE_STORAGE_READ)
    if not fs.isOpened():
        raise ValueError(f"cannot open OpenCV calibration file: {path}")
    try:

        def node(name: str) -> NDArray[np.float64]:
            n = fs.getNode(name)
            if n.empty():
                raise ValueError(f"OpenCV calibration file missing node {name!r}")
            return np.asarray(n.mat(), np.float64)

        left = _K_matrix_to_intrinsics(node("cameraMatrix1"), node("distCoeffs1"))
        right = _K_matrix_to_intrinsics(node("cameraMatrix2"), node("distCoeffs2"))
        return _rig(left, right, node("R"), node("T"))
    finally:
        fs.release()


IMPORTERS = {
    "dice": from_dice_xml,
    "matchid": from_matchid_caldat,
    "opencorr": from_opencorr_csv,
    "mmc": from_mmc_mat,
    "matlabcv": from_matlabcv_mat,
    "opencv_yaml": from_opencv_yaml,
}


def load_calibration(path: str | Path, fmt: str) -> StereoRig:
    """Dispatch to the importer for ``fmt`` (one of :data:`IMPORTERS`)."""
    if fmt not in IMPORTERS:
        raise ValueError(f"unknown calibration format {fmt!r}; choose from {sorted(IMPORTERS)}")
    return IMPORTERS[fmt](path)
