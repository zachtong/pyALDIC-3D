"""Shared helpers for concrete correspondence strategies (Qt-free)."""

from __future__ import annotations

import math
import warnings
from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.matching.seed import match_seed_patch, resolve_init_guess, uniform_u0
from al_dic_3d.matching.seed_propagation import SeedU0Result, build_seed_u0

if TYPE_CHECKING:
    from al_dic.core.data_structures import DICMesh, DICPara

    from al_dic_3d.matching.contracts import CorrespondenceConfig
    from al_dic_3d.sequence import StereoSequence

#: Minimum fraction of a region's mesh nodes the F-aware BFS must solve for the
#: propagated ``U0`` to be preferred over FFT. Below it the field is mostly the
#: OUTPUT-side IDW extrapolation of a few solved seeds (the external-mesh path
#: skips the FFT path's per-node input inpaint + IC-GN refinement — see
#: ``seed_propagation`` module docstring), which is a worse frame-1 prior than a
#: dense FFT integer search. Half the trackable nodes is a deliberately
#: conservative floor: a healthy propagation solves the vast majority
#: (test_seed_u0_reproduces_sheared_affine_field asserts > 90 %), whereas a BFS
#: that stalls on a decorrelating band — exactly where FFT is wanted — solves
#: only a handful, so anything under 50 % degrades to FFT rather than keeping a
#: sparse, IDW-extrapolated guess.
MIN_SEED_COVERAGE = 0.5


def _accept_seed_u0(res: SeedU0Result | None) -> bool:
    """Whether a propagated ``U0`` covers enough region nodes to beat FFT.

    Rejects (and warns, so the degrade is never silent) a sparse propagation —
    a BFS stall that solved fewer than :data:`MIN_SEED_COVERAGE` of the
    trackable region nodes — so the caller falls back to FFT seeding.
    """
    if res is None or res.n_region_nodes <= 0 or res.n_solved <= 0:
        return False
    coverage = res.n_solved / res.n_region_nodes
    if coverage >= MIN_SEED_COVERAGE:
        return True
    warnings.warn(
        f"seed propagation solved only {res.n_solved}/{res.n_region_nodes} region "
        f"nodes ({coverage:.0%} < {MIN_SEED_COVERAGE:.0%} coverage) — "
        f"falling back to FFT seeding.",
        UserWarning,
        stacklevel=3,
    )
    return False


class FrameView(Sequence):
    """Indexed float64 raw-frame view over one camera's provider (P1.2).

    Replaces the strategies' eager ``[seq.frame(cam, k) for k ...]`` lists —
    which materialize the WHOLE camera stream and defeat a lazy provider —
    with per-index access: ``view[k]`` fetches frame ``k`` from the provider
    (LRU-cached when lazy, the existing array when eager). ``np.asarray`` on an
    already-float64 array is a no-copy pass-through, so the eager path stays
    byte-identical.
    """

    def __init__(self, seq: StereoSequence, cam: str) -> None:
        self._provider = seq.providers[cam]

    def __len__(self) -> int:
        return len(self._provider)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return [self[i] for i in range(*idx.indices(len(self)))]
        return np.asarray(self._provider.get_normalized(idx), dtype=np.float64)


def frame_view(seq: StereoSequence, cam: str) -> FrameView:
    """The lazy indexed raw-frame sequence for ``cam`` (see :class:`FrameView`)."""
    return FrameView(seq, cam)


def resolve_init(
    cfg: CorrespondenceConfig,
    left0: NDArray[np.float64],
    right0: NDArray[np.float64],
) -> tuple[str, tuple[float, float] | None]:
    """The effective init-guess mode + the frame-1 stereo disparity prior.

    Seed presence is judged from the effective seed list (``seed_points`` or the
    legacy ``seed_point``), so a multi-seed config without a singular
    ``seed_point`` still resolves to ``"seed"``. An explicit ``cfg.disparity_offset``
    always wins (the config field stays an override); otherwise, in seed mode,
    the PRIMARY seed patch is template-matched L1 -> R1 to derive the scalar
    offset (None on a low-NCC failure — the stereo NCC search then runs
    uncentered, exactly as before F2). See :mod:`al_dic_3d.matching.seed` for
    the full mode -> engine mapping.
    """
    seeds = effective_seed_points(cfg)
    primary = seeds[0] if seeds else None
    mode = resolve_init_guess(cfg.init_guess, primary)
    offset = cfg.disparity_offset
    if offset is None and mode == "seed" and primary is not None:
        offset = match_seed_patch(left0, right0, primary)
    return mode, offset


def temporal_u0(
    mode: str,
    frame0: NDArray[np.float64],
    frame1: NDArray[np.float64],
    seed_xy: tuple[float, float] | None,
    n_nodes: int,
) -> NDArray[np.float64] | None:
    """The single-seed ``u0`` for :func:`al_dic_3d.matching.temporal.temporal_track`.

    ``"seed"`` -> uniform shift from template-matching the seed patch
    frame 1 -> frame 2 (None -> engine FFT when the match fails or no seed is
    available for this camera); ``"previous"`` -> zeros (no cross-correlation,
    pure warm-start chain); ``"fft"`` -> None (engine FFT on frame 1). This is
    the single-seed / fallback path; the multi-seed F-aware field is built by
    :func:`temporal_camera_u0`.
    """
    if mode == "previous":
        return np.zeros(2 * n_nodes, dtype=np.float64)
    if mode == "seed" and seed_xy is not None:
        shift = match_seed_patch(frame0, frame1, seed_xy)
        return None if shift is None else uniform_u0(n_nodes, shift)
    return None


