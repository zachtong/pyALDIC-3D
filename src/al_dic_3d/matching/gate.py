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

A passing score is not enough on its own. A subset partly covering a region
that decorrelated (an occlusion, a glare, a lost speckle patch) can score ZNCC
0.7-0.85 while IC-GN converged 0.5-1.5 px away from where that subset
correlates best: the solver's fixed point weights the residual by the
REFERENCE image gradient, so the decorrelated pixels pull it off the score
minimum (local DIC and ADMM alike). The minimum check therefore also requires
every node scoring above ``GATE_MINIMUM_MIN_ZNSSD`` to sit at a minimum of its
own score, within a tolerance that grows with the precision the subset can
locate that minimum with (see the constants below). On a synthetic stereo pair
with one right-camera patch replaced by an unrelated speckle it removes the
right nodes shipped 0.4-1.4 px off (3D errors up to 2.9 mm); clean nodes there
sit within 0.08 px of their minimum.
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

# Minimum check (see the module docstring). The gate ZNSSD is sampled on a
# 3x3 translation stencil around the tracked motion, a quadratic is fitted, and
# a node whose fitted minimum lies further than its tolerance (or that has no
# minimum) fails. The step is a whole pixel so every sample has the same
# sub-pixel phase: interpolation smooths image noise more at half-pixel
# positions, which ripples the score with a 1 px period and can turn a correct
# track into a local maximum on a 0.5 px stencil. The tolerance is the larger
# of a fixed floor and GATE_MINIMUM_SIGMAS times the precision the subset can
# locate its minimum with (noise, subset size, texture). Nodes scoring at or
# below the floor skip the check: their subsets correlate too well to hide a
# decorrelated part.
GATE_MINIMUM_STEP_PX = 1.0
GATE_MINIMUM_TOL_PX = 0.25
GATE_MINIMUM_SIGMAS = 4.0
GATE_MINIMUM_MIN_ZNSSD = 0.1

# Stencil offsets (dx, dy) in units of the step, row-major; index 4 is the centre.
_STENCIL = np.array([(dx, dy) for dy in (-1.0, 0.0, 1.0) for dx in (-1.0, 0.0, 1.0)])
_STENCIL_CENTRE = 4
# Smallest fitted curvature (relative to the score's magnitude) that counts as
# a minimum; below it the fit only sees floating-point rounding.
_MIN_RELATIVE_CURVATURE = 1e-9

ScoreFn = Callable[..., NDArray[np.float64]]


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


