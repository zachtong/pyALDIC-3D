"""Large-scale synthetic stereo stress dataset generator (batch G4, report-only).

Adapts the math of ``tests/synth_surface.py`` (curved Gaussian-bump surface +
image-space fixed-point Lagrangian warp, analytic ground truth) to
production-scale rectangular images (12-25 Mpx) and hundreds-to-thousands of
frames. The per-pixel fixed-point solve of the test generator is O(W*H) per
frame and unusable at 12 Mpx x 1000+ images, so here the warp is solved on a
COARSE pixel grid (stride ~8 px) and bilinearly upsampled into one
full-resolution ``cv2.remap`` of the speckle texture. The displacement field
is smooth on a >= 50 mm scale (bump sigma), so the coarse solve is exact to
well below 0.01 px at stride 8 — negligible against the DIC noise floor.

Outputs per dataset directory:
    L_%05d.tif / R_%05d.tif   8-bit grayscale TIFFs
    calib.yml                 OpenCV-YAML stereo calibration (mild distortion)
    scene.json                the SceneSpec (analytic GT is derivable from it)
    config.toml               ready-to-run headless pipeline config

Frame rendering is parallelized with a process pool (spawn-safe: each worker
re-derives the deterministic texture from the seed in its initializer).

NOT part of the package and NOT collected by pytest; lives in tools/ per the
G4 stress-test protocol. Run via ``tools/stress_test.py gen``.
"""

from __future__ import annotations

import dataclasses
import json
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from scipy.ndimage import gaussian_filter

from al_dic_3d.calibration import CameraIntrinsics, project_points

# Mild Brown-Conrady distortion (about half of tests/synth_surface.py — the
# pipeline undistorts point coordinates either way; this keeps the path hot
# without dominating the geometry at 4000 px scale).
DIST_L = dict(k1=-0.10, k2=0.03, p1=0.0004, p2=-0.0002)
DIST_R = dict(k1=-0.08, k2=0.025, p1=-0.0003, p2=0.0004)


@dataclass(frozen=True)
class SceneSpec:
    """Everything needed to (re)render the dataset and evaluate analytic GT."""

    width: int = 4000
    height: int = 3000
    n_frames: int = 150
    seed: int = 11
    fov_x_mm: float = 220.0  # field of view at Z0 -> fx = W * z0 / fov_x
    z0_mm: float = 800.0
    conv_deg: float = 18.0  # converging half-rig angle (right camera)
    bump_amp_mm: float = 30.0  # static surface relief
    bump_sigma_mm: float = 60.0
    def_sigma_mm: float = 70.0  # out-of-plane deformation bulge width
    ex_total: float = 0.04  # total in-plane strain (x) at the last frame
    ey_total: float = -0.016
    tx_total_px: float = 70.0  # total in-plane translation, LEFT-image pixels
    ty_total_px: float = 35.0
    w_total_mm: float = 25.0  # total out-of-plane bulge amplitude
    stride: int = 8  # coarse warp-solve grid stride (px)
    speckle_sigma: float = 3.0  # texture-pixel speckle feature scale

    # --- derived helpers ---------------------------------------------------
    @property
    def mm_per_px(self) -> float:
        return self.fov_x_mm / self.width

    @property
    def fx(self) -> float:
        return self.width * self.z0_mm / self.fov_x_mm

    @property
    def tx_total_mm(self) -> float:
        return self.tx_total_px * self.mm_per_px

    @property
    def ty_total_mm(self) -> float:
        return self.ty_total_px * self.mm_per_px


# --- cameras -------------------------------------------------------------


def cameras(spec: SceneSpec):
    """(intr_L, intr_R, R, T): 18-deg converging rig, axes meet at (0,0,z0)."""
    th = np.deg2rad(spec.conv_deg)
    R = np.array(
        [[np.cos(th), 0, np.sin(th)], [0, 1, 0], [-np.sin(th), 0, np.cos(th)]],
        dtype=np.float64,
    )
    T = np.array(
        [-spec.z0_mm * np.sin(th), 0.0, spec.z0_mm * (1.0 - np.cos(th))], dtype=np.float64
    )
    cx, cy = (spec.width - 1) / 2.0, (spec.height - 1) / 2.0
    f = spec.fx
    intr_L = CameraIntrinsics(
        fx=f, fy=f, cx=cx, cy=cy, width=spec.width, height=spec.height, **DIST_L
    )
    intr_R = CameraIntrinsics(
        fx=f, fy=f, cx=cx, cy=cy, width=spec.width, height=spec.height, **DIST_R
    )
    return intr_L, intr_R, R, T


