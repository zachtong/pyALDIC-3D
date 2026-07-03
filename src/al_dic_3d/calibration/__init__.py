"""Calibration — camera model, stereo rig, importers, undistortion.

``CameraIntrinsics`` / ``StereoRig`` frozen dataclasses, the six calibration-file
format importers (MATLAB/OpenCV/...), and point-level undistortion. World frame =
left camera (R=I, T=0).

Layer: compute (**Qt-free**).  Lands: Phase 1.  Spec: docs/architecture/01 §B.1, §E.
"""
