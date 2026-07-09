"""F3.1 failure-reporting audit — the Qt-free diagnostics layer.

Every silent failure path (honesty-gate kills, stereo rejects, quality-gate
demotions, empty results) must become countable rows + a summary that the CLI
prints and the GUI logs. These tests pin the row schema, the summary math, and
the JSON-serializability contract (rows ride in ``RunResult.meta`` through the
session file and the parameters export).
"""

from __future__ import annotations

import json

import numpy as np

from al_dic_3d.matching.contracts import CorrespondenceSet, DisparityField
from al_dic_3d.matching.diagnostics import (
    GATE_NOTE,
    LOW_VALIDITY_FRAC,
    frame_row,
    stereo_rows,
    summarize_run,
    summary_lines,
    temporal_rows,
)
from al_dic_3d.matching.temporal import TemporalField


def _fake_tf(n_frames: int = 3, n: int = 8, gated=(0, 2, 5)) -> TemporalField:
    ref = np.column_stack([np.arange(n, dtype=float), np.zeros(n)])
    u = np.zeros((n_frames, n, 2))
    valid = np.ones((n_frames, n), dtype=bool)
    for k, g in enumerate(gated):
        valid[k, : int(g)] = False
    return TemporalField(
        ref_coords=ref, u_accum=u, valid=valid, n_gated=np.asarray(gated, dtype=np.int64)
    )


def _fake_cs(n_frames: int = 4, n_pts: int = 10, diagnostics=()) -> CorrespondenceSet:
    xL = np.zeros((n_frames, n_pts, 2))
    xR = np.ones((n_frames, n_pts, 2))
    quality = np.zeros((n_frames, n_pts))
    source = np.zeros((n_frames, n_pts), dtype=np.uint8)
    return CorrespondenceSet(
        strategy="fake", xL=xL, xR=xR, quality=quality, source=source, diagnostics=diagnostics
    )


def test_temporal_rows_carry_gate_counts_and_reason():
    rows = temporal_rows("L", _fake_tf())
    assert [r["frame"] for r in rows] == [0, 1, 2]
    assert all(r["cam"] == "L" and r["n_pts"] == 8 for r in rows)
    assert [r["n_gated"] for r in rows] == [0, 2, 5]
    assert rows[0]["note"] == "" and rows[2]["note"] == GATE_NOTE
    assert [r["n_valid"] for r in rows] == [8, 6, 3]


def test_stereo_rows_report_match_rate():
    n = 6
    d = np.zeros((n, 2))
    d[4:] = np.nan
    valid = np.array([True, True, True, True, False, False])
    field = DisparityField(
        frame_idx=0, left_pts=np.zeros((n, 2)), d=d, znssd=np.zeros(n), valid=valid
    )
    (row,) = stereo_rows(field)
    assert row == frame_row(0, "stereo", 6, 4, note="frame-1 stereo match")


def test_summarize_run_low_frames_and_gated_aggregation():
    diag = (
        frame_row(0, "stereo", 10, 9, note="frame-1 stereo match"),
        *temporal_rows("L", _fake_tf(gated=(0, 3, 0))),
        *temporal_rows("R", _fake_tf(gated=(0, 1, 4))),
    )
    cs = _fake_cs(n_frames=3, n_pts=10, diagnostics=diag)
    points = np.zeros((3, 10, 3))
    points[1, 4:] = np.nan  # frame 1: 40% valid -> below the 70% threshold

    s = summarize_run(cs, points)
    assert s.n_frames == 3 and s.n_pts == 10
    assert s.valid_frac[1] == 0.4 and s.low_frames == (1,)
    assert not s.all_empty
    assert (s.stereo_n_valid, s.stereo_n_pts) == (9, 10)
    assert s.gated_by_cam == {"L": 3, "R": 5}
    assert 0.4 < s.median_valid_frac <= 1.0

    meta = s.to_meta()
    json.dumps(meta)  # must survive session.json / parameters export
    assert meta["low_frames"] == [1] and meta["gated_by_cam"] == {"L": 3, "R": 5}


def test_summarize_run_all_empty_and_without_points():
    cs = _fake_cs(n_frames=2, n_pts=5)
    points = np.full((2, 5, 3), np.nan)
    assert summarize_run(cs, points).all_empty
    # Without 3D points the validity comes from the correspondence itself.
    s = summarize_run(cs)
    assert not s.all_empty and s.valid_frac == (1.0, 1.0)


def test_summary_lines_levels_and_wording():
    diag = (frame_row(0, "stereo", 10, 3, note="frame-1 stereo match"),)
    cs = _fake_cs(n_frames=2, n_pts=10, diagnostics=diag)
    points = np.zeros((2, 10, 3))
    points[1, 3:] = np.nan  # 30% valid
    lines = summary_lines(
        summarize_run(cs, points), gates={"znssd_demoted": 4, "reproj_demoted": 0}
    )
    levels = [lv for lv, _ in lines]
    text = "\n".join(msg for _, msg in lines)
    assert "3/10" in text  # stereo match rate, warned (30% < 70%)
    assert levels[0] == "warning"
    assert "frame 1: only 30%" in text
    assert "quality gate (ZNSSD) removed 4" in text
    assert "reprojection gate" not in text  # zero-count gates stay silent
    assert levels[-1] == "info" and "analysis complete" in text

    empty = summary_lines(summarize_run(cs, np.full((2, 10, 3), np.nan)))
    assert empty[-1][0] == "error" and "empty result" in empty[-1][1]


def test_low_validity_threshold_is_70_percent():
    assert LOW_VALIDITY_FRAC == 0.7  # wording in GUI/CLI messages says 70%


def test_correspondence_set_diagnostics_default_and_quality_gate_preserved():
    from al_dic_3d.matching.quality import apply_znssd_gate

    cs = _fake_cs(diagnostics=(frame_row(0, "stereo", 10, 10),))
    assert CorrespondenceSet.empty("s", 2, 3).diagnostics == ()
    quality = cs.quality.copy()
    quality[1, :2] = 9.0  # above the gate
    cs2 = CorrespondenceSet(
        strategy=cs.strategy,
        xL=cs.xL,
        xR=cs.xR,
        quality=quality,
        source=cs.source,
        diagnostics=cs.diagnostics,
    )
    gated = apply_znssd_gate(cs2, 0.5)
    assert gated.diagnostics == cs.diagnostics  # accounting survives the gate
