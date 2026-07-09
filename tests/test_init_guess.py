"""Batch F2 — seed-point initial guess + right-camera mask warp (Qt-free layers).

Covers: the seed patch template match (known shift recovered; low-NCC fallback
with a warning), the uniform-``U0`` builder, the mode resolution / auto-fallback,
the draft -> RunConfig -> CorrespondenceConfig wiring incl. TOML and session
round-trips, the seed-driven stereo offset on a synthetic shifted pair, and the
left->right ROI-mask warp (holes preserved; degenerate input falls back).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np
import pytest

from al_dic_3d.matching.seed import (
    match_seed_patch,
    resolve_init_guess,
    uniform_u0,
)
from al_dic_3d.project import AppState3D, ProjectDraft, load_session, save_session

cv2 = pytest.importorskip("cv2")


def _speckle(size: int = 240, seed: int = 3) -> np.ndarray:
    from scipy.ndimage import gaussian_filter

    rng = np.random.default_rng(seed)
    f = gaussian_filter(rng.standard_normal((size, size)), sigma=2.0, mode="nearest")
    f -= f.min()
    return 20.0 + 200.0 * f / f.max()


# --- match_seed_patch ----------------------------------------------------------


def test_seed_patch_recovers_known_shift():
    src = _speckle()
    dx, dy = 23, -11
    dst = np.roll(np.roll(src, dy, axis=0), dx, axis=1)
    shift = match_seed_patch(src, dst, (120.0, 130.0))
    assert shift is not None
    assert shift == pytest.approx((dx, dy), abs=0.5)


def test_seed_patch_near_edge_still_matches():
    src = _speckle()
    dst = np.roll(src, 9, axis=1)
    shift = match_seed_patch(src, dst, (3.0, 5.0))  # template window clamps inside
    assert shift is not None
    assert shift == pytest.approx((9, 0), abs=0.5)


def test_seed_patch_low_ncc_warns_and_returns_none():
    src = _speckle(seed=1)
    noise = _speckle(seed=99)  # independent texture — no true correspondence
    with pytest.warns(UserWarning, match="NCC peak"):
        assert match_seed_patch(src, noise, (120.0, 120.0)) is None


def test_seed_patch_tiny_image_warns_and_returns_none():
    tiny = np.random.default_rng(0).random((12, 12))
    with pytest.warns(UserWarning, match="too small"):
        assert match_seed_patch(tiny, tiny, (6.0, 6.0)) is None


def test_uniform_u0_is_interleaved_uv():
    u0 = uniform_u0(3, (2.5, -1.0))
    assert u0.shape == (6,)
    assert np.allclose(u0[0::2], 2.5) and np.allclose(u0[1::2], -1.0)
    with pytest.raises(ValueError):
        uniform_u0(0, (1.0, 1.0))


# --- mode resolution + strategy helpers -----------------------------------------


def test_resolve_init_guess_fallback_and_validation():
    assert resolve_init_guess("fft", None) == "fft"
    assert resolve_init_guess("previous", None) == "previous"
    assert resolve_init_guess("seed", (10.0, 20.0)) == "seed"
    with pytest.warns(UserWarning, match="falling back to FFT"):
        assert resolve_init_guess("seed", None) == "fft"
    with pytest.raises(ValueError, match="init_guess"):
        resolve_init_guess("bogus", None)


def test_resolve_init_derives_stereo_offset_from_seed():
    from al_dic_3d.matching.contracts import CorrespondenceConfig
    from al_dic_3d.matching.strategies._common import resolve_init

    left = _speckle()
    right = np.roll(left, 30, axis=1)  # uniform 30 px disparity
    cfg = CorrespondenceConfig(init_guess="seed", seed_point=(110.0, 120.0))
    mode, offset = resolve_init(cfg, left, right)
    assert mode == "seed"
    assert offset == pytest.approx((30, 0), abs=0.5)

    # An explicit disparity_offset stays an override (seed match not consulted).
    cfg2 = CorrespondenceConfig(
        init_guess="seed", seed_point=(110.0, 120.0), disparity_offset=(-5.0, 2.0)
    )
    _, offset2 = resolve_init(cfg2, left, right)
    assert offset2 == (-5.0, 2.0)


def test_temporal_u0_per_mode():
    from al_dic_3d.matching.strategies._common import temporal_u0

    f0 = _speckle()
    f1 = np.roll(f0, 6, axis=0)  # 6 px downward motion
    assert temporal_u0("fft", f0, f1, (100.0, 100.0), 5) is None

    zeros = temporal_u0("previous", f0, f1, None, 5)
    assert zeros is not None and zeros.shape == (10,) and not zeros.any()

    seeded = temporal_u0("seed", f0, f1, (100.0, 100.0), 4)
    assert seeded is not None and seeded.shape == (8,)
    assert np.allclose(seeded[0::2], 0.0, atol=0.5)
    assert np.allclose(seeded[1::2], 6.0, atol=0.5)

    # seed mode without a usable point for THIS camera -> engine FFT (None).
    assert temporal_u0("seed", f0, f1, None, 4) is None


# --- config plumbing --------------------------------------------------------------


def _ready_draft(tmp_path: Path) -> ProjectDraft:
    return ProjectDraft(
        calibration_file=tmp_path / "calib.yml",
        left=["L_0.png", "L_1.png"],
        right=["R_0.png", "R_1.png"],
        roi=(10, 100, 10, 100),
    )


def test_draft_defaults_and_build_forwarding(tmp_path):
    d = _ready_draft(tmp_path)
    assert d.init_guess == "seed" and d.seed_point is None  # GUI default: seed
    d.init_guess = "previous"
    d.seed_point = (42.0, 24.0)
    cfg = d.build()
    assert cfg.init_guess == "previous"
    assert cfg.seed_point == (42.0, 24.0)


def test_runconfig_default_is_fft_and_reaches_correspondence_config():
    from al_dic_3d.matching.contracts import CorrespondenceConfig
    from al_dic_3d.runner import RunConfig

    assert RunConfig.__dataclass_fields__["init_guess"].default == "fft"
    assert CorrespondenceConfig().init_guess == "fft"  # headless behavior unchanged


def test_toml_matching_init_guess_round_trip(tmp_path):
    from al_dic_3d.runner import load_config

    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(
        "\n".join(
            [
                "[calibration]",
                'file = "calib.yml"',
                'format = "opencv_yaml"',
                "[sequence]",
                'left = "L_*.png"',
                'right = "R_*.png"',
                "[roi]",
                "xmin = 0",
                "xmax = 10",
                "ymin = 0",
                "ymax = 10",
                "[matching]",
                'init_guess = "seed"',
                "seed_point = [120.5, 88.0]",
            ]
        )
    )
    cfg = load_config(cfg_path)
    assert cfg.init_guess == "seed"
    assert cfg.seed_point == (120.5, 88.0)

    bad = tmp_path / "bad.toml"
    bad.write_text(cfg_path.read_text().replace('"seed"', '"warp9"'))
    with pytest.raises(ValueError, match="init_guess"):
        load_config(bad)


def test_seed_survives_session_round_trip(tmp_path):
    d = _ready_draft(tmp_path)
    d.init_guess = "seed"
    d.seed_point = (77.25, 33.5)
    cfg = d.build()
    state = AppState3D(draft=d, config=cfg)
    loaded = load_session(save_session(state, tmp_path / "p.aldic3d"))
    assert loaded.draft == d  # dataclass equality: seed tuple restored, not a list
    assert loaded.draft.seed_point == (77.25, 33.5)
    assert loaded.config is not None and loaded.config.seed_point == (77.25, 33.5)
    assert loaded.config.init_guess == "seed"


def test_run_pipeline_falls_back_when_seed_missing(tmp_path):
    """init_guess='seed' without a point must WARN and run as FFT, not block."""
    from al_dic_3d.runner import load_config, run_pipeline
    from tests.synth_stereo import build_scene, write_config

    scene = build_scene(tmp_path, n_frames=2)
    cfg = dataclasses.replace(load_config(write_config(tmp_path, scene)), init_guess="seed")
    with pytest.warns(UserWarning, match="falling back to FFT"):
        result = run_pipeline(cfg)
    assert result.correspondence.n_frames == 2


# --- right-camera mask warp (F2.3) ---------------------------------------------


def test_warp_mask_preserves_holes():
    from al_dic_3d.viz3d.maskwarp import warp_mask_left_to_right

    h = w = 200
    # Left mask: solid block with a hole.
    mask_l = np.zeros((h, w), dtype=bool)
    mask_l[40:160, 30:150] = True
    mask_l[90:110, 80:100] = False  # the hole

    # Frame-1 correspondence: uniform shift right by 25 px, down by 5 px.
    gx, gy = np.meshgrid(np.arange(35, 150, 8, dtype=float), np.arange(45, 155, 8, dtype=float))
    xl0 = np.column_stack([gx.ravel(), gy.ravel()])
    xr0 = xl0 + np.array([25.0, 5.0])

    warped = warp_mask_left_to_right(mask_l, xl0, xr0, (h, w))
    assert warped is not None and warped.dtype == bool

    # Inside the correspondence hull the mask follows the shift...
    assert warped[100 + 5, 100 + 25]  # solid region maps True
    # ...the hole is preserved (center of the shifted hole is False)...
    assert not warped[100 + 5, 90 + 25]
    # ...and pixels left of the shifted mask edge are outside.
    assert not warped[100 + 5, 40]


def test_warp_mask_handles_nan_rows_and_degenerate_input():
    from al_dic_3d.viz3d.maskwarp import warp_mask_left_to_right

    mask = np.ones((50, 50), dtype=bool)
    # Too few finite correspondences -> None (caller falls back to F1.5 support).
    xl = np.array([[10.0, 10.0], [np.nan, np.nan], [20.0, 20.0]])
    xr = xl + 2.0
    assert warp_mask_left_to_right(mask, xl, xr, (50, 50)) is None
    # Collinear points -> no 2D mapping -> None (QhullError path).
    xl3 = np.array([[10.0, 10.0], [20.0, 10.0], [30.0, 10.0]])
    assert warp_mask_left_to_right(mask, xl3, xl3 + 1.0, (50, 50)) is None
