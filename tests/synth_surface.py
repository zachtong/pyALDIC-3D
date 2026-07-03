"""Non-planar synthetic stereo ground-truth generator (Phase 2 item 5).

A curved (Gaussian-bump) surface undergoes a KNOWN 3D Lagrangian displacement
field (in-plane biaxial stretch + growing out-of-plane bulge), viewed by two
distorted, converging cameras. Because the surface is non-planar, images cannot
be produced by a plane homography — each (camera, frame) is rendered by a genuine
**fixed-point-iteration Lagrangian warp** in image space (the stereo analogue of
the 2D practice ``xi_{n+1} = x - u(xi_n)``), projectively consistent across views.

Ground truth is analytic/forward-only (project ``X_k(material)`` through each
camera), independent of the iterative renderer and of the tracker under test.

NOT collected by pytest (no ``test_`` prefix).
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates

from al_dic_3d.calibration import CameraIntrinsics, StereoRig, project_points

FX = FY = 1500.0
Z0 = 800.0
BUMP_AMP = 35.0  # surface relief (mm)
BUMP_SIGMA = 45.0  # surface bump width (mm)
DEF_SIGMA = 50.0  # out-of-plane deformation bulge width (mm)
DIST_L = dict(k1=-0.15, k2=0.05, p1=0.0005, p2=-0.0003)
DIST_R = dict(k1=-0.12, k2=0.04, p1=-0.0004, p2=0.0006)

# Texture <-> material-parameter mapping: (a, b) in mm -> texture pixel.
_MAT_LO, _MAT_HI = -140.0, 140.0


def _speckle(res: int, seed: int, sigma: float = 3.0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    f = gaussian_filter(rng.standard_normal((res, res)), sigma=sigma, mode="nearest")
    f -= f.min()
    f /= f.max()
    return 20.0 + 215.0 * f


def _cameras(img: int):
    c = (img - 1) / 2.0
    th = np.deg2rad(18.0)
    R = np.array(
        [[np.cos(th), 0, np.sin(th)], [0, 1, 0], [-np.sin(th), 0, np.cos(th)]], dtype=np.float64
    )
    T = np.array([-Z0 * np.sin(th), 0.0, Z0 * (1.0 - np.cos(th))], dtype=np.float64)
    intr_L = CameraIntrinsics(fx=FX, fy=FY, cx=c, cy=c, width=img, height=img, **DIST_L)
    intr_R = CameraIntrinsics(fx=FX, fy=FY, cx=c, cy=c, width=img, height=img, **DIST_R)
    rig = StereoRig(cameras={"L": intr_L, "R": intr_R}, extrinsics={("L", "R"): (R, T)})
    return intr_L, intr_R, R, T, rig


def _surface_z(ab: np.ndarray) -> np.ndarray:
    """Reference surface height Z0 + Gaussian bump over material coords (a, b)."""
    r2 = ab[:, 0] ** 2 + ab[:, 1] ** 2
    return Z0 + BUMP_AMP * np.exp(-r2 / (2.0 * BUMP_SIGMA**2))


def _grad_h(ab: np.ndarray) -> np.ndarray:
    """Gradient (dh/da, dh/db) of the surface bump (for the ray-Newton step)."""
    r2 = ab[:, 0] ** 2 + ab[:, 1] ** 2
    g = BUMP_AMP * np.exp(-r2 / (2.0 * BUMP_SIGMA**2))
    return np.column_stack([-g * ab[:, 0] / BUMP_SIGMA**2, -g * ab[:, 1] / BUMP_SIGMA**2])


def _X_ref(ab: np.ndarray) -> np.ndarray:
    return np.column_stack([ab[:, 0], ab[:, 1], _surface_z(ab)])


def _displacement(ab: np.ndarray, k: int, deform: float) -> np.ndarray:
    """Known cumulative Lagrangian 3D displacement U_k(a, b) at frame k."""
    r2 = ab[:, 0] ** 2 + ab[:, 1] ** 2
    bulge = np.exp(-r2 / (2.0 * DEF_SIGMA**2))
    ex, ey, w = 0.012 * deform, -0.006 * deform, 6.0 * deform
    return k * np.column_stack([ex * ab[:, 0], ey * ab[:, 1], w * bulge])


def _X_k(ab: np.ndarray, k: int, deform: float) -> np.ndarray:
    return _X_ref(ab) + _displacement(ab, k, deform)


def _cam_center(R: np.ndarray, T: np.ndarray) -> np.ndarray:
    return -R.T @ T


def _back_project(
    pixels: np.ndarray, intr: CameraIntrinsics, R: np.ndarray, T: np.ndarray, iters: int = 12
) -> np.ndarray:
    """Reference back-projection R_C: pixel -> material (a, b) on the reference surface.

    Intersects each undistorted ray with the height-field Z = Z0 + h(a, b) by Newton
    iteration on the ray parameter (a genuine ray-vs-curved-surface solve).
    """
    pts = np.ascontiguousarray(pixels, np.float64).reshape(-1, 1, 2)
    crit = (cv2.TERM_CRITERIA_COUNT | cv2.TERM_CRITERIA_EPS, 40, 1e-12)
    xn = cv2.undistortPoints(pts, intr.K, intr.dist_coeffs, R=None, P=None, criteria=crit).reshape(
        -1, 2
    )
    dir_cam = np.column_stack([xn, np.ones(len(xn))])
    dW = dir_cam @ R  # ray direction in world (R^T @ dir_cam, row-wise)
    cc = _cam_center(R, T)

    t = (Z0 - cc[2]) / dW[:, 2]  # planar guess at Z0
    for _ in range(iters):
        pos = cc[None, :] + t[:, None] * dW
        ab = pos[:, :2]
        g = pos[:, 2] - _surface_z(ab)
        gh = _grad_h(ab)
        gp = dW[:, 2] - (gh[:, 0] * dW[:, 0] + gh[:, 1] * dW[:, 1])
        t = t - g / gp
    pos = cc[None, :] + t[:, None] * dW
    return pos[:, :2]


def _mat_to_tex(ab: np.ndarray, res: int) -> np.ndarray:
    s = (res - 1) / (_MAT_HI - _MAT_LO)
    return (ab - _MAT_LO) * s  # (n, 2) texture (col, row)=(a, b) scaled


def _render(texture: np.ndarray, img: int, intr, R, T, k, deform, iters: int = 6) -> np.ndarray:
    """Render one (camera, frame) via image-space fixed-point Lagrangian warp."""
    uu, vv = np.meshgrid(np.arange(img, dtype=np.float64), np.arange(img, dtype=np.float64))
    p = np.column_stack([uu.ravel(), vv.ravel()])  # (N, 2) target pixels

    q = p.copy()  # corrected reference-pixel estimate
    ab = _back_project(q, intr, R, T)
    for _ in range(iters):
        img_def = project_points(_X_k(ab, k, deform), intr, R, T)
        img_ref = project_points(_X_ref(ab), intr, R, T)
        delta = img_def - img_ref  # image-space displacement of this material point
        q = p - delta
        ab = _back_project(q, intr, R, T)

    res = texture.shape[0]
    tex = _mat_to_tex(ab, res)
    vals = map_coordinates(texture, [tex[:, 1], tex[:, 0]], order=1, mode="constant", cval=0.0)
    return vals.reshape(img, img)


def _u16(x: np.ndarray) -> np.ndarray:
    return np.clip(x * 256.0, 0, 65535).astype(np.uint16)


def _write_calib(path: Path, intr_L, intr_R, R, T) -> None:
    fs = cv2.FileStorage(str(path), cv2.FILE_STORAGE_WRITE)
    fs.write("cameraMatrix1", intr_L.K)
    fs.write("distCoeffs1", intr_L.dist_coeffs.reshape(1, -1))
    fs.write("cameraMatrix2", intr_R.K)
    fs.write("distCoeffs2", intr_R.dist_coeffs.reshape(1, -1))
    fs.write("R", R)
    fs.write("T", T.reshape(3, 1))
    fs.release()


def build_surface_scene(
    out_dir: Path, *, img: int = 320, n_frames: int = 5, deform: float = 1.0, seed: int = 7
) -> dict:
    """Render the non-planar dataset to disk; return a scene dict for GT + config."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    intr_L, intr_R, R, T, rig = _cameras(img)
    texture = _speckle(res=1400, seed=seed)

    for k in range(n_frames):
        cv2.imwrite(
            str(out_dir / f"L_{k:03d}.png"),
            _u16(_render(texture, img, intr_L, np.eye(3), np.zeros(3), k, deform)),
        )
        cv2.imwrite(
            str(out_dir / f"R_{k:03d}.png"), _u16(_render(texture, img, intr_R, R, T, k, deform))
        )

    _write_calib(out_dir / "calib.yml", intr_L, intr_R, R, T)
    return {
        "dir": out_dir,
        "img": img,
        "n_frames": n_frames,
        "deform": deform,
        "intr_L": intr_L,
        "intr_R": intr_R,
        "R": R,
        "T": T,
        "rig": rig,
    }


