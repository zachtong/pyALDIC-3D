"""R3 — Numba plane-fit kernel: equivalence, fallback, and dispatch tests.

The Numba engine must reproduce the batched-SVD engine (P3.5 reference) to
< 1e-9 across dense grids, NaN-hole patterns, boundary nodes with few
neighbours, rank-deficient windows, and every coordinate mode — with identical
NaN (void) patterns.  When numba is unavailable the dispatcher must fall back
to the batched path silently.
"""

from __future__ import annotations

import numpy as np
import pytest

from al_dic_3d.strain3d import kernels
from al_dic_3d.strain3d.gradients import MIN_NEIGHBORS, _fit_gradients_loop, fit_gradients

pytestmark = pytest.mark.skipif(not kernels.HAS_NUMBA, reason="numba not importable")

VSG = 32.5
EQUIV_TOL = 1e-9  # R3 numerical contract vs the batched-SVD engine


@pytest.fixture(scope="module", autouse=True)
def _warm_jit():
    kernels.warmup()  # never let a timed/first test pay JIT compilation


def _cloud(seed: int = 42, n_side: int = 25):
    """Grid cloud with NaN holes, a disc void, and a rank-deficient stripe."""
    rng = np.random.default_rng(seed)
    ii, jj = np.meshgrid(np.arange(n_side), np.arange(n_side))
    ii, jj = ii.ravel(), jj.ravel()
    ref_2d = np.column_stack([ii * 16.0 + 40.0, jj * 16.0 + 40.0])
    x = (ii - n_side / 2) * 2.0
    y = (jj - n_side / 2) * 2.0
    ref_3d = np.column_stack([x, y, 800.0 + 0.5 * np.sin(x / 10) + rng.normal(0, 0.01, x.size)])
    disp = np.column_stack(
        [
            0.01 * x + rng.normal(0, 1e-4, x.size),
            0.005 * y + rng.normal(0, 1e-4, x.size),
            0.02 * np.cos(y / 8) + rng.normal(0, 1e-4, x.size),
        ]
    )
    disp[rng.random(x.size) < 0.1] = np.nan  # random holes -> boundary nodes
    disp[((ii - n_side * 0.7) ** 2 + (jj - n_side * 0.3) ** 2) < (n_side * 0.12) ** 2] = np.nan
    # Rank-deficient stripe: coincident (x, y) collapses the plane fit and
    # gradient fit -> exercises the degenerate lstsq-fallback in both engines.
    ref_3d[:n_side, :2] = 0.0
    return ref_2d, ref_3d, disp


def _assert_equiv(a: np.ndarray, b: np.ndarray, tol: float = EQUIV_TOL) -> None:
    assert np.array_equal(np.isnan(a), np.isnan(b))  # identical void pattern
    finite = np.isfinite(a)
    if finite.any():
        assert np.max(np.abs(a[finite] - b[finite])) < tol


@pytest.mark.parametrize("coordinate", ["local", "camera0", "specific"])
def test_numba_matches_batched(coordinate):
    rng = np.random.default_rng(7)
    specimen = np.linalg.qr(rng.normal(size=(3, 3)))[0] if coordinate == "specific" else None
    ref_2d, ref_3d, disp = _cloud()
    kw = dict(coordinate=coordinate, specimen_R=specimen)
    batched = fit_gradients(ref_2d, ref_3d, disp, VSG, engine="batched", **kw)
    numba = fit_gradients(ref_2d, ref_3d, disp, VSG, engine="numba", **kw)
    _assert_equiv(batched, numba)
    # And both stay honest against the historical per-node loop.
    loop = _fit_gradients_loop(ref_2d, ref_3d, disp, VSG, **kw)
    _assert_equiv(loop, numba)


def test_numba_matches_batched_specific_without_R_falls_to_local():
    ref_2d, ref_3d, disp = _cloud(seed=3)
    kw = dict(coordinate="specific", specimen_R=None)  # documented local fallback
    _assert_equiv(
        fit_gradients(ref_2d, ref_3d, disp, VSG, engine="batched", **kw),
        fit_gradients(ref_2d, ref_3d, disp, VSG, engine="numba", **kw),
    )


def test_all_invalid_frame_is_all_nan_in_both_engines():
    ref_2d, ref_3d, disp = _cloud()
    disp[:] = np.nan
    for engine in ("batched", "numba"):
        assert np.isnan(fit_gradients(ref_2d, ref_3d, disp, VSG, engine=engine)).all()


