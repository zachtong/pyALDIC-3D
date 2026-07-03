"""Drive a whole ``CorrespondenceSet`` through triangulation (01 §E, Phase 1 item 5).

Turns the strategy-/mode-agnostic per-frame image correspondence into world 3D:
each frame's left/right pixel positions are undistorted to normalized coordinates
and triangulated (left camera = world). The result carries the per-frame points
``P^k``, the displacement ``D^k = P^k - P^1``, and the per-point reprojection
error — the ``Reconstruction3D`` that ``strain3d`` consumes next.

This is a **downstream** module: it depends only on the ``CorrespondenceSet``
contract (never a concrete strategy) plus the camera model. ``NaN`` propagates —
a point invalid in either view (or at the reference frame, for displacement) is
``NaN`` in the output.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.calibration.geometry import undistort_points
from al_dic_3d.reconstruct.triangulate import reprojection_error, triangulate_dlt

if TYPE_CHECKING:
    from al_dic_3d.calibration import StereoRig
    from al_dic_3d.matching.contracts import CorrespondenceSet


@dataclass(frozen=True)
class Reconstruction3D:
    """Per-frame reconstructed surface points, displacement, and QC (01 §E).

    ``points[0]`` is the reference surface ``P^1``; ``displacement[k] = points[k]
    - points[0]``. ``source`` is passed through from the ``CorrespondenceSet``.
    """

    points: NDArray[np.float64]  # (n_frames, n_pts, 3) world coords; NaN = invalid
    displacement: NDArray[np.float64]  # (n_frames, n_pts, 3) = points - points[0]
    reproj_error: NDArray[np.float64]  # (n_frames, n_pts) normalized RMS
    source: NDArray[np.uint8]  # (n_frames, n_pts): TRACKED/STEREO_REFRESH/RESCUED/INVALID

    def __post_init__(self) -> None:
        if self.points.ndim != 3 or self.points.shape[2] != 3:
            raise ValueError(f"points must be (n_frames, n_pts, 3); got {self.points.shape}")
        if self.displacement.shape != self.points.shape:
            raise ValueError(
                f"displacement {self.displacement.shape} != points {self.points.shape}"
            )
        expected = self.points.shape[:2]
        if self.reproj_error.shape != expected or self.source.shape != expected:
            raise ValueError(
                f"reproj_error/source must be {expected}; got "
                f"{self.reproj_error.shape}, {self.source.shape}"
            )

    @property
    def n_frames(self) -> int:
        return int(self.points.shape[0])

    @property
    def n_pts(self) -> int:
        return int(self.points.shape[1])


def reconstruct_correspondence(
    cs: CorrespondenceSet,
    rig: StereoRig,
    *,
    cam_left: str = "L",
    cam_right: str = "R",
) -> Reconstruction3D:
    """Triangulate every frame of a correspondence set into world 3D.

    Args:
        cs: the per-frame image-plane correspondence (isolation-wall contract).
        rig: stereo rig; ``cam_left`` is the world camera, ``cam_right`` the pair.
        cam_left, cam_right: camera keys into ``rig`` (v1 = ``"L"``/``"R"``).

    Returns:
        A :class:`Reconstruction3D`. Points invalid in either view are ``NaN``;
        displacement is ``NaN`` wherever the point or its frame-1 anchor is.
    """
    R, T = rig.pose(cam_right)
    intr_left = rig.cameras[cam_left]
    intr_right = rig.cameras[cam_right]

    n_frames, n_pts = cs.n_frames, cs.n_pts
    points = np.full((n_frames, n_pts, 3), np.nan, dtype=np.float64)
    reproj = np.full((n_frames, n_pts), np.nan, dtype=np.float64)

    for k in range(n_frames):
        xn_left = undistort_points(cs.xL[k], intr_left)
        xn_right = undistort_points(cs.xR[k], intr_right)
        pk = triangulate_dlt(xn_left, xn_right, R, T)
        points[k] = pk
        reproj[k] = reprojection_error(pk, xn_left, xn_right, R, T)

    # D^k = P^k - P^1; NaN reference anchors propagate to NaN displacement.
    displacement = points - points[0][None, :, :]

    return Reconstruction3D(
        points=points,
        displacement=displacement,
        reproj_error=reproj,
        source=np.asarray(cs.source, dtype=np.uint8).copy(),
    )
