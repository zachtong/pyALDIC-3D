"""Per-camera temporal tracking and scattered resampling (Qt-free).

Drives the 2D engine's accumulative pipeline (:func:`al_dic.run_aldic`) on ONE
camera stream from a fixed reference mesh, reading the **cumulative** node
displacement (``FrameResult.U_accum``) on the frame-1 mesh — never rebuilding the
mesh per frame (the MATLAB per-frame rebuild is a known hazard). The right camera
is tracked on its own dense grid; :func:`resample_to_points` then interpolates
that field onto the scattered correspondence points.

Every ``al_dic`` symbol imported here is recorded in ``docs/DEPENDS_ON_2D.md``.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np
from al_dic.core.data_structures import DICMesh, DICPara, split_uv
from al_dic.core.pipeline import run_aldic
from al_dic.io.image_ops import compute_clamped_roi, normalize_one
from al_dic.mesh.mesh_setup import mesh_setup
from al_dic.solver.seed_prop_pipeline import build_grid_for_roi
from numpy.typing import NDArray

# Raw frames indexed like a list: a real ``list`` of arrays (tests, GUI small
# runs) or any lazy view exposing ``__len__``/``__getitem__`` (perf batch P1.2).
FrameSeq = Sequence[NDArray[np.float64]]


class _EngineFrames:
    """Engine-protocol ``FrameProvider`` over raw frames, normalizing on demand.

    Implements the 2D engine's structural provider interface
    (``__len__`` / ``shape`` / ``clamped_roi`` / ``get_normalized``,
    al_dic ``core/data_structures.py:26``) so ``run_aldic`` never materializes
    a second, fully-normalized copy of the stack (``ListFrameProvider`` would).
    Normalization is byte-identical to the engine's eager list path: the same
    ``compute_clamped_roi`` + ``normalize_one`` on the same float64-coerced
    frames, just computed per request behind a small LRU. The engine ``.copy()``s
    every frame it fetches (``core/pipeline.py:816,831``), so serving cached
    arrays is safe.
    """

    _CAPACITY = 4  # ref + current frame + slack for incremental (k-1, k) pairs

    def __init__(self, frames: FrameSeq, roi) -> None:
        self._frames = frames
        first = frames[0]
        self._shape: tuple[int, int] = tuple(first.shape)
        self._clamped_roi = compute_clamped_roi(self._shape, roi)
        self._cache: OrderedDict[int, NDArray[np.float64]] = OrderedDict()

    def __len__(self) -> int:
        return len(self._frames)

    @property
    def shape(self) -> tuple[int, int]:
        return self._shape

    @property
    def clamped_roi(self):
        return self._clamped_roi

    def get_normalized(self, idx: int) -> NDArray[np.float64]:
        cached = self._cache.get(idx)
        if cached is not None:
            self._cache.move_to_end(idx)
            return cached
        raw = np.ascontiguousarray(self._frames[idx], dtype=np.float64)
        normed = normalize_one(raw, self._clamped_roi)
        self._cache[idx] = normed
        if len(self._cache) > self._CAPACITY:
            self._cache.popitem(last=False)
        return normed


@dataclass(frozen=True)
class TemporalField:
    """Cumulative per-frame node displacement from one accumulative DIC run.

    ``u_accum[0]`` is all-zero (the reference frame); ``u_accum[k]`` is the
    frame-0 -> frame-k cumulative displacement on ``ref_coords`` nodes.
    ``n_gated`` counts, per frame, the nodes invalidated by the ZNSSD honesty
    gate (F3.1: the gate must be visible, never a silent NaN) — ``None`` when
    the gate was disabled.
    """

    ref_coords: NDArray[np.float64]  # (n, 2) [x, y] frame-1 mesh nodes
    u_accum: NDArray[np.float64]  # (n_frames, n, 2) [u, v]; [0] == 0
    valid: NDArray[np.bool_]  # (n_frames, n)
    n_gated: NDArray[np.int64] | None = None  # (n_frames,) honesty-gate kills

    @property
    def n_frames(self) -> int:
        return int(self.u_accum.shape[0])


def build_grid_mesh(
    para: DICPara,
    img_h: int,
    img_w: int,
) -> DICMesh:
    """Build a uniform Q8 reference mesh over ``para``'s ROI (frame-1 material points).

    Reuses the exact FFT-path grid (:func:`build_grid_for_roi` + :func:`mesh_setup`)
    so node coordinates match what ``run_aldic`` would generate internally.
    """
    x0, y0 = build_grid_for_roi(para, img_h, img_w)
    return mesh_setup(x0, y0, para)


def temporal_track(
    frames: FrameSeq,
    mesh: DICMesh,
    para: DICPara,
    masks: Sequence[NDArray[np.float64]] | None = None,
    u0: NDArray[np.float64] | None = None,
    stop: Callable[[], bool] | None = None,
    gate_znssd: float = 1.0,
) -> TemporalField:
    """Track one camera's frames from a fixed reference mesh (accumulative).

    Args:
        frames: ``[f0, f1, ...]`` raw ``(H, W)`` float64 images — a list, or any
            lazy indexed view (``__len__``/``__getitem__``) so long sequences
            never need the whole stack resident; ``f0`` is the reference and
            must correspond to ``mesh``'s coordinate frame. The engine consumes
            them through a normalize-on-demand provider either way, so list and
            lazy inputs are byte-identical.
        mesh: the external reference mesh (its ``coordinates_fem`` are the tracked
            material points). Not rebuilt per frame.
        para: local-only accumulative ``DICPara``.
        masks: optional per-frame masks (same length as ``frames``): a list of
            arrays, or a lazy indexed sequence serving contiguous float64 (e.g.
            :class:`al_dic_3d.sequence.LazyMaskList`), which is passed through
            unmaterialized. Default all-ones (ONE shared array — the engine
            ``.astype``-copies what it indexes, al_dic ``core/pipeline.py:815,824``)
            — which keeps the external mesh byte-identical so the returned
            ``ref_coords`` equal ``mesh.coordinates_fem`` exactly.
        u0: optional frame-0->frame-1 seed of length ``2*n_nodes``. ``None`` lets
            ``run_aldic`` compute an FFT integer guess (robust to larger motion).
        gate_znssd: honesty gate — per frame, each node's CUMULATIVE track is
            re-verified by ZNSSD between the frame-0 subset at X and the frame-k
            image at X + U^k (translation warp); nodes above the threshold are
            invalidated (``NaN``). The 2D engine launders every per-node failure
            into finite values (IC-GN bad points are IDW-refilled, subpb2's FEM
            field is finite everywhere, composition nearest-fills), so without
            this gate ``isfinite`` validity is structurally all-True and a
            silently frozen/garbage frame flows downstream as "valid" (the S3
            frame-3 failure in BOTH modes). ``<= 0`` disables. ZNSSD is in
            ``[0, 4]``: 1.0 corresponds to ZNCC 0.5. The translation-only warp
            inflates ZNSSD under very large strain — widen when gating
            legitimately large-deformation data.

    Returns:
        A :class:`TemporalField`. Raises ``RuntimeError`` if a frame fails to
        solve (``run_aldic`` None-filters failures, breaking positional
        alignment — a partial run is surfaced rather than silently misaligned).
    """
    n_frames = len(frames)
    if n_frames < 2:
        raise ValueError(f"need >=2 frames, got {n_frames}")
    h, w = frames[0].shape
    if masks is None:
        # ONE shared all-ones array (P1.1): the engine .astype-copies whatever
        # it indexes, so per-frame duplicates would only burn n_frames x H x W
        # float64 for identical content.
        ones = np.ones((h, w), dtype=np.float64)
        masks = [ones] * n_frames
    if len(masks) != n_frames:
        raise ValueError(f"masks ({len(masks)}) must match frames ({n_frames})")
    if isinstance(masks, (list, tuple)):
        # Coerce eager mask lists once (no-copy for contiguous float64 — the
        # shared-ones and shared-roi_mask paths keep sharing one array). Lazy
        # mask sequences already serve contiguous float64 and pass through.
        masks = [np.ascontiguousarray(m, dtype=np.float64) for m in masks]
    mask0 = np.ascontiguousarray(masks[0], dtype=np.float64)  # engine mutates para

    import warnings

    try:
        # The 2D engine zero-fills an ALL-NaN ICGN field with only a UserWarning
        # ("All nodes are NaN, cannot interpolate. Returning zeros.") — silent
        # zeros would flow downstream as a perfectly "valid" frozen camera (the
        # S3 real-data failure). Promote that warning to a hard error below.
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = run_aldic(
                para,
                # Normalize-on-demand provider (P1.2): the engine otherwise
                # eagerly materializes a full normalized float64 copy of the
                # stack (ListFrameProvider). Byte-identical, streaming instead.
                _EngineFrames(frames, para.gridxy_roi_range),
                masks,
                stop_fn=stop,
                compute_strain=False,
                mesh=mesh,
                U0=u0,
            )
    except RuntimeError:
        # The engine raises its own abort message when stop_fn trips; normalise
        # to the uniform cooperative-cancel contract. Genuine errors re-raise.
        if stop is not None and stop():
            raise RuntimeError("cancelled") from None
        raise
    for w in caught:
        if "All nodes are NaN" in str(w.message):
            raise RuntimeError(
                "2D engine solved NO nodes (all-NaN field silently zero-filled): "
                "the temporal track failed outright — check masks/ROI/texture "
                "instead of trusting a frozen zero-displacement camera."
            )
        warnings.warn_explicit(w.message, w.category, w.filename, w.lineno)
    if stop is not None and stop():
        raise RuntimeError("cancelled")

    ref_coords = np.asarray(result.dic_mesh.coordinates_fem, dtype=np.float64)
    n = ref_coords.shape[0]
    if len(result.result_disp) != n_frames - 1:
        raise RuntimeError(
            f"run_aldic returned {len(result.result_disp)} deformed frames for "
            f"{n_frames - 1} expected — a frame failed and positional alignment "
            f"is unreliable (partial-run handling is deferred to Phase 2)."
        )

    u_accum = np.zeros((n_frames, n, 2), dtype=np.float64)
    valid = np.zeros((n_frames, n), dtype=bool)
    valid[0] = True  # reference frame: zero displacement, all valid
    incremental = getattr(para, "reference_mode", "accumulative") == "incremental"
    for k, fr in enumerate(result.result_disp, start=1):
        if fr.U_accum is None:
            if incremental and k > 1:
                # In incremental mode fr.U is the RAW k-1 -> k increment; letting
                # it masquerade as the cumulative field silently loses the whole
                # 0 -> k-1 history (the engine only skips composing when a chain
                # ancestor failed).
                raise RuntimeError(
                    f"engine returned no composed cumulative field for frame {k} "
                    f"(incremental chain broke upstream) — refusing to report the "
                    f"raw increment as cumulative displacement."
                )
            vec = fr.U  # accumulative direct-to-root: U IS the cumulative field
        else:
            vec = fr.U_accum
        uu, vv = split_uv(np.asarray(vec, dtype=np.float64))
        u_accum[k, :, 0] = uu
        u_accum[k, :, 1] = vv
        valid[k] = np.isfinite(uu) & np.isfinite(vv)

    n_gated = None
    if gate_znssd > 0:
        n_gated = _gate_by_znssd(frames, mask0, ref_coords, u_accum, valid, para, gate_znssd)

    return TemporalField(ref_coords=ref_coords, u_accum=u_accum, valid=valid, n_gated=n_gated)


def _gate_by_znssd(
    frames: FrameSeq,
    mask0: NDArray[np.float64],
    ref_coords: NDArray[np.float64],
    u_accum: NDArray[np.float64],
    valid: NDArray[np.bool_],
    para: DICPara,
    threshold: float,
) -> NDArray[np.int64]:
    """Invalidate (in place) tracked nodes whose frame-0 -> frame-k correlation fails.

    Independent verification of the shipped quantity itself: the frame-0 subset
    at X must still correlate with frame k at X + U^k. Catches BOTH silent
    failure shapes seen on S3: accumulative sibling-warm-start freeze (IC-GN
    "converges" with a zero update on a decorrelated pattern) and incremental
    garbage increments faithfully composed into the cumulative field.

    Returns the per-frame count of nodes the gate killed (F3.1: gate kills feed
    the run diagnostics instead of vanishing as anonymous NaN).
    """
    from al_dic_3d.matching.primitives import _znssd

    ref = np.ascontiguousarray(frames[0], dtype=np.float64)
    n = ref_coords.shape[0]
    zeros_f = np.zeros((n, 4), dtype=np.float64)
    n_gated = np.zeros(u_accum.shape[0], dtype=np.int64)
    for k in range(1, u_accum.shape[0]):
        pre = valid[k].copy()
        if not pre.any():
            continue
        z = _znssd(
            ref,
            np.ascontiguousarray(frames[k], dtype=np.float64),
            ref_coords,
            u_accum[k],
            zeros_f,
            para.winsize,
            pre,
            mask0,
        )
        bad = pre & ~(z <= threshold)  # NaN znssd (no support) also fails
        if bad.any():
            u_accum[k, bad] = np.nan
            valid[k, bad] = False
            n_gated[k] = int(bad.sum())
    return n_gated


def resample_to_points(
    ref_coords: NDArray[np.float64],
    values: NDArray[np.float64],
    query: NDArray[np.float64],
    *,
    fill_nearest: bool = True,
) -> NDArray[np.float64]:
    """Interpolate a scattered vector field onto arbitrary query points (NaN-aware).

    Builds a Delaunay-based linear interpolant from the FINITE rows of ``values``
    (so NaN/invalid nodes never contaminate a neighborhood) and evaluates it at
    ``query``. Points outside the convex hull are ``NaN`` from the linear pass; if
    ``fill_nearest`` they are back-filled with the nearest finite node (a mild,
    clearly-bounded extrapolation for corr points that drift just past the hull).

    Args:
        ref_coords: ``(n, 2)`` field node coordinates ``[x, y]``.
        values: ``(n, 2)`` field values ``[u, v]`` (rows may be ``NaN``).
        query: ``(m, 2)`` points to sample at.

    Returns:
        ``(m, 2)`` interpolated values; ``NaN`` rows where no estimate exists.
    """
    from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator

    ref = np.asarray(ref_coords, dtype=np.float64).reshape(-1, 2)
    val = np.asarray(values, dtype=np.float64).reshape(-1, 2)
    q = np.asarray(query, dtype=np.float64).reshape(-1, 2)

    finite = np.isfinite(val).all(axis=1) & np.isfinite(ref).all(axis=1)
    out = np.full((q.shape[0], 2), np.nan, dtype=np.float64)
    if finite.sum() < 3:
        return out  # Delaunay needs >=3 non-collinear points

    src = ref[finite]
    dst = val[finite]
    lin = LinearNDInterpolator(src, dst)
    out[:] = lin(q)

    if fill_nearest:
        # Only fill FINITE queries that fell outside the hull; a non-finite query
        # row has no estimate and must stay NaN (documented contract) — never
        # feed it to the KD-tree (scipy raises on non-finite query points).
        missing = (~np.isfinite(out).all(axis=1)) & np.isfinite(q).all(axis=1)
        if missing.any():
            nearest = NearestNDInterpolator(src, dst)
            out[missing] = nearest(q[missing])
    return out