# --- surface + motion (analytic, shared by renderer and GT) ---------------


def _surface_z(spec: SceneSpec, ab: np.ndarray) -> np.ndarray:
    r2 = ab[:, 0] ** 2 + ab[:, 1] ** 2
    return spec.z0_mm + spec.bump_amp_mm * np.exp(-r2 / (2.0 * spec.bump_sigma_mm**2))


def _grad_h(spec: SceneSpec, ab: np.ndarray) -> np.ndarray:
    r2 = ab[:, 0] ** 2 + ab[:, 1] ** 2
    g = spec.bump_amp_mm * np.exp(-r2 / (2.0 * spec.bump_sigma_mm**2))
    s2 = spec.bump_sigma_mm**2
    return np.column_stack([-g * ab[:, 0] / s2, -g * ab[:, 1] / s2])


def _X_ref(spec: SceneSpec, ab: np.ndarray) -> np.ndarray:
    return np.column_stack([ab[:, 0], ab[:, 1], _surface_z(spec, ab)])


def displacement(spec: SceneSpec, ab: np.ndarray, k: int) -> np.ndarray:
    """Cumulative Lagrangian 3D displacement U_k(a, b): stretch + translation + bulge."""
    s = k / max(spec.n_frames - 1, 1)
    r2 = ab[:, 0] ** 2 + ab[:, 1] ** 2
    bulge = np.exp(-r2 / (2.0 * spec.def_sigma_mm**2))
    return np.column_stack(
        [
            s * (spec.ex_total * ab[:, 0] + spec.tx_total_mm),
            s * (spec.ey_total * ab[:, 1] + spec.ty_total_mm),
            s * spec.w_total_mm * bulge,
        ]
    )


def _X_k(spec: SceneSpec, ab: np.ndarray, k: int) -> np.ndarray:
    return _X_ref(spec, ab) + displacement(spec, ab, k)


def _back_project(
    spec: SceneSpec, pixels: np.ndarray, intr: CameraIntrinsics, R: np.ndarray, T: np.ndarray
) -> np.ndarray:
    """pixel -> material (a, b) on the REFERENCE surface (ray-Newton, 12 iters)."""
    pts = np.ascontiguousarray(pixels, np.float64).reshape(-1, 1, 2)
    crit = (cv2.TERM_CRITERIA_COUNT | cv2.TERM_CRITERIA_EPS, 40, 1e-12)
    xn = cv2.undistortPoints(pts, intr.K, intr.dist_coeffs, R=None, P=None, criteria=crit)
    xn = xn.reshape(-1, 2)
    dW = np.column_stack([xn, np.ones(len(xn))]) @ R  # R^T @ dir, row-wise
    cc = -R.T @ T
    t = (spec.z0_mm - cc[2]) / dW[:, 2]
    for _ in range(12):
        pos = cc[None, :] + t[:, None] * dW
        ab = pos[:, :2]
        g = pos[:, 2] - _surface_z(spec, ab)
        gh = _grad_h(spec, ab)
        gp = dW[:, 2] - (gh[:, 0] * dW[:, 0] + gh[:, 1] * dW[:, 1])
        t = t - g / gp
    return (cc[None, :] + t[:, None] * dW)[:, :2]


# --- texture ----------------------------------------------------------------


def _texture_extent(spec: SceneSpec) -> tuple[float, float]:
    """Material half-extents (mm) the texture must cover for both cameras + motion."""
    fov_y = spec.height * spec.mm_per_px
    ext_x = 0.75 * spec.fov_x_mm + abs(spec.tx_total_mm) + 8.0
    ext_y = 0.75 * fov_y + abs(spec.ty_total_mm) + 8.0
    return ext_x, ext_y


def make_texture(spec: SceneSpec) -> tuple[np.ndarray, float, float, float]:
    """(texture, lo_x, lo_y, mm_per_texpx): deterministic speckle over the extent."""
    ext_x, ext_y = _texture_extent(spec)
    tex_mm = 0.9 * spec.mm_per_px  # slightly finer than an image pixel
    res_x = int(np.ceil(2.0 * ext_x / tex_mm)) + 1
    res_y = int(np.ceil(2.0 * ext_y / tex_mm)) + 1
    rng = np.random.default_rng(spec.seed)
    f = rng.standard_normal((res_y, res_x), dtype=np.float32)
    f = gaussian_filter(f, sigma=spec.speckle_sigma, mode="nearest")
    f -= f.min()
    f /= max(f.max(), 1e-9)
    return 20.0 + 215.0 * f, -ext_x, -ext_y, tex_mm


