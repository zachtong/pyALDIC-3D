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

# Hard error raised when the engine silently zero-filled an all-NaN field —
# shared with the parallel track-both path, which enforces the same guard from
# its own thread-safe warning recorder (P3.6).
ZERO_FILL_ERROR = (
    "2D engine solved NO nodes (all-NaN field silently zero-filled): "
    "the temporal track failed outright — check masks/ROI/texture "
    "instead of trusting a frozen zero-displacement camera."
)


class _EngineFrames:
    """Engine-protocol ``FrameProvider`` over raw frames, normalizing on demand.

    Implements the 2D engine's structural provider interface
    (``__len__`` / ``shape`` / ``clamped_roi`` / ``get_normalized``,
    al_dic ``core/data_structures.py:26``) so ``run_aldic`` never materializes
    a second, fully-normalized copy of the stack (``ListFrameProvider`` would).
    Normalization is byte-identical to the engine's eager list path: the same
    ``compute_clamped_roi`` + ``normalize_one`` on the same float64-coerced
    frames, just computed per request behind a small LRU. The engine ``.copy()``s
    every frame it fetches (al-dic 0.7.0 ``core/pipeline.py:987,1002``), so
    serving cached arrays is safe.
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

    Partial-run bookkeeping (R2, engine 0.7 partial-results-on-cancel): a
    cooperative stop mid-run KEEPS the tracked prefix — frames
    ``[0, stopped_at_frame)`` carry real data, every later frame is all-NaN /
    invalid. ``stopped_at_frame`` is the 0-based index of the first UNTRACKED
    frame (equals the count of kept frames); ``None`` for a complete run.
    """

    ref_coords: NDArray[np.float64]  # (n, 2) [x, y] frame-1 mesh nodes
    u_accum: NDArray[np.float64]  # (n_frames, n, 2) [u, v]; [0] == 0
    valid: NDArray[np.bool_]  # (n_frames, n)
    n_gated: NDArray[np.int64] | None = None  # (n_frames,) honesty-gate kills
    stopped_early: bool = False  # a cooperative stop cut the track short
    stopped_at_frame: int | None = None  # 0-based first UNTRACKED frame
    stop_reason: str = ""  # engine's reason string (English)

    @property
    def n_frames(self) -> int:
        return int(self.u_accum.shape[0])

    @property
    def n_tracked(self) -> int:
        """Leading frames with tracked data — ``n_frames`` for a complete run."""
        return self.n_frames if self.stopped_at_frame is None else int(self.stopped_at_frame)


