"""Pure-function matching primitives (Qt-free) — the FIRST runtime `al_dic` coupling.

These thin wrappers reuse the 2D engine's solver by import only (the 2D repo is
never modified, decision D11). Every `al_dic` symbol imported here is recorded in
``docs/DEPENDS_ON_2D.md``.

``match_points`` is the keystone: scattered-point local IC-GN (no mesh, no ADMM),
the basis for the frame-1 cross-camera match and for strategies S2/S3 (02 §5.3).
The 2D solver returns only ``(U, F, conv_iter)`` and never a correlation value, so
ZNSSD is computed here independently (same objective, no dependency on the
solver's internal precompute dict).
"""

from __future__ import annotations

import numpy as np

# --- 2D engine (al_dic) imports — see docs/DEPENDS_ON_2D.md -------------------
from al_dic.core.config import dicpara_default
from al_dic.core.data_structures import DICPara
from al_dic.io.image_ops import compute_image_gradient
from al_dic.solver.local_icgn import local_icgn_precompute, local_icgn_solve_subset
from numpy.typing import NDArray
from scipy.ndimage import label, map_coordinates

# Per-subset 4-connectivity structure for the batched connected-component step:
# the (3, 3, 3) structure connects the 4-neighbourhood WITHIN each (S, S) slice
# but never across the stack axis, so subsets are labelled independently and the
# result is invariant to how points are chunked (matches the engine's per-node
# ``scipy.ndimage.label`` with default 4-connectivity, icgn_batch.py:864).
_CC_STRUCTURE = np.zeros((3, 3, 3), dtype=bool)
_CC_STRUCTURE[1] = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=bool)


def make_dicpara(
    img_size: tuple[int, int],
    roi: tuple[int, int, int, int],
    winsize: int = 32,
    winstepsize: int = 16,
    winsize_min: int = 8,
    icgn_max_iter: int = 100,
    tol: float = 1e-2,
    img_ref_mask: NDArray[np.float64] | None = None,
    reference_mode: str = "accumulative",
    use_global_step: bool = True,
    admm_max_iter: int = 3,
    fft_search: int = 20,
    fft_auto_expand: bool = True,
    frame_schedule=None,
) -> DICPara:
    """A validated ``DICPara`` for the 3D layer's temporal-tracking runs.

    ``use_global_step=True`` (DEFAULT — matches the MATLAB trusted path's
    ``UseGlobal``) enables the Augmented-Lagrangian global step: Subproblem 2
    (FEM) + the ADMM loop capped at ``admm_max_iter`` (engine default 3).
    ``use_global_step=False`` gives local-only IC-GN. NOTE the frame-1 STEREO
    match never consumes these flags: it is scattered-point local IC-GN by
    design — the MATLAB anchor is also ICGN-only there, because the L->R
    disparity field carries projective viewpoint geometry rather than material
    deformation, so the FEM displacement-compatibility regularizer does not
    apply to it.

    ``roi = (xmin, xmax, ymin, ymax)`` in pixels (x=col, y=row). ``img_ref_mask``
    (``(H, W)`` float, 1=valid) gates reference-subset validity in matching and
    per-frame ROI normalization in ``run_aldic``; ``None`` -> no masking.
    ``reference_mode`` selects the FrameSchedule (``"accumulative"`` -> every frame
    vs frame 1; ``"incremental"`` -> frame k vs k-1, engine composes to cumulative).
    ``fft_search`` is the FFT integer-search half-width (px) for temporal seeding
    (engine default 20). The engine's auto-expand only fires on boundary-CLIPPED
    peaks; a decorrelated large jump yields an in-bounds noise peak instead, so
    when per-frame motion can exceed ~20 px set this to cover it explicitly
    (S3 inc-mode lesson: a true 21 px increment seeded garbage at the default).
    ``fft_auto_expand`` maps to the engine's ``fft_auto_expand_search`` (Q8:
    auto-enlarge the FFT search when the peak lands on the region boundary;
    engine default True). ``frame_schedule`` is an optional explicit engine
    ``FrameSchedule`` (Q5 reference-update policies); ``None`` lets ``run_aldic``
    derive the schedule from ``reference_mode``.
    """
    from al_dic.core.data_structures import GridxyROIRange

    xmin, xmax, ymin, ymax = roi
    overrides: dict = dict(
        winsize=winsize,
        winstepsize=winstepsize,
        winsize_min=winsize_min,
        gridxy_roi_range=GridxyROIRange(gridx=(xmin, xmax), gridy=(ymin, ymax)),
        img_size=img_size,
        use_global_step=use_global_step,
        reference_mode=reference_mode,
        icgn_max_iter=icgn_max_iter,
        tol=tol,
        admm_max_iter=max(1, admm_max_iter),
        size_of_fft_search_region=max(4, int(fft_search)),
        fft_auto_expand_search=bool(fft_auto_expand),
        frame_schedule=frame_schedule,
    )
    if img_ref_mask is not None:
        overrides["img_ref_mask"] = np.ascontiguousarray(img_ref_mask, dtype=np.float64)
    return dicpara_default(**overrides)


