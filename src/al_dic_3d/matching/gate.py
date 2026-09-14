"""The temporal honesty gate: re-verify every tracked node against frame 0 (Qt-free).

The 2D engine launders per-node failures into finite values (bad IC-GN points are
IDW-refilled, the FEM step is finite everywhere, composition nearest-fills), so
``isfinite`` says nothing about whether a track is right. The gate checks the
shipped quantity itself: the frame-0 subset at ``X`` must still correlate with
frame ``k`` at ``X + U^k``.

Fix batch V made the check deformation-aware. It used to compare the subsets
with a pure translation; under ~12% strain and above a correct track then scores
a high ZNSSD and was deleted (on the Stereo-DIC Challenge 1.0 S3 tension-to-
failure data, 75% of the frame-20 kills were clean tracks). The subset warp now
uses the local displacement gradient of the tracked field itself, estimated by a
least-squares plane fit over each node's neighbours; a node that fails the
affine check is re-scored with the translation-only warp and keeps the better
score, so a gradient corrupted near a crack or a boundary can never make a good
node fail. Subsets are also required to keep a minimum pixel support, so a
subset warped almost entirely off the image cannot pass on a handful of pixels.

The gate is two-tier. A node scoring ``<= GATE_STRONG_FRACTION x threshold``
(0.6 at the default threshold 1.0, i.e. ZNCC >= 0.7) passes on its own. A node
between that and the threshold (ZNCC 0.5 at the default) passes only when its
displacement agrees with a plane fitted to at least
``GATE_MIN_SUPPORT_NEIGHBOURS`` strong neighbours (within
``GATE_SUPPORT_TOL_PX``): on uncorrelated speckle an IC-GN local optimum reaches
ZNCC 0.5 for roughly 2% of nodes, and those isolated false locks carry
displacements tens of pixels off their surroundings, whereas a genuinely
high-strain node sits inside a coherent field. The strong tier scales with the
threshold so that raising the threshold (the GUI's "Tracking check") relaxes
both tiers: on the Stereo-DIC Challenge 1.0 Sample 3 tension-to-failure test
the default keeps 37 % of all nodes in the last frame, where a plain 1.0
threshold would keep 46 % -- the extra 9 % sit in neighbourhoods where no node
correlates strongly any more, which is also what a decorrelated region that
the solver froze on its previous displacement looks like.
"""

from __future__ import annotations

import os
from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray

# Threads used to evaluate the gate's per-frame ZNSSD point chunks. Bounded
# (not cpu_count) because the gate may overlap the sibling camera's engine
# solve, and the kernel turns memory-bound past ~8 threads (12 Mpx, 27k nodes:
# 3.47 s at 1 worker, 1.24 s at 4, 0.93 s at 8). Chunks stay bit-identical at
# any worker count.
_GATE_MAX_WORKERS = 8

# Minimum fraction of the full (winsize+1)^2 subset that must remain valid
# (in image, in mask, finite deformed sample) for a gate score to count.
GATE_MIN_SUPPORT = 0.25

# Neighbours used for the per-node gradient fit (the node itself included).
_GRAD_K = 9

# Two-tier gate (see module docstring): the strong tier is this fraction of
# the threshold (0.6 at the default threshold 1.0).
GATE_STRONG_FRACTION = 0.6
GATE_STRONG_ZNSSD = GATE_STRONG_FRACTION * 1.0  # the default, kept for reference
GATE_MIN_SUPPORT_NEIGHBOURS = 3
GATE_SUPPORT_TOL_PX = 1.0


def _gate_workers() -> int:
    """Thread count for the gate's ZNSSD chunks — leaves headroom for the OS."""
    return min(_GATE_MAX_WORKERS, max(1, (os.cpu_count() or 1) - 2))


class NeighbourIndex:
    """k-nearest-neighbour stencil of fixed mesh nodes, built once per track.

    ``idx[i]`` lists the ``_GRAD_K`` nearest nodes of node ``i`` (itself first);
    ``usable`` drops stencil members further than twice the node's own nearest-
    neighbour distance, so a stencil never reaches across a hole or an element
    size jump on a quadtree-refined mesh.
    """

    def __init__(self, ref_coords: NDArray[np.float64]) -> None:
        from scipy.spatial import cKDTree

        c = np.asarray(ref_coords, dtype=np.float64).reshape(-1, 2)
        self.coords = c
        n = c.shape[0]
        k = min(_GRAD_K, n)
        if k < 3:
            self.idx = np.zeros((n, 0), dtype=np.int64)
            self.usable = np.zeros((n, 0), dtype=bool)
            return
        dist, idx = cKDTree(c).query(c, k=k)
        d1 = dist[:, 1:2] if k > 1 else np.ones((n, 1))
        self.idx = idx.astype(np.int64)
        self.usable = dist <= 2.0 * np.maximum(d1, 1e-12)


