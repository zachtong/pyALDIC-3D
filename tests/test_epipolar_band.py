"""The frame-1 stereo seed search runs along the epipolar line, inside a band.

A left point's match lies on its epipolar line in the right image (up to the
calibration error); its position along the line depends on the unknown depth.
The seed search therefore scans a narrow band along the line instead of a
square window: fewer candidates, and a look-alike off the line cannot win.
"""

from __future__ import annotations

import os
from dataclasses import replace

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from al_dic_3d import synthetic as syn  # noqa: E402
from al_dic_3d.matching.primitives import make_dicpara  # noqa: E402
from al_dic_3d.matching.stereo import (  # noqa: E402
    STEREO_BAND_PX,
    _ncc_seed,
    epipolar_line_frames,
    search_band_px,
    stereo_match_pair,
)

HALF = 16


@pytest.fixture(scope="module")
def scene(tmp_path_factory):
    d = tmp_path_factory.mktemp("band")
    sc = syn.build_scene(d, img=320, n_frames=2, seed=7)
    left = cv2.imread(str(d / "L_000.png"), cv2.IMREAD_UNCHANGED).astype(np.float64)
    right = cv2.imread(str(d / "R_000.png"), cv2.IMREAD_UNCHANGED).astype(np.float64)
    xs, ys = np.meshgrid(np.arange(80, 241, 16.0), np.arange(80, 241, 16.0))
    pts = np.column_stack([xs.ravel(), ys.ravel()])
    truth = syn.gt_tracks(sc, pts)["xR"][0]
    return sc, left, right, pts, truth


def test_the_line_passes_through_the_true_match(scene):
    sc, _, _, pts, truth = scene
    centres = truth + np.array([4.0, 0.5])  # a prior a few pixels off
    foot, tangent = epipolar_line_frames(sc["rig"], pts, centres)
    assert np.allclose(np.linalg.norm(tangent, axis=1), 1.0)
    rel = truth - foot
    off_line = np.abs(rel[:, 0] * tangent[:, 1] - rel[:, 1] * tangent[:, 0])
    assert off_line.max() < 0.3
    assert np.linalg.norm(rel, axis=1).max() < 6.0  # the foot sits near the prior


def test_band_and_square_seeds_agree_on_clean_images(scene):
    sc, left, right, pts, truth = scene
    rng = np.random.default_rng(3)
    offset = truth - pts + rng.uniform(-3, 3, pts.shape)
    sq, ok_sq = _ncc_seed(left, right, pts, offset, 48, HALF)
    foot, tan = epipolar_line_frames(sc["rig"], pts, pts + offset)
    bd, ok_bd = _ncc_seed(left, right, pts, offset, 48, HALF, band=(foot, tan, 3.0))
    assert ok_sq.all() and ok_bd.all()
    for seed in (sq, bd):
        err = np.linalg.norm(pts + seed - truth, axis=1)
        assert np.mean(err <= 1.5) >= 0.95


def test_a_look_alike_off_the_line_does_not_win(scene):
    sc, left, right, pts, truth = scene
    i = int(np.argmin(np.linalg.norm(pts - 160.0, axis=1)))
    p, q = pts[i : i + 1], truth[i : i + 1]
    foot, tan = epipolar_line_frames(sc["rig"], p, q)
    normal = np.array([-tan[0, 1], tan[0, 0]])
    decoy = np.round(q[0] + 30.0 * normal).astype(int)  # 30 px off the line, inside the square
    px, py = np.round(p[0]).astype(int)
    patch = left[py - HALF : py + HALF + 1, px - HALF : px + HALF + 1]
    fake = right.copy()
    fake[decoy[1] - HALF : decoy[1] + HALF + 1, decoy[0] - HALF : decoy[0] + HALF + 1] = patch
    offset = q - p
    sq, _ = _ncc_seed(left, fake, p, offset, 48, HALF)
    bd, ok = _ncc_seed(left, fake, p, offset, 48, HALF, band=(foot, tan, 3.0))
    assert np.linalg.norm(p + sq - decoy) <= 1.0, "the square window locks on the look-alike"
    assert ok[0] and np.linalg.norm(p + bd - q) <= 1.5, "the band keeps the true match"


