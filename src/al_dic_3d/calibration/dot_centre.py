"""Coded-grid dot centres: a background-subtracted window centroid (Qt-free).

The coded detector's first centre is the intensity-weighted centroid inside the
dot's binary contour (``detect._weighted_center``). The contour sits at the
binarization's threshold, on the pixel grid, so that centre is 0.017 px from
the true disc centroid on noise-free ground-truth renders. This module refines
it (calibration diagnostics brief, 2026-09-14, section 3.4 and WP3):

1. measure the dot's ellipse from its half-grey outline around the current
   centre (holes filled, so a donut fiducial is one dot);
2. over an elliptical window of 1.45 dot radii, weight each pixel by its
   contrast relative to the background, less a noise floor: the background
   is a plane through the 1.35-1.5 radius annulus at the annulus median, the
   floor three times the annulus's robust spread;
3. move to the weighted centroid; twice.

The brief's prototype used a constant background at the annulus's 90th
percentile. On real photos that failed twice: under uneven light it pulled
every centre of the Challenge 1.0 S5 calibration photos about 1 px towards the
darker side (calibration RMS 0.59 -> 0.85 px), and the background pixels
inside the window, all weighted, carried the board's texture into the centre.
The plane, the relative contrast and the noise floor remove both.

Ground truth (stereo_gt reproduction script
``plans/2026-09-14_wp3_window_centroid_repro.py``, 20 poses x 2 cameras, the
detector with this refinement): coded grid 0.0168 -> 0.0007 px without noise,
0.0171 -> 0.0040 px at 1.5 grey levels of noise, 0.0179 -> 0.0078 px at 3;
fiducial and ordinary dots alike. On the plain circle grid the prototype's gain
vanished at 3 grey levels, so ``findCirclesGrid`` centres are left alone, as
are the border-arc centres.

A dot whose window would reach other dark pixels (a neighbour, a fiducial
ring, the image edge) keeps its first centre; so does one whose refinement
fails or moves too far.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

WINDOW_RADII = 1.45  # weighted-centroid window, in dot radii
ANNULUS_RADII = (1.35, 1.5)  # background annulus, in dot radii (fiducial rings start at 1.7)
# Background level: the annulus median about its plane, with contrast below 3
# annulus spreads (1.4826 x MAD) carrying no weight. The brief's 90th-percentile
# level gave the background pixels inside the window a weight of their own; on
# real photos their texture and uneven light then moved the centre. Measured
# (release-object RMS on the full views; ground-truth error at 1.5 / 3 grey
# levels of noise): 90th percentile 0.0338 / 0.0371 px (Challenge 1.0 S1, L / R),
# 0.0376 / 0.0503 px (Challenge 2.0 08), 0.0044 / 0.0086 px (ground truth);
# median + 3 spreads 0.0294 / 0.0324, 0.0313 / 0.0435, 0.0040 / 0.0078 px.
BACKGROUND_PERCENTILE = 50.0  # of the annulus residuals, dark dots (100 - this for light dots)
NOISE_FLOOR_SIGMA = 3.0  # contrast below this many annulus spreads carries no weight
ITERATIONS = 2
PATCH_PITCH = 0.45  # half-size of the patch that measures the dot, in lattice pitches
MAX_SHIFT_RADII = 0.5  # a refined centre further than this from the first one is rejected
_MIN_ANNULUS_PIXELS = 8
_MIN_DOT_PIXELS = 12

Shape = tuple[float, float, float]  # (semi-major a, semi-minor b, major-axis angle) in px, rad


def dot_shape(
    gray: NDArray[np.uint8], x: float, y: float, half: int, *, dark: bool
) -> tuple[Shape, bool] | None:
    """``((a, b, theta), crowded)`` of the dot at ``(x, y)``, or None.

    The dot is the smallest outer half-grey outline around the point (holes
    filled, so a donut's centre hole belongs to it) in a patch of ``half``
    pixels around it, clipped at the image edge; its ellipse comes from the
    filled outline's second moments. A dot too large for the patch (a tilted
    view: the pitch is the foreshortened spacing) is measured again in a patch
    that fits its background annulus. ``crowded`` is True when other dark
    pixels lie within the annulus's outer radius.
    """
    first = _measure(gray, x, y, half, dark)
    if first is None:
        return None
    shape, crowded, fits = first
    if fits:
        return shape, crowded
    larger = _measure(gray, x, y, int(np.ceil(ANNULUS_RADII[1] * shape[0])) + 3, dark)
    if larger is None:
        return None
    return larger[0], larger[1] or not larger[2]


def _measure(
    gray: NDArray[np.uint8], x: float, y: float, half: int, dark: bool
) -> tuple[Shape, bool, bool] | None:
    """``(shape, crowded, fits)`` from one patch; ``fits``: the annulus lies in it."""
    import cv2

    h, w = gray.shape
    x0, y0 = int(round(x)), int(round(y))
    top, left = max(y0 - half, 0), max(x0 - half, 0)
    patch = gray[top : min(y0 + half + 1, h), left : min(x0 + half + 1, w)].astype(np.float32)
    px, py = float(x - left), float(y - top)
    if patch.size == 0 or not (0.0 <= px < patch.shape[1] and 0.0 <= py < patch.shape[0]):
        return None
    lo, hi = np.percentile(patch, (2.0, 90.0) if dark else (10.0, 98.0))
    if hi - lo <= 0.0:
        return None
    mid = 0.5 * (lo + hi)
    mask = ((patch < mid) if dark else (patch > mid)).astype(np.uint8)
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    if hierarchy is None:
        return None
    best, best_area = None, 0.0
    for cnt, (_n, _p, _child, parent) in zip(contours, hierarchy[0], strict=True):
        if parent != -1 or cv2.pointPolygonTest(cnt, (px, py), False) < 0:
            continue
        area = cv2.contourArea(cnt)
        if best is None or area < best_area:
            best, best_area = cnt, area
    if best is None:
        return None
    own = np.zeros_like(mask)
    cv2.drawContours(own, [best], -1, 1, thickness=-1)  # the dot, holes filled
    m = cv2.moments(own, binaryImage=True)
    if m["m00"] < _MIN_DOT_PIXELS:
        return None
    cov = np.array([[m["mu20"], m["mu11"]], [m["mu11"], m["mu02"]]]) / m["m00"]
    evals, evecs = np.linalg.eigh(cov)
    b, a = 2.0 * np.sqrt(np.maximum(evals, 1e-12))  # a filled ellipse: variance = axis^2 / 4
    shape = (float(a), float(b), float(np.arctan2(evecs[1, 1], evecs[0, 1])))
    reach = ANNULUS_RADII[1] * a + 1.0
    ph, pw = patch.shape
    # The annulus must lie in the patch, except where the image edge cuts the
    # patch: there the window centroid refuses the dot anyway.
    fits = (
        (px - reach >= 0 or left == 0)
        and (px + reach < pw or left + pw == w)
        and (py - reach >= 0 or top == 0)
        and (py + reach < ph or top + ph == h)
    )
    rho = _elliptic_radius(
        np.arange(pw, dtype=np.float64) - px, np.arange(ph, dtype=np.float64) - py, shape
    )
    foreign = (mask > 0) & (own == 0) & (rho <= ANNULUS_RADII[1] + 0.1)
    return shape, bool(foreign.any()), bool(fits)


def _elliptic_radius(dx: NDArray, dy: NDArray, shape: Shape) -> NDArray[np.float64]:
    """Elliptic radius (1 on the dot's outline) on the ``dx`` x ``dy`` grid."""
    a, b, theta = shape
    c, s = np.cos(theta), np.sin(theta)
    dx = np.asarray(dx, np.float64)[None, :]
    dy = np.asarray(dy, np.float64)[:, None]
    return np.hypot((dx * c + dy * s) / a, (-dx * s + dy * c) / b)


def window_centroid(
    gray: NDArray[np.uint8], x: float, y: float, shape: Shape, *, dark: bool
) -> tuple[float, float] | None:
    """The background-subtracted weighted centroid of the dot, or None.

    The background is a plane fitted to the annulus at the annulus median, and
    each pixel's weight is its contrast less :data:`NOISE_FLOOR_SIGMA` annulus
    spreads, relative to the background and clipped at zero. The plane removes
    the pull of the background pixels under a lighting gradient, the relative
    contrast the tilt the light gives the dot itself (together about 1 px
    towards the darker side on the Challenge 1.0 S5 photos), and the floor the
    weight of the background's own texture. None when the window leaves the
    image, the annulus is too small, or no pixel stands out of the background.
    """
    a = shape[0]
    r = int(np.ceil(ANNULUS_RADII[1] * a)) + 2
    h, w = gray.shape
    pct = BACKGROUND_PERCENTILE if dark else 100.0 - BACKGROUND_PERCENTILE
    for _ in range(ITERATIONS):
        xi, yi = int(round(x)), int(round(y))
        if not (r <= xi < w - r and r <= yi < h - r):
            return None
        patch = gray[yi - r : yi + r + 1, xi - r : xi + r + 1].astype(np.float64)
        cols = np.arange(xi - r, xi + r + 1, dtype=np.float64)
        rows = np.arange(yi - r, yi + r + 1, dtype=np.float64)
        rho = _elliptic_radius(cols - x, rows - y, shape)
        ring = (rho >= ANNULUS_RADII[0]) & (rho <= ANNULUS_RADII[1])
        if int(ring.sum()) < _MIN_ANNULUS_PIXELS:
            return None
        background, spread = _plane_background(patch, ring, cols - x, rows - y, pct, dark)
        contrast = (background - patch) if dark else (patch - background)
        contrast = contrast - NOISE_FLOOR_SIGMA * spread
        relative = contrast / np.maximum(background, 1.0)  # the light scales board and ink alike
        weight = np.clip(relative, 0.0, None) * (rho <= WINDOW_RADII)
        total = float(weight.sum())
        if total <= 0.0:
            return None
        x = float((weight.sum(axis=0) * cols).sum() / total)
        y = float((weight.sum(axis=1) * rows).sum() / total)
    return x, y


def _plane_background(
    patch: NDArray[np.float64],
    ring: NDArray[np.bool_],
    dx: NDArray[np.float64],
    dy: NDArray[np.float64],
    pct: float,
    dark: bool,
) -> tuple[NDArray[np.float64], float]:
    """Background over the patch and the annulus's robust spread about it.

    The background is a plane through the annulus at the ``pct`` percentile of
    the annulus residuals; its slope comes from a least-squares plane through
    the annulus pixels without their darkest (for dark dots) fifth, which a
    dot's blur skirt or a speck would otherwise tilt. The spread is 1.4826
    times the residuals' median absolute deviation.
    """
    gx = np.broadcast_to(dx[None, :], patch.shape)[ring]
    gy = np.broadcast_to(dy[:, None], patch.shape)[ring]
    vals = patch[ring]
    keep = vals >= np.percentile(vals, 20.0) if dark else vals <= np.percentile(vals, 80.0)
    design = np.column_stack([np.ones(int(keep.sum())), gx[keep], gy[keep]])
    coef, *_ = np.linalg.lstsq(design, vals[keep], rcond=None)
    resid = vals - (coef[0] + coef[1] * gx + coef[2] * gy)
    level = float(np.percentile(resid, pct))
    spread = 1.4826 * float(np.median(np.abs(resid - np.median(resid))))
    return coef[0] + level + coef[1] * dx[None, :] + coef[2] * dy[:, None], spread


def refine_dot_centres(
    gray: NDArray[np.uint8],
    centres: NDArray[np.float64],
    *,
    dark: bool,
    pitch_px: float,
    refinable: NDArray[np.bool_] | None = None,
) -> tuple[NDArray[np.float64], int]:
    """Refined ``(n, 2)`` centres and how many kept their first centre.

    ``pitch_px`` (the lattice pitch in the image) sizes the patch the dot is
    measured in; ``refinable`` False marks centres to leave alone (the
    border-arc ones).
    """
    out = np.array(centres, dtype=np.float64, copy=True)
    half = max(8, int(PATCH_PITCH * float(pitch_px)))
    kept = 0
    for k, (x, y) in enumerate(out):
        if refinable is not None and not refinable[k]:
            kept += 1
            continue
        measured = dot_shape(gray, x, y, half, dark=dark)
        if measured is None or measured[1]:
            kept += 1
            continue
        shape = measured[0]
        centre = window_centroid(gray, x, y, shape, dark=dark)
        if centre is None or np.hypot(centre[0] - x, centre[1] - y) > MAX_SHIFT_RADII * shape[0]:
            kept += 1
            continue
        out[k] = centre
    return out, kept
