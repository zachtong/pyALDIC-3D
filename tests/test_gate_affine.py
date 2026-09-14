"""Deformation-aware honesty gate (fix batch V, finding H1).

The gate used to compare the frame-0 subset with frame k under a pure
translation, so a CORRECT track scored a high ZNSSD once the subset itself
deformed (~12% strain upward) and was deleted. It now warps with the local
gradient of the tracked field and keeps the better of the affine and
translation scores.
"""

from __future__ import annotations

import cv2
import numpy as np
import pytest
from scipy.ndimage import gaussian_filter

from al_dic_3d.matching.gate import NeighbourIndex, gate_by_znssd, node_gradients

IMG = 256
WIN = 32


def _speckle(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    f = gaussian_filter(rng.standard_normal((IMG, IMG)), sigma=2.0, mode="nearest")
    return 20.0 + 215.0 * (f - f.min()) / (f.max() - f.min())


def _grid(step: int = 16, margin: int = 48) -> np.ndarray:
    g = np.arange(margin, IMG - margin + 1, step, dtype=np.float64)
    xx, yy = np.meshgrid(g, g)
    return np.column_stack([xx.ravel(), yy.ravel()])


def _stretch(img: np.ndarray, ex: float) -> tuple[np.ndarray, callable]:
    """Deformed image for x' = c + (1 + ex)(x - c) (uniaxial, about the centre)."""
    c = (IMG - 1) / 2.0
    yy, xx = np.mgrid[0:IMG, 0:IMG].astype(np.float32)
    map_x = (c + (xx - c) / (1.0 + ex)).astype(np.float32)  # inverse map
    g = cv2.remap(img.astype(np.float32), map_x, yy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

    def disp(pts: np.ndarray) -> np.ndarray:
        u = ex * (pts[:, 0] - c)
        return np.column_stack([u, np.zeros_like(u)])

    return g.astype(np.float64), disp


def test_node_gradients_recover_a_linear_field_exactly():
    ref = _grid()
    A = np.array([[0.12, -0.03], [0.05, 0.2]])  # [[du/dx, du/dy], [dv/dx, dv/dy]]
    u = ref @ A.T + np.array([3.0, -1.0])
    g = node_gradients(ref, u)
    assert np.allclose(g[:, 0], 0.12) and np.allclose(g[:, 1], 0.05)
    assert np.allclose(g[:, 2], -0.03) and np.allclose(g[:, 3], 0.2)


def test_node_gradients_skip_nan_neighbours_and_isolated_nodes():
    ref = _grid()
    u = ref * 0.1
    u[::3] = np.nan
    g = node_gradients(ref, u, NeighbourIndex(ref))
    finite_rows = np.isfinite(u).all(axis=1)
    assert np.allclose(g[finite_rows][:, 0], 0.1, atol=1e-9)
    lone = np.array([[10.0, 10.0], [200.0, 200.0]])
    assert np.array_equal(node_gradients(lone, np.zeros((2, 2))), np.zeros((2, 4)))


def _run_gate(ref_img, dfm_img, pts, u, *, affine, threshold=0.6):
    u_accum = np.stack([np.zeros_like(u), u.copy()])
    valid = np.ones((2, len(pts)), dtype=bool)
    z = np.full((2, len(pts)), np.nan)
    mask = np.ones_like(ref_img)
    n_gated, stopped = gate_by_znssd(
        [ref_img, dfm_img], mask, pts, u_accum, valid, WIN, threshold,
        affine=affine, znssd_out=z, workers=1,
    )  # fmt: skip
    assert stopped is None
    return n_gated, valid, z


@pytest.mark.parametrize("ex", [0.10, 0.20, 0.30])
def test_affine_gate_keeps_correct_tracks_under_large_strain(ex):
    f = _speckle(1)
    g, disp = _stretch(f, ex)
    pts = _grid()
    u = disp(pts)
    _, valid_aff, z_aff = _run_gate(f, g, pts, u, affine=True)
    assert valid_aff[1].all(), f"affine gate killed {int((~valid_aff[1]).sum())} correct tracks"
    assert np.nanmax(z_aff[1]) < 0.2
    _, valid_tr, _ = _run_gate(f, g, pts, u, affine=False)
    if ex >= 0.3:
        # The old translation-only warp deletes correct tracks at this strain
        # (translation ZNSSD: median 0.49, max 0.79 on this speckle).
        assert (~valid_tr[1]).sum() > 0


def test_affine_gate_still_rejects_uncorrelated_texture():
    f = _speckle(1)
    other = _speckle(2)
    pts = _grid()
    u = np.zeros((len(pts), 2))
    n_gated, valid, _ = _run_gate(f, other, pts, u, affine=True)
    assert not valid[1].any()
    assert n_gated[1] == len(pts)


def test_gate_requires_a_minimum_pixel_support():
    """A subset warped almost entirely off the image cannot pass on a sliver."""
    f = _speckle(1)
    pts = np.array([[128.0, 128.0]])
    u = np.array([[-(128.0 + 14.0), 0.0]])  # lands with only ~2 columns in view
    shifted = np.roll(f, -142, axis=1)
    _, valid, z = _run_gate(f, shifted, pts, u, affine=True)
    assert not valid[1].any() and np.isnan(z[1, 0])


def test_raising_the_threshold_relaxes_the_strong_tier_too(monkeypatch):
    # Fix batch V: the strong tier is a fraction of the threshold, so the GUI's
    # "Tracking check" also relaxes the neighbour-support rule when raised.
    from al_dic_3d.matching import gate

    n = 49
    xs, ys = np.meshgrid(np.arange(20, 90, 10.0), np.arange(20, 90, 10.0))
    coords = np.column_stack([xs.ravel(), ys.ravel()])
    frames = [np.zeros((120, 120)), np.zeros((120, 120))]
    z = np.full(n, 0.7)  # every node scores 0.7: weak at 1.0 (strong <= 0.6)
    monkeypatch.setattr("al_dic_3d.matching.primitives._znssd", lambda *a, **k: z.copy())

    def gated(threshold: float) -> int:
        u = np.zeros((2, n, 2))
        valid = np.ones((2, n), bool)
        kills, _ = gate.gate_by_znssd(
            frames, np.ones((120, 120)), coords, u, valid, 16, threshold, workers=1
        )
        return int(kills[1])

    assert gated(1.0) == n  # no strong neighbour anywhere: all weak nodes fail
    assert gated(1.5) == 0  # strong tier 0.9: every node passes on its own
