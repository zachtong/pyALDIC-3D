"""Synthetic *parity-gate* dataset — a distorted, tilted-plane stereo scene.

Stands in for a MATLAB baseline until a real dataset is available: a textured,
TILTED plane (depth varies across the field) under a known affine material
deformation, viewed by two calibrated cameras WITH lens distortion, so the whole
pipeline — including ``undistortPoints`` — is exercised against analytic ground
truth.

Rendering is exact and non-iterative: every (camera, frame) image is a single
``cv2.remap`` of the reference left image ``L0``. For a target pixel ``(u, v)``:
undistort -> back-project ray -> intersect the fixed material plane at the world
point ``Pw`` -> invert the frame-k affine to the material coordinate ``M`` ->
project ``M``'s reference world position back through the left camera -> source
pixel ``p0`` -> sample ``L0``. Because the plane is fixed, ``Pw`` is computed once
per camera; only the (closed-form) affine inverse changes per frame.

NOT collected by pytest (no ``test_`` prefix).
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from scipy.ndimage import gaussian_filter

from al_dic_3d.calibration import CameraIntrinsics, StereoRig, project_points

# --- scene constants ---------------------------------------------------------
FX = FY = 1500.0
Z0 = 800.0  # plane depth at the optical axis (world mm)
# Mild plane tilt: normal a few degrees off the optical axis so depth ranges over
# the field (tests triangulation across a depth spread). Plane: n . X = d.
_TILT = np.deg2rad(9.0)
PLANE_N = np.array([np.sin(_TILT), 0.35 * np.sin(_TILT), np.cos(_TILT)], dtype=np.float64)
PLANE_N = PLANE_N / np.linalg.norm(PLANE_N)
PLANE_D = float(PLANE_N[2] * Z0)  # passes through (0, 0, Z0)

# Realistic Brown-Conrady distortion (different per camera).
DIST_L = dict(k1=-0.16, k2=0.05, p1=0.0006, p2=-0.0004, k3=0.0)
DIST_R = dict(k1=-0.13, k2=0.04, p1=-0.0005, p2=0.0007, k3=0.0)


def _speckle(img: int, seed: int = 7, sigma: float = 1.9) -> np.ndarray:
    rng = np.random.default_rng(seed)
    f = gaussian_filter(rng.standard_normal((img, img)), sigma=sigma, mode="nearest")
    f -= f.min()
    f /= f.max()
    return 20.0 + 215.0 * f


def cameras(
    img: int,
) -> tuple[CameraIntrinsics, CameraIntrinsics, np.ndarray, np.ndarray, StereoRig]:
    """18 deg converging rig, left = world, both cameras distorted."""
    c = (img - 1) / 2.0
    th = np.deg2rad(18.0)
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
    """Undistort pixels and intersect their rays with the material plane -> world (N,3)."""
    pts = np.ascontiguousarray(pixels, np.float64).reshape(-1, 1, 2)
    crit = (cv2.TERM_CRITERIA_COUNT | cv2.TERM_CRITERIA_EPS, 40, 1e-12)
    norm = cv2.undistortPoints(pts, intr.K, intr.dist_coeffs, R=None, P=None, criteria=crit)
    xn = norm.reshape(-1, 2)
    dir_cam = np.column_stack([xn, np.ones(len(xn))])  # (N,3)
    dir_world = dir_cam @ R  # R^T @ dir_cam, row-wise
    cc = -R.T @ T  # camera center in world
    denom = dir_world @ PLANE_N
    lam = (PLANE_D - PLANE_N @ cc) / denom
    return cc[None, :] + lam[:, None] * dir_world


def _render(
    l0: np.ndarray,
    intr: CameraIntrinsics,
    R: np.ndarray,
    T: np.ndarray,
    intr_L: CameraIntrinsics,
    k: int,
) -> np.ndarray:
    """Render camera ``(intr,R,T)`` at frame k as a single remap of the reference L0."""
    h, w = l0.shape
    uu, vv = np.meshgrid(np.arange(w, dtype=np.float64), np.arange(h, dtype=np.float64))
    pix = np.column_stack([uu.ravel(), vv.ravel()])
    pw = _backproject(pix, intr, R, T)  # deformed world point per target pixel

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


def _u16(img: np.ndarray) -> np.ndarray:
    return np.clip(img * 256.0, 0, 65535).astype(np.uint16)


def _write_calib(
    path: Path, intr_L: CameraIntrinsics, intr_R: CameraIntrinsics, R: np.ndarray, T: np.ndarray
) -> None:
    fs = cv2.FileStorage(str(path), cv2.FILE_STORAGE_WRITE)
    fs.write("cameraMatrix1", intr_L.K)
    fs.write("distCoeffs1", intr_L.dist_coeffs.reshape(1, -1))
    fs.write("cameraMatrix2", intr_R.K)
    fs.write("distCoeffs2", intr_R.dist_coeffs.reshape(1, -1))
    fs.write("R", R)
    fs.write("T", T.reshape(3, 1))
    fs.release()


def build_parity_scene(out_dir: Path, *, img: int = 320, n_frames: int = 5, seed: int = 7) -> dict:
    """Render the distorted parity dataset to disk; return a scene dict for GT + config."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    intr_L, intr_R, R, T, rig = cameras(img)
    l0 = _speckle(img, seed=seed)

    for k in range(n_frames):
        cv2.imwrite(
            str(out_dir / f"L_{k:03d}.png"),
            _u16(_render(l0, intr_L, np.eye(3), np.zeros(3), intr_L, k)),
        )
        cv2.imwrite(str(out_dir / f"R_{k:03d}.png"), _u16(_render(l0, intr_R, R, T, intr_L, k)))

    _write_calib(out_dir / "calib.yml", intr_L, intr_R, R, T)
    return {
        "dir": out_dir,
        "img": img,
        "n_frames": n_frames,
        "intr_L": intr_L,
        "intr_R": intr_R,
        "R": R,
        "T": T,
        "rig": rig,
    }


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


# --- parity-gate metrics + tolerances (shared by the test and the report) ----

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


def write_config(out_dir: Path, scene: dict, *, prefix: str = "parity") -> Path:
    """Write a config.toml with an ROI safely inside the field; return its path."""
    img = scene["img"]
    lo, hi = int(round(0.16 * img)), int(round(0.84 * img))
    cfg = f"""
[calibration]
file = "calib.yml"
format = "opencv_yaml"

[sequence]
left = "L_*.png"
right = "R_*.png"

[roi]
xmin = {lo}
xmax = {hi}
ymin = {lo}
ymax = {hi}

[matching]
strategy = "track_both"
winsize = 32
winstepsize = 16

[output]
dir = "out"
prefix = "{prefix}"
"""
    path = Path(out_dir) / "config.toml"
    path.write_text(cfg.strip() + "\n", encoding="utf-8")
    return path
