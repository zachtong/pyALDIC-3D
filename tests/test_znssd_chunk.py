"""Perf batch P1.3: point-chunked ZNSSD must be bit-identical to monolithic.

Each point's ZNSSD is independent, so evaluating in blocks changes peak memory
(~10x lower at production point counts) but must never change a single bit of
the result — including NaN placement (out-of-bounds / no-support points).
"""

from __future__ import annotations

import numpy as np

from al_dic_3d.matching.primitives import _znssd


def _random_case(seed: int, n: int = 257, hw: int = 96, winsize: int = 16):
    rng = np.random.default_rng(seed)
    ref = rng.uniform(0, 255, size=(hw, hw))
    dfm = rng.uniform(0, 255, size=(hw, hw))
    # Points spread across the image INCLUDING near-border ones (out-of-bounds
    # rows must stay NaN in both evaluations).
    pts = rng.uniform(0, hw - 1, size=(n, 2))
    u = rng.normal(0, 1.5, size=(n, 2))
    f = rng.normal(0, 0.01, size=(n, 4))
    valid = rng.uniform(size=n) > 0.1
    mask = np.ones((hw, hw), dtype=np.float64)
    mask[40:52, 10:30] = 0.0  # a masked hole exercises the support counting
    return ref, dfm, pts, u, f, winsize, valid, mask


def test_chunked_equals_monolithic_bitwise():
    for seed in (0, 1, 2):
        args = _random_case(seed)
        mono = _znssd(*args, chunk=10**9)  # one block == the pre-P1.3 evaluation
        for chunk in (1, 7, 64, 2048):
            out = _znssd(*args, chunk=chunk)
            assert np.array_equal(out, mono, equal_nan=True), (
                f"chunk={chunk} diverged from monolithic (seed={seed})"
            )


def test_default_chunk_is_used_and_finite_somewhere():
    args = _random_case(3)
    out = _znssd(*args)  # default chunk path
    assert out.shape == (args[2].shape[0],)
    assert np.isfinite(out).any()  # sanity: the kernel actually evaluated
