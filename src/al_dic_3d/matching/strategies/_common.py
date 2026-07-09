"""Shared helpers for concrete correspondence strategies (Qt-free)."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.matching.seed import match_seed_patch, resolve_init_guess, uniform_u0

if TYPE_CHECKING:
    from al_dic_3d.matching.contracts import CorrespondenceConfig
    from al_dic_3d.sequence import StereoSequence


def resolve_init(
    cfg: CorrespondenceConfig,
    left0: NDArray[np.float64],
    right0: NDArray[np.float64],
) -> tuple[str, tuple[float, float] | None]:
    """The effective init-guess mode + the frame-1 stereo disparity prior.

    An explicit ``cfg.disparity_offset`` always wins (the config field stays an
    override); otherwise, in seed mode, the seed patch is template-matched
    L1 -> R1 to derive the offset (None on a low-NCC failure — the stereo NCC
    search then runs uncentered, exactly as before F2). See
    :mod:`al_dic_3d.matching.seed` for the full mode -> engine mapping.
    """
    mode = resolve_init_guess(cfg.init_guess, cfg.seed_point)
    offset = cfg.disparity_offset
    if offset is None and mode == "seed":
        offset = match_seed_patch(left0, right0, cfg.seed_point)
    return mode, offset


def temporal_u0(
    mode: str,
    frame0: NDArray[np.float64],
    frame1: NDArray[np.float64],
    seed_xy: tuple[float, float] | None,
    n_nodes: int,
) -> NDArray[np.float64] | None:
    """The ``u0`` to hand :func:`al_dic_3d.matching.temporal.temporal_track`.

    ``"seed"`` -> uniform shift from template-matching the seed patch
    frame 1 -> frame 2 (None -> engine FFT when the match fails or no seed is
    available for this camera); ``"previous"`` -> zeros (no cross-correlation,
    pure warm-start chain); ``"fft"`` -> None (engine FFT on frame 1).
    """
    if mode == "previous":
        return np.zeros(2 * n_nodes, dtype=np.float64)
    if mode == "seed" and seed_xy is not None:
        shift = match_seed_patch(frame0, frame1, seed_xy)
        return None if shift is None else uniform_u0(n_nodes, shift)
    return None


def mask_stream(seq: StereoSequence, cam: str) -> list[NDArray[np.float64]] | None:
    """Per-frame masks for ``cam`` as float64 arrays, or None when absent.

    Strategies MUST forward these into :func:`temporal_track`: tracking a
    background-heavy bounding-box mesh without masks lets textureless nodes
    poison the FFT seed search (escalating search zones break even the good
    nodes) — the failure mode found on the Stereo DIC Challenge S3 dataset,
    where the 2D engine then silently zero-filled an all-NaN field.
    """
    if seq.masks.get(cam) is None:
        return None
    return [np.asarray(seq.mask(cam, k), dtype=np.float64) for k in range(seq.n_frames)]


def bbox_roi(
    points: NDArray[np.float64],
    img_h: int,
    img_w: int,
    margin: int,
) -> tuple[int, int, int, int]:
    """Axis-aligned pixel ROI ``(xmin, xmax, ymin, ymax)`` around finite points."""
    p = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    p = p[np.isfinite(p).all(axis=1)]
    if p.size == 0:
        raise ValueError("no finite points to bound an ROI")
    xmin = max(0, int(math.floor(p[:, 0].min())) - margin)
    xmax = min(img_w - 1, int(math.ceil(p[:, 0].max())) + margin)
    ymin = max(0, int(math.floor(p[:, 1].min())) - margin)
    ymax = min(img_h - 1, int(math.ceil(p[:, 1].max())) + margin)
    return xmin, xmax, ymin, ymax