# --- rendering ----------------------------------------------------------------


def _coarse_grid(spec: SceneSpec) -> tuple[np.ndarray, np.ndarray, int, int]:
    """Uniform coarse grid EXACTLY spanning [0, W-1] x [0, H-1] (endpoint-aligned)."""
    nx = int(np.ceil((spec.width - 1) / spec.stride)) + 1
    ny = int(np.ceil((spec.height - 1) / spec.stride)) + 1
    xs = np.linspace(0.0, spec.width - 1.0, nx)
    ys = np.linspace(0.0, spec.height - 1.0, ny)
    return xs, ys, nx, ny


def render_frame(
    spec: SceneSpec,
    texture: np.ndarray,
    tex_lo: tuple[float, float],
    tex_mm: float,
    intr: CameraIntrinsics,
    R: np.ndarray,
    T: np.ndarray,
    k: int,
    iters: int = 5,
) -> np.ndarray:
    """Render one (camera, frame) 8-bit image via the coarse Lagrangian warp."""
    xs, ys, nx, ny = _coarse_grid(spec)
    gx, gy = np.meshgrid(xs, ys)
    p = np.column_stack([gx.ravel(), gy.ravel()])  # coarse target pixels

    q = p.copy()
    ab = _back_project(spec, q, intr, R, T)
    for _ in range(iters):
        img_def = project_points(_X_k(spec, ab, k), intr, R, T)
        img_ref = project_points(_X_ref(spec, ab), intr, R, T)
        q = p - (img_def - img_ref)
        ab = _back_project(spec, q, intr, R, T)

    # material -> texture pixel coordinates, on the coarse grid
    tex_x = ((ab[:, 0] - tex_lo[0]) / tex_mm).astype(np.float32).reshape(ny, nx)
    tex_y = ((ab[:, 1] - tex_lo[1]) / tex_mm).astype(np.float32).reshape(ny, nx)

    # upsample the SMOOTH coarse maps to full resolution (bilinear via remap)
    dx = (spec.width - 1.0) / (nx - 1)
    dy = (spec.height - 1.0) / (ny - 1)
    fx = (np.arange(spec.width, dtype=np.float32) / dx)[None, :].repeat(spec.height, axis=0)
    fy = (np.arange(spec.height, dtype=np.float32) / dy)[:, None].repeat(spec.width, axis=1)
    map_x = cv2.remap(tex_x, fx, fy, cv2.INTER_LINEAR)
    map_y = cv2.remap(tex_y, fx, fy, cv2.INTER_LINEAR)

    img = cv2.remap(texture, map_x, map_y, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    return np.clip(img, 0.0, 255.0).astype(np.uint8)


# --- process-pool workers -------------------------------------------------

_G: dict = {}


def _init_worker(spec_dict: dict, out_dir: str) -> None:
    spec = SceneSpec(**spec_dict)
    texture, lo_x, lo_y, tex_mm = make_texture(spec)
    intr_L, intr_R, R, T = cameras(spec)
    _G.update(
        spec=spec, texture=texture, tex_lo=(lo_x, lo_y), tex_mm=tex_mm,
        intr_L=intr_L, intr_R=intr_R, R=R, T=T, out=Path(out_dir),
    )


def _render_pair(k: int) -> tuple[int, float]:
    t0 = time.perf_counter()
    spec, out = _G["spec"], _G["out"]
    for tag, intr, R, T in (
        ("L", _G["intr_L"], np.eye(3), np.zeros(3)),
        ("R", _G["intr_R"], _G["R"], _G["T"]),
    ):
        path = out / f"{tag}_{k:05d}.tif"
        if path.exists() and path.stat().st_size > 0:
            continue
        img = render_frame(spec, _G["texture"], _G["tex_lo"], _G["tex_mm"], intr, R, T, k)
        cv2.imwrite(str(path), img)
    return k, time.perf_counter() - t0


# --- scene build ---------------------------------------------------------------


def _write_calib(path: Path, spec: SceneSpec) -> None:
    intr_L, intr_R, R, T = cameras(spec)
    fs = cv2.FileStorage(str(path), cv2.FILE_STORAGE_WRITE)
    fs.write("cameraMatrix1", intr_L.K)
    fs.write("distCoeffs1", intr_L.dist_coeffs.reshape(1, -1))
    fs.write("cameraMatrix2", intr_R.K)
    fs.write("distCoeffs2", intr_R.dist_coeffs.reshape(1, -1))
    fs.write("R", R)
    fs.write("T", T.reshape(3, 1))
    fs.release()


def default_roi(spec: SceneSpec, margin_frac: float = 0.12) -> tuple[int, int, int, int]:
    mx, my = int(spec.width * margin_frac), int(spec.height * margin_frac)
    return mx, spec.width - 1 - mx, my, spec.height - 1 - my


def write_config(
    out_dir: Path,
    spec: SceneSpec,
    *,
    winstepsize: int = 16,
    prefix: str = "stress",
    strain: bool = True,
    seed_mode: bool = True,
) -> Path:
    xmin, xmax, ymin, ymax = default_roi(spec)
    seed_lines = ""
    if seed_mode:
        sx, sy = (xmin + xmax) // 2, (ymin + ymax) // 2
        seed_lines = f'init_guess = "seed"\nseed_point = [{sx}, {sy}]\n'
    cfg = f"""
[calibration]
file = "calib.yml"
format = "opencv_yaml"

[sequence]
left = "L_*.tif"
right = "R_*.tif"

[roi]
xmin = {xmin}
xmax = {xmax}
ymin = {ymin}
ymax = {ymax}

[matching]
strategy = "track_both"
winsize = 32
winstepsize = {winstepsize}
stereo_search = 48
{seed_lines}
[strain]
enabled = {str(strain).lower()}
strain_size = 5

[output]
dir = "out"
prefix = "{prefix}"
"""
    path = Path(out_dir) / "config.toml"
    path.write_text(cfg.strip() + "\n", encoding="utf-8")
    return path


def build_scene(
    out_dir: str | Path, spec: SceneSpec, *, workers: int = 6, log=print
) -> dict:
    """Render the dataset (resumable: existing frames are skipped); return stats."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "scene.json").write_text(
        json.dumps(dataclasses.asdict(spec), indent=2), encoding="utf-8"
    )
    _write_calib(out_dir / "calib.yml", spec)

    todo = [
        k
        for k in range(spec.n_frames)
        if not all(
            (out_dir / f"{t}_{k:05d}.tif").exists()
            and (out_dir / f"{t}_{k:05d}.tif").stat().st_size > 0
            for t in ("L", "R")
        )
    ]
    t0 = time.perf_counter()
    if todo:
        log(f"rendering {len(todo)}/{spec.n_frames} frame pairs with {workers} workers ...")
        with ProcessPoolExecutor(
            max_workers=workers,
            initializer=_init_worker,
            initargs=(dataclasses.asdict(spec), str(out_dir)),
        ) as pool:
            done = 0
            for k, dt in pool.map(_render_pair, todo, chunksize=4):
                done += 1
                if done % 25 == 0 or done == len(todo):
                    log(f"  rendered {done}/{len(todo)} (frame {k}, {dt:.2f}s/pair/worker)")
    build_s = time.perf_counter() - t0
    n_bytes = sum(f.stat().st_size for f in out_dir.glob("*.tif"))
    return {
        "n_frames": spec.n_frames,
        "rendered": len(todo),
        "build_s": round(build_s, 1),
        "dataset_gb": round(n_bytes / 1024**3, 2),
    }


# --- analytic ground truth ------------------------------------------------


def gt_tracks(spec: SceneSpec, ref_coords: np.ndarray, frames: list[int]) -> dict:
    """Analytic GT (world + L/R pixels) for LEFT frame-1 pixel nodes, given frames."""
    intr_L, intr_R, R, T = cameras(spec)
    material = _back_project(spec, ref_coords, intr_L, np.eye(3), np.zeros(3))
    out = {"frames": frames, "world": [], "xL": [], "xR": []}
    for k in frames:
        Xk = _X_k(spec, material, k)
        out["world"].append(Xk)
        out["xL"].append(project_points(Xk, intr_L, np.eye(3), np.zeros(3)))
        out["xR"].append(project_points(Xk, intr_R, R, T))
    return out


def load_spec(dataset_dir: str | Path) -> SceneSpec:
    d = json.loads((Path(dataset_dir) / "scene.json").read_text(encoding="utf-8"))
    return SceneSpec(**d)
