"""Post-calibration verification by known distances (iDICs idiom, Qt-free).

The iDICs Good Practices Guide stresses that a low reprojection RMS is
necessary but NOT sufficient — a calibration must also be verified against an
independent physical measurement. This module triangulates the board points of
one verification stereo pair with the calibrated rig and compares the
reconstructed neighbor distances against the board's known pitch:

- ``scale_error``  — relative error of the mean reconstructed pitch (a wrong
  baseline / focal ratio shows up here even when RMS looks perfect);
- ``distance_rmse`` — spread of individual neighbor distances (noise level);
- ``plane_rms``    — out-of-plane residual of the reconstructed board (a
  flat target must reconstruct flat).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.calibration.boards import (
    BoardSpec,
    CharucoSpec,
    ChessboardSpec,
    CircleGridSpec,
    CodedCircleGridSpec,
)
from al_dic_3d.calibration.detect import BoardDetection
from al_dic_3d.calibration.model import StereoRig


@dataclass(frozen=True)
class StabilityResult:
    """Leave-p-out resampling spread of the calibration parameters.

    Analytic std-devs assume the chosen views ARE the population; resampling
    exposes view-selection sensitivity and overfitting they cannot see (the
    MMC 'domain of solution' idea). ``samples[key]`` holds one value per
    successful subset re-calibration; ``reference[key]`` is the full-set value.
    Keys: ``fx, fy, cx, cy, k1, baseline, rms`` (left camera).
    """

    samples: dict[str, NDArray[np.float64]]
    reference: dict[str, float]
    n_views: int
    n_dropped: int

    def spread(self, key: str) -> tuple[float, float, float]:
        """(std, min, max) of one parameter's subset ensemble."""
        s = self.samples[key]
        return float(s.std(ddof=1)), float(s.min()), float(s.max())


def _rig_stats(result) -> dict[str, float]:
    left = result.rig.cameras["L"]
    return {
        "fx": left.fx,
        "fy": left.fy,
        "cx": left.cx,
        "cy": left.cy,
        "k1": left.k1,
        "baseline": result.baseline,
        "rms": result.rms,
    }


def stability_jackknife(
    left: list[BoardDetection],
    right: list[BoardDetection],
    image_size: tuple[int, int],
    reference,
    *,
    drop_fraction: float = 0.2,
    n_samples: int = 10,
    seed: int = 0,
    min_pairs: int = 6,
    **solve_kwargs,
) -> StabilityResult:
    """Re-calibrate on random leave-p-out view subsets and collect the spread.

    ``reference`` is the full-set :class:`~al_dic_3d.calibration.solve.StereoResult`.
    Subsets that become infeasible (too few usable pairs) are skipped; fewer
    than 3 successful subsets raises.
    """
    from al_dic_3d.calibration.solve import calibrate_stereo

    n = len(left)
    n_drop = max(1, round(drop_fraction * n))
    if n - n_drop < min_pairs:
        raise ValueError(f"dropping {n_drop} of {n} views leaves fewer than min_pairs={min_pairs}")
    rng = np.random.default_rng(seed)
    collected: dict[str, list[float]] = {k: [] for k in _rig_stats(reference)}
    for _s in range(n_samples):
        keep = sorted(rng.choice(n, n - n_drop, replace=False).tolist())
        try:
            res = calibrate_stereo(
                [left[i] for i in keep],
                [right[i] for i in keep],
                image_size,
                min_pairs=min_pairs,
                **solve_kwargs,
            )
        except ValueError:
            continue  # infeasible subset — skipped, not fatal
        for k, v in _rig_stats(res).items():
            collected[k].append(v)
    n_ok = len(collected["fx"])
    if n_ok < 3:
        raise ValueError(f"only {n_ok} of {n_samples} subset calibrations succeeded (need >= 3)")
    return StabilityResult(
        samples={k: np.asarray(v, dtype=np.float64) for k, v in collected.items()},
        reference=_rig_stats(reference),
        n_views=n,
        n_dropped=n_drop,
    )


