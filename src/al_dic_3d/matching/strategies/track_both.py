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

import sys
import threading
import warnings
from collections.abc import Callable
from typing import TYPE_CHECKING, ClassVar

import numpy as np
from numpy.typing import NDArray

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
    effective_seed_points,
    frame_view,
    map_seeds_left_to_right,
    mask_stream,
    resolve_init,
    stereo_seed_u0,
    temporal_camera_u0,
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

# Fraction of the overall progress covered by the two temporal tracks (P3.6);
# the assembly loop maps into the remainder so the reported fraction stays
# monotonic. Parallel: the two cameras share the band as equal halves, each
# reporting 0..1 of its own track. Sequential: the band is split into two
# consecutive halves, L then R (P4 — before that the sequential path forwarded
# no track progress at all, so the DEFAULT configuration showed nothing at all
# while both cameras tracked, then jumped during assembly).
_TRACK_PROGRESS_SHARE = 0.9


def _camera_band(cam: str, progress: Callable[[float, str], None] | None):
    """Map one camera's own 0..1 track progress into its half of the band."""
    if progress is None:
        return None
    offset = 0.0 if cam == "L" else 0.5

    def cb(frac: float, msg: str) -> None:
        share = min(1.0, max(0.0, float(frac))) * 0.5 + offset
        progress(share * _TRACK_PROGRESS_SHARE, f"{cam}: {msg}")

    return cb