@pytest.mark.parametrize("angle_deg", [45.0, -30.0, 90.0])
def test_a_slanted_band_masks_its_box(angle_deg):
    """A slanted band's box holds positions off the band; none of them may win."""
    speckle = syn.speckle(240, seed=11)
    shift = np.array([9.0, 6.0])
    right = np.roll(speckle, (int(shift[1]), int(shift[0])), axis=(0, 1))
    p = np.array([[120.0, 120.0]])
    q = p + shift
    t = np.array([[np.cos(np.deg2rad(angle_deg)), np.sin(np.deg2rad(angle_deg))]])
    normal = np.array([-t[0, 1], t[0, 0]])
    # 15 px off the line inside the band's box, its window clear of the true one.
    decoy = np.round(q[0] + 45.0 * t[0] + 15.0 * normal).astype(int)
    assert np.abs(decoy - q[0]).max() > 2 * HALF + 1
    fake = right.copy()
    fake[decoy[1] - HALF : decoy[1] + HALF + 1, decoy[0] - HALF : decoy[0] + HALF + 1] = speckle[
        104 : 104 + 2 * HALF + 1, 104 : 104 + 2 * HALF + 1
    ]
    square, _ = _ncc_seed(speckle, fake, p, shift, 60, HALF)
    seed, ok = _ncc_seed(speckle, fake, p, shift, 60, HALF, band=(q, t, 3.0))
    assert ok[0] and np.allclose(p[0] + seed[0], q[0]), (p[0] + seed[0], q[0], decoy)
    if angle_deg != 90.0:  # a slanted box holds the look-alike, which the square finds
        assert np.allclose(p[0] + square[0], decoy)


def test_a_zero_band_is_the_square_window(scene):
    sc, left, right, pts, truth = scene
    para = make_dicpara(img_size=left.shape, roi=(60, 260, 60, 260), winsize=32)
    off = (truth - pts).mean(axis=0)
    a = stereo_match_pair(left, right, pts, para, disparity_offset=tuple(off), search_radius=48)
    b = stereo_match_pair(
        left,
        right,
        pts,
        para,
        disparity_offset=tuple(off),
        search_radius=48,
        rig=sc["rig"],
        band_px=0.0,
    )
    np.testing.assert_array_equal(a.d, b.d)
    np.testing.assert_array_equal(a.valid, b.valid)


def test_the_band_links_the_scene(scene):
    sc, left, right, pts, truth = scene
    para = make_dicpara(img_size=left.shape, roi=(60, 260, 60, 260), winsize=32)
    off = (truth - pts).mean(axis=0)
    field = stereo_match_pair(
        left,
        right,
        pts,
        para,
        disparity_offset=tuple(off),
        search_radius=48,
        rig=sc["rig"],
        band_px=3.0,
    )
    err = np.linalg.norm(field.right_pts - truth, axis=1)
    assert field.valid.mean() > 0.95 and np.nanmedian(err[field.valid]) < 0.1


@pytest.mark.parametrize(
    ("band", "limit", "expected"),
    [
        (3.0, 2.0, 3.0),
        (3.0, 10.0, 10.0),  # never narrower than the epipolar limit
        (0.0, 2.0, 0.0),  # band off: square window
        (3.0, 0.0, 0.0),  # epipolar check off: the calibration is not trusted
        (3.0, None, 0.0),
        (-1.0, 2.0, 0.0),
        (float("nan"), 2.0, 0.0),
    ],
)
def test_the_band_width_rule(band, limit, expected):
    assert search_band_px(band, limit) == expected