def test_min_neighbors_nan_contract_preserved_exactly():
    # 3x3 block (9 nodes = MIN_NEIGHBORS) + one isolated far node: the block
    # fits, the isolated node must stay NaN in BOTH engines.
    ii, jj = np.meshgrid(np.arange(3), np.arange(3))
    ref_2d = np.column_stack([ii.ravel() * 16.0, jj.ravel() * 16.0])
    ref_2d = np.vstack([ref_2d, [900.0, 900.0]])
    rng = np.random.default_rng(0)
    ref_3d = np.column_stack([ref_2d, np.full(len(ref_2d), 800.0)])
    ref_3d[:, 2] += rng.normal(0, 0.01, len(ref_2d))
    disp = rng.normal(0, 0.01, (len(ref_2d), 3))

    batched = fit_gradients(ref_2d, ref_3d, disp, VSG, engine="batched")
    numba = fit_gradients(ref_2d, ref_3d, disp, VSG, engine="numba")
    assert np.isnan(batched[-1]).all() and np.isnan(numba[-1]).all()
    assert np.isfinite(batched[:9]).any()  # the block DID fit (9 >= MIN_NEIGHBORS)
    assert MIN_NEIGHBORS == 9
    _assert_equiv(batched, numba)


def test_collinear_window_takes_identical_lstsq_fallback():
    # All nodes on one image row with coincident (X, Y): plane + gradient fits
    # are rank-deficient -> both engines must return lstsq's min-norm answer.
    n = 12
    ref_2d = np.column_stack([np.arange(n) * 4.0, np.zeros(n)])
    ref_3d = np.zeros((n, 3))
    ref_3d[:, 2] = 800.0 + np.arange(n) * 0.01
    rng = np.random.default_rng(5)
    disp = rng.normal(0, 0.01, (n, 3))
    for coordinate in ("local", "camera0"):
        a = fit_gradients(ref_2d, ref_3d, disp, VSG, coordinate=coordinate, engine="batched")
        b = fit_gradients(ref_2d, ref_3d, disp, VSG, coordinate=coordinate, engine="numba")
        assert np.array_equal(np.isnan(a), np.isnan(b))
        finite = np.isfinite(a)
        if finite.any():  # bit-identical: both took the same per-node fallback
            np.testing.assert_array_equal(a[finite], b[finite])


def test_neighbor_cache_shared_across_engines():
    ref_2d, ref_3d, disp = _cloud(seed=9)
    cache: dict = {}
    a = fit_gradients(ref_2d, ref_3d, disp, VSG, neighbor_cache=cache, engine="numba")
    assert len(cache) == 1
    table = next(iter(cache.values()))
    b = fit_gradients(ref_2d, ref_3d, disp, VSG, neighbor_cache=cache, engine="batched")
    assert next(iter(cache.values())) is table  # one table serves both engines
    _assert_equiv(a, b)


def test_auto_engine_falls_back_to_batched_silently(monkeypatch):
    ref_2d, ref_3d, disp = _cloud(seed=1)
    expected = fit_gradients(ref_2d, ref_3d, disp, VSG, engine="batched")
    monkeypatch.setattr(kernels, "HAS_NUMBA", False)
    got = fit_gradients(ref_2d, ref_3d, disp, VSG)  # default engine="auto"
    np.testing.assert_array_equal(got, expected)  # byte-identical batched result
    with pytest.raises(RuntimeError, match="numba"):
        fit_gradients(ref_2d, ref_3d, disp, VSG, engine="numba")


def test_unknown_engine_rejected():
    ref_2d, ref_3d, disp = _cloud(seed=2)
    with pytest.raises(ValueError, match="engine"):
        fit_gradients(ref_2d, ref_3d, disp, VSG, engine="turbo")


def test_compute_surface_strain_identical_between_engines(monkeypatch):
    # End-to-end: the frame loop (progress + cache) with the numba default vs
    # a monkeypatched numba-free run must agree < 1e-9 with identical NaN.
    from al_dic_3d.matching.contracts import TRACKED
    from al_dic_3d.reconstruct import Reconstruction3D
    from al_dic_3d.strain3d import STRAIN_FIELDS, compute_surface_strain

    ref_2d, ref_3d, disp = _cloud(seed=11)
    points = np.stack([ref_3d, ref_3d + disp, ref_3d + 2 * disp])
    rec = Reconstruction3D(
        points,
        points - points[0][None],
        np.zeros(points.shape[:2]),
        np.full(points.shape[:2], TRACKED, np.uint8),
    )
    ticks: list[float] = []
    with_numba = compute_surface_strain(
        rec, ref_2d, strain_size=5, winstepsize=16, progress_cb=lambda f, m: ticks.append(f)
    )
    assert ticks == pytest.approx([1 / 3, 2 / 3, 1.0])  # progress intact (P3.5)
    monkeypatch.setattr(kernels, "HAS_NUMBA", False)
    without = compute_surface_strain(rec, ref_2d, strain_size=5, winstepsize=16)
    for name in STRAIN_FIELDS:
        _assert_equiv(getattr(with_numba, name), getattr(without, name))