@dataclass(frozen=True)
class DistanceVerification:
    """Known-distance verification metrics of one stereo pair."""

    n_points: int  # triangulated common points
    n_distances: int  # neighbor distances measured
    pitch_true: float  # mm (board spec)
    pitch_measured: float  # mm (mean reconstructed neighbor distance)
    scale_error: float  # (measured - true) / true
    distance_rmse: float  # mm, rms of individual neighbor-distance errors
    plane_rms: float  # mm, out-of-plane residual of the reconstructed board


def _grid_geometry(spec: BoardSpec) -> tuple[int, float]:
    """(row length in point ids, neighbor pitch mm) for row-major grid boards."""
    if isinstance(spec, ChessboardSpec):
        return spec.cols, spec.square_size
    if isinstance(spec, CharucoSpec):
        return spec.squares_x - 1, spec.square_size
    if isinstance(spec, CodedCircleGridSpec):
        return spec.cols, spec.spacing
    if isinstance(spec, CircleGridSpec):
        if spec.asymmetric:
            raise ValueError("known-distance verification does not support asymmetric grids")
        return spec.cols, spec.spacing
    raise TypeError(f"unknown board spec type: {type(spec).__name__}")


def triangulate_pair(
    rig: StereoRig,
    pts_l: NDArray[np.float64],
    pts_r: NDArray[np.float64],
) -> NDArray[np.float64]:
    """DLT-triangulate matched distorted-pixel points -> ``(n, 3)`` world mm."""
    import cv2

    intr_l, intr_r = rig.cameras["L"], rig.cameras["R"]
    ul = cv2.undistortPoints(
        np.float64(pts_l).reshape(-1, 1, 2), intr_l.K, intr_l.dist_coeffs, P=intr_l.K
    ).reshape(-1, 2)
    ur = cv2.undistortPoints(
        np.float64(pts_r).reshape(-1, 1, 2), intr_r.K, intr_r.dist_coeffs, P=intr_r.K
    ).reshape(-1, 2)
    xh = cv2.triangulatePoints(rig.projection_matrix("L"), rig.projection_matrix("R"), ul.T, ur.T)
    return (xh[:3] / xh[3]).T


def verify_known_distance(
    rig: StereoRig,
    det_l: BoardDetection,
    det_r: BoardDetection,
    spec: BoardSpec,
) -> DistanceVerification:
    """Verify ``rig`` against the known geometry of one board stereo pair."""
    if not (det_l.ok and det_r.ok):
        raise ValueError(
            f"verification pair not detected (L: {det_l.reason or 'ok'}; R: {det_r.reason or 'ok'})"
        )
    ids, il, ir = np.intersect1d(det_l.ids, det_r.ids, return_indices=True)
    if ids.size < 8:
        raise ValueError(f"only {ids.size} common points in the verification pair (need >= 8)")

    cols, pitch = _grid_geometry(spec)
    pts3d = triangulate_pair(rig, det_l.image_points[il], det_r.image_points[ir])

    # Neighbor distances along rows (id, id+1 same row) and columns (id, id+cols).
    index_of = {int(i): k for k, i in enumerate(ids)}
    dists: list[float] = []
    for i in ids:
        i = int(i)
        right = i + 1
        if right in index_of and right % cols != 0:  # same row
            dists.append(float(np.linalg.norm(pts3d[index_of[i]] - pts3d[index_of[right]])))
        down = i + cols
        if down in index_of:
            dists.append(float(np.linalg.norm(pts3d[index_of[i]] - pts3d[index_of[down]])))
    if len(dists) < 4:
        raise ValueError(f"only {len(dists)} neighbor distances found (need >= 4)")
    d = np.asarray(dists, dtype=np.float64)

    centered = pts3d - pts3d.mean(axis=0)
    plane_rms = float(np.sqrt(np.linalg.svd(centered, compute_uv=False)[-1] ** 2 / len(pts3d)))

    measured = float(d.mean())
    return DistanceVerification(
        n_points=int(ids.size),
        n_distances=int(d.size),
        pitch_true=float(pitch),
        pitch_measured=measured,
        scale_error=(measured - pitch) / pitch,
        distance_rmse=float(np.sqrt(np.mean((d - pitch) ** 2))),
        plane_rms=plane_rms,
    )
