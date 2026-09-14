"""Small synthetic ``RunResult`` builders for the export tests (no pipeline run).

A regular node grid seen by both cameras (the right camera is the left one
shifted by a constant disparity), a smoothly varying 3D displacement so every
frame has a non-degenerate colour range, optional strain, and the run metadata
the exporters read (``image_size``, ``run_params``). Fast and deterministic, so
the export tests exercise real rendering without a DIC run.
"""

from __future__ import annotations

import numpy as np

from al_dic_3d.matching.contracts import TRACKED, CorrespondenceSet
from al_dic_3d.reconstruct import Reconstruction3D
from al_dic_3d.runner import RunResult
from al_dic_3d.strain3d.model import STRAIN_FIELDS, StrainResult3D

Z0 = 800.0


def grid_result(
    *,
    nx: int = 9,
    ny: int = 9,
    step: float = 16.0,
    origin: tuple[float, float] = (40.0, 40.0),
    n_frames: int = 3,
    with_strain: bool = True,
    image_size: tuple[int, int] = (200, 200),
    right_shift: tuple[float, float] = (12.0, 0.0),
    run_step: int | None = 16,
    crack_aware: bool = False,
) -> RunResult:
    """A consistent grid ``RunResult``; ``run_step=None`` omits ``run_params``."""
    ii, jj = np.meshgrid(np.arange(nx), np.arange(ny))
    ii, jj = ii.ravel().astype(float), jj.ravel().astype(float)
    ref_2d = np.column_stack([ii * step + origin[0], jj * step + origin[1]])
    n_pts = ref_2d.shape[0]

    xw = (ii - (nx - 1) / 2.0) * 2.0
    yw = (jj - (ny - 1) / 2.0) * 2.0
    ref_3d = np.column_stack([xw, yw, np.full_like(xw, Z0)])
    points = np.empty((n_frames, n_pts, 3))
    for k in range(n_frames):
        disp = np.column_stack([0.01 * k * (ii + 1), 0.02 * k * (jj + 1), 0.005 * k * (ii + jj)])
        points[k] = ref_3d + disp
    displacement = points - points[0][None]
    rec = Reconstruction3D(
        points,
        displacement,
        np.zeros((n_frames, n_pts)),
        np.full((n_frames, n_pts), TRACKED, np.uint8),
    )
    xl = np.stack([ref_2d + k * np.array([0.5, 0.25]) for k in range(n_frames)])
    cs = CorrespondenceSet(
        strategy="track_both",
        xL=xl,
        xR=xl + np.asarray(right_shift, dtype=float),
        quality=np.zeros((n_frames, n_pts)),
        source=np.full((n_frames, n_pts), TRACKED, np.uint8),
    )
    strain = None
    if with_strain:
        rng = np.random.default_rng(3)
        strain = StrainResult3D(
            **{name: rng.normal(1e-3, 2e-4, size=(n_frames, n_pts)) for name in STRAIN_FIELDS}
        )
    meta: dict = {
        "strategy": "track_both",
        "n_frames": n_frames,
        "n_pts": n_pts,
        "image_size": tuple(image_size),
        "crack_aware": bool(crack_aware),
    }
    if run_step is not None:
        meta["run_params"] = {
            "strategy": "track_both",
            "reference_mode": "accumulative",
            "winsize": 32,
            "winstepsize": int(run_step),
            "winsize_min": 8,
            "stereo_search": 48,
            "fft_search": 20,
            "init_guess": "seed",
            "use_global_step": True,
            "admm_max_iter": 3,
            "temporal_gate_znssd": 0.5,
            "stereo_znssd_max": 0.5,
            "stereo_epipolar_max_px": 2.0,
            "roi": [0, image_size[1], 0, image_size[0]],
        }
    return RunResult(
        strategy="track_both",
        ref_coords=ref_2d,
        correspondence=cs,
        reconstruction=rec,
        strain=strain,
        meta=meta,
    )


def write_gray_frames(
    folder, prefix: str, n: int, shape: tuple[int, int], *, dtype=np.uint8, hi: int = 255
) -> list[str]:
    """Write ``n`` speckle-like grayscale frames; returns their paths (sorted)."""
    import cv2

    from al_dic_3d.pathsafe import imwrite_unicode

    rng = np.random.default_rng(5)
    base = cv2.GaussianBlur(rng.uniform(0, 1, shape).astype(np.float32), (0, 0), 1.5)
    base = (base - base.min()) / max(1e-9, float(base.max() - base.min()))
    paths = []
    for k in range(n):
        img = np.roll(base, k, axis=1)
        arr = np.round(img * hi).astype(dtype)
        p = folder / f"{prefix}_{k:03d}.png"
        imwrite_unicode(p, arr)
        paths.append(str(p))
    return paths
