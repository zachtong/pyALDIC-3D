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

import re
import threading
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

from al_dic_3d.matching.gate import _GATE_MAX_WORKERS, _gate_workers, gate_by_znssd  # noqa: F401
from al_dic_3d.matching.resample import (  # noqa: F401 - re-exported (moved, fix batch V)
    _RESAMPLE_CACHE,
    _long_simplices,
    _ResampleGeometryCache,
    node_spacing,
    resample_to_points,
)
from al_dic_3d.sequence.lazy import as_binary_mask, binary_mask_sequence

# Raw frames indexed like a list: a real ``list`` of arrays (tests, GUI small
# runs) or any lazy view exposing ``__len__``/``__getitem__`` (perf batch P1.2).
FrameSeq = Sequence[NDArray[np.float64]]

# Hard error raised when the engine silently zero-filled an all-NaN field —
# shared with the parallel track-both path, which enforces the same guard from
# its own thread-safe warning recorder (P3.6).
_FRAME_RE = re.compile(r"Frame (\d+)/\d+")

ZERO_FILL_ERROR = (
    "2D engine solved NO nodes (all-NaN field silently zero-filled): "
    "the temporal track failed outright — check masks/ROI/texture "
    "instead of trusting a frozen zero-displacement camera."
)

# Share of ONE camera's temporal-track progress owned by the 2D engine's solve
# loop; the ZNSSD honesty gate reports over the remainder (perf batch P4).
# The gate re-verifies every tracked frame AFTER run_aldic returns, so on long
# sequences it is a large, previously INVISIBLE slice of the wall time — the
# 400-frame Tier B run froze the bar at 100% for ~16 min per camera. Splitting
# the band keeps one camera's reported fraction monotonic across both stages.
_ENGINE_PROGRESS_SHARE = 0.6

# Per-thread zero-fill bookkeeping for tracks that do not capture warnings
# themselves (the parallel track-both path holds ONE process-wide recorder).
# The recorder runs in the thread that emitted the warning, so it can pin the
# warning to that thread's camera and frame (fix batch V: in parallel mode one
# unsolvable frame used to fail the whole run instead of that frame).
_ZERO_FILL_LOCAL = threading.local()