# Pre-audit name kept as an alias: the 2026-07-07 core-algorithm audit flipped
# the default to the full AL-DIC global step, so "local" no longer describes
# what this factory builds.
make_local_dicpara = make_dicpara


def match_points(
    ref_img: NDArray[np.float64],
    def_img: NDArray[np.float64],
    points: NDArray[np.float64],
    U0: NDArray[np.float64],
    para: DICPara,
    tol: float = 1e-3,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.bool_]]:
    """Local IC-GN at arbitrary scattered points (no mesh, no ADMM).

    Args:
        ref_img, def_img: ``(H, W)`` float64 images (same intensity scale).
        points: ``(n, 2)`` ``[x, y]`` (col, row) query points.
        U0: ``(n, 2)`` ``[u, v]`` initial displacement guess, row-aligned to points.
        para: local-only ``DICPara`` (see :func:`make_local_dicpara`); ``winsize`` and
            ``icgn_max_iter`` are read.
        tol: IC-GN convergence tolerance (``1e-3``, matching StereoMatch_STAQ).

    Returns:
        ``(U (n,2), znssd (n,), valid (n,))``. Invalid points get ``NaN`` in ``U``
        and ``znssd``; ``znssd`` is in ``[0, 4]`` (``0`` = perfect, ``2(1-ZNCC)``).
    """
    ref = np.ascontiguousarray(ref_img, dtype=np.float64)
    dfm = np.ascontiguousarray(def_img, dtype=np.float64)
    h, w = ref.shape
    mask = getattr(para, "img_ref_mask", None)
    mask = np.ones((h, w), dtype=np.float64) if mask is None else np.asarray(mask, np.float64)

    grad = compute_image_gradient(ref * mask, mask, img_raw=ref)
    ctx = local_icgn_precompute(np.ascontiguousarray(points, np.float64), grad, ref, para)
    u_2d, f_2d, conv_iter = local_icgn_solve_subset(
        ctx, None, np.ascontiguousarray(U0, np.float64), dfm, tol
    )

    valid = conv_iter <= para.icgn_max_iter
    znssd = _znssd(ref, dfm, np.asarray(points, np.float64), u_2d, f_2d, para.winsize, valid, mask)

    out_u = u_2d.astype(np.float64).copy()
    out_u[~valid] = np.nan
    znssd[~valid] = np.nan
    return out_u, znssd, valid


# ZNSSD point-chunk size: the vectorized kernel materializes ~8 float64 arrays of
# shape (chunk, S, S); at 2048 points and winsize 64 that is ~280 MB peak instead
# of the multi-GB monolithic evaluation at 20k+ points (perf batch P1.3).
_ZNSSD_CHUNK = 2048


def _znssd(
    ref: NDArray[np.float64],
    dfm: NDArray[np.float64],
    points: NDArray[np.float64],
    u_2d: NDArray[np.float64],
    f_2d: NDArray[np.float64],
    winsize: int,
    valid: NDArray[np.bool_],
    mask: NDArray[np.float64],
    chunk: int = _ZNSSD_CHUNK,
) -> NDArray[np.float64]:
    """ZNSSD per point at the converged warp (independent of the solver internals).

    Replicates the IC-GN objective: extract the reference subset, warp+sample the
    deformed subset with the 6-DOF affine ``(F, U)``, and compare zero-normalized.
    ``znssd = Σ[(f-f̄)/Δf − (g-ḡ)/Δg]²``.

    Boundary handling mirrors the engine's DEFAULT (Numba) backend so this gate
    metric matches the objective it is scoring (audit A3-1/A3-2/A3-3):
      * only the CENTER pixel need be in the reference image (partial edge
        subsets are scored on their in-image support, numba_kernels.py:606-619),
      * reference samples off the image or outside the mask are excluded, and
        the mask is restricted to the CENTER-connected component
        (``_connected_center_mask``, icgn_batch.py:864),
      * deformed samples that warp off the image are excluded via
        ``|g| > 1e-10`` (cval=0 out-of-bounds, icgn_batch.py:437),
      * a subset needs ``>= 4`` combined-valid pixels (the engine floor).

    Evaluated in point chunks of ``chunk`` (each point is independent, so chunking
    is bit-identical to the monolithic evaluation) to bound the peak size of the
    ``(m, S, S)`` intermediates.
    """
    h, w = ref.shape
    n = points.shape[0]
    half = winsize // 2
    offs = np.arange(-half, half + 1)
    xx, yy = np.meshgrid(offs.astype(np.float64), offs.astype(np.float64))  # (S, S)
    z = np.full(n, np.nan, dtype=np.float64)

    x0 = np.round(points[:, 0])
    y0 = np.round(points[:, 1])
    # Engine default rule: the node's CENTER pixel must lie inside the reference
    # image; partial edge subsets are still tracked (their off-image pixels are
    # excluded below), not rejected wholesale.
    in_bounds = valid & (x0 >= 0) & (x0 <= w - 1) & (y0 >= 0) & (y0 <= h - 1)
    idx = np.where(in_bounds)[0]
    if idx.size == 0:
        return z

    # The center-connected-component restriction only changes the result when
    # the mask actually has interior/edge barriers; skip it (identical result)
    # on the common unmasked path.
    mask_has_holes = bool((np.asarray(mask) <= 0.5).any())

    chunk = max(1, int(chunk))
    for start in range(0, idx.size, chunk):
        sel = idx[start : start + chunk]
        z[sel] = _znssd_block(ref, dfm, sel, x0, y0, u_2d, f_2d, offs, xx, yy, mask, mask_has_holes)
    return z