def gt_tracks(scene: dict, ref_coords: np.ndarray) -> dict:
    """Analytic ground truth for the runner's left mesh nodes (pixels in L1)."""
    intr_L, intr_R, R, T = scene["intr_L"], scene["intr_R"], scene["R"], scene["T"]
    deform, nf = scene["deform"], scene["n_frames"]
    material = _back_project(ref_coords, intr_L, np.eye(3), np.zeros(3))  # (n, 2) labels
    n = ref_coords.shape[0]
    world = np.empty((nf, n, 3))
    xL = np.empty((nf, n, 2))
    xR = np.empty((nf, n, 2))
    for k in range(nf):
        Xk = _X_k(material, k, deform)
        world[k] = Xk
        xL[k] = project_points(Xk, intr_L, np.eye(3), np.zeros(3))
        xR[k] = project_points(Xk, intr_R, R, T)
    return {"world": world, "displacement": world - world[0][None], "xL": xL, "xR": xR}


def write_config(
    out_dir: Path, scene: dict, *, prefix: str = "surface", strategy: str = "track_both"
) -> Path:
    img = scene["img"]
    lo, hi = int(round(0.18 * img)), int(round(0.82 * img))
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
strategy = "{strategy}"
winsize = 32
winstepsize = 16

[output]
dir = "out"
prefix = "{prefix}"
"""
    path = Path(out_dir) / "config.toml"
    path.write_text(cfg.strip() + "\n", encoding="utf-8")
    return path
