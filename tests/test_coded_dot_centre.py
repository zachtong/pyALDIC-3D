"""WP3: coded-grid dot centres refined by a background-subtracted window centroid.

Calibration diagnostics brief (2026-09-14), section 3.4 and WP3. The coded
detector's intensity-weighted centroid inside the binary contour is 0.017 px
from the true disc centroid on ground-truth renders (0.035 px on this suite's
renders); a weighted centroid over an elliptical window of 1.45 dot radii, with
the background taken from the 1.35-1.5 radius annulus, reaches 0.0007 px on
the ground-truth renders (reproduction script in the stereo_gt project,
``plans/2026-09-14_wp3_window_centroid_repro.py``). The background is a plane,
so an illumination gradient does not pull the centre (real photos). The
circle-grid path (``findCirclesGrid``) and the border-arc path stay unchanged.
"""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from al_dic_3d.calibration import CodedCircleGridSpec, detect_board
from al_dic_3d.calibration.dot_centre import refine_dot_centres, window_centroid
from al_dic_3d.calibration.solve import _disc_centroid_offsets
from tests import synth_calib as sc

CODED = CodedCircleGridSpec(cols=11, rows=9, spacing=12.0)
SUPERSAMPLE = 8


def _render(size, dots, background=220.0, ink=30.0, blur_px=0.8):
    """Anti-aliased dots: ``dots`` = (x, y, a, b, theta_rad, hole_radius, ring) each.

    Rendered at 8x and area-averaged, then blurred, so the intensity centroid of
    each dot is its geometric centre. ``ring`` adds a concentric annulus at
    1.7-2.3 dot radii (the synthetic coded fiducial).
    """
    h, w = size
    s = SUPERSAMPLE
    yy, xx = np.mgrid[0 : h * s, 0 : w * s].astype(np.float64)
    xx = (xx + 0.5) / s - 0.5
    yy = (yy + 0.5) / s - 0.5
    dark = np.zeros_like(xx, dtype=bool)
    for x, y, a, b, th, hole, ring in dots:
        u = (xx - x) * np.cos(th) + (yy - y) * np.sin(th)
        v = -(xx - x) * np.sin(th) + (yy - y) * np.cos(th)
        rho = np.hypot(u / a, v / b)
        dark |= rho <= 1.0
        if hole:
            dark &= ~(np.hypot(xx - x, yy - y) <= hole)
        if ring:
            dark |= (rho >= 1.7) & (rho <= 2.3)
    img = np.where(dark, ink, background).reshape(h, s, w, s).mean(axis=(1, 3))
    return cv2.GaussianBlur(img, (0, 0), blur_px)


def _u8(img):
    return np.clip(np.round(img), 0, 255).astype(np.uint8)


@pytest.mark.parametrize(
    ("label", "dot"),
    [
        ("round dot", (40.37, 38.81, 9.0, 9.0, 0.0, 0.0, False)),
        ("tilted dot", (41.62, 39.14, 11.0, 6.5, 0.6, 0.0, False)),
        ("donut fiducial", (40.21, 40.73, 9.0, 9.0, 0.0, 2.0, False)),
        ("ring fiducial", (40.58, 39.47, 7.0, 7.0, 0.0, 0.0, True)),
    ],
)
def test_the_window_centroid_finds_the_dot_centre(label, dot):
    img = _u8(_render((80, 82), [dot]))
    start = (dot[0] + 0.3, dot[1] - 0.25)  # a coarse first centre, as the contour gives
    refined, kept = refine_dot_centres(img, np.array([start]), dark=True, pitch_px=60.0)
    assert kept == 0, label
    assert np.hypot(*(refined[0] - dot[:2])) < 0.01, label


@pytest.mark.parametrize("slope", [(0.4, 0.0), (0.0, -0.5), (0.3, 0.3)])
def test_an_illumination_gradient_does_not_pull_the_centre(slope):
    # Real photos (Challenge 1.0 S5: large dots, lighting falls across the board):
    # a constant background under a 1.45-radius window pulled every centre about
    # 1 px towards the darker side, and the calibration RMS rose from 0.59 to
    # 0.85 px. The background is a plane fitted to the annulus, and the contrast
    # is taken relative to it (the light multiplies board and ink alike).
    dot = (60.37, 58.81, 20.0, 20.0, 0.0, 0.0, False)
    img = _render((120, 124), [dot])
    yy, xx = np.mgrid[0:120, 0:124].astype(np.float64)
    light = 1.0 + (slope[0] * (xx - 62.0) + slope[1] * (yy - 60.0)) / 220.0
    lit = img * light  # the background changes by `slope` grey levels per pixel
    refined, kept = refine_dot_centres(
        _u8(lit), np.array([[60.6, 58.5]]), dark=True, pitch_px=120.0
    )
    assert kept == 0
    assert np.hypot(*(refined[0] - dot[:2])) < 0.02