def note_zero_fill() -> bool:
    """Record an engine zero-fill for the calling thread's track, if one is running.

    Called by an external warning recorder. Returns True when the warning was
    attributed (the caller should then drop it), False when the calling thread
    is not inside a non-capturing :func:`track_engine`.
    """
    if not getattr(_ZERO_FILL_LOCAL, "active", False):
        return False
    _ZERO_FILL_LOCAL.frames.add(int(_ZERO_FILL_LOCAL.frame))
    return True


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
    # (n_frames, n) final honesty-gate ZNSSD per verified node (NaN elsewhere);
    # None when the gate was disabled. Feeds the per-frame correspondence quality.
    znssd: NDArray[np.float64] | None = None
    # Frames on which the 2D engine solved NO node and silently zero-filled the
    # field (fix batch V): invalidated here instead of failing the whole track.
    zero_filled: tuple[int, ...] = ()
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
    verify_partial: bool = True,
) -> TemporalField:
    """Track one camera's frames from a fixed reference mesh (accumulative).

    Args:
        verify_partial: what to do when a cooperative stop ended the ENGINE
            early. ``True`` (default) verifies every frame the engine finished
            with the honesty gate, ignoring the stop, so the kept partial result
            is the whole tracked prefix (fix batch V: the gate used to see the
            already-tripped stop after its first frame and drop every later
            tracked frame, so a cancel kept one frame at most). ``False`` skips
            the verification and drops the unverified frames -- for a caller
            that will discard this track anyway (track-both's left camera when
            the right camera will not be tracked).
        progress: optional ``(fraction, message)`` callback covering the WHOLE
            track: the engine's own ``progress_fn`` is rescaled into
            ``[0, _ENGINE_PROGRESS_SHARE]`` and the ZNSSD honesty gate reports
            over the remainder ("verifying frame k/N"), so the fraction rises
            monotonically to 1.0 instead of freezing at 100% for the length of
            the gate (P4). The parallel track-both path scales and serializes
            the two cameras' reports through it (P3.6).
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
    return finish_track(
        track_engine(
            frames,
            mesh,
            para,
            masks=masks,
            u0=u0,
            stop=stop,
            gate_znssd=gate_znssd,
            progress=progress,
            capture_warnings=capture_warnings,
            verify_partial=verify_partial,
        )
    )


@dataclass
class EngineTrack:
    """One camera's engine output awaiting the honesty gate (:func:`finish_track`).

    Fix batch V split :func:`temporal_track` into its engine phase and its
    verification phase so track-both can verify the left camera while the
    right camera's engine runs. Arrays are filled in place by the gate.
    """

    frames: object
    mask0: NDArray[np.float64]
    ref_coords: NDArray[np.float64]
    u_accum: NDArray[np.float64]
    valid: NDArray[np.bool_]
    para: DICPara
    gate_znssd: float
    stop: Callable[[], bool] | None
    report: Callable[[float, str], None] | None
    stopped_early: bool
    stopped_at: int | None
    stop_reason: str
    zero_filled: tuple[int, ...]
    verify_partial: bool

    @property
    def n_tracked(self) -> int:
        """Leading frames the engine tracked (before any verification)."""
        n = int(self.u_accum.shape[0])
        return n if self.stopped_at is None else int(self.stopped_at)


def track_engine(
    frames: FrameSeq,
    mesh: DICMesh,
    para: DICPara,
    masks: Sequence[NDArray[np.float64]] | None = None,
    u0: NDArray[np.float64] | None = None,
    stop: Callable[[], bool] | None = None,
    gate_znssd: float = 1.0,
    progress: Callable[[float, str], None] | None = None,
    capture_warnings: bool = True,
    verify_partial: bool = True,
) -> EngineTrack:
    """Engine phase of :func:`temporal_track` (everything before the honesty gate)."""
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
    masks = binary_mask_sequence(masks)  # {0,1} float64 — see as_binary_mask
    mask0 = as_binary_mask(masks[0])  # engine mutates para

    import contextlib
    import warnings

    report = _Ratchet(progress) if progress is not None else None
    # The engine's own "Frame k/N" progress messages say which deformed frame is
    # in flight, so a zero-fill warning can be pinned to its frame (fix batch V).
    engine_frame = [0]

    def engine_progress(frac: float, msg: str) -> None:
        m = _FRAME_RE.search(str(msg))
        if m:
            engine_frame[0] = int(m.group(1))
            _ZERO_FILL_LOCAL.frame = engine_frame[0]
        if report is not None:
            report(_clamp01(frac) * _ENGINE_PROGRESS_SHARE, msg)

    try:
        # The 2D engine zero-fills an ALL-NaN ICGN field with only a UserWarning
        # ("All nodes are NaN, cannot interpolate. Returning zeros.") — silent
        # zeros would flow downstream as a perfectly "valid" frozen camera (the
        # S3 real-data failure). Promote that warning to a hard error below.
        # ``capture_warnings=False`` (parallel tracks, P3.6): the caller holds
        # ONE thread-safe recorder instead — catch_warnings is process-global.
        caught: list[tuple[int, warnings.WarningMessage]] = []
        if not capture_warnings:
            _ZERO_FILL_LOCAL.active = True
            _ZERO_FILL_LOCAL.frames = set()
            _ZERO_FILL_LOCAL.frame = 0
        capture = warnings.catch_warnings() if capture_warnings else contextlib.nullcontext()
        with capture:
            if capture_warnings:
                warnings.simplefilter("always")

                def _record(message, category, filename, lineno, file=None, line=None):  # noqa: ARG001
                    caught.append(
                        (
                            engine_frame[0],
                            warnings.WarningMessage(message, category, filename, lineno),
                        )
                    )

                warnings.showwarning = _record
            result = run_aldic(
                para,
                # Normalize-on-demand provider (P1.2): the engine otherwise
                # eagerly materializes a full normalized float64 copy of the
                # stack (ListFrameProvider). Byte-identical, streaming instead.
                _EngineFrames(frames, para.gridxy_roi_range),
                masks,
                progress_fn=engine_progress,
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
    finally:
        external = set(getattr(_ZERO_FILL_LOCAL, "frames", ()) or ())
        _ZERO_FILL_LOCAL.active = False
        _ZERO_FILL_LOCAL.frames = set()
    zero_filled: set[int] = set() if capture_warnings else external
    for frame_k, w in caught:
        if "All nodes are NaN" in str(w.message):
            zero_filled.add(int(frame_k))
            continue
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

    # A frame the engine zero-filled carries NO information — invalidate it
    # (never ship a frozen camera as valid), keep every other frame: each one is
    # verified independently against frame 0 by the honesty gate below. Only
    # when NO deformed frame survives is the track a failure.
    zero_filled_frames = tuple(sorted(k for k in zero_filled if 0 < k < n_frames))
    for k in zero_filled_frames:
        u_accum[k] = np.nan
        valid[k] = False
    if zero_filled_frames and not valid[1:].any():
        raise RuntimeError(ZERO_FILL_ERROR)

    return EngineTrack(
        frames=frames,
        mask0=mask0,
        ref_coords=ref_coords,
        u_accum=u_accum,
        valid=valid,
        para=para,
        gate_znssd=gate_znssd,
        stop=stop,
        report=report,
        stopped_early=stopped_early,
        stopped_at=stopped_at,
        stop_reason=stop_reason,
        zero_filled=zero_filled_frames,
        verify_partial=verify_partial,
    )


def finish_track(et: EngineTrack) -> TemporalField:
    """Verification phase of :func:`temporal_track`: honesty gate, then the field."""
    frames, mask0, ref_coords, para = et.frames, et.mask0, et.ref_coords, et.para
    u_accum, valid, gate_znssd, stop, report = (
        et.u_accum,
        et.valid,
        et.gate_znssd,
        et.stop,
        et.report,
    )
    stopped_early, stopped_at, stop_reason = et.stopped_early, et.stopped_at, et.stop_reason
    zero_filled_frames, verify_partial = et.zero_filled, et.verify_partial
    n_gated = None
    gate_z = None
    engine_stopped = stopped_early
    if engine_stopped and gate_znssd > 0 and not verify_partial:
        # The caller discards this partial track: skip verifying it and drop
        # the frames rather than ship them unverified.
        u_accum[1:] = np.nan
        valid[1:] = False
        stopped_at = 1
    elif gate_znssd > 0:
        gate_z = np.full(u_accum.shape[:2], np.nan, dtype=np.float64)
        gate_progress = None
        if report is not None:

            def gate_progress(frac: float, msg: str) -> None:
                span = 1.0 - _ENGINE_PROGRESS_SHARE
                if engine_stopped:
                    msg = f"{msg} (keeping the frames tracked before the stop)"
                report(_ENGINE_PROGRESS_SHARE + span * _clamp01(frac), msg)

        n_gated, gate_stopped_at = _gate_by_znssd(
            frames,
            mask0,
            ref_coords,
            u_accum,
            valid,
            para,
            gate_znssd,
            progress=gate_progress,
            # A stop that already ended the engine has done its job; the frames
            # it left are the partial result and must all be verified. A stop
            # that trips DURING verification of a complete run still cuts the
            # pass short (P4) and drops the unverified frames.
            stop=None if engine_stopped else stop,
            znssd_out=gate_z,
        )
        if gate_stopped_at is not None:
            # A cancel cut the verification short. Frames the gate never reached
            # were never verified, and shipping an UNVERIFIED frame as tracked is
            # exactly the silent-failure shape this gate exists to stop (S3), so
            # they are dropped like any other untracked frame (R2 partial-run
            # contract). ``stopped_at`` only ever shrinks.
            stopped_at = gate_stopped_at if stopped_at is None else min(stopped_at, gate_stopped_at)
            u_accum[stopped_at:] = np.nan
            valid[stopped_at:] = False
            gate_z[stopped_at:] = np.nan
            stopped_early = True
            stop_reason = stop_reason or "Computation cancelled by user."
    if report is not None:
        # Always land on 1.0 — with the gate disabled the engine band alone
        # would leave this camera's share stuck at _ENGINE_PROGRESS_SHARE.
        report(1.0, "temporal track complete")

    return TemporalField(
        ref_coords=ref_coords,
        u_accum=u_accum,
        valid=valid,
        n_gated=n_gated,
        stopped_early=stopped_early,
        stopped_at_frame=stopped_at,
        stop_reason=stop_reason,
        znssd=gate_z,
        zero_filled=zero_filled_frames,
    )


def _clamp01(value: float) -> float:
    """Clamp a reported progress fraction into ``[0, 1]``."""
    return min(1.0, max(0.0, float(value)))


class _Ratchet:
    """Progress sink whose reported fraction never decreases.

    The 2D engine's own ``progress_fn`` is NOT monotonic (al-dic 0.7 reports the
    end-of-loop fraction and then a LOWER "Assembling results..." tick,
    ``core/pipeline.py:1716,1832``), and the 2D repo is read-only. A bar that
    jumps backwards reads as a stall or a restart, so the number is ratcheted
    here — for the engine band, the gate band and their junction alike. Messages
    always pass through unchanged; only the fraction is clamped upward.
    """

    __slots__ = ("_fn", "_high")

    def __init__(self, fn: Callable[[float, str], None]) -> None:
        self._fn = fn
        self._high = 0.0

    def __call__(self, frac: float, msg: str) -> None:
        self._high = max(self._high, _clamp01(frac))
        self._fn(self._high, msg)


def _gate_by_znssd(
    frames: FrameSeq,
    mask0: NDArray[np.float64],
    ref_coords: NDArray[np.float64],
    u_accum: NDArray[np.float64],
    valid: NDArray[np.bool_],
    para: DICPara,
    threshold: float,
    *,
    progress: Callable[[float, str], None] | None = None,
    stop: Callable[[], bool] | None = None,
    workers: int | None = None,
    affine: bool = True,
    znssd_out: NDArray[np.float64] | None = None,
) -> tuple[NDArray[np.int64], int | None]:
    """Honesty gate for one camera track — see :func:`al_dic_3d.matching.gate.gate_by_znssd`."""
    return gate_by_znssd(
        frames,
        mask0,
        ref_coords,
        u_accum,
        valid,
        int(para.winsize),
        threshold,
        progress=progress,
        stop=stop,
        workers=workers,
        affine=affine,
        znssd_out=znssd_out,
    )