def _quadratic_fit(
    z9: NDArray[np.float64], step: float
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Fitted quadratic on the stencil: ``(distance to its minimum, smallest curvature)``.

    ``z9`` is ``(n, 9)``: a score sampled at ``_STENCIL * step``. A least-squares
    ``z = c0 + c1 dx + c2 dy + c3 dx^2 + c4 dx dy + c5 dy^2`` is fitted per row.
    The curvature is the smallest eigenvalue of the fitted Hessian
    ``[[2 c3, c4], [c4, 2 c5]]``. Both are NaN where a sample is missing or the
    quadratic has no minimum (not positive definite).
    """
    z9 = np.asarray(z9, dtype=np.float64).reshape(-1, _STENCIL.shape[0])
    d = _STENCIL * float(step)
    design = np.column_stack(
        [np.ones(len(d)), d[:, 0], d[:, 1], d[:, 0] ** 2, d[:, 0] * d[:, 1], d[:, 1] ** 2]
    )
    coef = z9 @ np.linalg.pinv(design).T  # (n, 6)
    gx, gy, a, b, c = coef[:, 1], coef[:, 2], coef[:, 3], coef[:, 4], coef[:, 5]
    det = 4.0 * a * c - b * b
    lam = (a + c) - np.hypot(a - c, b)  # smallest eigenvalue of the Hessian
    # A curvature at rounding level is no minimum: a flat score fits to +-1e-17
    # coefficients whose signs differ between CPUs (x86 vs Apple silicon).
    scale = np.abs(z9).max(axis=1) if z9.size else np.zeros(0)
    ok = (
        np.isfinite(coef).all(axis=1)
        & (a > 0)
        & (det > 0)
        & (lam > _MIN_RELATIVE_CURVATURE * scale)
    )
    shift = np.full(z9.shape[0], np.nan, dtype=np.float64)
    curv = np.full(z9.shape[0], np.nan, dtype=np.float64)
    # argmin of the quadratic: [[2a, b], [b, 2c]] s = -[gx, gy]
    sx = (b[ok] * gy[ok] - 2.0 * c[ok] * gx[ok]) / det[ok]
    sy = (b[ok] * gx[ok] - 2.0 * a[ok] * gy[ok]) / det[ok]
    shift[ok] = np.hypot(sx, sy)
    curv[ok] = lam[ok]
    return shift, curv


def quadratic_minimum_shift(z9: NDArray[np.float64], step: float) -> NDArray[np.float64]:
    """Distance from the stencil centre to the minimum of a fitted quadratic.

    See :func:`_quadratic_fit`; NaN where there is no minimum.
    """
    return _quadratic_fit(z9, step)[0]


def minimum_tolerance(
    z: NDArray[np.float64], count: NDArray[np.float64], curvature: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Largest accepted shift to the score minimum, per node (px).

    Least squares locates the minimum of ``z = sum r^2`` over ``count`` pixels
    with covariance ``2 (z / count) H^-1``; ``curvature`` is the smallest
    eigenvalue of ``H``, so ``sigma = sqrt(2 z / (count * curvature))`` is the
    worst-direction precision (0.003 px on a clean synthetic subset, ~0.1 px at
    ZNCC 0.7 from noise). Returns ``max(GATE_MINIMUM_TOL_PX,
    GATE_MINIMUM_SIGMAS * sigma)``.
    """
    with np.errstate(divide="ignore", invalid="ignore"):
        sigma = np.sqrt(2.0 * z / (np.maximum(count, 1.0) * curvature))
    return np.fmax(GATE_MINIMUM_TOL_PX, GATE_MINIMUM_SIGMAS * sigma)


def minimum_shift(
    score: ScoreFn,
    u: NDArray[np.float64],
    f2d: NDArray[np.float64],
    z_centre: NDArray[np.float64],
    sel: NDArray[np.bool_],
    step: float = GATE_MINIMUM_STEP_PX,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.bool_]]:
    """Shift from each selected node's motion to the nearest minimum of its gate score.

    ``score(u, f2d, sel, counts_out=...)`` is the gate ZNSSD at motion ``u`` and
    warp gradient ``f2d``; ``z_centre`` is its value at ``u`` itself. The score
    is sampled on the 3x3 translation stencil of ``step`` px (gradient fixed)
    and a quadratic locates the minimum. Returns ``(shift, tolerance,
    testable)``, all ``(n,)``; ``shift`` and ``tolerance`` are NaN outside
    ``sel`` and ``shift`` also where no minimum is found. A node is testable
    only when every stencil sample scores the same pixels: a subset running
    off the deformed image gains or loses pixels as it shifts, and scores over
    different pixels are not comparable.
    """
    n = u.shape[0]
    shift = np.full(n, np.nan, dtype=np.float64)
    tol = np.full(n, np.nan, dtype=np.float64)
    testable = np.zeros(n, dtype=bool)
    if not sel.any():
        return shift, tol, testable
    z9 = np.full((n, _STENCIL.shape[0]), np.nan, dtype=np.float64)
    z9[:, _STENCIL_CENTRE] = z_centre
    c_min = np.full(n, np.iinfo(np.int64).max, dtype=np.int64)
    c_max = np.zeros(n, dtype=np.int64)
    for j, (dx, dy) in enumerate(_STENCIL):
        if j == _STENCIL_CENTRE:
            continue
        cnt = np.zeros(n, dtype=np.int64)
        z9[:, j] = score(u + np.array([dx * step, dy * step]), f2d, sel, counts_out=cnt)
        c_min = np.minimum(c_min, cnt)
        c_max = np.maximum(c_max, cnt)
    s_sel, curv = _quadratic_fit(z9[sel], step)
    shift[sel] = s_sel
    tol[sel] = minimum_tolerance(z_centre[sel], c_min[sel].astype(np.float64), curv)
    testable[sel] = c_min[sel] == c_max[sel]
    return shift, tol, testable


