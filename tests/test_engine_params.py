"""No-op displacement smoothing is dropped only where it is provably a no-op.

The engine's sparse Gaussian displacement smoothing searches ``0.75 x`` the local
element edge around each node (default ``disp_smoothness``). On the uniform grid
3D builds that ball holds only the node itself, so the smoothing returns its
input bit for bit; :mod:`al_dic_3d.matching.engine_params` then hands the engine
``disp_smoothness = 0`` and the tracks must stay IDENTICAL. On a quadtree-refined
mesh the smoothing really averages and must be kept.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest
from al_dic.core.pipeline import _smooth_disp
from al_dic.utils.region_analysis import precompute_node_regions
from scipy.ndimage import gaussian_filter

import al_dic_3d.matching.temporal as temporal
from al_dic_3d.matching.crack_mesh import cut_mesh_at_barriers
from al_dic_3d.matching.engine_params import disp_smoothing_is_noop, engine_para
from al_dic_3d.matching.primitives import make_dicpara
from al_dic_3d.matching.temporal import build_grid_mesh, temporal_track
from al_dic_3d.run_mesh import build_reference_mesh

cv2 = pytest.importorskip("cv2")

H = W = 240
ROI = (30, W - 30, 30, H - 30)


def _speckle(seed: int = 5) -> np.ndarray:
    rng = np.random.default_rng(seed)
    f = gaussian_filter(rng.standard_normal((H, W)), sigma=2.3, mode="nearest")
    f = (f - f.min()) / (f.max() - f.min())
    return 20.0 + 215.0 * f


def _frames(n: int) -> list[np.ndarray]:
    """Cumulative stretch + shift, growing per frame (identity at frame 0)."""
    f0 = _speckle()
    out = [f0]
    for k in range(1, n):
        a = 1.0 + 0.004 * k
        m = np.array([[a, 0.0, 0.4 * k], [0.0, 1.0 - 0.002 * k, 0.25 * k]], dtype=np.float64)
        out.append(
            cv2.warpAffine(f0, m, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        )
    return out


def _hole_mask() -> np.ndarray:
    yy, xx = np.mgrid[0:H, 0:W]
    mask = np.ones((H, W), dtype=np.float64)
    mask[(yy - H / 2) ** 2 + (xx - W / 2) ** 2 < 22.0**2] = 0.0
    return mask


def _para(mode: str = "accumulative", mask: np.ndarray | None = None):
    return make_dicpara(
        img_size=(H, W),
        roi=ROI,
        winsize=32,
        winstepsize=16,
        reference_mode=mode,
        img_ref_mask=mask,
    )


def _engine_smooth(mesh, para, values, mask=None) -> np.ndarray:
    m = np.ones((H, W)) if mask is None else mask
    regions = precompute_node_regions(np.asarray(mesh.coordinates_fem), m, (H, W))
    return _smooth_disp(values, mesh.coordinates_fem, para, regions, mesh=mesh)


def _field(mesh, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    u = rng.standard_normal(2 * mesh.coordinates_fem.shape[0])
    u[::7] = np.nan  # NaN nodes take the engine's NaN-aware branch
    return u


def test_uniform_grid_smoothing_is_bitwise_noop_in_the_engine():
    para = _para()
    mesh = build_grid_mesh(para, H, W)
    u = _field(mesh)
    out = _engine_smooth(mesh, para, u)
    assert np.array_equal(out, u, equal_nan=True)
    assert disp_smoothing_is_noop(mesh, para)


def test_masked_and_cut_meshes_stay_noop():
    mask = _hole_mask()
    para = _para(mask=mask)
    mesh = build_grid_mesh(para, H, W)
    cut = cut_mesh_at_barriers(mesh, mask)
    trimmed = replace(mesh, elements_fem=mesh.elements_fem[::2])  # any element subset
    for m in (mesh, cut, trimmed):
        u = _field(m, seed=1)
        assert np.array_equal(_engine_smooth(m, para, u, mask), u, equal_nan=True)
        assert disp_smoothing_is_noop(m, para)


def test_refined_mesh_keeps_smoothing_because_it_averages():
    mask = _hole_mask()
    mesh = build_reference_mesh(H, W, ROI, winsize=32, winstepsize=16, refine_inner=True, mask=mask)
    para = _para(mask=mask)
    assert mesh.coordinates_fem.shape[0] > build_grid_mesh(para, H, W).coordinates_fem.shape[0]
    u = _field(mesh, seed=2)
    u[np.isnan(u)] = 0.0
    out = _engine_smooth(mesh, para, u, mask)
    assert not np.array_equal(out, u)  # the engine really smooths here ...
    assert not disp_smoothing_is_noop(mesh, para)  # ... so the guard keeps it
    assert engine_para(para, mesh) is para


def test_guard_rejects_coincident_nodes_and_honours_larger_smoothness():
    para = _para()
    mesh = build_grid_mesh(para, H, W)
    coords = np.asarray(mesh.coordinates_fem).copy()
    coords[1] = coords[0]
    assert not disp_smoothing_is_noop(replace(mesh, coordinates_fem=coords), para)
    # 3 * 500 * 1e-3 = 1.5 node spacings: the neighbours are inside the ball.
    assert not disp_smoothing_is_noop(mesh, replace(para, disp_smoothness=1e-3))
    # Already off, or no global step to run it: nothing to prove.
    assert disp_smoothing_is_noop(mesh, replace(para, disp_smoothness=0.0))
    assert disp_smoothing_is_noop(mesh, replace(para, use_global_step=False))


def test_engine_para_drops_only_disp_smoothness():
    para = _para()
    mesh = build_grid_mesh(para, H, W)
    out = engine_para(para, mesh)
    assert out.disp_smoothness == 0.0
    assert replace(out, disp_smoothness=para.disp_smoothness) == para


def _capture_engine_para(monkeypatch):
    seen = []
    real = temporal.run_aldic

    def spy(para, *a, **k):
        seen.append(para)
        return real(para, *a, **k)

    monkeypatch.setattr(temporal, "run_aldic", spy)
    return seen


def test_temporal_track_hands_the_engine_zero_disp_smoothness(monkeypatch):
    seen = _capture_engine_para(monkeypatch)
    para = _para()
    mesh = build_grid_mesh(para, H, W)
    temporal_track(_frames(2), mesh, para)
    assert seen and seen[0].disp_smoothness == 0.0
    assert para.disp_smoothness > 0.0  # the caller's para is not mutated


@pytest.mark.parametrize(
    ("mode", "masked"),
    [("accumulative", False), ("incremental", False), ("incremental", True)],
)
def test_tracks_identical_with_and_without_the_noop_smoothing(monkeypatch, mode, masked):
    frames = _frames(4)
    mask = _hole_mask() if masked else None
    para = _para(mode, mask)
    mesh = build_grid_mesh(para, H, W)
    masks = [mask] * len(frames) if masked else None

    fast = temporal_track(frames, mesh, para, masks=masks)
    monkeypatch.setattr(temporal, "engine_para", lambda p, m: p)  # engine smoothing ON
    slow = temporal_track(frames, mesh, para, masks=masks)

    assert np.array_equal(fast.u_accum, slow.u_accum, equal_nan=True)
    assert np.array_equal(fast.valid, slow.valid)
    assert np.isfinite(fast.u_accum[-1]).mean() > 0.5
