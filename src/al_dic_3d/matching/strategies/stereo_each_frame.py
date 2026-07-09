"""``StereoEachFrameStrategy`` — the S2 correspondence strategy (02 §2, §5).

ONE temporal chain (the left camera), plus a fresh stereo match at EVERY frame:

  1. **Left temporal track** on ``mesh_L`` -> ``x_L^k = X_L + U_L^k``.
  2. **Per-frame stereo match** ``S(L_k -> R_k)`` evaluated at the scattered tracked
     points ``x_L^k`` via the local IC-GN primitive (``match_points``) -> disparity
     ``d^k``; ``x_R^k = x_L^k + d^k``. Warm-started from ``d^{k-1}`` (the disparity
     field varies slowly frame to frame), so no per-frame NCC seed after frame 0
     and ZERO resampling.

Every position is ``source=STEREO_REFRESH``. Vs S1: one drift chain instead of two,
and each frame satisfies the epipolar constraint, so the reprojection error is a
true QC signal — at the cost of a fresh (non-cancelling) stereo noise per frame in
the 3D displacement. Best for long / drift-sensitive sequences (02 §3).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, ClassVar

import numpy as np

from al_dic_3d.matching.contracts import (
    INVALID,
    STEREO_REFRESH,
    CorrespondenceConfig,
    CorrespondenceSet,
)
from al_dic_3d.matching.primitives import make_dicpara, match_points
from al_dic_3d.matching.stereo import stereo_match_pair
from al_dic_3d.matching.strategies._common import (
    bbox_roi,
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
class StereoEachFrameStrategy:
    """Stereo-each-frame (S2): one left temporal chain + a per-frame stereo match."""

    name: ClassVar[str] = "stereo_each_frame"

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
        left = [np.asarray(seq.frame("L", k), dtype=np.float64) for k in range(n_frames)]
        right = [np.asarray(seq.frame("R", k), dtype=np.float64) for k in range(n_frames)]
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

        # The ONLY temporal chain: the left camera.
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

        prev_d = np.zeros((n_pts, 2), dtype=np.float64)  # warm-start seed (last good disparity)
        for k in range(n_frames):
            if stop is not None and stop():
                break
            xl_k = coords_L + tf_L.u_accum[k]  # tracked left positions in L_k
            valid_l = tf_L.valid[k] & np.isfinite(xl_k).all(axis=1)

            if k == 0:
                # Establish the disparity with a full NCC-seeded stereo match.
                field = stereo_match_pair(
                    left[0],
                    right[0],
                    coords_L,
                    para_L,
                    disparity_offset=stereo_offset,
                    search_radius=self.stereo_search,
                    frame_idx=0,
                )
                d_k, znssd_k, valid_s = field.d, field.znssd, field.valid
            else:
                # Warm-start from the previous frame's disparity (slowly varying);
                # scattered local IC-GN at x_L^k -> no NCC, no resampling.
                d_k, znssd_k, valid_s = match_points(
                    left[k], right[k], xl_k, np.nan_to_num(prev_d, nan=0.0), para_L, tol=1e-3
                )

            good = valid_l & valid_s
            xl_ok = np.isfinite(xl_k).all(axis=1)
            good &= xl_ok & np.isfinite(d_k).all(axis=1)

            xL[k][good] = xl_k[good]
            xR[k][good] = xl_k[good] + d_k[good]
            quality[k][good] = znssd_k[good]
            source[k][good] = STEREO_REFRESH

            # Carry a valid disparity forward as the next warm-start; keep the last
            # good value for points that failed this frame so they can recover.
            prev_d = np.where(good[:, None], d_k, prev_d)

            if progress is not None:
                progress((k + 1) / n_frames, f"stereo_each_frame {k + 1}/{n_frames}")

        return CorrespondenceSet(strategy=self.name, xL=xL, xR=xR, quality=quality, source=source)
