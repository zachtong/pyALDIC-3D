"""Calibration — camera model, built-in calibration, importers, undistortion.

``CameraIntrinsics`` / ``StereoRig`` frozen dataclasses; the built-in stereo
calibrator (D12: board specs -> detection -> mono/stereo solve -> QC report ->
``opencv_yaml``); the six calibration-file format importers (MATLAB/OpenCV/...);
and point-level undistortion. World frame = left camera (R=I, T=0).

Layer: compute (**Qt-free**).  Lands: Phase 1 (+D12).  Spec: 01 §B.1, §E.
"""

from al_dic_3d.calibration.boards import (
    BoardSpec,
    CharucoSpec,
    ChessboardSpec,
    CircleGridSpec,
    CodedCircleGridSpec,
)
from al_dic_3d.calibration.bundle import bundle_refine
from al_dic_3d.calibration.detect import BoardDetection, detect_board
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
from al_dic_3d.calibration.printout import save_board_pdf, spec_summary
from al_dic_3d.calibration.report import (
    coverage_fraction,
    euler_to_rotation,
    point_residuals,
    summarize,
    to_opencv_yaml,
)
from al_dic_3d.calibration.solve import (
    MonoCalibration,
    PairQC,
    StereoResult,
    calibrate_mono,
    calibrate_stereo,
)
from al_dic_3d.calibration.verify import (
    DistanceVerification,
    StabilityResult,
    stability_jackknife,
    triangulate_pair,
    verify_known_distance,
)

__all__ = [
    "IMPORTERS",
    "BoardDetection",
    "BoardSpec",
    "CameraIntrinsics",
    "CharucoSpec",
    "ChessboardSpec",
    "CircleGridSpec",
    "CodedCircleGridSpec",
    "DistanceVerification",
    "MonoCalibration",
    "StabilityResult",
    "PairQC",
    "StereoResult",
    "StereoRig",
    "bundle_refine",
    "calibrate_mono",
    "calibrate_stereo",
    "coverage_fraction",
    "detect_board",
    "euler_to_rotation",
    "from_dice_xml",
    "from_matchid_caldat",
    "from_matlabcv_mat",
    "from_mmc_mat",
    "from_opencorr_csv",
    "from_opencv_yaml",
    "load_calibration",
    "point_residuals",
    "project_points",
    "save_board_pdf",
    "stability_jackknife",
    "spec_summary",
    "summarize",
    "to_opencv_yaml",
    "triangulate_pair",
    "undistort_points",
    "verify_known_distance",
]