def _off_minimum(
    score: ScoreFn,
    u: NDArray[np.float64],
    f2d: NDArray[np.float64],
    z: NDArray[np.float64],
    candidates: NDArray[np.bool_],
) -> tuple[NDArray[np.bool_], NDArray[np.float64]]:
    """Candidates whose motion is not at a minimum of their gate score.

    Checks the candidates scoring above ``GATE_MINIMUM_MIN_ZNSSD`` with the
    warp gradient that produced ``z``. A node failing with a non-zero gradient
    is re-checked with the translation-only warp and passes if either check
    does, so a gradient corrupted by bad neighbours cannot fail a good node
    (the same rule as the score's translation retry). A node the check cannot
    test (see :func:`minimum_shift`) keeps the verdict of its score; an
    untestable retry does not rescue a node that failed. Returns
    ``(off_min, shift)``; ``shift`` comes from the warp that passed best (NaN
    where unchecked or where neither warp has a minimum).
    """
    n = u.shape[0]
    check = candidates & (z > GATE_MINIMUM_MIN_ZNSSD)
    if not check.any():
        return np.zeros(n, dtype=bool), np.full(n, np.nan, dtype=np.float64)
    shift, tol, testable = minimum_shift(score, u, f2d, z, check)
    ratio = np.where(testable, shift / tol, 0.0)  # NaN (no minimum) never passes
    off = check & ~(ratio <= 1.0)
    retry = off & f2d.any(axis=1)
    if retry.any():
        zeros_f = np.zeros_like(f2d)
        z_t = score(u, zeros_f, retry)
        clean_t = retry & (z_t <= GATE_MINIMUM_MIN_ZNSSD)
        rest = retry & ~clean_t
        shift_t, tol_t, testable_t = minimum_shift(score, u, zeros_f, z_t, rest)
        # Only a retry that could be tested can rescue a node that failed.
        ratio_t = np.where(testable_t, shift_t / tol_t, np.nan)
        better = rest & (ratio_t <= np.nan_to_num(ratio, nan=np.inf))
        shift[better] = shift_t[better]
        ratio[better] = ratio_t[better]
        shift[clean_t] = 0.0
        ratio[clean_t] = 0.0
        off = check & ~(ratio <= 1.0)
    return off, shift


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
    minimum_check: bool = True,
    shift_out: NDArray[np.float64] | None = None,
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
        minimum_check: also require the tracked motion to sit at a minimum of
            the gate score (module docstring). ``False`` restores the
            score-only gate.
        shift_out: optional ``(n_frames, n)`` array receiving the shift to the
            nearest score minimum of each node the minimum check examined (NaN
            elsewhere, and where no minimum was found).
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

            def score(u_k, f2d, sel, counts_out=None, dfm=dfm, coeffs=coeffs):
                return _znssd(
                    ref, dfm, ref_coords, u_k, f2d, winsize, sel, mask0,
                    workers=threads, min_count=min_count, coeffs=coeffs,
                    counts_out=counts_out,
                )  # fmt: skip

            u_k = u_accum[k]
            f_used = zeros_f
            if affine:
                grad = node_gradients(ref_coords, u_k, stencil)
                z = score(u_k, grad, pre)
                f_used = grad.copy()
                retry = pre & ~(z <= threshold) & grad.any(axis=1)
                if retry.any():
                    z_t = score(u_k, zeros_f, retry)
                    # Same as fmin(z, z_t); remember which warp scored best.
                    use_t = retry & np.isfinite(z_t) & ~(z <= z_t)
                    z[use_t] = z_t[use_t]
                    f_used[use_t] = 0.0
            else:
                z = score(u_k, zeros_f, pre)
            # Minimum check: a passing score is not enough if a nearby motion
            # scores clearly better (module docstring).
            off_min = np.zeros_like(pre)
            if minimum_check:
                off_min, shift = _off_minimum(score, u_k, f_used, z, pre & (z <= threshold))
                if shift_out is not None:
                    shift_out[k] = shift
            # Two-tier acceptance: strong nodes pass outright; the rest up to the
            # threshold need a coherent strong neighbourhood (module docstring).
            strong_thr = GATE_STRONG_FRACTION * threshold
            strong = pre & (z <= strong_thr) & ~off_min
            weak = pre & ~strong & ~off_min & (z <= threshold)
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