def effective_seed_points(cfg: CorrespondenceConfig) -> tuple[tuple[float, float], ...]:
    """The seed list to propagate from: ``cfg.seed_points`` else the primary seed.

    A headless ``RunConfig``/``CorrespondenceConfig`` may carry only the legacy
    ``seed_point`` (single); the GUI/full path fills ``seed_points`` (the placed
    list). Either yields the same tuple so the strategies have one source.
    """
    pts = getattr(cfg, "seed_points", ()) or ()
    if pts:
        return tuple((float(p[0]), float(p[1])) for p in pts)
    if cfg.seed_point is not None:
        return ((float(cfg.seed_point[0]), float(cfg.seed_point[1])),)
    return ()


def map_seeds_left_to_right(
    left0: NDArray[np.float64],
    right0: NDArray[np.float64],
    seed_points: tuple[tuple[float, float], ...],
) -> tuple[tuple[float, float], ...]:
    """Map LEFT frame-1 seed pixels into the RIGHT frame via per-seed NCC patch match.

    Each left seed's neighborhood is template-matched L1 -> R1 (reusing
    :func:`al_dic_3d.matching.seed.match_seed_patch`); the seed's right-frame
    location is ``left + disparity``. Seeds whose L -> R match fails (low NCC)
    are dropped, so the right camera keeps only reliably-mapped seeds (an empty
    result -> the right track keeps the engine FFT).
    """
    out: list[tuple[float, float]] = []
    for s in seed_points:
        shift = match_seed_patch(left0, right0, s)
        if shift is not None:
            out.append((s[0] + shift[0], s[1] + shift[1]))
    return tuple(out)


def temporal_camera_u0(
    mode: str,
    frame0: NDArray[np.float64],
    frame1: NDArray[np.float64],
    mesh: DICMesh,
    mask: NDArray[np.float64],
    seed_points: tuple[tuple[float, float], ...],
    single_seed: tuple[float, float] | None,
    para: DICPara,
    n_nodes: int,
    *,
    search_radius: int,
) -> NDArray[np.float64] | None:
    """One camera's temporal ``u0``: multi-seed F-aware field else the single path.

    In ``seed`` mode with placed seeds, a full per-node ``U0`` is built by F-aware
    propagation (:func:`al_dic_3d.matching.seed_propagation.build_seed_u0`); on
    any propagation failure (no seed in a region, region unseedable, low NCC) it
    degrades to :func:`temporal_u0` (single-seed uniform / previous-zeros /
    engine FFT). For ``fft`` / ``previous`` it IS ``temporal_u0`` unchanged.
    """
    if mode == "seed" and seed_points:
        res = build_seed_u0(
            frame0, frame1, mesh, mask, seed_points, para, search_radius=search_radius
        )
        if _accept_seed_u0(res):
            return res.u0
    return temporal_u0(mode, frame0, frame1, single_seed, n_nodes)


def stereo_seed_u0(
    mode: str,
    left0: NDArray[np.float64],
    right0: NDArray[np.float64],
    mesh_left: DICMesh,
    mask_left: NDArray[np.float64],
    seed_points: tuple[tuple[float, float], ...],
    para_left: DICPara,
    *,
    search_radius: int,
) -> NDArray[np.float64] | None:
    """Per-node L -> R disparity prior ``(n, 2)`` for ``stereo_match_pair(seed_u0=)``.

    Propagates the seeds over the LEFT reference mesh with ``g = right frame 1``,
    giving a spatially-varying disparity prior (strong on wide baselines). ``None``
    outside seed mode or on propagation failure — the stereo match then uses the
    scalar ``disparity_offset`` + per-point NCC search exactly as before.
    """
    if mode == "seed" and seed_points:
        res = build_seed_u0(
            left0, right0, mesh_left, mask_left, seed_points, para_left, search_radius=search_radius
        )
        if _accept_seed_u0(res):
            return res.u0_2d
    return None


def mask_stream(seq: StereoSequence, cam: str) -> Sequence[NDArray[np.float64]] | None:
    """Per-frame masks for ``cam`` as an indexed float64 sequence, or None.

    Strategies MUST forward these into :func:`temporal_track`: tracking a
    background-heavy bounding-box mesh without masks lets textureless nodes
    poison the FFT seed search (escalating search zones break even the good
    nodes) — the failure mode found on the Stereo DIC Challenge S3 dataset,
    where the 2D engine then silently zero-filled an all-NaN field.

    Eager list/tuple streams are coerced element-wise (no-copy for float64, so
    the runner's shared constant roi_mask stays ONE array); any other sequence
    (e.g. :class:`al_dic_3d.sequence.LazyMaskList`) already serves float64 and
    passes through unmaterialized (P1.2).
    """
    stream = seq.masks.get(cam)
    if stream is None:
        return None
    if isinstance(stream, (list, tuple)):
        return [np.asarray(m, dtype=np.float64) for m in stream]
    return stream


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
