"""Calibration — camera model, stereo rig, importers, undistortion.

``CameraIntrinsics`` / ``StereoRig`` frozen dataclasses, the six calibration-file
format importers (MATLAB/OpenCV/...), and point-level undistortion. World frame =
left camera (R=I, T=0).

Layer: compute (**Qt-free**).  Lands: Phase 1.  Spec: docs/architecture/01 §B.1, §E.
"""

from al_dic_3d.calibration.geometry import project_points, undistort_points
from al_dic_3d.calibration.importers import (
    IMPORTERS,
    from_dice_xml,
    from_matchid_caldat,
    from_matlabcv_mat,
    from_mmc_mat,
    from_opencorr_csv,
    from_opencv_yaml,
    load_calibration,
)
from al_dic_3d.calibration.model import CameraIntrinsics, StereoRig

__all__ = [
    "IMPORTERS",
    "CameraIntrinsics",
    "StereoRig",
    "from_dice_xml",
    "from_matchid_caldat",
    "from_matlabcv_mat",
    "from_mmc_mat",
    "from_opencorr_csv",
    "from_opencv_yaml",
    "load_calibration",
    "project_points",
    "undistort_points",
]