def _plane_fit(
    st: NeighbourIndex,
    u: NDArray[np.float64],
    weights: NDArray[np.bool_],
    min_count: int = 3,
) -> tuple[NDArray[np.float64], NDArray[np.bool_]]:
    """Least-squares ``u = a + b dx + c dy`` per node over its weighted stencil.

    ``weights`` is ``(n, k)`` over ``st.idx``. Returns ``(theta (n, 3, 2),
    solvable (n,))``; ``theta[:, 0]`` is the plane's value AT the node (the
    stencil is centred on it), ``theta[:, 1:]`` the gradient. Nodes with fewer
    than ``min_count`` members or a degenerate (collinear) stencil are not
    solvable.
    """
    c = st.coords
    n = c.shape[0]
    theta = np.zeros((n, 3, 2), dtype=np.float64)
    nb = st.idx
    w = weights & st.usable
    enough = w.sum(axis=1) >= min_count
    if not enough.any():
        return theta, enough
    uu = np.asarray(u, dtype=np.float64).reshape(n, 2)
    dx = c[nb, 0] - c[:, None, 0]  # (n, k) centred on the node
    dy = c[nb, 1] - c[:, None, 1]
    A = np.stack([np.ones_like(dx), dx, dy], axis=2) * w[..., None]  # (n, k, 3)
    b = np.nan_to_num(uu[nb]) * w[..., None]  # (n, k, 2)
    ata = np.einsum("nki,nkj->nij", A, A)
    atb = np.einsum("nki,nkj->nij", A, b)
    det = np.linalg.det(ata)
    scale = np.einsum("nii->n", ata) ** 3 + 1e-30
    solvable = enough & (np.abs(det) > 1e-9 * scale)
    if solvable.any():
        theta[solvable] = np.linalg.solve(ata[solvable], atb[solvable])
    return theta, solvable


def node_gradients(
    ref_coords: NDArray[np.float64],
    u: NDArray[np.float64],
    stencil: NeighbourIndex | None = None,
) -> NDArray[np.float64]:
    """Per-node displacement gradient in the engine's warp layout.

    Returns ``(n, 4)`` columns ``[du/dx, dv/dx, du/dy, dv/dy]`` (the ``f_2d`` layout
    :func:`al_dic_3d.matching.primitives._znssd` warps with). Each node fits
    ``u = a + b x + c y`` by least squares over its finite stencil members;
    nodes with fewer than 3 usable finite neighbours, or a degenerate
    (collinear) stencil, get a zero gradient -- the translation-only warp.
    """
    st = stencil if stencil is not None else NeighbourIndex(ref_coords)
    n = st.coords.shape[0]
    out = np.zeros((n, 4), dtype=np.float64)
    if st.idx.shape[1] < 3:
        return out
    uu = np.asarray(u, dtype=np.float64).reshape(n, 2)
    theta, solvable = _plane_fit(st, uu, np.isfinite(uu[st.idx]).all(axis=2))
    out[solvable, 0] = theta[solvable, 1, 0]  # du/dx
    out[solvable, 1] = theta[solvable, 1, 1]  # dv/dx
    out[solvable, 2] = theta[solvable, 2, 0]  # du/dy
    out[solvable, 3] = theta[solvable, 2, 1]  # dv/dy
    return out


def neighbour_supported(
    u: NDArray[np.float64],
    strong: NDArray[np.bool_],
    candidates: NDArray[np.bool_],
    stencil: NeighbourIndex,
    *,
    min_neighbours: int = GATE_MIN_SUPPORT_NEIGHBOURS,
    tol_px: float = GATE_SUPPORT_TOL_PX,
) -> NDArray[np.bool_]:
    """Candidates whose displacement matches a plane fit to their STRONG neighbours.

    The node itself is excluded from its own fit. Returns ``(n,)`` bool, True
    only for candidate nodes with at least ``min_neighbours`` strong stencil
    members and a displacement within ``tol_px`` of the fitted plane's value.
    """
    n = stencil.coords.shape[0]
    out = np.zeros(n, dtype=bool)
    if stencil.idx.shape[1] < 3 or not candidates.any():
        return out
    uu = np.asarray(u, dtype=np.float64).reshape(n, 2)
    w = strong[stencil.idx].copy()
    w[:, 0] = False  # stencil column 0 is the node itself
    theta, solvable = _plane_fit(stencil, uu, w, min_count=min_neighbours)
    ok = candidates & solvable
    resid = np.linalg.norm(uu - theta[:, 0, :], axis=1)
    out[ok] = resid[ok] <= tol_px
    return out


