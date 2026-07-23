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
from al_dic_3d.matching.primitives import make_dicpara, match_points
from al_dic_3d.matching.stereo import stereo_match_pair
from al_dic_3d.matching.strategies._common import (
    bbox_roi,
    frame_view,
    mask_stream,
    resolve_init,
    temporal_u0,
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
        temporal_gate_znssd: float = 1.0,
    ) -> None:
        self.winsize = winsize
        self.winstepsize = winstepsize
        self.winsize_min = winsize_min
        self.stereo_search = stereo_search
        self.use_global_step = use_global_step
        self.admm_max_iter = admm_max_iter
        self.fft_search = fft_search
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
        )

        # Initial-guess resolution (F2): effective mode + seed-derived stereo
        # offset (an explicit cfg.disparity_offset overrides the seed match).
        init_mode, stereo_offset = resolve_init(cfg, left[0], right[0])

        u0_L = temporal_u0(init_mode, left[0], left[1], cfg.seed_point, n_pts)
        tf_L = temporal_track(
            left,
            mesh_L,
            para_L,
            masks=mask_stream(seq, "L"),
            u0=u0_L,
            stop=stop,
            gate_znssd=self.temporal_gate_znssd,
        )
        if not np.allclose(tf_L.ref_coords, coords_L, atol=1e-6):
            raise RuntimeError("left temporal mesh drifted from mesh_L (masked track = Phase 2b)")

        xL = np.full((n_frames, n_pts, 2), np.nan, dtype=np.float64)
        xR = np.full((n_frames, n_pts, 2), np.nan, dtype=np.float64)
        quality = np.full((n_frames, n_pts), np.nan, dtype=np.float64)
        source = np.full((n_frames, n_pts), INVALID, dtype=np.uint8)

        diag: list[dict] = list(temporal_rows("L", tf_L))
        prev_m = np.zeros((n_pts, 2), dtype=np.float64)  # chain seed for M(L1 -> R_k)
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
                field = stereo_match_pair(
                    left[0],
                    right[0],
                    coords_L,
                    para_L,
                    disparity_offset=stereo_offset,
                    search_radius=self.stereo_search,
                    frame_idx=0,
                )
                m_k, znssd_k, valid_m = field.d, field.znssd, field.valid
                diag += stereo_rows(field)
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
                m_k, znssd_k, valid_m = match_points(
                    left[0], right[k], coords_L, np.nan_to_num(prev_m, nan=0.0), para_L, tol=1e-3
                )

            m_ok = valid_m & np.isfinite(m_k).all(axis=1)  # cross-match converged
            if k > 0:
                diag.append(
                    frame_row(k, "cross", n_pts, int(m_ok.sum()), note="direct L1->Rk match")
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
                progress((k + 1) / n_frames, f"ref_direct {k + 1}/{n_frames}")

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
