"""The frame-1 stereo check explains itself in the run log (GitHub issue #1).

On a rough as-built surface seen at a 29 deg stereo angle, correct links
correlate at ZNCC ~0.7, so the default stereo check (ZNSSD 0.6) removed 810 of
2008 links and the run kept 49 % of the specimen. The log reported it as
"camera stereo: 822 node-frames removed (validity gate: correlation vs frame 1
failed)" — wrong for a left-right check, and silent about the threshold that
would keep them. A calibration that does not match the images (the reporter's
original one put every true link 17.6 px off its epipolar line) was not named
either; the median epipolar residual of the frame-1 links says it at once.
"""

from __future__ import annotations

import numpy as np
import pytest

from al_dic_3d.matching.contracts import CorrespondenceSet, DisparityField
from al_dic_3d.matching.diagnostics import (
    frame_row,
    stereo_check_advice,
    stereo_rows,
    summarize_run,
    summary_lines,
)


def _field(n: int = 100, n_valid: int = 80) -> DisparityField:
    valid = np.zeros(n, dtype=bool)
    valid[:n_valid] = True
    return DisparityField(
        frame_idx=0,
        left_pts=np.zeros((n, 2)),
        d=np.zeros((n, 2)),
        znssd=np.zeros(n),
        valid=valid,
    )


def _cs(rows) -> CorrespondenceSet:
    n_frames, n_pts = 2, 100
    return CorrespondenceSet(
        strategy="fake",
        xL=np.zeros((n_frames, n_pts, 2)),
        xR=np.ones((n_frames, n_pts, 2)),
        quality=np.zeros((n_frames, n_pts)),
        source=np.zeros((n_frames, n_pts), dtype=np.uint8),
        diagnostics=tuple(rows),
    )


def test_the_stereo_row_carries_the_split_and_the_epipolar_residual():
    (row,) = stereo_rows(_field(), rejected=(30, 5), epipolar_median_px=0.4)
    assert (row["n_znssd"], row["n_epipolar"]) == (30, 5) and row["n_gated"] == 35
    assert row["epipolar_median_px"] == pytest.approx(0.4)
    (clean,) = stereo_rows(_field())
    assert clean == frame_row(0, "stereo", 100, 80, note="frame-1 stereo match")


def test_stereo_rejections_are_not_reported_as_a_temporal_gate():
    rows = stereo_rows(_field(n_valid=40), rejected=(50, 2), epipolar_median_px=0.3)
    s = summarize_run(_cs(rows))
    assert "stereo" not in s.gated_by_cam
    assert (s.stereo_rejected_znssd, s.stereo_rejected_epipolar) == (50, 2)
    assert s.stereo_epipolar_median_px == pytest.approx(0.3)
    meta = s.to_meta()
    assert meta["stereo_rejected_znssd"] == 50 and meta["stereo_epipolar_median_px"] == 0.3
    text = " ".join(t for _, t in summary_lines(s))
    assert "correlation vs frame 1" not in text
    assert "stereo check removed 50 links" in text and "2 for epipolar distance" in text


def _summary(n_z: int, n_e: int, median: float | None, n_valid: int = 40):
    rows = stereo_rows(_field(n_valid=n_valid), rejected=(n_z, n_e), epipolar_median_px=median)
    return summarize_run(_cs(rows))


def test_a_weakly_correlating_surface_gets_the_threshold_advice():
    assert stereo_check_advice(_summary(50, 2, 0.3)) == "raise_znssd"  # half the links
    assert stereo_check_advice(_summary(5, 1, 0.3, n_valid=90)) is None  # a few: normal
    meta = {"run_params": {"stereo_znssd_max": 0.6, "stereo_epipolar_max_px": 2.0}}
    text = " ".join(t for _, t in summary_lines(_summary(50, 2, 0.3), stopped=meta))
    assert "stereo_znssd_max" in text and "1.0" in text


def test_a_calibration_that_does_not_match_the_images_is_named():
    # Most links off their epipolar line, median far beyond the limit.
    assert stereo_check_advice(_summary(3, 60, 17.6, n_valid=30)) == "calibration"
    # A median residual beyond the limit alone (few links left to reject).
    assert stereo_check_advice(_summary(0, 4, 6.5, n_valid=90)) == "calibration"
    meta = {"run_params": {"stereo_znssd_max": 0.6, "stereo_epipolar_max_px": 2.0}}
    text = " ".join(t for _, t in summary_lines(_summary(3, 60, 17.6, n_valid=30), stopped=meta))
    assert "calibration" in text and "17.6 px" in text


def test_a_run_whose_links_all_fail_the_epipolar_check_names_the_calibration(tmp_path):
    """The synthetic rig with the right camera's calibration shifted ~8 px: every
    true link is found, then rejected for its distance from the epipolar line.
    The error used to say "check the seed point / disparity prior"."""
    pytest.importorskip("al_dic")
    from al_dic_3d.runner import load_config, run_pipeline
    from tests import synth_stereo

    scene = synth_stereo.build_scene(tmp_path, n_frames=2)
    R, T = synth_stereo.rig_rt()
    shift = np.array([0.0, 8.0 * synth_stereo.Z0 / synth_stereo.FY, 0.0])  # ~8 px vertical
    synth_stereo._write_opencv_yaml(tmp_path / scene["calib"], R, T + shift)
    with pytest.raises(RuntimeError) as exc:
        run_pipeline(load_config(synth_stereo.write_config(tmp_path, scene)))
    message = str(exc.value)
    assert "calibration" in message and "epipolar" in message
    assert "seed point" not in message
    median = float(message.split("median ")[1].split(" px")[0])
    assert 5.0 < median < 11.0


def test_no_links_message_points_at_the_cause():
    from al_dic_3d.matching.diagnostics import no_stereo_links_message

    epi = no_stereo_links_message(500, 48, (10.0, 0.0), rejected=(3, 480), epipolar_median_px=17.6)
    assert "calibration" in epi and "17.6 px" in epi and "seed point" not in epi
    corr = no_stereo_links_message(500, 48, (10.0, 0.0), rejected=(470, 2))
    assert "stereo_znssd_max" in corr
    plain = no_stereo_links_message(500, 48, (10.0, 0.0))
    assert "seed point" in plain
