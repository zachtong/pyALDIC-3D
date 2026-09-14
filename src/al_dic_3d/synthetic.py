"""Synthetic stereo-DIC scene with analytic ground truth (Qt-free, deterministic).

A textured, TILTED plane (depth varies across the field) under a known affine
material deformation, viewed by an 18 deg convergent stereo rig WITH lens
distortion, so the whole pipeline -- including point undistortion -- runs
against analytic ground truth. It backs the synthetic parity gate (tests), the
mini stereo run of ``al-dic-3d self-test`` and ``al-dic-3d demo``.

Rendering is exact and non-iterative: every (camera, frame) image is a single
``cv2.remap`` of the reference left image ``L0``. For a target pixel ``(u, v)``:
undistort -> back-project ray -> intersect the fixed material plane at the world
point ``Pw`` -> invert the frame-k affine to the material coordinate ``M`` ->
project ``M``'s reference world position back through the left camera -> source
pixel ``p0`` -> sample ``L0``. Because the plane is fixed, ``Pw`` is computed once
per camera; only the (closed-form) affine inverse changes per frame.

Files are written through :mod:`al_dic_3d.pathsafe`, so output folders whose
names contain spaces or non-ASCII characters work on Windows. The same seed
always produces byte-identical images and calibration.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.calibration import CameraIntrinsics, StereoRig, project_points, undistort_points

# --- scene constants ---------------------------------------------------------
FX = FY = 1500.0
Z0 = 800.0  # plane depth at the optical axis (world mm)
RIG_ANGLE_DEG = 18.0  # convergence angle between the two optical axes
# Mild plane tilt: normal a few degrees off the optical axis so depth ranges over
# the field (tests triangulation across a depth spread). Plane: n . X = d.
_TILT = np.deg2rad(9.0)
PLANE_N = np.array([np.sin(_TILT), 0.35 * np.sin(_TILT), np.cos(_TILT)], dtype=np.float64)
PLANE_N = PLANE_N / np.linalg.norm(PLANE_N)
PLANE_D = float(PLANE_N[2] * Z0)  # passes through (0, 0, Z0)

# Realistic Brown-Conrady distortion (different per camera).
DIST_L = dict(k1=-0.16, k2=0.05, p1=0.0006, p2=-0.0004, k3=0.0)
DIST_R = dict(k1=-0.13, k2=0.04, p1=-0.0005, p2=0.0007, k3=0.0)

CALIB_NAME = "calib.yml"
CONFIG_NAME = "config.toml"
_FRAME_NAME = re.compile(r"[LR]_(\d{3,})\.png")  # build_scene's L_000.png / R_000.png
#: First line of every config this module writes. ``al-dic-3d demo`` only
#: rewrites an existing folder whose config.toml starts with it.
CONFIG_MARKER = "# pyALDIC-3D synthetic stereo dataset (al_dic_3d.synthetic)"

_MIN_IMAGE_PX = 64


def speckle(size: int, seed: int = 7, sigma: float = 1.9) -> NDArray[np.float64]:
    """Deterministic Gaussian-filtered random speckle in ``[20, 235]``, ``size`` x ``size``."""
    from scipy.ndimage import gaussian_filter

    rng = np.random.default_rng(seed)
    f = gaussian_filter(rng.standard_normal((size, size)), sigma=sigma, mode="nearest")
    f -= f.min()
    f /= f.max()
    return 20.0 + 215.0 * f


_speckle = speckle  # name used before the move out of tests/synth_parity.py


def cameras(
    img: int,
) -> tuple[CameraIntrinsics, CameraIntrinsics, np.ndarray, np.ndarray, StereoRig]:
    """18 deg converging rig, left = world, both cameras distorted."""
    c = (img - 1) / 2.0
    th = np.deg2rad(RIG_ANGLE_DEG)
    R = np.array(
        [[np.cos(th), 0, np.sin(th)], [0, 1, 0], [-np.sin(th), 0, np.cos(th)]],
        dtype=np.float64,
    )
    T = np.array([-Z0 * np.sin(th), 0.0, Z0 * (1.0 - np.cos(th))], dtype=np.float64)
    intr_L = CameraIntrinsics(fx=FX, fy=FY, cx=c, cy=c, width=img, height=img, **DIST_L)
    intr_R = CameraIntrinsics(fx=FX, fy=FY, cx=c, cy=c, width=img, height=img, **DIST_R)
    rig = StereoRig(cameras={"L": intr_L, "R": intr_R}, extrinsics={("L", "R"): (R, T)})
    return intr_L, intr_R, R, T, rig


def affine(k: int) -> tuple[np.ndarray, np.ndarray]:
    """Cumulative in-plane material affine at frame k (identity at k=0).

    A gentle non-rigid field: uniaxial-ish stretch + shear + a small translation
    growing linearly with the frame index.
    """
    G = np.array([[0.0020, 0.0006], [0.0004, -0.0011]], dtype=np.float64)  # strain/frame
    A = np.eye(2) + k * G
    t = np.array([0.35 * k, 0.18 * k], dtype=np.float64)  # world mm
    return A, t


def _plane_z(xy: np.ndarray) -> np.ndarray:
    return (PLANE_D - PLANE_N[0] * xy[:, 0] - PLANE_N[1] * xy[:, 1]) / PLANE_N[2]


def _on_plane(xy: np.ndarray) -> np.ndarray:
    return np.column_stack([xy, _plane_z(xy)])


def _backproject(
    pixels: np.ndarray, intr: CameraIntrinsics, R: np.ndarray, T: np.ndarray
) -> np.ndarray:
    """Undistort pixels and intersect their rays with the material plane -> world (N,3).

    Undistortion goes through :func:`al_dic_3d.calibration.undistort_points`
    (tight iteration criteria, OpenCV 4.x and 5.x), the same call the
    reconstruction uses.
    """
    xn = undistort_points(np.asarray(pixels, dtype=np.float64).reshape(-1, 2), intr)
    dir_cam = np.column_stack([xn, np.ones(len(xn))])  # (N,3)
    dir_world = dir_cam @ R  # R^T @ dir_cam, row-wise
    cc = -R.T @ T  # camera center in world
    denom = dir_world @ PLANE_N
    lam = (PLANE_D - PLANE_N @ cc) / denom
    return cc[None, :] + lam[:, None] * dir_world


def _pixel_grid(h: int, w: int) -> np.ndarray:
    uu, vv = np.meshgrid(np.arange(w, dtype=np.float64), np.arange(h, dtype=np.float64))
    return np.column_stack([uu.ravel(), vv.ravel()])


def _remap_frame(
    l0: np.ndarray, pw: np.ndarray, intr_L: CameraIntrinsics, k: int
) -> NDArray[np.float32]:
    """Sample ``l0`` for the camera whose per-pixel plane points are ``pw`` at frame k."""
    import cv2

    h, w = l0.shape
    A, t = affine(k)
    a_inv = np.linalg.inv(A)
    material = (pw[:, :2] - t) @ a_inv.T  # M = A^{-1} (Pw_xy - t)
    ref_world = _on_plane(material)  # material's reference (k=0) world position
    p0 = project_points(ref_world, intr_L, np.eye(3), np.zeros(3))  # -> left-ref pixel
    map_x = p0[:, 0].reshape(h, w).astype(np.float32)
    map_y = p0[:, 1].reshape(h, w).astype(np.float32)
    return cv2.remap(
        l0.astype(np.float32), map_x, map_y, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT
    )


def _render(
    l0: np.ndarray,
    intr: CameraIntrinsics,
    R: np.ndarray,
    T: np.ndarray,
    intr_L: CameraIntrinsics,
    k: int,
) -> np.ndarray:
    """Render camera ``(intr,R,T)`` at frame k as a single remap of the reference L0."""
    pw = _backproject(_pixel_grid(*l0.shape), intr, R, T)  # plane point per target pixel
    return _remap_frame(l0, pw, intr_L, k)


def _u16(img: np.ndarray) -> np.ndarray:
    return np.clip(img * 256.0, 0, 65535).astype(np.uint16)


def _write_calib(
    path: Path, intr_L: CameraIntrinsics, intr_R: CameraIntrinsics, R: np.ndarray, T: np.ndarray
) -> None:
    """OpenCV stereo YAML (``[calibration] format = "opencv_yaml"``), unicode-path safe."""
    from al_dic_3d.pathsafe import filestorage_write

    with filestorage_write(path) as fs:
        fs.write("cameraMatrix1", intr_L.K)
        fs.write("distCoeffs1", intr_L.dist_coeffs.reshape(1, -1))
        fs.write("cameraMatrix2", intr_R.K)
        fs.write("distCoeffs2", intr_R.dist_coeffs.reshape(1, -1))
        fs.write("R", R)
        fs.write("T", T.reshape(3, 1))


def build_scene(
    out_dir: str | Path, *, img: int = 320, n_frames: int = 5, seed: int = 7
) -> dict[str, Any]:
    """Render the distorted stereo dataset to ``out_dir``; return the scene dict.

    Writes ``L_000.png`` ... / ``R_000.png`` ... (16-bit) and ``calib.yml``. The
    returned dict carries what :func:`gt_tracks` and :func:`write_config` need:
    ``dir``, ``img``, ``n_frames``, the intrinsics/extrinsics, the ``rig`` and
    the ``left`` / ``right`` file names.

    Raises:
        ValueError: ``img`` or ``n_frames`` is too small for a stereo run.
        OSError: a file cannot be written.
    """
    from al_dic_3d.pathsafe import imwrite_unicode

    if int(img) < _MIN_IMAGE_PX:
        raise ValueError(f"image size must be at least {_MIN_IMAGE_PX} px, got {img}")
    if int(n_frames) < 2:
        raise ValueError(f"need at least 2 frames (a reference and a deformed one), got {n_frames}")
    img, n_frames = int(img), int(n_frames)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    intr_L, intr_R, R, T, rig = cameras(img)
    l0 = speckle(img, seed=seed)
    grid = _pixel_grid(img, img)
    # The material plane is fixed, so each camera's per-pixel plane point is
    # computed once; only the affine inverse changes per frame.
    pw_left = _backproject(grid, intr_L, np.eye(3), np.zeros(3))
    pw_right = _backproject(grid, intr_R, R, T)

    left, right = [], []
    for k in range(n_frames):
        name_l, name_r = f"L_{k:03d}.png", f"R_{k:03d}.png"
        imwrite_unicode(out_dir / name_l, _u16(_remap_frame(l0, pw_left, intr_L, k)))
        imwrite_unicode(out_dir / name_r, _u16(_remap_frame(l0, pw_right, intr_L, k)))
        left.append(name_l)
        right.append(name_r)

    _write_calib(out_dir / CALIB_NAME, intr_L, intr_R, R, T)
    return {
        "dir": out_dir,
        "img": img,
        "n_frames": n_frames,
        "intr_L": intr_L,
        "intr_R": intr_R,
        "R": R,
        "T": T,
        "rig": rig,
        "left": left,
        "right": right,
    }


build_parity_scene = build_scene  # name used by the parity-gate tests


def gt_tracks(scene: dict, ref_coords: np.ndarray) -> dict:
    """Analytic ground truth for the runner's left mesh nodes (pixels in L1).

    Returns world points, displacement (P^k - P^1), and L/R pixel tracks, each
    shaped ``(n_frames, n, ...)``.
    """
    intr_L, intr_R, R, T = scene["intr_L"], scene["intr_R"], scene["R"], scene["T"]
    m0 = _backproject(ref_coords, intr_L, np.eye(3), np.zeros(3))[:, :2]  # material coords
    nf, n = scene["n_frames"], ref_coords.shape[0]

    world = np.empty((nf, n, 3))
    xL = np.empty((nf, n, 2))
    xR = np.empty((nf, n, 2))
    for k in range(nf):
        A, t = affine(k)
        moved = m0 @ A.T + t
        pk = _on_plane(moved)
        world[k] = pk
        xL[k] = project_points(pk, intr_L, np.eye(3), np.zeros(3))
        xR[k] = project_points(pk, intr_R, R, T)
    disp = world - world[0][None]
    return {"world": world, "displacement": disp, "xL": xL, "xR": xR}


# --- parity-gate metrics + tolerances (shared by the tests and the reports) --

# Tolerances at ~1.6-2x the observed accuracy: robust to seed/size while still
# catching gross regressions (an L/R swap, wrong undistort, or sign flip would
# blow past these by orders of magnitude). Observed (multi-seed): xL med 0.042 px,
# 3D point med ~43 um, disp med ~48 um, reproj ~5e-6 px.
GATE = {
    "coverage_min": 0.97,
    "xL_med": 0.07,
    "xL_p90": 0.10,
    "xR_med": 0.05,
    "xR_p90": 0.08,
    "point_med_mm": 0.08,
    "point_p90_mm": 0.15,
    "disp_med_mm": 0.08,
    "disp_p90_mm": 0.12,
    "inplane_med_mm": 0.04,
    "reproj_med_px": 1e-4,
}


def metrics(result, gt: dict) -> dict:
    """Per-point error arrays (recovered vs analytic GT) over tracked points."""
    from al_dic_3d.matching.contracts import INVALID

    cs, rec = result.correspondence, result.reconstruction
    tracked = cs.source != INVALID
    xl, xr, pe, de, ip, cov = [], [], [], [], [], []
    for k in range(cs.n_frames):
        tr = tracked[k]
        cov.append(float(tr.mean()))
        xl.append(np.linalg.norm(cs.xL[k][tr] - gt["xL"][k][tr], axis=1))
        xr.append(np.linalg.norm(cs.xR[k][tr] - gt["xR"][k][tr], axis=1))
        pe.append(np.linalg.norm(rec.points[k][tr] - gt["world"][k][tr], axis=1))
        if k > 0:
            com = tr & tracked[0]
            de.append(np.linalg.norm(rec.displacement[k][com] - gt["displacement"][k][com], axis=1))
            ip.append(
                np.linalg.norm(
                    rec.displacement[k][com][:, :2] - gt["displacement"][k][com][:, :2], axis=1
                )
            )
    return {
        "coverage_min": min(cov),
        "xL": np.concatenate(xl),
        "xR": np.concatenate(xr),
        "point": np.concatenate(pe),
        "disp": np.concatenate(de),
        "inplane": np.concatenate(ip),
        "reproj": rec.reproj_error,
    }


def gate_rows(m: dict) -> list[dict]:
    """Evaluate each gate criterion -> rows for the report table / test assertions."""

    def row(name: str, value: float, tol: float, op: str) -> dict:
        ok = value <= tol if op == "<=" else value >= tol
        return {"name": name, "value": float(value), "tol": tol, "op": op, "pass": bool(ok)}

    return [
        row("coverage (min frac)", m["coverage_min"], GATE["coverage_min"], ">="),
        row("xL error median (px)", np.median(m["xL"]), GATE["xL_med"], "<="),
        row("xL error p90 (px)", np.percentile(m["xL"], 90), GATE["xL_p90"], "<="),
        row("xR error median (px)", np.median(m["xR"]), GATE["xR_med"], "<="),
        row("xR error p90 (px)", np.percentile(m["xR"], 90), GATE["xR_p90"], "<="),
        row("3D point median (mm)", np.median(m["point"]), GATE["point_med_mm"], "<="),
        row("3D point p90 (mm)", np.percentile(m["point"], 90), GATE["point_p90_mm"], "<="),
        row("3D disp median (mm)", np.median(m["disp"]), GATE["disp_med_mm"], "<="),
        row("3D disp p90 (mm)", np.percentile(m["disp"], 90), GATE["disp_p90_mm"], "<="),
        row("in-plane disp median (mm)", np.median(m["inplane"]), GATE["inplane_med_mm"], "<="),
        row("reproj median (px)", np.nanmedian(m["reproj"]), GATE["reproj_med_px"], "<="),
    ]


def gate_passed(m: dict) -> bool:
    return all(r["pass"] for r in gate_rows(m))


def _stat(values: np.ndarray, q: float) -> float:
    """Percentile ``q`` of ``values`` (``NaN`` when empty, never a warning)."""
    return float(np.percentile(values, q)) if np.size(values) else float("nan")


def accuracy_summary(result, scene: dict) -> dict[str, float]:
    """Headline accuracy of a run on this scene against the analytic ground truth.

    Keys: ``coverage_min`` (lowest per-frame fraction of tracked points),
    ``disp_median_mm`` / ``disp_p90_mm`` (3D displacement error over the
    deformed frames), ``point_median_mm`` (3D position error), ``xL_median_px``,
    ``n_points`` and ``n_frames``.
    """
    m = metrics(result, gt_tracks(scene, np.asarray(result.ref_coords, dtype=np.float64)))
    return {
        "coverage_min": float(m["coverage_min"]),
        "disp_median_mm": _stat(m["disp"], 50),
        "disp_p90_mm": _stat(m["disp"], 90),
        "point_median_mm": _stat(m["point"], 50),
        "xL_median_px": _stat(m["xL"], 50),
        "n_points": float(result.correspondence.n_pts),
        "n_frames": float(result.correspondence.n_frames),
    }


def _toml_list(names: list[str]) -> str:
    return "[" + ", ".join(json.dumps(n, ensure_ascii=False) for n in names) + "]"


def write_config(
    out_dir: str | Path,
    scene: dict,
    *,
    prefix: str = "parity",
    explicit_files: bool = False,
    output_dir: str = "out",
    strain: bool = False,
) -> Path:
    """Write a config.toml with an ROI safely inside the field; return its path.

    ``explicit_files=True`` lists the image files instead of the ``L_*.png`` /
    ``R_*.png`` globs, so the config stays valid in folders whose names contain
    glob metacharacters (``[``, ``]``). ``strain=True`` also enables the
    surface-strain pass. Every path in the file is relative to ``out_dir``.
    """
    img = scene["img"]
    lo, hi = int(round(0.16 * img)), int(round(0.84 * img))
    if explicit_files:
        left, right = _toml_list(scene["left"]), _toml_list(scene["right"])
    else:
        left, right = '"L_*.png"', '"R_*.png"'
    strain_table = "\n[strain]\nenabled = true\n" if strain else ""
    cfg = f"""{CONFIG_MARKER}

