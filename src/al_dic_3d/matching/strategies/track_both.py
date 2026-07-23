"""``TrackBothStrategy`` — the S1 correspondence strategy (02 §5.3).

Both cameras are tracked temporally from their own frame-1 reference; the two
streams are linked ONCE by a frame-1 stereo match. The design deliberately
decouples *where* the correspondence points are (fixed by the L1<->R1 match) from
*how* each camera's pixels move over time (independent dense DIC tracking):

  1. **Frame-1 stereo match** L1->R1 at the reference mesh nodes -> ``right_pts``.
  2. **Left temporal track** on ``mesh_L`` -> cumulative node motion; because the
     corr points ARE the mesh_L nodes, the left position needs no resampling.
  3. **Right temporal track** on an INDEPENDENT dense grid ``mesh_R``, then the
     right field is **resampled** at the scattered ``right_pts``.

Every per-frame position is ``source=TRACKED`` for S1; a point invalid at the
frame-1 stereo link (or that leaves either ROI) is ``NaN``/``INVALID`` for all
frames. The 3D layer downstream reads only the resulting ``CorrespondenceSet``.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import TYPE_CHECKING, ClassVar

import numpy as np

from al_dic_3d.matching.contracts import (
    INVALID,
    TRACKED,
    CorrespondenceConfig,
    CorrespondenceSet,
)
from al_dic_3d.matching.diagnostics import stereo_rows, temporal_rows
from al_dic_3d.matching.primitives import make_dicpara
from al_dic_3d.matching.stereo import stereo_match_pair
from al_dic_3d.matching.strategies._common import (
    bbox_roi,
    frame_view,
    mask_stream,
    resolve_init,
    temporal_u0,
)
from al_dic_3d.matching.strategy import register_strategy
from al_dic_3d.matching.temporal import (
    ZERO_FILL_ERROR,
    build_grid_mesh,
    resample_to_points,
    temporal_track,
)

if TYPE_CHECKING:
    from al_dic import DICMesh  # type-only; ledgered in DEPENDS_ON_2D.md

    from al_dic_3d.calibration import StereoRig
    from al_dic_3d.sequence import StereoSequence

# Fraction of the overall progress covered by the two temporal tracks when
# they run in parallel (P3.6); the assembly loop maps into the remainder so
# the reported fraction stays monotonic.
_TRACK_PROGRESS_SHARE = 0.9


@register_strategy
class TrackBothStrategy:
    """Track-both (S1): per-camera temporal tracking linked by a frame-1 match."""

    name: ClassVar[str] = "track_both"

    def __init__(
        self,
        *,
        winsize: int = 32,
        winstepsize: int = 16,
        winsize_min: int = 8,
        stereo_search: int = 48,
        use_global_step: bool = True,
        admm_max_iter: int = 3,
        fft_search: int = 20,
        temporal_gate_znssd: float = 1.0,
        parallel_cameras: bool = False,
    ) -> None:
        # Matching scale (mesh_R density + subset/template size). Powers-of-two
        # where the 2D validator requires it (winstepsize, winsize_min). Overridable
        # so a run can match a MATLAB baseline's parameters; no-arg construction
        # (as the registry uses) keeps the defaults.
        self.winsize = winsize
        self.winstepsize = winstepsize
        self.winsize_min = winsize_min
        self.stereo_search = stereo_search
        self.use_global_step = use_global_step
        self.admm_max_iter = admm_max_iter
        self.fft_search = fft_search
        self.temporal_gate_znssd = temporal_gate_znssd
        # P3.6 opt-in: run the two independent temporal tracks concurrently
        # (~2x faster on numba/numpy-heavy engines that release the GIL, at
        # the cost of BOTH camera stacks' working sets being live at once).
        self.parallel_cameras = parallel_cameras

    def compute(
        self,
        seq: StereoSequence,
        rig: StereoRig,  # epipolar seeding / QC only — never a math shortcut
        mesh_L: DICMesh,
        cfg: CorrespondenceConfig,
        progress: Callable[[float, str], None] | None = None,
        stop: Callable[[], bool] | None = None,
    ) -> CorrespondenceSet:
        seq.validate()
        n_frames = seq.n_frames
        # Indexed raw-frame views (P1.2): never materialize the camera streams.
        left = frame_view(seq, "L")
        right = frame_view(seq, "R")
        img_h, img_w = seq.providers["L"].shape

        coords_L = np.asarray(mesh_L.coordinates_fem, dtype=np.float64)
        n_pts = coords_L.shape[0]

        mask_L1 = seq.mask("L", 0)
        roi_L = bbox_roi(coords_L, img_h, img_w, margin=self.winsize)
        para_L = make_dicpara(
            img_size=(img_h, img_w),
            roi=roi_L,
            winsize=self.winsize,
            winstepsize=self.winstepsize,
            winsize_min=self.winsize_min,
            img_ref_mask=mask_L1,
            reference_mode=cfg.reference_mode,
            use_global_step=self.use_global_step,
            admm_max_iter=self.admm_max_iter,
            fft_search=self.fft_search,
        )

        # Initial-guess resolution (F2): effective mode + seed-derived stereo
        # offset (an explicit cfg.disparity_offset overrides the seed match).
        init_mode, stereo_offset = resolve_init(cfg, left[0], right[0])

        # (1) frame-1 cross-camera match at the reference mesh nodes.
        disp = stereo_match_pair(
            left[0],
            right[0],
            coords_L,
            para_L,
            disparity_offset=stereo_offset,
            search_radius=self.stereo_search,
        )
        right_pts = disp.right_pts  # (n_pts, 2); NaN where the stereo link failed
        base_valid = disp.valid  # (n_pts,)
        if not base_valid.any():
            raise RuntimeError(
                f"frame-1 stereo match found no valid correspondences "
                f"(0/{n_pts} candidates matched L1->R1; search_radius="
                f"{self.stereo_search}, disparity offset={stereo_offset}) — "
                f"check the seed point / disparity prior and stereo overlap."
            )

        # (2) per-camera temporal tracks. The right camera runs on an
        # INDEPENDENT dense grid over right_pts; its setup (para/mesh/u0) is
        # hoisted BEFORE tracking so both tracks can launch together (P3.6).
        u0_L = temporal_u0(init_mode, left[0], left[1], cfg.seed_point, n_pts)

        valid_rp = np.isfinite(right_pts).all(axis=1)
        roi_R = bbox_roi(right_pts[valid_rp], img_h, img_w, margin=self.winsize)
        mask_R1 = seq.mask("R", 0)
        para_R = make_dicpara(
            img_size=(img_h, img_w),
            roi=roi_R,
            winsize=self.winsize,
            winstepsize=self.winstepsize,
            winsize_min=self.winsize_min,
            img_ref_mask=mask_R1,
            reference_mode=cfg.reference_mode,
            use_global_step=self.use_global_step,
            admm_max_iter=self.admm_max_iter,
            fft_search=self.fft_search,
        )
        mesh_R = build_grid_mesh(para_R, img_h, img_w)
        # The right camera's seed is the stereo-matched location of the left
        # seed (seed + offset); without a usable offset the right track keeps
        # the engine FFT (temporal_u0 handles seed_R=None).
        seed_R = None
        if init_mode == "seed" and stereo_offset is not None and cfg.seed_point is not None:
            seed_R = (
                cfg.seed_point[0] + stereo_offset[0],
                cfg.seed_point[1] + stereo_offset[1],
            )
        n_r_nodes = int(np.asarray(mesh_R.coordinates_fem).shape[0])
        u0_R = temporal_u0(init_mode, right[0], right[1], seed_R, n_r_nodes)

        def _check_left_alignment(tf) -> None:
            if not np.allclose(tf.ref_coords, coords_L, atol=1e-6):
                raise RuntimeError(
                    "left temporal mesh drifted from mesh_L (node re-trim); xL alignment "
                    "cannot be guaranteed — masked temporal tracking is deferred to Phase 2."
                )

        track_kwargs = {
            "L": dict(masks=mask_stream(seq, "L"), u0=u0_L),
            "R": dict(masks=mask_stream(seq, "R"), u0=u0_R),
        }
        if self.parallel_cameras:
            tf_L, tf_R = self._track_parallel(
                left, right, mesh_L, mesh_R, para_L, para_R, track_kwargs, progress, stop
            )
            _check_left_alignment(tf_L)
        else:
            tf_L = temporal_track(
                left,
                mesh_L,
                para_L,
                stop=stop,
                gate_znssd=self.temporal_gate_znssd,
                **track_kwargs["L"],
            )
            _check_left_alignment(tf_L)
            tf_R = temporal_track(
                right,
                mesh_R,
                para_R,
                stop=stop,
                gate_znssd=self.temporal_gate_znssd,
                **track_kwargs["R"],
            )

        # Partial-run bookkeeping (R2, engine 0.7): either camera may have
        # stopped early on a user cancel. A correspondence needs BOTH cameras
        # at frame k, so the kept prefix is the intersection of the two tracked
        # prefixes (a cancel during the LEFT track leaves the right track zero
        # frames — only the frame-0 stereo link survives, and the runner then
        # treats the run as fully cancelled).
        stopped_early = tf_L.stopped_early or tf_R.stopped_early
        stopped_at = min(tf_L.n_tracked, tf_R.n_tracked) if stopped_early else None
        stop_reason = tf_L.stop_reason or tf_R.stop_reason

        # (3) assemble the CorrespondenceSet frame by frame. Deliberately NO
        # stop poll here: the heavy engine work is already done, assembling the
        # frames that DID track is cheap, and it is exactly the partial result
        # a cancel promises to keep (untracked frames are all-NaN in tf_L/tf_R
        # and assemble to INVALID rows on their own).
        xL = np.full((n_frames, n_pts, 2), np.nan, dtype=np.float64)
        xR = np.full((n_frames, n_pts, 2), np.nan, dtype=np.float64)
        quality = np.full((n_frames, n_pts), np.nan, dtype=np.float64)
        source = np.full((n_frames, n_pts), INVALID, dtype=np.uint8)

        for k in range(n_frames):
            xl_k = coords_L + tf_L.u_accum[k]

            motion_r = np.full((n_pts, 2), np.nan, dtype=np.float64)
            if valid_rp.any():
                motion_r[valid_rp] = resample_to_points(
                    tf_R.ref_coords, tf_R.u_accum[k], right_pts[valid_rp]
                )
            xr_k = right_pts + motion_r

            good = (
                base_valid
                & tf_L.valid[k]
                & np.isfinite(xl_k).all(axis=1)
                & np.isfinite(xr_k).all(axis=1)
            )
            xL[k][good] = xl_k[good]
            xR[k][good] = xr_k[good]
            # For S1 the correspondence quality is set by the frame-1 stereo link
            # (the weakest point); per-frame temporal ZNSSD is a Phase-2 refinement.
            quality[k][good] = disp.znssd[good]
            source[k][good] = TRACKED

            if progress is not None:
                frac = (k + 1) / n_frames
                if self.parallel_cameras:
                    # The tracks already reported [0, _TRACK_PROGRESS_SHARE];
                    # the assembly covers the remainder (monotonic overall).
                    frac = _TRACK_PROGRESS_SHARE + (1.0 - _TRACK_PROGRESS_SHARE) * frac
                progress(frac, f"track_both frame {k + 1}/{n_frames}")

        # F3.1: per-stage failure accounting rides along with the result.
        diagnostics = (
            *stereo_rows(disp),
            *temporal_rows("L", tf_L),
            *temporal_rows("R", tf_R),
        )
        return CorrespondenceSet(
            strategy=self.name,
            xL=xL,
            xR=xR,
            quality=quality,
            source=source,
            diagnostics=diagnostics,
            stopped_early=stopped_early,
            stopped_at_frame=stopped_at,
            stop_reason=stop_reason,
        )

    def _track_parallel(
        self,
        left,
        right,
        mesh_L,
        mesh_R,
        para_L,
        para_R,
        track_kwargs: dict,
        progress: Callable[[float, str], None] | None,
        stop: Callable[[], bool] | None,
    ):
        """Run the two independent temporal tracks concurrently (P3.6, opt-in).

        The engine is numba/numpy-heavy (the GIL is mostly released), so two
        threads overlap well. Per-camera progress (each 0..1) is serialized
        under a lock and combined as equal halves of the tracks' overall share.
        A failure/cancel in either camera trips a shared abort so the sibling
        exits at its next cooperative checkpoint instead of running to
        completion. The honesty gate and diagnostics stay per-camera — each
        ``temporal_track`` call returns its own :class:`TemporalField`.

        ``warnings.catch_warnings`` is process-global (NOT thread-safe), so the
        per-call capture inside ``temporal_track`` is disabled here and ONE
        thread-safe recorder wraps both tracks instead — the engine's silent
        zero-fill warning still becomes a hard error, never lost to a race.
        """
        import warnings
        from concurrent.futures import ThreadPoolExecutor

        abort = threading.Event()

        def stop_fn() -> bool:
            return abort.is_set() or bool(stop is not None and stop())

        lock = threading.Lock()
        fractions = {"L": 0.0, "R": 0.0}

        def cam_progress(cam: str) -> Callable[[float, str], None] | None:
            if progress is None:
                return None

            def cb(frac: float, msg: str) -> None:
                with lock:  # serialize the two threads' reports
                    fractions[cam] = min(1.0, max(0.0, float(frac)))
                    overall = 0.5 * (fractions["L"] + fractions["R"]) * _TRACK_PROGRESS_SHARE
                    progress(overall, f"{cam}: {msg}")

            return cb

        def run(cam: str, frames, mesh, para):
            return temporal_track(
                frames,
                mesh,
                para,
                stop=stop_fn,
                gate_znssd=self.temporal_gate_znssd,
                progress=cam_progress(cam),
                capture_warnings=False,  # ONE recorder below (thread safety)
                **track_kwargs[cam],
            )

        records: list[tuple] = []
        rec_lock = threading.Lock()

        def _record(message, category, filename, lineno, file=None, line=None):  # noqa: ARG001
            with rec_lock:
                records.append((message, category, filename, lineno))

        with warnings.catch_warnings():  # entered by THIS thread only
            warnings.simplefilter("always")
            warnings.showwarning = _record
            with ThreadPoolExecutor(max_workers=2, thread_name_prefix="track_both") as pool:
                futures = {
                    "L": pool.submit(run, "L", left, mesh_L, para_L),
                    "R": pool.submit(run, "R", right, mesh_R, para_R),
                }
                results: dict = {}
                first_error: BaseException | None = None
                for cam in ("L", "R"):
                    try:
                        results[cam] = futures[cam].result()
                    except BaseException as exc:  # noqa: BLE001 - re-raised below
                        abort.set()  # the sibling aborts at its next checkpoint
                        if first_error is None:
                            first_error = exc
                if first_error is not None:
                    raise first_error
        # Enforce temporal_track's zero-fill guard from the shared recorder
        # (either camera trips it); re-emit everything else on the restored
        # warning state so engine notices (e.g. FFT auto-scaling) stay visible.
        for message, category, filename, lineno in records:
            if "All nodes are NaN" in str(message):
                raise RuntimeError(ZERO_FILL_ERROR)
            warnings.warn_explicit(message, category, filename, lineno)
        return results["L"], results["R"]