def gate_by_znssd(
    frames,
    mask0: NDArray[np.float64],
    ref_coords: NDArray[np.float64],
    u_accum: NDArray[np.float64],
    valid: NDArray[np.bool_],
    winsize: int,
    threshold: float,
    *,
    progress: Callable[[float, str], None] | None = None,
    stop: Callable[[], bool] | None = None,
    workers: int | None = None,
    affine: bool = True,
    min_support: float = GATE_MIN_SUPPORT,
    znssd_out: NDArray[np.float64] | None = None,
) -> tuple[NDArray[np.int64], int | None]:
    """Invalidate (in place) tracked nodes whose frame-0 -> frame-k correlation fails.

    Catches both silent failure shapes seen on real data: an accumulative
    sibling warm-start freeze (IC-GN "converges" with a zero update on a
    decorrelated pattern) and incremental garbage increments faithfully
    composed into the cumulative field.

    Args:
        affine: warp the frame-0 subset with the local gradient of ``u_accum[k]``
            (default). Nodes failing that check are re-scored with the
            translation-only warp and keep the lower ZNSSD. ``False`` restores
            the translation-only gate.
        min_support: minimum fraction of the full subset that must stay valid.
        znssd_out: optional ``(n_frames, n)`` array receiving each verified
            node's final ZNSSD (NaN where not verified).
        progress: receives ``(k / n_deformed, "verifying frame k/N")`` per frame.
        stop: polled AFTER each verified frame, so a cancel costs at most one
            more frame and every frame reported as tracked was verified.
        workers: threads for the per-frame point chunks (bit-identical).

    Returns:
        ``(n_gated, stopped_at)``: per-frame kill counts, and the 0-based index of
        the first frame never verified (``None`` when all were verified) — the
        caller drops those frames rather than shipping them unverified.
    """
    from al_dic_3d.matching.primitives import _znssd, spline_coefficients

    ref = np.ascontiguousarray(frames[0], dtype=np.float64)
    n = ref_coords.shape[0]
    zeros_f = np.zeros((n, 4), dtype=np.float64)
    n_frames = u_accum.shape[0]
    n_deformed = max(1, n_frames - 1)
    n_gated = np.zeros(n_frames, dtype=np.int64)
    threads = _gate_workers() if workers is None else max(1, int(workers))
    min_count = int(np.ceil(min_support * (winsize + 1) ** 2)) if min_support > 0 else 0
    stencil = NeighbourIndex(ref_coords) if affine else None
    stopped_at: int | None = None
    for k in range(1, n_frames):
        pre = valid[k].copy()
        verified = pre.any()
        if verified:
            dfm = np.ascontiguousarray(frames[k], dtype=np.float64)
            # One cubic prefilter per frame, shared by the affine pass and the
            # translation retry (it used to run once per call).
            coeffs = spline_coefficients(dfm)

            def score(f2d, sel, dfm=dfm, u_k=u_accum[k], coeffs=coeffs):
                return _znssd(
                    ref, dfm, ref_coords, u_k, f2d, winsize, sel, mask0,
                    workers=threads, min_count=min_count, coeffs=coeffs,
                )  # fmt: skip

            if affine:
                grad = node_gradients(ref_coords, u_accum[k], stencil)
                z = score(grad, pre)
                retry = pre & ~(z <= threshold) & grad.any(axis=1)
                if retry.any():
                    z_t = score(zeros_f, retry)
                    z[retry] = np.fmin(z[retry], z_t[retry])
            else:
                z = score(zeros_f, pre)
            # Two-tier acceptance: strong nodes pass outright; the rest up to the
            # threshold need a coherent strong neighbourhood (module docstring).
            strong_thr = GATE_STRONG_FRACTION * threshold
            strong = pre & (z <= strong_thr)
            weak = pre & ~strong & (z <= threshold)
            if weak.any():
                if stencil is None:
                    stencil = NeighbourIndex(ref_coords)
                supported = neighbour_supported(u_accum[k], strong, weak, stencil)
            else:
                supported = np.zeros_like(pre)
            bad = pre & ~(strong | supported)  # NaN znssd (no support) also fails
            if znssd_out is not None:
                znssd_out[k] = np.where(pre, z, np.nan)
            if bad.any():
                u_accum[k, bad] = np.nan
                valid[k, bad] = False
                n_gated[k] = int(bad.sum())
        if progress is not None:
            progress(k / n_deformed, f"verifying frame {k}/{n_deformed}")
        # Polled AFTER the frame's work: the kept prefix is exactly the verified
        # prefix. Frames with no tracked nodes cost nothing, so they never
        # trigger a truncation of their own.
        if verified and stop is not None and stop():
            if k + 1 < n_frames:  # a stop racing the LAST frame lost nothing
                stopped_at = k + 1
            break
    return n_gated, stopped_at
