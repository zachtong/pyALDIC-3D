"""Benchmark the strain3d gradient-fit engines (R3): batched SVD vs Numba.

Times :func:`al_dic_3d.strain3d.gradients.fit_gradients` over synthetic frame
sequences that mirror the production path of ``compute_surface_strain``: one
shared neighbour cache per run, a FIXED validity pattern with NaN holes
(random dropouts + a disc hole), displacement evolving per frame.  The Numba
JIT is ALWAYS warmed before timing (2D-engine lesson: never time compilation).

Usage:
    python tools/bench_strain3d.py [--engines batched numba] [--repeat 3]

Reports per case: total seconds, ms/frame, speedup vs batched, and the
cross-engine max|delta| + NaN-pattern equality (equivalence evidence).
"""

from __future__ import annotations

import argparse
import time

import numpy as np

from al_dic_3d.strain3d import kernels
from al_dic_3d.strain3d.gradients import fit_gradients

VSG_RADIUS = 32.5  # strain_size=5, winstepsize=16 (production default)

# (label, grid side, n frames, coordinate): 2.5k/10k grids + the ~20k x 30
# realistic scale, plus the two non-default coordinate modes at 10k.
CASES = [
    ("50x50 x10 local", 50, 10, "local"),
    ("100x100 x10 local", 100, 10, "local"),
    ("141x141 x30 local", 141, 30, "local"),
    ("100x100 x10 camera0", 100, 10, "camera0"),
    ("100x100 x10 specific", 100, 10, "specific"),
]


def make_case(side: int, n_frames: int, seed: int = 0):
    """Grid nodes + smooth 3D surface + per-frame displacement with NaN holes."""
    rng = np.random.default_rng(seed)
    ii, jj = np.meshgrid(np.arange(side), np.arange(side), indexing="ij")
    ii, jj = ii.ravel(), jj.ravel()
    ref_2d = np.column_stack([ii * 16.0 + 40.0, jj * 16.0 + 40.0])
    x = (ii - side / 2) * 2.0
    y = (jj - side / 2) * 2.0
    ref_3d = np.column_stack([x, y, 800.0 + 0.5 * np.sin(x / 25.0) + 0.3 * np.cos(y / 30.0)])

    invalid = rng.random(ii.size) < 0.05  # random dropouts
    invalid |= ((ii - side * 0.6) ** 2 + (jj - side * 0.35) ** 2) < (side * 0.08) ** 2  # hole
    disps = []
    for k in range(n_frames):
        s = (k + 1) / n_frames
        d = np.column_stack(
            [
                s * (0.01 * x + 0.02 * np.sin(y / 9.0)),
                s * (0.006 * y),
                s * (0.05 * np.cos(x / 11.0)),
            ]
        ) + rng.normal(0, 1e-4, (ii.size, 3))
        d[invalid] = np.nan
        disps.append(d)
    return ref_2d, ref_3d, disps


def run_engine(engine, ref_2d, ref_3d, disps, coordinate, specimen):
    """Time the production-shaped frame loop (fresh neighbour cache included)."""
    cache: dict = {}
    out = []
    t0 = time.perf_counter()
    for d in disps:
        out.append(
            fit_gradients(
                ref_2d,
                ref_3d,
                d,
                VSG_RADIUS,
                coordinate=coordinate,
                specimen_R=specimen,
                neighbor_cache=cache,
                engine=engine,
            )
        )
    return time.perf_counter() - t0, out


def main() -> None:
    default_engines = ["batched", "numba"] if kernels.HAS_NUMBA else ["batched"]
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--engines", nargs="+", default=default_engines)
    ap.add_argument("--repeat", type=int, default=3, help="best-of-N timing")
    args = ap.parse_args()

    if "numba" in args.engines:
        t0 = time.perf_counter()
        kernels.warmup()  # JIT compile / load cache OUTSIDE the timings
        print(f"numba warmup (compile or cache load): {time.perf_counter() - t0:.2f}s")

    header = f"{'case':<22}{'nodes':>7}{'frames':>7}"
    for e in args.engines:
        header += f"{e + ' s':>12}{'ms/frame':>10}"
    if len(args.engines) > 1:
        header += f"{'speedup':>9}{'max|delta|':>12}{'NaN==':>7}"
    print(header)
    print("-" * len(header))

    for label, side, n_frames, coordinate in CASES:
        ref_2d, ref_3d, disps = make_case(side, n_frames)
        specimen = None
        if coordinate == "specific":
            specimen = np.linalg.qr(np.random.default_rng(1).normal(size=(3, 3)))[0]

        times, results = [], []
        for engine in args.engines:
            runs = [
                run_engine(engine, ref_2d, ref_3d, disps, coordinate, specimen)
                for _ in range(args.repeat)
            ]
            best, out = min(runs, key=lambda r: r[0])
            times.append(best)
            results.append(np.stack(out))

        row = f"{label:<22}{side * side:>7}{n_frames:>7}"
        for t in times:
            row += f"{t:>12.3f}{t / n_frames * 1e3:>10.1f}"
        if len(results) > 1:
            a, b = results[0], results[-1]
            nan_eq = bool(np.array_equal(np.isnan(a), np.isnan(b)))
            finite = np.isfinite(a) & np.isfinite(b)
            delta = float(np.max(np.abs(a[finite] - b[finite]))) if finite.any() else 0.0
            row += f"{times[0] / times[-1]:>9.2f}{delta:>12.2e}{'yes' if nan_eq else 'NO':>7}"
        print(row)


if __name__ == "__main__":
    main()
