"""Stereo-link acceptance: converged is not accepted (fix batch V, finding H4).

The frame-1 stereo match accepted every link whose IC-GN converged, whatever its
correlation and wherever it landed relative to the epipolar line. On the
Stereo-DIC Challenge 1.0 S3 data 102 accepted links had ZNSSD > 1, ~24 px
reprojection error and up to ~30 mm depth error (the quality gate is off by
default). Genuine links there score a median ZNSSD of 0.02 and sit ~0.1 px from
their epipolar line.
"""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("al_dic")

from al_dic_3d.calibration import CameraIntrinsics, StereoRig, project_points  # noqa: E402
from al_dic_3d.matching.contracts import DisparityField  # noqa: E402
from al_dic_3d.matching.stereo import (  # noqa: E402
    STEREO_EPIPOLAR_MAX_PX,
    STEREO_ZNSSD_MAX,
    accept_field,
    accept_links,
    epipolar_distance_px,
)
from al_dic_3d.runner import load_config, run_pipeline  # noqa: E402
from tests import synth_stereo  # noqa: E402


def _rig() -> StereoRig:
    a = np.deg2rad(-15.0)
    R = np.array([[np.cos(a), 0.0, np.sin(a)], [0.0, 1.0, 0.0], [-np.sin(a), 0.0, np.cos(a)]])
    left = CameraIntrinsics(fx=1200, fy=1205, cx=639.5, cy=511.5, k1=-0.1, k2=0.02)
    right = CameraIntrinsics(fx=1185, fy=1190, cx=650, cy=505, k1=-0.08)
    return StereoRig(
        cameras={"L": left, "R": right}, extrinsics={("L", "R"): (R, np.array([-120.0, 0, 0]))}
    )


def _pairs(rig: StereoRig, n: int = 200):
    rng = np.random.default_rng(4)
    X = np.column_stack(
        [rng.uniform(-100, 100, n), rng.uniform(-80, 80, n), rng.uniform(900, 1100, n)]
    )
    RL, TL = rig.pose("L")
    RR, TR = rig.pose("R")
    return project_points(X, rig.cameras["L"], RL, TL), project_points(X, rig.cameras["R"], RR, TR)


def test_true_correspondences_lie_on_their_epipolar_lines():
    rig = _rig()
    pl, pr = _pairs(rig)
    d = epipolar_distance_px(rig, pl, pr)
    assert np.nanmax(d) < 1e-6


def test_epipolar_distance_measures_an_off_line_shift():
    rig = _rig()
    pl, pr = _pairs(rig)
    d = epipolar_distance_px(rig, pl, pr + np.array([0.0, 8.0]))  # ~vertical shift
    assert np.nanmedian(d) > 5.0  # lines are near-horizontal for this rig


def test_nan_points_give_nan_distance():
    rig = _rig()
    pl, pr = _pairs(rig, 3)
    pr[1] = np.nan
    d = epipolar_distance_px(rig, pl, pr)
    assert np.isnan(d[1]) and np.isfinite(d[[0, 2]]).all()


def test_accept_links_rejects_poor_correlation_and_epipolar_outliers():
    rig = _rig()
    pl, pr = _pairs(rig, 6)
    pr[2] += np.array([0.0, 20.0])  # false lock far off its epipolar line
    znssd = np.array([0.02, 0.9, 0.03, 0.05, 0.01, 0.04])  # link 1 correlates badly
    valid = np.ones(6, dtype=bool)
    v, n_z, n_e = accept_links(pl, pr, znssd, valid, rig=rig)
    assert v.tolist() == [True, False, False, True, True, True]
    assert (n_z, n_e) == (1, 1)


def test_thresholds_can_be_disabled():
    rig = _rig()
    pl, pr = _pairs(rig, 3)
    pr[0] += 30.0
    v, n_z, n_e = accept_links(
        pl,
        pr,
        np.array([3.0, 0.1, 0.1]),
        np.ones(3, bool),
        rig=rig,
        znssd_max=0,
        epipolar_max_px=None,
    )
    assert v.all() and (n_z, n_e) == (0, 0)


def test_accept_field_nans_the_rejected_links():
    rig = _rig()
    pl, pr = _pairs(rig, 4)
    field = DisparityField(0, pl, pr - pl, np.array([0.01, 0.02, 0.95, 0.03]), np.ones(4, bool))
    out, n_z, n_e = accept_field(field, rig=rig)
    assert (n_z, n_e) == (1, 0)
    assert not out.valid[2] and np.isnan(out.d[2]).all() and np.isnan(out.znssd[2])
    assert out.valid[[0, 1, 3]].all()


def test_defaults_are_the_documented_values():
    assert STEREO_ZNSSD_MAX == 0.6 and STEREO_EPIPOLAR_MAX_PX == 2.0


def test_clean_scene_loses_no_links_to_the_acceptance_check(tmp_path):
    scene = synth_stereo.build_scene(tmp_path, n_frames=2)
    result = run_pipeline(load_config(synth_stereo.write_config(tmp_path, scene)))
    rows = [r for r in result.meta["diagnostics"] if r["cam"] == "stereo"]
    assert rows and rows[0]["n_gated"] == 0, rows[0]
