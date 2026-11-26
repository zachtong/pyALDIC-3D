"""The honesty gate's minimum check.

A subset partly covering a region that decorrelated (an occlusion, a glare, a
lost speckle patch) can still score a passing ZNSSD while IC-GN has converged
up to ~1.5 px away from where that subset correlates best: the solver's fixed
point weights the residual by the REFERENCE image gradient, so the decorrelated
pixels pull it off the score minimum. The gate now also requires the tracked
motion to sit at a minimum of its own score.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.ndimage import gaussian_filter, shift

from al_dic_3d.matching import gate
from al_dic_3d.matching.gate import (
    GATE_MINIMUM_MIN_ZNSSD,
    GATE_MINIMUM_STEP_PX,
    GATE_MINIMUM_TOL_PX,
    gate_by_znssd,
    minimum_shift,
    quadratic_minimum_shift,
)
from al_dic_3d.matching.primitives import _znssd

IMG = 200
WIN = 32
SHIFT = np.array([3.3, -1.7])  # true translation (u, v)


def _stencil_values(fn) -> np.ndarray:
    h = GATE_MINIMUM_STEP_PX
    return np.array([[fn(dx * h, dy * h) for dx, dy in gate._STENCIL]])


def test_an_exact_quadratic_gives_its_minimum():
    s = np.array([0.12, -0.21])
    A = np.array([[1.3, 0.4], [0.4, 0.8]])  # positive definite, tilted

    def q(dx, dy):
        d = np.array([dx, dy]) - s
        return 0.3 + d @ A @ d

    out = quadratic_minimum_shift(_stencil_values(q), GATE_MINIMUM_STEP_PX)
    assert out[0] == pytest.approx(np.hypot(*s), abs=1e-12)


@pytest.mark.parametrize(
    "fn",
    [
        lambda dx, dy: 0.5 + dx * dx - dy * dy,  # saddle
        lambda dx, dy: 0.5 - dx * dx - dy * dy,  # maximum
        lambda dx, dy: 0.7,  # flat
        lambda dx, dy: 0.7 + 1e-14 * (dx * dx + dy * dy),  # curvature at rounding level
    ],
)
def test_no_minimum_is_nan(fn):
    assert np.isnan(quadratic_minimum_shift(_stencil_values(fn), GATE_MINIMUM_STEP_PX)[0])


def test_a_missing_sample_is_nan():
    z9 = _stencil_values(lambda dx, dy: dx * dx + dy * dy)
    z9[0, 2] = np.nan
    assert np.isnan(quadratic_minimum_shift(z9, GATE_MINIMUM_STEP_PX)[0])


def _speckle(seed: int, size: int = IMG) -> np.ndarray:
    rng = np.random.default_rng(seed)
    f = gaussian_filter(rng.standard_normal((size, size)), sigma=2.0, mode="nearest")
    return 20.0 + 215.0 * (f - f.min()) / (f.max() - f.min())


def _nodes() -> np.ndarray:
    g = np.arange(50.0, IMG - 49.0, 20.0)
    xx, yy = np.meshgrid(g, g)
    return np.column_stack([xx.ravel(), yy.ravel()])


def _noisy_pair(noise: float) -> tuple[np.ndarray, np.ndarray]:
    """Reference and a translated copy with heavy noise (passing, not clean, scores)."""
    ref = _speckle(3)
    # ndimage.shift moves content by (dy, dx): x' = x + u
    dfm = shift(ref, (SHIFT[1], SHIFT[0]), order=3, mode="nearest")
    dfm = dfm + np.random.default_rng(4).normal(0.0, noise, dfm.shape)
    return ref, dfm


def _gate(ref, dfm, pts, u, *, minimum_check=True):
    u_accum = np.stack([np.zeros_like(u), u.copy()])
    valid = np.ones((2, len(pts)), dtype=bool)
    z = np.full((2, len(pts)), np.nan)
    s = np.full((2, len(pts)), np.nan)
    gate_by_znssd(
        [ref, dfm], np.ones_like(ref), pts, u_accum, valid, WIN, 1.0,
        workers=1, znssd_out=z, minimum_check=minimum_check, shift_out=s,
    )  # fmt: skip
    return valid[1], z[1], s[1]


def _solve(ref, dfm, pts) -> tuple[np.ndarray, np.ndarray]:
    """The engine's local IC-GN at ``pts`` (what a working tracker ships)."""
    from al_dic_3d.matching.primitives import make_dicpara, match_points

    para = make_dicpara((IMG, IMG), (0, IMG - 1, 0, IMG - 1), winsize=WIN, use_global_step=False)
    u, _, ok = match_points(ref, dfm, pts, np.tile(SHIFT, (len(pts), 1)), para)
    return u, ok


