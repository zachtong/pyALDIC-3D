"""WP2: the model-adequacy check (calibration diagnostics brief, section 6).

About 1 px of lens distortion the 5-coefficient model cannot represent was
absorbed into fx, cx and cy on the stereo_gt dry run while the RMS only rose
from 0.029 to 0.051 px. The residuals then have spatial structure; two
statistics measure it (pre-check B is their normative definition):

* ``excess``: residuals averaged in a 6 x 5 grid of image cells,
  ``sum(n_c |mean_c|^2) / (2 C sigma^2)``, about 1 for pure noise;
* ``field``: rms of a cubic vector field fitted to the residuals, over the rms
  such a fit gives on pure noise.

``LENS_MODEL_INADEQUATE`` needs both above their thresholds.

The synthetic geometry follows the dry run (Stereo-DIC Challenge 2.0 camera,
a 9 x 6 chessboard of 10 mm squares at 600 mm, tilts to 35 deg): the per-view
pose re-fit absorbs the low-order part of any field over a view's footprint,
so boards that fill only a small part of the image hide it (measured while
writing this test: 14-27 % footprints left an excess of 2.4-4.8 for the same
1 px field that reaches 12.1-12.8 here).
"""

from __future__ import annotations

import numpy as np
import pytest

import tests.synth_calib_points as sp
from al_dic_3d.calibration import CameraIntrinsics, ChessboardSpec, StereoRig
from al_dic_3d.calibration.diagnostics import (
    LENS_MODEL_INADEQUATE,
    MODEL_CHECK_SKIPPED,
    RESIDUAL_EXCESS_THRESHOLD,
    RESIDUAL_FIELD_THRESHOLD,
    DiagnosticThresholds,
    binned_excess,
    diagnose_camera,
    field_ratio,
)

W, H = 2448, 2048
SIZE = (W, H)
CAM = CameraIntrinsics(
    fx=10144.9, fy=10144.9, cx=(W - 1) / 2, cy=(H - 1) / 2, k1=-0.12, k2=0.20, width=W, height=H
)
RIG = StereoRig(cameras={"L": CAM}, extrinsics={})
BOARD = ChessboardSpec(cols=9, rows=6, square_size=10.0)
EXTENT = (80.0, 50.0)


def _poses(seed: int = 0, n: int = 20, standoff: float = 600.0):
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        tilt = rng.uniform(-35.0, 35.0, size=2)
        spin = rng.uniform(-20.0, 20.0)
        shift = rng.uniform([-25.0, -20.0, -60.0], [25.0, 20.0, 60.0])
        centre = (shift[0], shift[1], standoff + shift[2])
        out.append(sp.pose_at(EXTENT, centre, (tilt[0], tilt[1], spin)))
    return out


def _dets(noise_px: float, field=None, seed: int = 0, poses=None):
    return sp.detections(
        BOARD, RIG, poses or _poses(seed), "L",
        noise_px=noise_px, seed=seed + 10, extra_field=field,
    )  # fmt: skip


def test_statistics_are_about_one_for_pure_noise():
    rng = np.random.default_rng(11)
    excess, ratio = [], []
    for _ in range(60):
        uv = rng.uniform([0, 0], SIZE, size=(1200, 2))
        res = rng.normal(scale=0.03, size=(1200, 2))
        excess.append(binned_excess(uv, res, SIZE)[0])
        ratio.append(field_ratio(uv, res, CAM))
    assert np.mean(excess) == pytest.approx(1.0, abs=0.15)
    assert np.mean(ratio) == pytest.approx(1.0, abs=0.15)


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_a_field_the_model_cannot_represent_is_flagged(seed):
    report = diagnose_camera("L", CAM, _dets(0.03, sp.cubic_mismatch_field(1.0), seed), SIZE)
    d = report.camera_diagnostics
    assert d.residual_excess > RESIDUAL_EXCESS_THRESHOLD
    assert d.residual_field_ratio > RESIDUAL_FIELD_THRESHOLD
    finding = next(f for f in report.findings if f.code == LENS_MODEL_INADEQUATE)
    assert finding.severity == "warning" and finding.camera == "L"
    assert finding.values["residual_excess"] == pytest.approx(d.residual_excess)
    assert finding.values["residual_field_ratio"] == pytest.approx(d.residual_field_ratio)
    assert "flat" in finding.message_en  # names the board as a possible cause


@pytest.mark.parametrize("noise", [0.01, 0.03, 0.1])
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_distortion_the_model_represents_is_not_flagged(noise, seed):
    report = diagnose_camera("L", CAM, _dets(noise, seed=seed), SIZE)
    d = report.camera_diagnostics
    assert d.residual_excess < RESIDUAL_EXCESS_THRESHOLD
    assert d.residual_field_ratio < RESIDUAL_FIELD_THRESHOLD
    assert LENS_MODEL_INADEQUATE not in [f.code for f in report.findings]


def test_both_statistics_must_exceed_their_thresholds():
    dets = _dets(0.03, sp.cubic_mismatch_field(1.0))
    only_field = DiagnosticThresholds(residual_excess=1e9)
    codes = [f.code for f in diagnose_camera("L", CAM, dets, SIZE, thresholds=only_field).findings]
    assert LENS_MODEL_INADEQUATE not in codes


def test_too_few_populated_cells_skip_the_check():
    # Far boards near the centre fill only the two central image cells.
    small = _dets(0.03, poses=_poses(standoff=3000.0, n=6))
    report = diagnose_camera("L", CAM, small, SIZE)
    skipped = [f for f in report.findings if f.code == MODEL_CHECK_SKIPPED]
    assert len(skipped) == 1 and skipped[0].severity == "info"
    assert report.camera_diagnostics.residual_cells < 3
    assert np.isnan(report.camera_diagnostics.residual_excess)