def gate_stepwise(
    frames,
    masks,
    ref_coords: NDArray[np.float64],
    u_accum: NDArray[np.float64],
    valid: NDArray[np.bool_],
    winsize: int,
    threshold: float,
    parents,
    *,
    progress: Callable[[float, str], None] | None = None,
    stop: Callable[[], bool] | None = None,
    workers: int | None = None,
    affine: bool = True,
    min_support: float = GATE_MIN_SUPPORT,
    znssd_out: NDArray[np.float64] | None = None,
    minimum_check: bool = True,
    shift_out: NDArray[np.float64] | None = None,
) -> tuple[NDArray[np.int64], int | None]:
    """The honesty gate, step by step: frame ``k`` against the frame it was tracked from.

    ``parents[k]`` is the reference frame frame ``k`` was correlated from
    (``FrameSchedule.parent``; ``parents[0]`` is ignored). Each frame is scored
    exactly like :func:`gate_by_znssd` scores frame 1 against frame 0, with the
    reference frame's image and mask, the positions the track had there and the
    increment since. Composition makes every later step depend on a reference
    frame, so a node that fails on a reference frame stays invalid on every
    frame tracked from it. Accumulative tracks (every parent is frame 0) go
    through :func:`gate_by_znssd` unchanged.

    Why: an incremental track adds a tiny error at each step (~0.01 px on a
    notched specimen pulled to failure). Checking every node against its
    frame-0 subset dropped the drifted but genuinely tracked nodes (21 % kept
    after 135 steps while the engine tracked 99 %); a garbage step still fails
    here. ``n_gated[k]`` counts the engine-valid nodes dropped on frame ``k``,
    those whose reference frame was dropped included.
    """
    n_frames = u_accum.shape[0]
    parents = [int(p) for p in parents]
    if len(parents) != n_frames or any(not 0 <= parents[k] < k for k in range(1, n_frames)):
        raise ValueError(f"parents must name an earlier frame for every frame: {parents}")
    if all(p == 0 for p in parents[1:]):
        return gate_by_znssd(
            frames,
            masks[0],
            ref_coords,
            u_accum,
            valid,
            winsize,
            threshold,
            progress=progress,
            stop=stop,
            workers=workers,
            affine=affine,
            min_support=min_support,
            znssd_out=znssd_out,
            minimum_check=minimum_check,
            shift_out=shift_out,
        )
    n_gated = np.zeros(n_frames, dtype=np.int64)
    n_deformed = max(1, n_frames - 1)
    stopped_at: int | None = None
    for k in range(1, n_frames):
        r = parents[k]
        tracked = valid[k].copy()
        cand = tracked & valid[r] if r > 0 else tracked
        if znssd_out is not None:
            znssd_out[k] = np.nan
        if shift_out is not None:
            shift_out[k] = np.nan
        keep = cand
        if cand.any():
            idx = np.flatnonzero(cand)
            pos = ref_coords[idx] + (u_accum[r, idx] if r > 0 else 0.0)
            u_pair = np.zeros((2, idx.size, 2), dtype=np.float64)
            u_pair[1] = u_accum[k, idx] - (u_accum[r, idx] if r > 0 else 0.0)
            v_pair = np.ones((2, idx.size), dtype=bool)
            z_pair = np.full((2, idx.size), np.nan) if znssd_out is not None else None
            s_pair = np.full((2, idx.size), np.nan) if shift_out is not None else None
            gate_by_znssd(
                [frames[r], frames[k]],
                masks[r],
                pos,
                u_pair,
                v_pair,
                winsize,
                threshold,
                workers=workers,
                affine=affine,
                min_support=min_support,
                znssd_out=z_pair,
                minimum_check=minimum_check,
                shift_out=s_pair,
            )
            keep = np.zeros_like(cand)
            keep[idx] = v_pair[1]
            if z_pair is not None:
                znssd_out[k, idx] = z_pair[1]
            if s_pair is not None:
                shift_out[k, idx] = s_pair[1]
        bad = tracked & ~keep
        if bad.any():
            u_accum[k, bad] = np.nan
            valid[k, bad] = False
            n_gated[k] = int(bad.sum())
        if progress is not None:
            progress(k / n_deformed, f"verifying frame {k}/{n_deformed}")
        if cand.any() and stop is not None and stop():
            if k + 1 < n_frames:
                stopped_at = k + 1
            break
    return n_gated, stopped_at