def test_paper_texture_does_not_move_the_centre():
    # The background pixels inside the window must not carry weight: with the
    # brief's 90th-percentile background, 4 grey levels of paper texture moved
    # the centre by 0.05 px rms (0.016 px with the noise floor).
    dot = (60.37, 58.81, 20.0, 20.0, 0.0, 0.0, False)
    base = _render((120, 124), [dot])
    errors = []
    for seed in range(10):
        rng = np.random.default_rng(seed)
        texture = cv2.GaussianBlur(rng.normal(0.0, 1.0, base.shape), (0, 0), 2.0)
        texture *= 4.0 / texture.std()
        img = _u8(base + texture * (base > 100.0))  # on the paper, not on the ink
        refined, kept = refine_dot_centres(img, np.array([[60.6, 58.5]]), dark=True, pitch_px=120.0)
        assert kept == 0
        errors.append(np.hypot(*(refined[0] - dot[:2])))
    assert np.sqrt(np.mean(np.square(errors))) < 0.03


def test_light_dots_on_a_dark_board():
    dot = (40.37, 38.81, 9.0, 9.0, 0.0, 0.0, False)
    img = _u8(255.0 - _render((80, 82), [dot]))
    refined, kept = refine_dot_centres(img, np.array([[40.1, 39.0]]), dark=False, pitch_px=60.0)
    assert kept == 0
    assert np.hypot(*(refined[0] - dot[:2])) < 0.01


def test_a_dot_crowded_by_its_neighbour_keeps_its_centre():
    # 2 px apart edge to edge: each 1.5-radius window would reach the other dot.
    dots = [(30.2, 40.1, 8.0, 8.0, 0.0, 0.0, False), (48.2, 40.1, 8.0, 8.0, 0.0, 0.0, False)]
    img = _u8(_render((80, 80), dots))
    start = np.array([[30.5, 40.3], [48.5, 40.3]])
    refined, kept = refine_dot_centres(img, start, dark=True, pitch_px=60.0)
    assert kept == 2
    assert np.array_equal(refined, start)


def test_dots_near_the_image_edge_and_excluded_dots_keep_their_centres():
    dot = (6.0, 40.0, 9.0, 9.0, 0.0, 0.0, False)  # the window would leave the image
    img = _u8(_render((80, 82), [dot, (50.3, 40.2, 9.0, 9.0, 0.0, 0.0, False)]))
    start = np.array([[6.2, 40.1], [50.5, 40.4]])
    refined, kept = refine_dot_centres(
        img, start, dark=True, pitch_px=44.0, refinable=np.array([True, False])
    )
    assert kept == 2 and np.array_equal(refined, start)


def test_window_centroid_is_none_outside_the_image():
    img = _u8(_render((80, 82), [(40.0, 40.0, 9.0, 9.0, 0.0, 0.0, False)]))
    assert window_centroid(img, 2.0, 40.0, (9.0, 9.0, 0.0), dark=True) is None


@pytest.fixture(scope="module")
def coded_views():
    rig = sc.make_rig()
    extent = ((CODED.cols - 1) * CODED.spacing, (CODED.rows - 1) * CODED.spacing)
    poses = sc.board_poses(extent, n=8)
    lefts, rights = sc.render_stereo_set(CODED, rig, poses)
    return rig, poses, {"L": lefts, "R": rights}


def _disc_errors(rig, poses, images, cam):
    """Detected minus projected disc centroid, and whether each point is a fiducial."""
    r_cam, t_cam = rig.pose(cam)
    errs, fid = [], []
    for pose, img in zip(poses, images, strict=True):
        det = detect_board(img, CODED)
        assert det.ok, det.reason
        r_b, t_b = pose
        rvec = cv2.Rodrigues(r_cam @ r_b)[0]
        truth = sc.gt_pixels(CODED, pose, rig, cam)[det.ids] + _disc_centroid_offsets(
            det.object_points, CODED.dot_mm / 2, rvec, r_cam @ t_b + t_cam, rig.cameras[cam]
        )
        errs.append(np.linalg.norm(det.image_points - truth, axis=1))
        fid.append(np.isin(det.ids, list(CODED.fiducial_ids)))
    return np.concatenate(errs), np.concatenate(fid)


@pytest.mark.parametrize("cam", ["L", "R"])
def test_coded_centres_hit_the_projected_disc_centroid(coded_views, cam):
    rig, poses, images = coded_views
    err, _fid = _disc_errors(rig, poses, images[cam], cam)
    assert np.sqrt(np.mean(err**2)) < 0.015  # 0.035 px before WP3
    assert np.mean(err) < 0.01


@pytest.mark.parametrize("cam", ["L", "R"])
def test_fiducial_and_ordinary_dots_are_equally_precise(coded_views, cam):
    rig, poses, images = coded_views
    err, fid = _disc_errors(rig, poses, images[cam], cam)
    rms_f = np.sqrt(np.mean(err[fid] ** 2))
    rms_o = np.sqrt(np.mean(err[~fid] ** 2))
    assert rms_f < 0.015 and abs(rms_f - rms_o) < 0.01
