"""Automatic stereo disparity prior for runs without a starting point (Qt-free).

Fix batch V (finding H2). Without a placed point, the frame-1 stereo match
searched ``+/- stereo_search`` px around ZERO disparity. On a rig whose
disparity is larger than that box (wide baselines, high resolution) only part
of the ROI matched: a 12 Mpx synthetic rig matched 76 % of its nodes with no
point and 100 % with one. A placed point works because its ~97 px patch is
template-matched over the WHOLE right image. This module does the same
automatically: a few probe patches spread over the left ROI are matched over
the whole right image, checked against the epipolar geometry when a rig is
given, and combined into a per-node search centre -- an affine disparity field
when three or more probes agree, their median otherwise. The usual per-node
NCC search then runs around that centre.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.matching.seed import SEED_MIN_NCC, SEED_PATCH_HALF, match_seed_patch

#: Probe patches matched over the whole right image.
N_PROBES = 5
#: A probe match further than this from its epipolar line is a false lock. The
#: integer match of a ~97 px patch between two perspectives is only good to a
#: few pixels, so the bound is looser than the 2 px link acceptance.
PRIOR_EPIPOLAR_MAX_PX = 5.0
#: Probes whose disparity is further than this from the affine fit make the
#: fit untrustworthy; the median of the accepted probes is used instead.
MAX_AFFINE_RESIDUAL_PX = 8.0


@dataclass(frozen=True)
class DisparityPrior:
    """Per-node stereo search centres estimated from probe patches."""

    offsets: NDArray[np.float64]  # (n, 2) [dx, dy] search centre per node
    n_probes: int
    n_accepted: int
    model: str  # "affine" | "constant"
    median: tuple[float, float]
    probes: NDArray[np.float64]  # (k, 2) accepted probe nodes (left pixels)
    shifts: NDArray[np.float64]  # (k, 2) their whole-image L -> R matches

    def describe(self) -> str:
        """One line for the run diagnostics (English, like all compute text)."""
        dx, dy = self.median
        return (
            f"automatic disparity prior from {self.n_accepted}/{self.n_probes} probe "
            f"patches ({self.model}; median dx={dx:.0f} px, dy={dy:.0f} px)"
        )


def _probe_points(
    points: NDArray[np.float64],
    mask: NDArray[np.float64] | None,
    shape: tuple[int, int],
    half: int,
    n_probe: int,
) -> NDArray[np.float64]:
    """Up to ``n_probe`` nodes spread over the ROI: its centre and four quartiles."""
    h, w = shape
    pts = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    pts = pts[np.isfinite(pts).all(axis=1)]
    if mask is not None and pts.size:
        xi = np.clip(np.round(pts[:, 0]).astype(np.int64), 0, w - 1)
        yi = np.clip(np.round(pts[:, 1]).astype(np.int64), 0, h - 1)
        pts = pts[np.asarray(mask)[yi, xi] > 0]
    inside = (
        (pts[:, 0] >= half)
        & (pts[:, 0] <= w - 1 - half)
        & (pts[:, 1] >= half)
        & (pts[:, 1] <= h - 1 - half)
    )
    if inside.any():
        pts = pts[inside]
    if pts.shape[0] == 0:
        return pts
    centre = pts.mean(axis=0)
    span = pts.max(axis=0) - pts.min(axis=0)
    targets = [centre]
    for sx, sy in ((0.3, 0.0), (-0.3, 0.0), (0.0, 0.3), (0.0, -0.3)):
        targets.append(centre + np.array([sx * span[0], sy * span[1]]))
    chosen: list[int] = []
    for t in targets[: max(1, n_probe)]:
        i = int(np.argmin(np.hypot(pts[:, 0] - t[0], pts[:, 1] - t[1])))
        if i not in chosen:
            chosen.append(i)
    return pts[chosen]


def estimate_disparity_prior(
    left0: NDArray[np.float64],
    right0: NDArray[np.float64],
    points: NDArray[np.float64],
    mask: NDArray[np.float64] | None = None,
    rig=None,
    *,
    n_probe: int = N_PROBES,
    half: int = SEED_PATCH_HALF,
    min_ncc: float = SEED_MIN_NCC,
    epipolar_max_px: float = PRIOR_EPIPOLAR_MAX_PX,
) -> DisparityPrior | None:
    """Per-node L -> R search centres from probe patches, or ``None``.

    Each probe's ``(2*half+1)`` patch around a left ROI node is matched over
    the whole right image (:func:`al_dic_3d.matching.seed.match_seed_patch`);
    matches below ``min_ncc`` or, with ``rig``, further than
    ``epipolar_max_px`` from the epipolar line are rejected. Returns ``None``
    when no probe survives, so the caller keeps its zero-centred search.
    """
    left0 = np.ascontiguousarray(left0, dtype=np.float64)
    right0 = np.ascontiguousarray(right0, dtype=np.float64)
    pts = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    probes = _probe_points(pts, mask, left0.shape, int(half), int(n_probe))
    if probes.shape[0] == 0:
        return None

    # A flat patch has no defined NCC (OpenCV then reports a meaningless peak):
    # only textured probes are matched.
    floor = 1e-3 * float(left0.std()) + 1e-9

    def match(p: NDArray[np.float64]) -> tuple[float, float] | None:
        x, y = int(round(p[0])), int(round(p[1]))
        patch = left0[max(0, y - half) : y + half + 1, max(0, x - half) : x + half + 1]
        if patch.size == 0 or float(patch.std()) <= floor:
            return None
        # warn=False: a weak probe is expected and simply dropped (and silencing
        # a warning with catch_warnings is not thread-safe on this pool).
        return match_seed_patch(
            left0, right0, (float(p[0]), float(p[1])), half=half, min_ncc=min_ncc, warn=False
        )

    from concurrent.futures import ThreadPoolExecutor

    # cv2.matchTemplate releases the GIL: the probes run concurrently.
    with ThreadPoolExecutor(max_workers=min(len(probes), 5)) as pool:
        shifts = list(pool.map(match, probes))
    keep = np.array([s is not None for s in shifts], dtype=bool)
    if not keep.any():
        return None
    d = np.array([s if s is not None else (np.nan, np.nan) for s in shifts], dtype=np.float64)
    if rig is not None:
        from al_dic_3d.matching.stereo import epipolar_distance_px

        dist = epipolar_distance_px(rig, probes, probes + d)
        keep &= dist <= float(epipolar_max_px)
        if not keep.any():
            return None
    good_p, good_d = probes[keep], d[keep]
    median = np.median(good_d, axis=0)
    offsets = np.tile(median, (pts.shape[0], 1))
    model = "constant"
    if good_p.shape[0] >= 3:
        a = np.column_stack([np.ones(good_p.shape[0]), good_p])
        if np.linalg.matrix_rank(a) == 3:
            coef, *_ = np.linalg.lstsq(a, good_d, rcond=None)
            resid = np.abs(a @ coef - good_d).max()
            if resid <= MAX_AFFINE_RESIDUAL_PX:
                fin = np.isfinite(pts).all(axis=1)
                offsets[fin] = np.column_stack([np.ones(int(fin.sum())), pts[fin]]) @ coef
                model = "affine"
    return DisparityPrior(
        offsets=offsets,
        n_probes=int(probes.shape[0]),
        n_accepted=int(keep.sum()),
        model=model,
        median=(float(median[0]), float(median[1])),
        probes=good_p,
        shifts=good_d,
    )
