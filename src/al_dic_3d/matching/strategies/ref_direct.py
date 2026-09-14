"""``RefDirectStrategy`` — the S3 correspondence strategy (02 §2, §5).

Everything anchors to the frame-1 reference:

  1. **Left temporal track** (accumulative, forced) on ``mesh_L`` ->
     ``x_L^k = X_L + U_L^k``.
  2. **Direct cross match** ``m^k = M(L1 -> R_k)`` — from the LEFT reference image
     ``L1`` at the reference nodes ``X_L`` into the RIGHT frame ``R_k`` — via the
     scattered local IC-GN primitive; ``x_R^k = X_L + m^k``. Chain-seeded from
     ``m^{k-1}`` so the seed keeps up with the accumulating deformation.

Error structure is the cleanest of the three: ``err(x_R^k) = ε_M(k)`` — a single
match, no composition, no interpolation, ZERO drift. The price is that ``M``
absorbs the view difference AND all accumulated deformation at once, so a
first-order warp fails first under large deformation (a seed failure only slows
convergence — it never propagates error, because each ``m^k`` solves against
``L1`` independently). Best for small-deformation / metrology (02 §3).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, ClassVar

import numpy as np

from al_dic_3d.matching.contracts import (
    INVALID,
    TRACKED,
    CorrespondenceConfig,
    CorrespondenceSet,
)
from al_dic_3d.matching.diagnostics import frame_row, stereo_rows, temporal_rows
from al_dic_3d.matching.primitives import make_dicpara, match_points, prepare_reference
from al_dic_3d.matching.stereo import accept_field, accept_links, stereo_match_pair
from al_dic_3d.matching.strategies._common import (
    bbox_roi,
    effective_seed_points,
    frame_view,
    loop_frac,
    mask_stream,
    resolve_init,
    setup_note,
    stereo_search_centre,
    stereo_seed_u0,
    temporal_camera_u0,
    track_band,
)
from al_dic_3d.matching.strategy import register_strategy
from al_dic_3d.matching.temporal import temporal_track

if TYPE_CHECKING:
    from al_dic import DICMesh  # type-only; ledgered in DEPENDS_ON_2D.md

    from al_dic_3d.calibration import StereoRig
    from al_dic_3d.sequence import StereoSequence


@register_strategy
class RefDirectStrategy:
    """Ref-direct (S3): left temporal (acc) + direct L1 -> R_k cross matches."""

    name: ClassVar[str] = "ref_direct"

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
    ) -> None:
        self.winsize = winsize
        self.winstepsize = winstepsize
        self.winsize_min = winsize_min
        self.stereo_search = stereo_search
        self.use_global_step = use_global_step
        self.admm_max_iter = admm_max_iter
        self.fft_search = fft_search
        self.fft_auto_expand = fft_auto_expand
        self.temporal_gate_znssd = temporal_gate_znssd

    def compute(
        self,
        seq: StereoSequence,
        rig: StereoRig,
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
        # S3 is reference-direct by definition, so the left chain is forced
        # accumulative (frame 1 is the anchor for BOTH cameras).
        para_L = make_dicpara(
            img_size=(img_h, img_w),
            roi=roi_L,
            winsize=self.winsize,
            winstepsize=self.winstepsize,
            winsize_min=self.winsize_min,
            img_ref_mask=mask_L1,
            reference_mode="accumulative",
            use_global_step=self.use_global_step,
            admm_max_iter=self.admm_max_iter,
            fft_search=self.fft_search,
            fft_auto_expand=self.fft_auto_expand,
        )

        # Initial-guess resolution (F2): effective mode + seed-derived stereo
        # offset (an explicit cfg.disparity_offset overrides the seed match).
        init_mode, stereo_offset = resolve_init(cfg, left[0], right[0])
        seeds_L = effective_seed_points(cfg) if init_mode == "seed" else ()
        primary_L = seeds_L[0] if seeds_L else cfg.seed_point  # single-seed fallback

        # Batch S: F-aware propagated left-track U0 (falls back to single-seed).
        setup_note(progress, "Setup: left-camera initial guess")
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
        # Per-node L->R disparity prior for the frame-0 stereo match (seed mode).
        setup_note(progress, "Setup: frame-1 stereo disparity prior")
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
        tf_L = temporal_track(
            left,
            mesh_L,
            para_L,
            masks=mask_stream(seq, "L"),
            u0=u0_L,
            stop=stop,
            gate_znssd=self.temporal_gate_znssd,
            progress=track_band(progress),
        )
        if not np.allclose(tf_L.ref_coords, coords_L, atol=1e-6):
            raise RuntimeError("left temporal mesh drifted from mesh_L (masked track = Phase 2b)")

        xL = np.full((n_frames, n_pts, 2), np.nan, dtype=np.float64)
        xR = np.full((n_frames, n_pts, 2), np.nan, dtype=np.float64)
        quality = np.full((n_frames, n_pts), np.nan, dtype=np.float64)
        source = np.full((n_frames, n_pts), INVALID, dtype=np.uint8)

        diag: list[dict] = list(temporal_rows("L", tf_L))
        prev_m = np.zeros((n_pts, 2), dtype=np.float64)  # chain seed for M(L1 -> R_k)
        # The reference side of every L1 -> R_k match is the same (left frame 0
        # at the fixed nodes): build its gradient + subset precompute ONCE.
        ref_subsets = None
        # Partial-run bookkeeping (R2): S3 does REAL per-frame cross-match work,
        # so the loop still honours the stop — frames matched before the break
        # are kept (already written into xL/xR), later frames stay NaN.
        loop_stopped_at: int | None = None
        for k in range(n_frames):
            if stop is not None and stop():
                loop_stopped_at = k
                break
            xl_k = coords_L + tf_L.u_accum[k]
            valid_l = tf_L.valid[k] & np.isfinite(xl_k).all(axis=1)

            if k == 0:
                # m^0 = M(L1 -> R_1) is the frame-1 stereo disparity (NCC-seeded).
                stereo_prior, stereo_centre, stereo_note = stereo_search_centre(
                    stereo_prior,
                    stereo_offset,
                    left[0],
                    right[0],
                    mesh_L,
                    mask_L1,
                    rig,
                    para_L,
                    search_radius=self.stereo_search,
                )
                field = stereo_match_pair(
                    left[0],
                    right[0],
                    coords_L,
                    para_L,
                    disparity_offset=stereo_centre,
                    search_radius=self.stereo_search,
                    frame_idx=0,
                    seed_u0=stereo_prior,
                )
                field, n_rz, n_re = accept_field(
                    field,
                    rig=rig,
                    znssd_max=cfg.stereo_znssd_max,
                    epipolar_max_px=cfg.stereo_epipolar_max_px,
                )
                m_k, znssd_k, valid_m = field.d, field.znssd, field.valid
                diag += stereo_rows(field, note=stereo_note, rejected=(n_rz, n_re))
                if not valid_m.any():
                    raise RuntimeError(
                        f"frame-1 stereo match found no valid correspondences "
                        f"(0/{n_pts} candidates matched L1->R1; search_radius="
                        f"{self.stereo_search}, disparity offset={stereo_offset}) — "
                        f"check the seed point / disparity prior and stereo overlap."
                    )
            else:
                # Direct L1 -> R_k match at the reference nodes X_L, chain-seeded
                # from m^{k-1} (seed keeps up with the accumulating deformation).
                if ref_subsets is None:
                    ref_subsets = prepare_reference(left[0], coords_L, para_L)
                m_k, znssd_k, valid_m = match_points(
                    left[0],
                    right[k],
                    coords_L,
                    np.nan_to_num(prev_m, nan=0.0),
                    para_L,
                    tol=1e-3,
                    reference=ref_subsets,
                )
                # H4: the correlation check applies to the direct L1 -> R_k link;
                # the epipolar one does not (the two points are different instants).
                valid_m, n_rz, _ = accept_links(
                    coords_L,
                    coords_L + m_k,
                    znssd_k,
                    valid_m,
                    znssd_max=cfg.stereo_znssd_max,
                    epipolar_max_px=None,
                )
                m_k = np.where(valid_m[:, None], m_k, np.nan)

            m_ok = valid_m & np.isfinite(m_k).all(axis=1)  # cross-match converged
            if k > 0:
                diag.append(
                    frame_row(
                        k,
                        "cross",
                        n_pts,
                        int(m_ok.sum()),
                        n_gated=n_rz,
                        note="direct L1->Rk match" + (f"; rejected {n_rz} (ZNSSD)" if n_rz else ""),
                    )
                )
            good = valid_l & m_ok  # a usable correspondence also needs the left position
            xL[k][good] = xl_k[good]
            xR[k][good] = coords_L[good] + m_k[good]  # x_R^k = X_L + m^k
            quality[k][good] = znssd_k[good]
            source[k][good] = TRACKED  # reference-anchored in both cameras (no drift)

            # The seed chain follows the cross-match ALONE: m^k solves at the fixed
            # nodes X_L independent of the left track, so a transient left dropout
            # must not discard an otherwise-good cross-disparity (review, S3).
            prev_m = np.where(m_ok[:, None], m_k, prev_m)

            if progress is not None:
                progress(loop_frac(k, n_frames), f"ref_direct {k + 1}/{n_frames}")

        stopped_early = tf_L.stopped_early or loop_stopped_at is not None
        stopped_at = None
        stop_reason = ""
        if stopped_early:
            stopped_at = min(
                tf_L.n_tracked,
                n_frames if loop_stopped_at is None else loop_stopped_at,
            )
            stop_reason = tf_L.stop_reason or "Computation cancelled by user."
        return CorrespondenceSet(
            strategy=self.name,
            xL=xL,
            xR=xR,
            quality=quality,
            source=source,
            diagnostics=tuple(diag),
            stopped_early=stopped_early,
            stopped_at_frame=stopped_at,
            stop_reason=stop_reason,
        )