def _center_connected_stack(msub: NDArray[np.bool_]) -> NDArray[np.bool_]:
    """Keep only the CENTER-connected component of each ``(S, S)`` mask.

    Batched analogue of the engine's ``_connected_center_mask`` (scipy label,
    4-connectivity): each subset in the ``(m, S, S)`` stack is labelled
    independently (the structure has no cross-slice connectivity), then reduced
    to the component holding the center pixel. A subset whose center pixel is
    itself invalid collapses to all-False.
    """
    m, sy, sx = msub.shape
    if m == 0:
        return msub
    labeled, _ = label(msub, structure=_CC_STRUCTURE)
    center = labeled[:, sy // 2, sx // 2]  # (m,)
    return (labeled == center[:, None, None]) & (center[:, None, None] > 0)


def _znssd_block(
    ref: NDArray[np.float64],
    dfm: NDArray[np.float64],
    idx: NDArray[np.int64],
    x0: NDArray[np.float64],
    y0: NDArray[np.float64],
    u_2d: NDArray[np.float64],
    f_2d: NDArray[np.float64],
    offs: NDArray[np.int64],
    xx: NDArray[np.float64],
    yy: NDArray[np.float64],
    mask: NDArray[np.float64],
    mask_has_holes: bool = False,
) -> NDArray[np.float64]:
    """The vectorized ZNSSD kernel for one chunk of in-bounds point indices."""
    h, w = ref.shape
    s = xx.shape[0]
    rx = x0[idx].astype(np.int64)
    ry = y0[idx].astype(np.int64)
    rows = ry[:, None, None] + offs[None, :, None]  # (m, S, 1)
    cols = rx[:, None, None] + offs[None, None, :]  # (m, 1, S)

    # A3-3: partial edge subsets have off-image reference pixels. Clip indices
    # for a safe gather, then exclude those samples so they enter neither the
    # counts, the means/vars, nor the residual (engine treats OOB pixels as
    # mask=0, numba_kernels.py:614-619).
    ref_in = (rows >= 0) & (rows <= h - 1) & (cols >= 0) & (cols <= w - 1)  # (m, S, S)
    rows_c = np.clip(rows, 0, h - 1)
    cols_c = np.clip(cols, 0, w - 1)
    f = ref[rows_c, cols_c]  # (m, S, S)
    msub = (mask[rows_c, cols_c] > 0.5) & ref_in

    # A3-2: restrict the reference mask to the center-connected component so a
    # subset straddling a hole/barrier is scored only over the center's island.
    if mask_has_holes:
        msub = _center_connected_stack(msub)

    f11, f21, f12, f22 = f_2d[idx, 0], f_2d[idx, 1], f_2d[idx, 2], f_2d[idx, 3]
    uu, vv = u_2d[idx, 0], u_2d[idx, 1]
    gu = (
        (1 + f11[:, None, None]) * xx
        + f12[:, None, None] * yy
        + rx[:, None, None]
        + uu[:, None, None]
    )
    gv = (
        f21[:, None, None] * xx
        + (1 + f22[:, None, None]) * yy
        + ry[:, None, None]
        + vv[:, None, None]
    )
    g = map_coordinates(dfm, [gv.ravel(), gu.ravel()], order=3, mode="constant", cval=0.0)
    g = g.reshape(idx.size, s, s)

    # A3-1: deformed samples that warp off the image are sampled as cval=0;
    # exclude them exactly as the engine does (|tempg| > 1e-10, icgn_batch.py:437),
    # so off-image zeros never pollute meang/varg/residual.
    comb = msub & (np.abs(g) > 1e-10)
    cnt = comb.sum((1, 2))
    cnt_safe = np.maximum(cnt, 1)

    fm = f * comb
    meanf = fm.sum((1, 2)) / cnt_safe
    varf = ((fm - meanf[:, None, None] * comb) ** 2).sum((1, 2)) / cnt_safe
    bottomf = np.sqrt(np.maximum((cnt - 1) * varf, 1e-30))

    gm = g * comb
    meang = gm.sum((1, 2)) / cnt_safe
    varg = ((gm - meang[:, None, None] * comb) ** 2).sum((1, 2)) / cnt_safe
    bottomg = np.sqrt(np.maximum((cnt - 1) * varg, 1e-30))

    res = (fm - meanf[:, None, None]) / bottomf[:, None, None] - (
        gm - meang[:, None, None]
    ) / bottomg[:, None, None]
    zi = (res * res * comb).sum((1, 2))
    zi[cnt < 4] = np.nan
    return zi
