"""Calibration result writer + QC summary statistics (Qt-free, D12).

``to_opencv_yaml`` writes a ``cv2.FileStorage`` file that round-trips through
the existing ``from_opencv_yaml`` importer — the single funnel by which ALL
three calibration entry modes (built-in / import / manual) re-enter the
pipeline as ``calibration_file`` + ``calibration_format="opencv_yaml"``.
Provenance lands in extra ``meta_*`` nodes, which the importer ignores.

``summarize`` condenses a :class:`~al_dic_3d.calibration.solve.StereoResult`
into the flat numbers the GUI QC panel and the phase report plot.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.calibration.detect import BoardDetection
from al_dic_3d.calibration.importers import _euler_zyx_deg
from al_dic_3d.calibration.model import StereoRig
from al_dic_3d.calibration.solve import StereoResult


def euler_to_rotation(rx_deg: float, ry_deg: float, rz_deg: float) -> NDArray[np.float64]:
    """Public Euler(deg, Z-Y-X premultiply) -> R helper for manual entry."""
    return _euler_zyx_deg(rx_deg, ry_deg, rz_deg)


def to_opencv_yaml(
    rig: StereoRig,
    path: str | Path,
    *,
    meta: dict[str, float | str] | None = None,
) -> Path:
    """Write ``rig`` as an OpenCV stereo-calibration YAML (+ ``meta_*`` nodes).

    Nodes match ``from_opencv_yaml``'s contract exactly: ``cameraMatrix1/2``,
    ``distCoeffs1/2`` (1x5, ``[k1, k2, p1, p2, k3]``), ``R``, ``T`` with
    ``X_2 = R @ X_1 + T`` and camera 1 = left = world.
    """
    import cv2

    if set(rig.cameras) != {"L", "R"}:
        raise ValueError(f"opencv_yaml writer expects cameras L/R, got {sorted(rig.cameras)}")
    R, T = rig.pose("R")
    path = Path(path)
    fs = cv2.FileStorage(str(path), cv2.FILE_STORAGE_WRITE)
    if not fs.isOpened():
        raise ValueError(f"cannot open for writing: {path}")
    try:
        fs.write("cameraMatrix1", rig.cameras["L"].K)
        fs.write("distCoeffs1", rig.cameras["L"].dist_coeffs.reshape(1, -1))
        fs.write("cameraMatrix2", rig.cameras["R"].K)
        fs.write("distCoeffs2", rig.cameras["R"].dist_coeffs.reshape(1, -1))
        fs.write("R", np.asarray(R, np.float64))
        fs.write("T", np.asarray(T, np.float64).reshape(3, 1))
        for key, value in (meta or {}).items():
            node = f"meta_{key}"
            if isinstance(value, str):
                fs.write(node, value)
            else:
                fs.write(node, float(value))
    finally:
        fs.release()
    return path


def coverage_fraction(
    detections: Sequence[BoardDetection],
    image_size: tuple[int, int],
    grid: int = 8,
) -> float:
    """Fraction of a ``grid x grid`` sensor tiling hit by >= 1 detected point.

    Low coverage (empty border/corner cells) means distortion is unconstrained
    there — the classic silent failure mode of otherwise low-RMS calibrations.
    """
    pts = [d.image_points for d in detections if d.ok and d.n_points]
    if not pts:
        return 0.0
    all_pts = np.vstack(pts)
    w, h = int(image_size[0]), int(image_size[1])
    hist, _x, _y = np.histogram2d(all_pts[:, 0], all_pts[:, 1], bins=grid, range=[[0, w], [0, h]])
    return float((hist > 0).mean())


def summarize(
    result: StereoResult,
    left: Sequence[BoardDetection],
    right: Sequence[BoardDetection],
    image_size: tuple[int, int],
) -> dict[str, float | int | str]:
    """Flat QC numbers for the GUI panel / phase report / YAML provenance."""
    used = [p for p in result.pairs if p.used]
    tilts = np.array([p.tilt_deg for p in used], dtype=np.float64)
    dists = np.array([p.distance for p in used], dtype=np.float64)
    out: dict[str, float | int | str] = {
        "rms_px": result.rms,
        "epipolar_rms_px": result.epipolar_rms,
        "baseline": result.baseline,
        "n_pairs_total": len(result.pairs),
        "n_pairs_used": result.n_pairs_used,
        "rms_mono_left_px": result.mono["L"].rms,
        "rms_mono_right_px": result.mono["R"].rms,
        "coverage_left": coverage_fraction(left, image_size),
        "coverage_right": coverage_fraction(right, image_size),
        "tilt_min_deg": float(np.nanmin(tilts)) if tilts.size else float("nan"),
        "tilt_max_deg": float(np.nanmax(tilts)) if tilts.size else float("nan"),
        "distance_min": float(np.nanmin(dists)) if dists.size else float("nan"),
        "distance_max": float(np.nanmax(dists)) if dists.size else float("nan"),
        "joint_refined": int(result.joint_refined),
    }
    if result.warnings:
        out["warnings"] = " | ".join(result.warnings)
    return out
