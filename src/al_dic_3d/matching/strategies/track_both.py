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

from collections.abc import Callable
from typing import TYPE_CHECKING, ClassVar

import numpy as np

from al_dic_3d.matching.contracts import (
    INVALID,
    TRACKED,
    CorrespondenceConfig,
    CorrespondenceSet,
)
from al_dic_3d.matching.primitives import make_dicpara
from al_dic_3d.matching.stereo import stereo_match_pair
from al_dic_3d.matching.strategies._common import bbox_roi, mask_stream
from al_dic_3d.matching.strategy import register_strategy
from al_dic_3d.matching.temporal import (
    build_grid_mesh,
    resample_to_points,
    temporal_track,
)

if TYPE_CHECKING:
    from al_dic import DICMesh  # type-only; ledgered in DEPENDS_ON_2D.md

    from al_dic_3d.calibration import StereoRig
    from al_dic_3d.sequence import StereoSequence


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
        )

        # (1) frame-1 cross-camera match at the reference mesh nodes.
        disp = stereo_match_pair(
            left[0],
            right[0],
            coords_L,
            para_L,
            disparity_offset=cfg.disparity_offset,
            search_radius=self.stereo_search,
        )
        right_pts = disp.right_pts  # (n_pts, 2); NaN where the stereo link failed
        base_valid = disp.valid  # (n_pts,)
        if not base_valid.any():
            raise RuntimeError("frame-1 stereo match found no valid correspondences")

        # (2a) left temporal track — corr points ARE the mesh_L nodes (no resample).
        tf_L = temporal_track(left, mesh_L, para_L, masks=mask_stream(seq, "L"), stop=stop)
        if not np.allclose(tf_L.ref_coords, coords_L, atol=1e-6):
            raise RuntimeError(
                "left temporal mesh drifted from mesh_L (node re-trim); xL alignment "
                "cannot be guaranteed — masked temporal tracking is deferred to Phase 2."
            )

        # (2b) right temporal track on an INDEPENDENT dense grid over right_pts.
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
        )
        mesh_R = build_grid_mesh(para_R, img_h, img_w)
        tf_R = temporal_track(right, mesh_R, para_R, masks=mask_stream(seq, "R"), stop=stop)

        # (3) assemble the CorrespondenceSet frame by frame.
        xL = np.full((n_frames, n_pts, 2), np.nan, dtype=np.float64)
        xR = np.full((n_frames, n_pts, 2), np.nan, dtype=np.float64)
        quality = np.full((n_frames, n_pts), np.nan, dtype=np.float64)
        source = np.full((n_frames, n_pts), INVALID, dtype=np.uint8)

        for k in range(n_frames):
            if stop is not None and stop():
                break
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
                progress((k + 1) / n_frames, f"track_both frame {k + 1}/{n_frames}")

        return CorrespondenceSet(
            strategy=self.name,
            xL=xL,
            xR=xR,
            quality=quality,
            source=source,
        )
