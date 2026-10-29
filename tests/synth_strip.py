"""Narrow speckled strip on a nearly textureless background, translating sideways.

The set-up of issue #1 in miniature: a region of interest drawn on the LEFT
camera only, a static low-texture background (out-of-focus clutter plus sensor
noise) and a specimen that moves rigidly. Built on the analytic stereo rig of
:mod:`al_dic_3d.synthetic` (18 deg convergent pair with lens distortion), so the
ground truth is exact. Used by the right-camera ROI and epipolar-band tests.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter

from al_dic_3d import synthetic as syn
from al_dic_3d.calibration import project_points
from al_dic_3d.pathsafe import imwrite_unicode

PX_PER_MM = syn.FX / syn.Z0


def _material(pw_xy: np.ndarray, shift_mm: float) -> np.ndarray:
    return pw_xy - np.array([shift_mm, 0.0])


def write_strip_dataset(
    out: str | Path,
    *,
    img: int = 384,
    n_frames: int = 3,
    width_px: float = 80.0,
    length_px: float = 260.0,
    shift_px_per_frame: float = 5.0,
    noise: float = 1.0,
    reference_mode: str = "accumulative",
    seed: int = 7,
) -> Path:
    """Write images, calibration, the left ROI mask and a ``config.toml``; return its path."""
    import cv2

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    intr_L, intr_R, R, T, _ = syn.cameras(img)
    half_w, half_l = 0.5 * width_px / PX_PER_MM, 0.5 * length_px / PX_PER_MM
    texture = syn.speckle(img, seed=seed).astype(np.float32)
    rng = np.random.default_rng(seed + 1)
    grid = syn._pixel_grid(img, img)

    def inside(m: np.ndarray) -> np.ndarray:
        return (np.abs(m[:, 0]) <= half_w) & (np.abs(m[:, 1]) <= half_l)

    for i, (cam, intr, Rc, Tc) in enumerate(
        (("L", intr_L, np.eye(3), np.zeros(3)), ("R", intr_R, R, T))
    ):
        pw = syn._backproject(grid, intr, Rc, Tc)[:, :2]
        g = gaussian_filter(np.random.default_rng(100 + i).standard_normal((img, img)), 6.0)
        background = 45.0 + 3.0 * g / g.std()
        for k in range(n_frames):
            m = _material(pw, k * shift_px_per_frame / PX_PER_MM)
            p0 = project_points(syn._on_plane(m), intr_L, np.eye(3), np.zeros(3))
            spk = cv2.remap(
                texture,
                p0[:, 0].reshape(img, img).astype(np.float32),
                p0[:, 1].reshape(img, img).astype(np.float32),
                cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REFLECT,
            )
            frame = np.where(inside(m).reshape(img, img), spk, background)
            frame = frame + rng.normal(0.0, noise, frame.shape)
            imwrite_unicode(
                out / f"{cam}_{k:03d}.png", np.clip(np.round(frame), 0, 255).astype(np.uint8)
            )
        if cam == "L":
            roi = inside(_material(pw, 0.0)).reshape(img, img)
            imwrite_unicode(out / "roi_mask.png", roi.astype(np.uint8) * 255)
    syn._write_calib(out / "calib.yml", intr_L, intr_R, R, T)
    cfg = out / "config.toml"
    cfg.write_text(
        "\n".join(
            [
                "[calibration]",
                'file = "calib.yml"',
                'format = "opencv_yaml"',
                "",
                "[sequence]",
                'left = "L_*.png"',
                'right = "R_*.png"',
                "",
                "[roi]",
                'mask = "roi_mask.png"',
                "",
                "[matching]",
                'strategy = "track_both"',
                f'reference_mode = "{reference_mode}"',
                "winsize = 32",
                "winstepsize = 8",
                'init_guess = "fft"',
                "",
                "[output]",
                'dir = "out"',
                'prefix = "strip"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return cfg
