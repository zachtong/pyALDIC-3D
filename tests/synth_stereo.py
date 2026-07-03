"""Shared synthetic converging-stereo scene generator for integration tests.

NOT collected by pytest (no ``test_`` prefix). Builds an on-disk dataset — L/R
16-bit PNG sequences of a textured plane under a known in-plane affine motion,
plus an OpenCV-YAML stereo calibration — with analytic ground-truth 3D tracks,
via plane-induced homographies (zero modeling error). Mirrors the geometry of
``test_track_both_e2e.py`` so the CLI/runner path is validated end to end.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from scipy.ndimage import gaussian_filter

IMG = 260
FX = FY = 1400.0
CX = CY = 130.0
Z0 = 800.0


def _speckle(seed: int = 5) -> np.ndarray:
    rng = np.random.default_rng(seed)
    f = gaussian_filter(rng.standard_normal((IMG, IMG)), sigma=2.2, mode="nearest")
    f -= f.min()
    f /= f.max()
    return 20.0 + 215.0 * f


def _K() -> np.ndarray:
    return np.array([[FX, 0, CX], [0, FY, CY], [0, 0, 1]], dtype=np.float64)


def rig_rt() -> tuple[np.ndarray, np.ndarray]:
    """18 deg converging rig (optical axes meet at the plane center)."""
    th = np.deg2rad(18.0)
    R = np.array(
        [[np.cos(th), 0, np.sin(th)], [0, 1, 0], [-np.sin(th), 0, np.cos(th)]],
        dtype=np.float64,
    )
    T = np.array([-Z0 * np.sin(th), 0.0, Z0 * (1.0 - np.cos(th))], dtype=np.float64)
    return R, T


def _homographies(R: np.ndarray, T: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    K = _K()
    h_wl = K @ np.diag([1.0, 1.0, Z0])
    h_wr = K @ np.column_stack([R[:, 0], R[:, 1], Z0 * R[:, 2] + T])
    return h_wl, h_wr


def _affine_k(k: int) -> np.ndarray:
    a = 1.0 + 0.0006 * k
    tx, ty = 0.30 * k, 0.15 * k
    return np.array([[a, 0, tx], [0, a, ty], [0, 0, 1]], dtype=np.float64)


def _apply(M: np.ndarray, pts: np.ndarray) -> np.ndarray:
    ph = np.column_stack([pts, np.ones(len(pts))])
    q = ph @ M.T
    return q[:, :2] / q[:, 2:3]


def _warp(img: np.ndarray, M: np.ndarray) -> np.ndarray:
    return cv2.warpPerspective(
        img, M, (IMG, IMG), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT
    )


def _u16(img: np.ndarray) -> np.ndarray:
    return np.clip(img * 256.0, 0, 65535).astype(np.uint16)


def _write_opencv_yaml(path: Path, R: np.ndarray, T: np.ndarray) -> None:
    fs = cv2.FileStorage(str(path), cv2.FILE_STORAGE_WRITE)
    zeros = np.zeros((1, 5), dtype=np.float64)
    fs.write("cameraMatrix1", _K())
    fs.write("distCoeffs1", zeros)
    fs.write("cameraMatrix2", _K())
    fs.write("distCoeffs2", zeros)
    fs.write("R", R)
    fs.write("T", T.reshape(3, 1))
    fs.release()


def build_scene(out_dir: Path, n_frames: int = 3) -> dict:
    """Write L/R PNG sequences + calib.yml into ``out_dir``; return a scene dict."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    l1 = _speckle()
    R, T = rig_rt()
    h_wl, h_wr = _homographies(R, T)
    h_wl_inv = np.linalg.inv(h_wl)

    for k in range(n_frames):
        m = _affine_k(k)
        cv2.imwrite(str(out_dir / f"L_{k:03d}.png"), _u16(_warp(l1, h_wl @ m @ h_wl_inv)))
        cv2.imwrite(str(out_dir / f"R_{k:03d}.png"), _u16(_warp(l1, h_wr @ m @ h_wl_inv)))

    _write_opencv_yaml(out_dir / "calib.yml", R, T)
    return {
        "dir": out_dir,
        "left_glob": "L_*.png",
        "right_glob": "R_*.png",
        "calib": "calib.yml",
        "n_frames": n_frames,
        "h_wl": h_wl,
        "R": R,
        "T": T,
    }


def gt_world_points(scene: dict, ref_coords: np.ndarray) -> np.ndarray:
    """Analytic ground-truth world points ``(n_frames, n, 3)`` for the given left nodes."""
    world_xy = _apply(np.linalg.inv(scene["h_wl"]), ref_coords)
    nf = scene["n_frames"]
    n = ref_coords.shape[0]
    out = np.empty((nf, n, 3), dtype=np.float64)
    for k in range(nf):
        moved = _apply(_affine_k(k), world_xy)
        out[k] = np.column_stack([moved, np.full(n, Z0)])
    return out


def write_config(
    out_dir: Path, scene: dict, *, roi=(45, 175, 45, 215), prefix: str = "run"
) -> Path:
    """Write a config.toml next to the dataset; return its path."""
    xmin, xmax, ymin, ymax = roi
    cfg = f"""
[calibration]
file = "{scene["calib"]}"
format = "opencv_yaml"

[sequence]
left = "{scene["left_glob"]}"
right = "{scene["right_glob"]}"

[roi]
xmin = {xmin}
xmax = {xmax}
ymin = {ymin}
ymax = {ymax}

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