def test_a_strongly_distorted_lens_widens_the_band_by_the_bow():
    from al_dic_3d.calibration import CameraIntrinsics, StereoRig
    from al_dic_3d.matching.stereo import epipolar_band

    th = np.deg2rad(20.0)
    R = np.array([[np.cos(th), 0, np.sin(th)], [0, 1, 0], [-np.sin(th), 0, np.cos(th)]])
    T = np.array([-800 * np.sin(th), 0.0, 800 * (1 - np.cos(th))])
    cams = {
        c: CameraIntrinsics(fx=5000, fy=5000, cx=2560, cy=2560, width=5120, height=5120, k1=-0.3)
        for c in "LR"
    }
    rig = StereoRig(cameras=cams, extrinsics={("L", "R"): (R, T)})
    pts = np.array([[600.0, 500.0], [2560.0, 2560.0], [4500.0, 4700.0]])
    centres = pts + np.array([-150.0, 0.0])
    _, _, near = epipolar_band(rig, pts, centres, 48, 3.0)
    _, _, far = epipolar_band(rig, pts, centres, 400, 3.0)
    assert np.all(near >= 3.0) and np.all(near < 3.3)  # a short search: the line is straight
    assert far.max() > near.max() + 0.5  # a long one bows away from the tangent


def _scene_config(tmp_path, extra=""):
    from al_dic_3d.runner import load_config
    from tests import synth_stereo

    sc = synth_stereo.build_scene(tmp_path, n_frames=2)
    path = synth_stereo.write_config(tmp_path, sc)
    if extra:
        text = path.read_text(encoding="utf-8").replace("[matching]", "[matching]\n" + extra)
        path.write_text(text, encoding="utf-8")
    return load_config(path)


def test_the_band_width_comes_from_the_config(tmp_path):
    assert _scene_config(tmp_path / "a").stereo_band_px == STEREO_BAND_PX
    assert _scene_config(tmp_path / "b", "stereo_band_px = 5.5").stereo_band_px == 5.5


@pytest.mark.parametrize("value", ["-1.0", "inf", "nan", "5000.0"])
def test_a_bad_band_width_is_refused(tmp_path, value):
    with pytest.raises(ValueError, match="stereo_band_px"):
        _scene_config(tmp_path, f"stereo_band_px = {value}")


class _Captured(Exception):
    pass


@pytest.mark.parametrize("strategy", ["track_both", "stereo_each_frame", "ref_direct"])
@pytest.mark.parametrize(
    ("band", "limit", "expected"), [(5.5, 2.0, 5.5), (1.0, 2.0, 2.0), (0.0, 2.0, 0.0)]
)
def test_every_strategy_searches_the_band(tmp_path, monkeypatch, strategy, band, limit, expected):
    import importlib

    from al_dic_3d.runner import run_pipeline

    module = importlib.import_module(f"al_dic_3d.matching.strategies.{strategy}")
    seen = {}

    def spy(*args, **kwargs):
        seen.update(kwargs)
        raise _Captured

    monkeypatch.setattr(module, "stereo_match_pair", spy)
    cfg = replace(
        _scene_config(tmp_path),
        strategy=strategy,
        stereo_band_px=band,
        stereo_epipolar_max_px=limit,
    )
    with pytest.raises(_Captured):
        run_pipeline(cfg)
    assert seen["rig"] is not None
    assert seen["band_px"] == expected


def test_the_draft_carries_the_band_width(tmp_path):
    from al_dic_3d.project.draft import ProjectDraft

    draft = ProjectDraft()
    assert draft.stereo_band_px == STEREO_BAND_PX
    before = draft.result_signature()
    draft.stereo_band_px = 6.0
    assert draft.result_signature() != before


def test_the_sidebar_edits_the_band_width():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from al_dic_3d.gui.app import create_app
    from al_dic_3d.gui.main_window import MainWindow3D

    create_app([])
    win = MainWindow3D()
    left = win._left
    draft = win.controller.state.draft
    left._band_spin.setValue(7.5)
    assert draft.stereo_band_px == 7.5
    draft.stereo_band_px = 0.0
    left.refresh_all()
    assert left._band_spin.value() == 0.0 and left._band_spin.text() == "off"
    win.close()