[calibration]
file = "{CALIB_NAME}"
format = "opencv_yaml"

[sequence]
left = {left}
right = {right}

[roi]
xmin = {lo}
xmax = {hi}
ymin = {lo}
ymax = {hi}

[matching]
strategy = "track_both"
winsize = 32
winstepsize = 16
{strain_table}
[output]
dir = {json.dumps(output_dir, ensure_ascii=False)}
prefix = {json.dumps(prefix, ensure_ascii=False)}
"""
    path = Path(out_dir) / CONFIG_NAME
    path.write_text(cfg.strip() + "\n", encoding="utf-8")
    return path


def frame_files(folder: str | Path, *, first: int = 0) -> list[Path]:
    """The frame images :func:`build_scene` names (``L_000.png``, ``R_000.png``, ...).

    Only files matching that exact naming whose frame index is ``>= first``;
    sorted; empty when ``folder`` does not exist.
    """
    folder = Path(folder)
    if not folder.is_dir():
        return []
    found = []
    for path in folder.iterdir():
        match = _FRAME_NAME.fullmatch(path.name)
        if match and int(match.group(1)) >= first and path.is_file():
            found.append(path)
    return sorted(found)


def is_synthetic_dataset(folder: str | Path) -> bool:
    """True when ``folder`` holds a config.toml written by this module."""
    cfg = Path(folder) / CONFIG_NAME
    try:
        with cfg.open(encoding="utf-8", errors="replace") as fh:
            return fh.readline().rstrip("\r\n") == CONFIG_MARKER
    except OSError:
        return False


__all__ = [
    "CALIB_NAME",
    "CONFIG_MARKER",
    "CONFIG_NAME",
    "DIST_L",
    "DIST_R",
    "FX",
    "FY",
    "GATE",
    "PLANE_D",
    "PLANE_N",
    "RIG_ANGLE_DEG",
    "Z0",
    "accuracy_summary",
    "affine",
    "build_parity_scene",
    "build_scene",
    "cameras",
    "frame_files",
    "gate_passed",
    "gate_rows",
    "gt_tracks",
    "is_synthetic_dataset",
    "metrics",
    "speckle",
    "write_config",
]