def _derive_right_barrier(
    mask_left: NDArray[np.float64],
    coords_left: NDArray[np.float64],
    right_pts: NDArray[np.float64],
    mesh_right: DICMesh,
    out_shape: tuple[int, int],
) -> NDArray[np.float64] | None:
    """Warp the LEFT crack barrier into the RIGHT camera (Batch C, C2), or None.

    In the common configuration the user draws the ROI (with its thin crack
    barrier) on the LEFT camera only, so the right camera would bridge/smooth
    the crack. The frame-1 stereo correspondence ``coords_left -> right_pts``
    warps the left mask into right pixel space (reusing
    :func:`al_dic_3d.viz3d.maskwarp.warp_mask_left_to_right`, the same machinery
    the renderer uses). The result is returned ONLY when it actually cuts the
    fresh right grid — i.e. a thin barrier really is present — so a crack-free /
    plain-ROI run derives nothing and the right track stays byte-identical.
    """
    import warnings

    from al_dic_3d.matching.crack_mesh import mask_cuts_mesh
    from al_dic_3d.viz3d.maskwarp import warp_mask_left_to_right

    try:
        warped = warp_mask_left_to_right(
            np.asarray(mask_left, dtype=np.float64) > 0.5, coords_left, right_pts, out_shape
        )
    except Exception as exc:  # noqa: BLE001 - warp failure must not kill the run
        warnings.warn(
            f"could not warp the left crack barrier into the right camera "
            f"({type(exc).__name__}: {exc}); the right track is not crack-aware.",
            UserWarning,
            stacklevel=2,
        )
        return None
    if warped is None:
        return None
    barrier = warped.astype(np.float64)
    return barrier if mask_cuts_mesh(mesh_right, barrier) else None


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
        fft_auto_expand: bool = True,
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
        self.fft_auto_expand = fft_auto_expand
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
            fft_auto_expand=self.fft_auto_expand,
            frame_schedule=cfg.schedule_L,
        )

        # Initial-guess resolution (F2): effective mode + seed-derived stereo
        # offset (an explicit cfg.disparity_offset overrides the seed match).
        init_mode, stereo_offset = resolve_init(cfg, left[0], right[0])
        seeds_L = effective_seed_points(cfg) if init_mode == "seed" else ()
        primary_L = seeds_L[0] if seeds_L else cfg.seed_point  # single-seed fallback

        # (1) frame-1 cross-camera match at the reference mesh nodes. Batch S:
        # in seed mode the placed seeds propagate a per-node L->R disparity prior
        # (strong under wide-baseline disparity gradients); else the scalar
        # offset + per-point NCC search exactly as before.
        stereo_prior = stereo_seed_u0(
            init_mode,
            left[0],
            right[0],
            mesh_L,
            mask_L1,
            seeds_L,
            para_L,
            search_radius=self.stereo_search,
        )
        disp = stereo_match_pair(
            left[0],
            right[0],
            coords_L,
            para_L,
            disparity_offset=stereo_offset,
            search_radius=self.stereo_search,
            seed_u0=stereo_prior,
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
        # Batch S: the left track's U0 is the F-aware propagated field over the
        # placed seeds (falls back to the single-seed uniform / FFT path).
        u0_L = temporal_camera_u0(
            init_mode,
            left[0],
            left[1],
            mesh_L,
            mask_L1,
            seeds_L,
            primary_L,
            para_L,
            n_pts,
            search_radius=self.fft_search,
        )

        valid_rp = np.isfinite(right_pts).all(axis=1)
        roi_R = bbox_roi(right_pts[valid_rp], img_h, img_w, margin=self.winsize)
        mask_R1 = seq.mask("R", 0)
        right_masks = mask_stream(seq, "R")
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
            fft_auto_expand=self.fft_auto_expand,
            frame_schedule=cfg.schedule_R,
        )
        mesh_R = build_grid_mesh(para_R, img_h, img_w)
        # Batch C item 1 + C2: cut the right camera's external mesh at any thin
        # crack barrier. When only the LEFT mask carries the barrier (the common
        # config the runner auto-derives) the right reference mask is None here;
        # warp the left barrier into the right camera through the frame-1
        # correspondence so the RIGHT mesh is cut AND the right per-frame masks
        # feed the engine's crack-aware cumulative composition. Gated on the
        # warped mask actually cutting the fresh right grid, so crack-free /
        # plain-ROI runs leave mesh_R and the right mask stream byte-identical.
        from al_dic_3d.matching.crack_mesh import cut_mesh_at_barriers

        if mask_R1 is None and mask_L1 is not None:
            warped_R = _derive_right_barrier(mask_L1, coords_L, right_pts, mesh_R, (img_h, img_w))
            if warped_R is not None:
                mask_R1 = warped_R
                right_masks = [warped_R] * n_frames
        mesh_R = cut_mesh_at_barriers(mesh_R, mask_R1)
        # The right camera's seeds are the placed left seeds mapped into the
        # right frame (per-seed L->R NCC); the single-seed prior (seed + offset)
        # remains the fallback for the uniform path. Without a usable offset the
        # right track keeps the engine FFT (temporal_camera_u0 handles None).
        seeds_R = map_seeds_left_to_right(left[0], right[0], seeds_L) if seeds_L else ()
        seed_R = None
        if init_mode == "seed" and stereo_offset is not None and primary_L is not None:
            seed_R = (
                primary_L[0] + stereo_offset[0],
                primary_L[1] + stereo_offset[1],
            )
        n_r_nodes = int(np.asarray(mesh_R.coordinates_fem).shape[0])
        u0_R = temporal_camera_u0(
            init_mode,
            right[0],
            right[1],
            mesh_R,
            mask_R1,
            seeds_R,
            seed_R,
            para_R,
            n_r_nodes,
            search_radius=self.fft_search,
        )

        def _check_left_alignment(tf) -> None:
            if not np.allclose(tf.ref_coords, coords_L, atol=1e-6):
                raise RuntimeError(
                    "left temporal mesh drifted from mesh_L (node re-trim); xL alignment "
                    "cannot be guaranteed — masked temporal tracking is deferred to Phase 2."
                )

        track_kwargs = {
            "L": dict(masks=mask_stream(seq, "L"), u0=u0_L),
            "R": dict(masks=right_masks, u0=u0_R),
        }
        if self.parallel_cameras and sys.platform == "darwin":
            # numba's default macOS threading layer (workqueue) ABORTS the
            # process when two host threads enter JIT-parallel regions
            # concurrently — reproduced on the first macOS CI run (Abort
            # trap 6 in the parallel-cameras test). The measured gain is only
            # ~1.1x (the solver already saturates all cores), so on macOS we
            # run the two tracks sequentially instead of crashing.
            warnings.warn(
                "parallel camera tracking is unavailable on macOS "
                "(numba workqueue threading-layer constraint); "
                "running the two cameras sequentially.",
                UserWarning,
                stacklevel=2,
            )
        if self.parallel_cameras and sys.platform != "darwin":
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
                progress=_camera_band("L", progress),
                **track_kwargs["L"],
            )
            _check_left_alignment(tf_L)
            tf_R = temporal_track(
                right,
                mesh_R,
                para_R,
                stop=stop,
                gate_znssd=self.temporal_gate_znssd,
                progress=_camera_band("R", progress),
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
                # Both paths already reported [0, _TRACK_PROGRESS_SHARE] from the
                # two tracks; the assembly covers the remainder (monotonic).
                frac = _TRACK_PROGRESS_SHARE + (1.0 - _TRACK_PROGRESS_SHARE) * ((k + 1) / n_frames)
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