def build_frame_schedule(
    reference_mode: str,
    n_frames: int,
    *,
    ref_update_mode: str = "every_frame",
    ref_update_n: int = 2,
    ref_update_frames: Sequence[int] | None = None,
):
    """The explicit engine ``FrameSchedule`` for a reference-update policy (Q5).

    Returns ``None`` when no explicit schedule is needed — accumulative mode,
    or incremental with the default every-frame update — so ``run_aldic``
    derives its schedule from ``para.reference_mode`` exactly as before (the 2D
    GUI's wiring: an explicit schedule is built only for the non-default
    incremental policies).

    Args:
        reference_mode: ``"accumulative"`` or ``"incremental"``.
        n_frames: total frame count (reference frame 0 included).
        ref_update_mode: ``"every_frame"`` (default) | ``"every_n"`` |
            ``"custom"``.
        ref_update_n: reference interval for ``"every_n"`` (>= 1).
        ref_update_frames: 0-based reference frame indices for ``"custom"``
            (frame 0 is always a reference; the engine validates the rest).
    """
    if reference_mode != "incremental" or ref_update_mode == "every_frame":
        return None
    from al_dic.core.data_structures import FrameSchedule  # DEPENDS_ON_2D.md

    if ref_update_mode == "every_n":
        return FrameSchedule.from_every_n(max(1, int(ref_update_n)), n_frames)
    if ref_update_mode == "custom":
        frames = [int(f) for f in (ref_update_frames or [])]
        return FrameSchedule.from_custom(frames, n_frames)
    raise ValueError(
        f"unknown ref_update_mode {ref_update_mode!r}; "
        f"expected 'every_frame', 'every_n' or 'custom'"
    )


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
    progress: Callable[[float, str], None] | None = None,
    capture_warnings: bool = True,
) -> TemporalField:
    """Track one camera's frames from a fixed reference mesh (accumulative).

    Args:
        progress: optional ``(fraction, message)`` callback forwarded to the
            engine's ``progress_fn`` (P3.6) — the parallel track-both path
            scales and serializes the two cameras' reports through it.
        capture_warnings: promote the engine's silent zero-fill warning to a
            hard error here (default). ``warnings.catch_warnings`` mutates
            process-global state and is NOT thread-safe, so the parallel
            track-both path (P3.6) passes ``False`` and installs ONE
            thread-safe recorder around both tracks instead — the guard is
            then enforced by the caller, never skipped.
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
            ``.astype``-copies what it indexes, al-dic 0.7.0
            ``core/pipeline.py:986,995``) — which keeps the external mesh
            byte-identical so the returned ``ref_coords`` equal
            ``mesh.coordinates_fem`` exactly.
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
        A :class:`TemporalField`. A cooperative stop mid-run (engine 0.7
        partial-results contract: ``run_aldic`` RETURNS on a user cancel with
        ``stopped_early`` set and ``result_disp`` holding the contiguous prefix
        of completed frames) keeps the tracked frames and NaNs the rest — see
        the ``TemporalField`` partial-run fields. Raises ``RuntimeError`` if the
        engine drops frames WITHOUT flagging a stop (``run_aldic`` None-filters
        failures, breaking positional alignment — surfaced rather than silently
        misaligned).
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

    import contextlib
    import warnings

    try:
        # The 2D engine zero-fills an ALL-NaN ICGN field with only a UserWarning
        # ("All nodes are NaN, cannot interpolate. Returning zeros.") — silent
        # zeros would flow downstream as a perfectly "valid" frozen camera (the
        # S3 real-data failure). Promote that warning to a hard error below.
        # ``capture_warnings=False`` (parallel tracks, P3.6): the caller holds
        # ONE thread-safe recorder instead — catch_warnings is process-global.
        capture = (
            warnings.catch_warnings(record=True) if capture_warnings else contextlib.nullcontext([])
        )
        with capture as caught:
            if capture_warnings:
                warnings.simplefilter("always")
            result = run_aldic(
                para,
                # Normalize-on-demand provider (P1.2): the engine otherwise
                # eagerly materializes a full normalized float64 copy of the
                # stack (ListFrameProvider). Byte-identical, streaming instead.
                _EngineFrames(frames, para.gridxy_roi_range),
                masks,
                progress_fn=progress,
                stop_fn=stop,
                compute_strain=False,
                mesh=mesh,
                U0=u0,
            )
    except RuntimeError:
        # Engine 0.7 RETURNS a partial result on a user cancel (handled below),
        # so a RuntimeError here is a genuine failure; when the stop tripped
        # concurrently, normalise to the uniform cooperative-cancel contract
        # (the run was being abandoned either way).
        if stop is not None and stop():
            raise RuntimeError("cancelled") from None
        raise
    for w in caught:
        if "All nodes are NaN" in str(w.message):
            raise RuntimeError(ZERO_FILL_ERROR)
        warnings.warn_explicit(w.message, w.category, w.filename, w.lineno)

    ref_coords = np.asarray(result.dic_mesh.coordinates_fem, dtype=np.float64)
    if ref_coords.shape[0] == 0 and getattr(result, "stopped_early", False):
        # A stop before the FIRST frame completed leaves the engine's canonical
        # mesh empty (PipelineResult.dic_mesh snapshots per COMPLETED frame);
        # fall back to the external mesh so the all-NaN partial field keeps the
        # caller's node count and the strategies' alignment checks still hold.
        ref_coords = np.asarray(mesh.coordinates_fem, dtype=np.float64)
    n = ref_coords.shape[0]
    # Engine 0.7 partial-results contract: a user cancel RETURNS a partial
    # result with ``stopped_early`` set and ``result_disp`` holding the
    # contiguous PREFIX of completed frames (the engine's frame loop only ever
    # breaks — never skips — so None-filtering cannot create mid-list holes;
    # verified against al-dic 0.7.0 core/pipeline.py:937-1712). The tracked
    # prefix is kept; untracked frames stay NaN/invalid below.
    n_done = len(result.result_disp)
    stopped_early = bool(getattr(result, "stopped_early", False))
    stop_reason = str(getattr(result, "stop_reason", "") or "")
    if n_done >= n_frames - 1:
        stopped_early = False  # the stop raced the final frame: nothing lost
        stop_reason = ""
    elif not stopped_early:
        raise RuntimeError(
            f"run_aldic returned {n_done} deformed frames for "
            f"{n_frames - 1} expected without flagging a stop — a frame failed "
            f"and positional alignment is unreliable."
        )
    stopped_at = 1 + n_done if stopped_early else None

    u_accum = np.full((n_frames, n, 2), np.nan, dtype=np.float64)
    u_accum[0] = 0.0  # reference frame: zero displacement by definition
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

    return TemporalField(
        ref_coords=ref_coords,
        u_accum=u_accum,
        valid=valid,
        n_gated=n_gated,
        stopped_early=stopped_early,
        stopped_at_frame=stopped_at,
        stop_reason=stop_reason,
    )


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


class _ResampleGeometryCache:
    """Bounded, thread-safe cache of resampling geometry (P3.4).

    :func:`resample_to_points` is called once per frame from the strategy
    assembly loops, but the FINITE source-node set (and therefore the Delaunay
    triangulation and the nearest-fill KD-tree) rarely changes between frames.
    Entries are keyed by the exact source-point bytes — the coordinates fully
    determine both structures — so a hit is always geometrically identical to
    a rebuild. ``LinearNDInterpolator(tri, values)`` then reuses the cached
    triangulation with the per-frame values.

    ``delaunay_builds`` / ``kdtree_builds`` count actual constructions
    (observability + tests). The lock only guards the map; a rare concurrent
    double-build is idempotent.
    """

    def __init__(self, capacity: int = 4) -> None:
        import threading

        self._capacity = max(1, int(capacity))
        self._lock = threading.Lock()
        self._entries: OrderedDict[bytes, list] = OrderedDict()  # key -> [tri, tree]
        self.delaunay_builds = 0
        self.kdtree_builds = 0

    def _slot(self, key: bytes, idx: int):
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None:
                self._entries.move_to_end(key)
                return entry[idx]
        return None

    def _store(self, key: bytes, idx: int, obj) -> None:
        with self._lock:
            entry = self._entries.setdefault(key, [None, None])
            entry[idx] = obj
            self._entries.move_to_end(key)
            while len(self._entries) > self._capacity:
                self._entries.popitem(last=False)

    def triangulation(self, src: NDArray[np.float64]):
        """Delaunay of ``src`` — cached by the exact point bytes."""
        key = src.tobytes()
        tri = self._slot(key, 0)
        if tri is None:
            from scipy.spatial import Delaunay

            tri = Delaunay(src)
            self.delaunay_builds += 1
            self._store(key, 0, tri)
        return tri

    def kdtree(self, src: NDArray[np.float64]):
        """cKDTree of ``src`` — cached by the exact point bytes (nearest fill)."""
        key = src.tobytes()
        tree = self._slot(key, 1)
        if tree is None:
            from scipy.spatial import cKDTree

            tree = cKDTree(src)
            self.kdtree_builds += 1
            self._store(key, 1, tree)
        return tree

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
            self.delaunay_builds = 0
            self.kdtree_builds = 0


#: Module-level cache shared by every strategy's per-frame resampling calls.
_RESAMPLE_CACHE = _ResampleGeometryCache()


def resample_to_points(
    ref_coords: NDArray[np.float64],
    values: NDArray[np.float64],
    query: NDArray[np.float64],
    *,
    fill_nearest: bool = True,
    reuse_geometry: bool = True,
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
        fill_nearest: back-fill finite out-of-hull queries from the nearest node.
        reuse_geometry: serve the Delaunay/KD-tree from the module cache when
            the finite source-point set repeats across frames (P3.4). The cache
            key is the exact source bytes, so results are identical either way;
            disable only to benchmark or to avoid retaining the geometry.

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

    src = np.ascontiguousarray(ref[finite])
    dst = val[finite]
    if reuse_geometry:
        # LinearNDInterpolator(points, ...) builds Delaunay(points) internally;
        # passing the cached triangulation is the documented equivalent path.
        lin = LinearNDInterpolator(_RESAMPLE_CACHE.triangulation(src), dst)
    else:
        lin = LinearNDInterpolator(src, dst)
    out[:] = lin(q)

    if fill_nearest:
        # Only fill FINITE queries that fell outside the hull; a non-finite query
        # row has no estimate and must stay NaN (documented contract) — never
        # feed it to the KD-tree (scipy raises on non-finite query points).
        missing = (~np.isfinite(out).all(axis=1)) & np.isfinite(q).all(axis=1)
        if missing.any():
            if reuse_geometry:
                # NearestNDInterpolator == cKDTree.query + row gather; reuse
                # the cached tree instead of rebuilding it per frame.
                _, nearest_idx = _RESAMPLE_CACHE.kdtree(src).query(q[missing])
                out[missing] = dst[nearest_idx]
            else:
                nearest = NearestNDInterpolator(src, dst)
                out[missing] = nearest(q[missing])
    return out