# Noise ~0.35 of the speckle's own std: scores 0.16-0.36, so every node is
# checked (above the floor) yet passes the score tiers on its own.
NOISE = 13.0


@pytest.mark.parametrize("track", ["solver", "truth"])
def test_a_correct_track_on_noisy_images_passes(track):
    ref, dfm = _noisy_pair(NOISE)
    pts = _nodes()
    u = _solve(ref, dfm, pts)[0] if track == "solver" else np.tile(SHIFT, (len(pts), 1))
    valid, z, s = _gate(ref, dfm, pts, u)
    assert (z > GATE_MINIMUM_MIN_ZNSSD).all()  # the check really ran on every node
    assert valid.all()
    assert np.nanmax(s) < GATE_MINIMUM_TOL_PX


def test_a_track_off_the_score_minimum_fails():
    ref, dfm = _noisy_pair(NOISE)
    pts = _nodes()
    u = np.tile(SHIFT + [0.6, -0.45], (len(pts), 1))  # 0.75 px off
    old, z, _ = _gate(ref, dfm, pts, u, minimum_check=False)
    assert old.all() and (z <= gate.GATE_STRONG_FRACTION).all()  # the score alone keeps it
    new, _, s = _gate(ref, dfm, pts, u)
    assert not new.any()
    assert np.nanmin(s) > GATE_MINIMUM_TOL_PX


def test_subsets_straddling_a_decorrelated_region_are_caught():
    """The failure that motivated the check, with the engine's own solve."""
    ref, dfm = _noisy_pair(2.0)
    y0 = x0 = 100
    dfm[y0:, x0:] = _speckle(11)[y0:, x0:]  # a quarter of the image decorrelates
    # Nodes 10-12 px from its edge: 4-6 px of each 33 px subset lie inside it.
    edge = np.array(
        [[x0 - d, y] for d in (10.0, 12.0) for y in range(116, 172, 4)]
        + [[x, y0 - d] for d in (10.0, 12.0) for x in range(116, 172, 4)]
    )
    u, ok = _solve(ref, dfm, edge)
    pulled = ok & (np.linalg.norm(u - SHIFT, axis=1) > 0.5)
    old, _, _ = _gate(ref, dfm, edge[ok], u[ok], minimum_check=False)
    new, _, _ = _gate(ref, dfm, edge[ok], u[ok])
    kept_old = int((old & pulled[ok]).sum())
    kept_new = int((new & pulled[ok]).sum())
    assert kept_old >= 5, "test geometry: the score alone should keep several pulled nodes"
    assert kept_new <= kept_old // 5  # the check rejects at least 80 % of them


def test_clean_nodes_are_not_checked_at_all(monkeypatch):
    ref, dfm = _noisy_pair(0.5)
    pts = _nodes()
    calls = []
    real = gate.minimum_shift

    def spy(*a, **k):
        calls.append(int(a[4].sum()))
        return real(*a, **k)

    monkeypatch.setattr(gate, "minimum_shift", spy)
    valid, z, s = _gate(ref, dfm, pts, np.tile(SHIFT, (len(pts), 1)))
    assert valid.all() and (z <= GATE_MINIMUM_MIN_ZNSSD).all()
    assert not calls and np.isnan(s).all()


