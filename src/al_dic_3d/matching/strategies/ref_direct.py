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
from al_dic_3d.matching.primitives import make_local_dicpara, match_points
from al_dic_3d.matching.stereo import stereo_match_pair
from al_dic_3d.matching.strategies._common import bbox_roi, mask_stream
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
    ) -> None:
        self.winsize = winsize
        self.winstepsize = winstepsize
        self.winsize_min = winsize_min
        self.stereo_search = stereo_search

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
        # S3 is reference-direct by definition, so the left chain is forced
        # accumulative (frame 1 is the anchor for BOTH cameras).
        para_L = make_local_dicpara(
            img_size=(img_h, img_w),
            roi=roi_L,
            winsize=self.winsize,
            winstepsize=self.winstepsize,
            winsize_min=self.winsize_min,
            img_ref_mask=mask_L1,
            reference_mode="accumulative",
        )

        tf_L = temporal_track(left, mesh_L, para_L, masks=mask_stream(seq, "L"), stop=stop)
        if not np.allclose(tf_L.ref_coords, coords_L, atol=1e-6):
            raise RuntimeError("left temporal mesh drifted from mesh_L (masked track = Phase 2b)")

        xL = np.full((n_frames, n_pts, 2), np.nan, dtype=np.float64)
        xR = np.full((n_frames, n_pts, 2), np.nan, dtype=np.float64)
        quality = np.full((n_frames, n_pts), np.nan, dtype=np.float64)
        source = np.full((n_frames, n_pts), INVALID, dtype=np.uint8)

        prev_m = np.zeros((n_pts, 2), dtype=np.float64)  # chain seed for M(L1 -> R_k)
        for k in range(n_frames):
            if stop is not None and stop():
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
                    disparity_offset=cfg.disparity_offset,
                    search_radius=self.stereo_search,
                    frame_idx=0,
                )
                m_k, znssd_k, valid_m = field.d, field.znssd, field.valid
            else:
                # Direct L1 -> R_k match at the reference nodes X_L, chain-seeded
                # from m^{k-1} (seed keeps up with the accumulating deformation).
                m_k, znssd_k, valid_m = match_points(
                    left[0], right[k], coords_L, np.nan_to_num(prev_m, nan=0.0), para_L, tol=1e-3
                )

            m_ok = valid_m & np.isfinite(m_k).all(axis=1)  # cross-match converged
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

        return CorrespondenceSet(strategy=self.name, xL=xL, xR=xR, quality=quality, source=source)
