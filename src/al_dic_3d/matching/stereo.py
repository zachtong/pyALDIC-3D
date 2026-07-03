"""Frame-1 cross-camera stereo matcher (Qt-free) — the L1->R1 correspondence.

Ports the *math* of ``StereoMatch_STAQ.m`` without its MATLAB quadtree/RD
bookkeeping: given the reference material points in the left image, seed each
one with an integer NCC disparity (``cv2.matchTemplate`` TM_CCOEFF_NORMED,
honoring a coarse ``disparity_offset`` prior for wide baselines), then refine to
sub-pixel with the scattered-point local IC-GN primitive :func:`match_points`.

Reference = LEFT image, deformed = RIGHT image; the displacement solved IS the
left->right disparity, so ``right_pts == left_pts + d`` (01 §E). Invalid points
propagate as ``NaN`` with ``valid=False``.
"""

from __future__ import annotations

import numpy as np
from al_dic.core.data_structures import DICPara
from numpy.typing import NDArray

from al_dic_3d.matching.contracts import DisparityField
from al_dic_3d.matching.primitives import match_points


def _ncc_seed(
    left: NDArray[np.float64],
    right: NDArray[np.float64],
    points: NDArray[np.float64],
    offset: tuple[float, float],
    search: int,
    half: int,
) -> tuple[NDArray[np.float64], NDArray[np.bool_]]:
    """Per-point integer disparity via local NCC template matching.

    For each left point ``p`` a ``(2*half+1)`` template from ``left`` is matched
    inside a ``+/- search`` window of ``right`` centered at ``round(p + offset)``.
    Returns ``(seed (n,2), ok (n,))`` — the integer ``[du, dv]`` seed and whether
    the template/search windows fit inside both images.
    """
    import cv2

    hL, wL = left.shape
    hR, wR = right.shape
    lf = left.astype(np.float32)
    rf = right.astype(np.float32)
    ox, oy = float(offset[0]), float(offset[1])

    n = points.shape[0]
    side = 2 * half + 1  # template edge
    seed = np.zeros((n, 2), dtype=np.float64)
    ok = np.zeros(n, dtype=bool)

    for i in range(n):
        x, y = points[i]
        xi, yi = int(round(x)), int(round(y))
        # Template around p in the LEFT image.
        if xi - half < 0 or yi - half < 0 or xi + half >= wL or yi + half >= hL:
            continue
        tmpl = lf[yi - half : yi + half + 1, xi - half : xi + half + 1]

        # Search window in the RIGHT image, centered at round(p + offset) and
        # CLAMPED to image bounds (asymmetric near edges, like seed_single_point_fft)
        # so a point whose one-sided disparity would push a symmetric window
        # off-image stays alive as long as the clamped window still holds the match.
        cx, cy = int(round(x + ox)), int(round(y + oy))
        x_lo = max(0, cx - half - search)
        x_hi = min(wR, cx + half + search + 1)
        y_lo = max(0, cy - half - search)
        y_hi = min(hR, cy + half + search + 1)
        if x_hi - x_lo < side or y_hi - y_lo < side:
            continue  # clamped window smaller than the template — no valid position
        win = rf[y_lo:y_hi, x_lo:x_hi]

        ncc = cv2.matchTemplate(win, tmpl, cv2.TM_CCOEFF_NORMED)
        _, _, _, max_loc = cv2.minMaxLoc(ncc)  # max_loc = (col, row) of top-left
        pc, pr = max_loc
        # Matched template center in RIGHT pixel coords.
        matched_x = x_lo + pc + half
        matched_y = y_lo + pr + half
        seed[i, 0] = matched_x - x  # du
        seed[i, 1] = matched_y - y  # dv
        ok[i] = True

    return seed, ok


def stereo_match_pair(
    left: NDArray[np.float64],
    right: NDArray[np.float64],
    points_left: NDArray[np.float64],
    para: DICPara,
    *,
    disparity_offset: tuple[float, float] | None = None,
    search_radius: int = 40,
    tol: float = 1e-3,
    frame_idx: int = 0,
) -> DisparityField:
    """Match reference left points into the right image (frame-1 stereo).

    Args:
        left, right: ``(H, W)`` float64 images (same intensity scale). ``left`` is
            the reference; ``right`` is where correspondences are found.
        points_left: ``(n, 2)`` ``[x, y]`` reference material points in ``left``.
        para: local-only ``DICPara`` (see :func:`make_local_dicpara`); its
            ``winsize`` sizes both the NCC template and the IC-GN subset, and its
            ``img_ref_mask`` (if any) gates reference-subset validity.
        disparity_offset: coarse ``(dx, dy)`` prior recentering the NCC search
            (for large baselines). ``None`` -> zero offset.
        search_radius: NCC half-window (pixels) around the (offset) center.
        tol: IC-GN convergence tolerance (``1e-3``, matching StereoMatch_STAQ).
        frame_idx: frame this disparity belongs to (``0`` for the frame-1 match).

    Returns:
        A :class:`DisparityField` with ``left_pts``, disparity ``d`` (``right_pts
        = left_pts + d``), per-point ``znssd`` and ``valid``. Points whose NCC
        window falls off the image, or whose IC-GN fails, are ``NaN``/invalid.
    """
    left = np.ascontiguousarray(left, dtype=np.float64)
    right = np.ascontiguousarray(right, dtype=np.float64)
    pts = np.ascontiguousarray(points_left, dtype=np.float64).reshape(-1, 2)
    half = int(para.winsize) // 2
    offset = (0.0, 0.0) if disparity_offset is None else disparity_offset

    # (1) integer NCC seed per point (spatially-varying disparity prior).
    seed, seed_ok = _ncc_seed(left, right, pts, offset, int(search_radius), half)

    # (2) sub-pixel local IC-GN refinement at the scattered points.
    u, znssd, valid = match_points(left, right, pts, seed, para, tol=tol)

    # A point is only a real correspondence if BOTH the NCC seed fit and IC-GN
    # converged. Seed-failed points carry NaN disparity.
    d = u.astype(np.float64).copy()
    good = valid & seed_ok
    d[~good] = np.nan
    znssd = znssd.copy()
    znssd[~good] = np.nan

    return DisparityField(
        frame_idx=int(frame_idx),
        left_pts=pts,
        d=d,
        znssd=znssd,
        valid=good,
    )