def test_the_tolerance_grows_with_the_subset_uncertainty():
    from al_dic_3d.matching.gate import GATE_MINIMUM_SIGMAS, minimum_tolerance

    curv = np.array([0.2, 0.2, 0.2])
    tol = minimum_tolerance(np.array([0.01, 0.6, 0.6]), np.array([1089, 1089, 289]), curv)
    assert tol[0] == GATE_MINIMUM_TOL_PX  # a clean subset: the floor
    sigma = np.sqrt(2 * 0.6 / (np.array([1089, 289]) * 0.2))
    np.testing.assert_allclose(tol[1:], GATE_MINIMUM_SIGMAS * sigma)
    assert tol[2] > tol[1]  # a smaller subset locates its minimum less precisely


def _bowl_score(centre_affine, centre_zero, *, zero_untestable=False):
    """A fake gate score: a quadratic bowl whose centre depends on the warp.

    With ``zero_untestable`` the translation-only warp scores NaN on pixel
    counts that change with the shift (a subset losing support).
    """

    def score(u, f2d, sel, counts_out=None):
        zero = ~f2d.any(axis=1)
        c = np.where(zero[:, None], centre_zero, centre_affine)
        z = 0.3 + 0.1 * ((u - c) ** 2).sum(axis=1)
        cnt = np.full(len(u), 1000)
        if zero_untestable:
            z = np.where(zero, np.nan, z)
            cnt = np.where(zero, 900 + np.round(10 * u[:, 0]).astype(int), cnt)
        if counts_out is not None:
            counts_out[sel] = cnt[sel]
        return np.where(sel, z, np.nan)

    return score


def test_a_corrupted_gradient_cannot_fail_a_node_at_its_translation_minimum():
    u = np.zeros((1, 2))
    grad = np.array([[0.2, 0.0, 0.0, 0.1]])  # corrupted by bad neighbours
    score = _bowl_score(np.array([0.9, 0.0]), np.array([0.0, 0.0]))
    z = score(u, grad, np.ones(1, bool))
    off, shift = gate._off_minimum(score, u, grad, z, np.ones(1, bool))
    assert not off[0] and shift[0] == pytest.approx(0.0, abs=1e-9)


def test_an_untestable_retry_does_not_rescue_a_failed_node():
    u = np.zeros((1, 2))
    grad = np.array([[0.2, 0.0, 0.0, 0.1]])
    score = _bowl_score(np.array([0.9, 0.0]), np.array([0.0, 0.0]), zero_untestable=True)
    z = score(u, grad, np.ones(1, bool))
    off, _ = gate._off_minimum(score, u, grad, z, np.ones(1, bool))
    assert off[0]


def test_a_subset_running_off_the_image_keeps_its_score_verdict():
    """Shifting such a subset changes which pixels it scores, so it is not tested."""
    ref, dfm = _noisy_pair(NOISE)
    pts = np.array([[100.0, 100.0], [IMG - 5.0, 100.0]])  # the second runs off at +x
    u = np.tile(SHIFT + [0.6, -0.45], (2, 1))  # both 0.75 px off

    def score(u_k, f2d, sel, counts_out=None):
        return _znssd(ref, dfm, pts, u_k, f2d, WIN, sel, np.ones_like(ref), counts_out=counts_out)

    zeros_f = np.zeros((2, 4))
    z = score(u, zeros_f, np.ones(2, bool))
    _, _, testable = minimum_shift(score, u, zeros_f, z, np.ones(2, bool))
    assert testable.tolist() == [True, False]
    old, _, _ = _gate(ref, dfm, pts, u, minimum_check=False)
    new, _, _ = _gate(ref, dfm, pts, u)
    assert old.all()
    assert new.tolist() == [False, True]
