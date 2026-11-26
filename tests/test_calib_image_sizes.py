"""Board images: one size per camera, and each camera keeps its own size.

The calibration used to take the first LEFT image's size for both cameras
and never compared the other images' sizes, so a set with a cropped or
binned image, or a rig whose two cameras differ in resolution, calibrated
silently with a wrong image size on record.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from al_dic_3d.calibration import (
    ChessboardSpec,
    MixedImageSizeError,
    StereoRig,
    calibrate_stereo,
    coverage_fraction,
    run_calibration,
    stereo_image_sizes,
)
from tests import synth_calib as sc
from tests import synth_calib_points as sp

SPEC = ChessboardSpec(cols=9, rows=7, square_size=12.0)
SIZE_L = (sc.IMG_W, sc.IMG_H)
SIZE_R = (800, 600)


def _two_resolution_views():
    """A rig whose right camera is 800x600 (left 640x512), with exact board views."""
    base = sc.make_rig()
    right = replace(base.cameras["R"], width=SIZE_R[0], height=SIZE_R[1], cx=399.5, cy=299.5)
    rig = StereoRig(cameras={"L": base.cameras["L"], "R": right}, extrinsics=base.extrinsics)
    extent = ((SPEC.cols - 1) * SPEC.square_size, (SPEC.rows - 1) * SPEC.square_size)
    poses = sc.board_poses(extent, n=14)
    left = sp.detections(SPEC, rig, poses, "L", noise_px=0.02, seed=1)
    right_dets = sp.detections(SPEC, rig, poses, "R", noise_px=0.02, seed=2)
    return rig, left, right_dets


# ---- one size per camera ------------------------------------------------------


def test_stereo_image_sizes_returns_each_cameras_size():
    paths = ["L1.png", "L2.png", "R1.png", "R2.png"]
    sizes = [SIZE_L, SIZE_L, SIZE_R, SIZE_R]
    assert stereo_image_sizes(paths, sizes, n_left=2) == (SIZE_L, SIZE_R)


@pytest.mark.parametrize(("odd", "camera"), [(1, "left"), (3, "right")])
def test_stereo_image_sizes_names_the_image_that_differs(odd, camera):
    paths = ["a/L1.png", "a/L2.png", "a/R1.png", "a/R2.png"]
    sizes = [SIZE_L, SIZE_L, SIZE_L, SIZE_L]
    sizes[odd] = (320, 256)
    with pytest.raises(MixedImageSizeError) as info:
        stereo_image_sizes(paths, sizes, n_left=2)
    err = info.value
    assert err.camera == camera
    assert err.path == paths[odd] and err.size == (320, 256)
    assert err.first_path == paths[0 if camera == "left" else 2] and err.first_size == SIZE_L
    text = str(err)
    assert text.startswith(f"the {camera} board images are not all the same size")
    assert "L2.png" in text or "R2.png" in text
    assert "320x256" in text and "640x512" in text


# ---- each camera keeps its own size ----------------------------------------------


@pytest.mark.parametrize("joint", [False, True])
def test_the_right_camera_keeps_its_own_size(joint):
    truth, left, right = _two_resolution_views()
    result = calibrate_stereo(left, right, SIZE_L, image_size_right=SIZE_R, joint_refine=joint)
    cam_l, cam_r = result.rig.cameras["L"], result.rig.cameras["R"]
    assert (cam_l.width, cam_l.height) == SIZE_L
    assert (cam_r.width, cam_r.height) == SIZE_R
    assert cam_r.cx == pytest.approx(truth.cameras["R"].cx, abs=2.0)
    assert cam_r.fx == pytest.approx(truth.cameras["R"].fx, rel=5e-3)


def test_run_calibration_diagnoses_each_camera_at_its_own_size():
    _truth, left, right = _two_resolution_views()
    run = run_calibration(left, right, SIZE_L, image_size_right=SIZE_R, options={})
    cam_r = run.result.rig.cameras["R"]
    assert (cam_r.width, cam_r.height) == SIZE_R
    assert run.stats["coverage_right"] == pytest.approx(coverage_fraction(right, SIZE_R))
    assert run.stats["coverage_left"] == pytest.approx(coverage_fraction(left, SIZE_L))
    diag_r = run.diagnostics.cameras["R"]
    assert diag_r.coverage_fraction == pytest.approx(coverage_fraction(right, SIZE_R))


def test_one_size_still_serves_both_cameras():
    _truth, left, right = _two_resolution_views()
    result = calibrate_stereo(left, right, SIZE_L)
    cam_r = result.rig.cameras["R"]
    assert (cam_r.width, cam_r.height) == SIZE_L  # the caller's choice, as before
