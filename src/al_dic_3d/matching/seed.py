"""Seed-point initial-guess semantics (Qt-free) — Batch F2.

The GUI's INITIAL GUESS choice maps onto the ONLY lever the pinned 2D engine
exposes for external-mesh runs: the ``U0`` argument of ``run_aldic``. With an
external mesh (how :func:`al_dic_3d.matching.temporal.temporal_track` always
calls it), the engine behaves as follows (re-verified in
``al_dic/core/pipeline.py``, v0.7.0):

- ``need_fft = dic_mesh is None or current_U0 is None`` (pipeline.py:1058):
  passing ``U0`` SKIPS the frame-1 FFT integer search entirely; omitting it
  runs FFT once on frame 1 (the FFT grid is interpolated onto the external
  mesh, pipeline.py:1240-1274).
- Frames >= 2 always warm-start from the previous converged field on the same
  reference ("sibling reuse", pipeline.py:1297-1372). The per-frame FFT force
  of ``init_guess_mode == "fft"`` (pipeline.py:1026-1035) and the periodic
  ``fft_reset_interval`` (pipeline.py:1037-1051) are BOTH explicitly skipped
  when the mesh is external, so they are NOT controllable from here. (0.7
  flipped the ``init_guess_mode`` DEFAULT to ``"fft"`` — a no-op here because
  of that same external-mesh skip.)
- A reference switch (incremental mode) clears the warm start and forces FFT
  (pipeline.py:966-979) in every mode.

Hence the three 3D modes map to:

``"seed"`` (GUI default)
    The user clicks ONE point on the LEFT camera, frame 1. Its ~96x96
    neighborhood is template-matched (full-image NCC) (a) into the RIGHT
    frame 1 -> the stereo ``disparity_offset`` prior, and (b) into frame 2 of
    each camera -> a UNIFORM per-node ``U0`` (every node gets the same shift;
    IC-GN refines per node), skipping the frame-1 FFT. Limits: the uniform
    shift only seeds rigid-dominant first-pair motion; strong deformation
    gradients within the first pair still rely on IC-GN's basin. When the NCC
    peak is below :data:`SEED_MIN_NCC` the piece falls back to FFT (warned).
``"fft"``
    ``U0 = None`` — the engine's own path: FFT on frame 1 and on every
    reference switch, sibling warm-start elsewhere. (Pre-F2 behavior.)
``"previous"``
    ``U0 = zeros`` — no cross-correlation ever runs for the temporal track:
    frame 1 starts from zero (the "previous" frame IS the reference), later
    frames warm-start from the previous converged field. Fastest; can silently
    freeze on large motion or decorrelation (the v1.4.7 lesson) — the ZNSSD
    validity gate flags affected frames.
"""

from __future__ import annotations

import warnings

import numpy as np
from numpy.typing import NDArray

#: Half-width of the seed template (template edge = 2 * half + 1 ~ 96 px).
SEED_PATCH_HALF = 48
#: Minimum acceptable NCC peak for a seed template match.
SEED_MIN_NCC = 0.5

INIT_GUESS_MODES = ("seed", "fft", "previous")


def resolve_init_guess(init_guess: str, seed_point: tuple[float, float] | None) -> str:
    """Validate the mode and apply the seed->fft auto-fallback (never block).

    Returns the EFFECTIVE mode: ``"seed"`` without a placed point degrades to
    ``"fft"`` with a warning, per the F2 contract.
    """
    if init_guess not in INIT_GUESS_MODES:
        raise ValueError(f"init_guess must be one of {INIT_GUESS_MODES}, got {init_guess!r}")
    if init_guess == "seed" and seed_point is None:
        warnings.warn(
            "init_guess='seed' but no seed point was placed — falling back to FFT seeding.",
            UserWarning,
            stacklevel=2,
        )
        return "fft"
    return init_guess


def match_seed_patch(
    src: NDArray[np.float64],
    dst: NDArray[np.float64],
    seed_xy: tuple[float, float],
    *,
    half: int = SEED_PATCH_HALF,
    min_ncc: float = SEED_MIN_NCC,
) -> tuple[float, float] | None:
    """Template-match the seed's neighborhood from ``src`` into ``dst``.

    A ``(2*half+1)`` square template centered at ``seed_xy`` (clamped fully
    inside ``src``; the seed may sit near an edge) is matched against the WHOLE
    ``dst`` image with normalized cross-correlation
    (``cv2.matchTemplate`` TM_CCOEFF_NORMED). The returned ``(dx, dy)`` is the
    integer displacement of that patch — usable directly as a stereo disparity
    offset (src=L1, dst=R1) or a first-pair motion seed (src=f0, dst=f1).

    Returns ``None`` (with a warning) when the peak NCC is below ``min_ncc``
    or the images are too small to hold a meaningful template.
    """
    import cv2

    src = np.ascontiguousarray(src, dtype=np.float32)
    dst = np.ascontiguousarray(dst, dtype=np.float32)
    hs, ws = src.shape
    hd, wd = dst.shape
    # Shrink the template if either image cannot hold it (dst must be >= template).
    half = int(min(half, (min(hs, ws) - 1) // 2, (min(hd, wd) - 1) // 2))
    if half < 8:
        warnings.warn(
            "seed patch match skipped: images too small for a meaningful template.",
            UserWarning,
            stacklevel=2,
        )
        return None

    x, y = float(seed_xy[0]), float(seed_xy[1])
    # Template top-left, clamped so the window sits fully inside src.
    x0 = int(np.clip(round(x) - half, 0, ws - (2 * half + 1)))
    y0 = int(np.clip(round(y) - half, 0, hs - (2 * half + 1)))
    tmpl = src[y0 : y0 + 2 * half + 1, x0 : x0 + 2 * half + 1]

    ncc = cv2.matchTemplate(dst, tmpl, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(ncc)
    if not np.isfinite(max_val) or max_val < min_ncc:
        warnings.warn(
            f"seed patch NCC peak {max_val:.2f} < {min_ncc:.2f} — "
            "falling back to FFT seeding for this piece.",
            UserWarning,
            stacklevel=2,
        )
        return None
    # Displacement of the template window == displacement of the seed patch.
    return (float(max_loc[0] - x0), float(max_loc[1] - y0))


def uniform_u0(n_nodes: int, shift: tuple[float, float]) -> NDArray[np.float64]:
    """A uniform initial displacement for ``run_aldic``'s ``U0`` argument.

    Interleaved ``[u0, v0, u1, v1, ...]`` of length ``2 * n_nodes`` — every
    node gets the same ``(dx, dy)`` coarse shift; IC-GN refines per node.
    """
    if n_nodes <= 0:
        raise ValueError(f"n_nodes must be positive, got {n_nodes}")
    return np.tile(np.asarray(shift, dtype=np.float64), int(n_nodes))
