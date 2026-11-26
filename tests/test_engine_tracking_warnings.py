"""The 2D engine's tracking warnings reach the run summary (robustness audit 2026-11-26).

``run_aldic`` reports nodes whose displacement "was copied from that node and
may be wrong" (and material lost from tracking) only through :mod:`logging`:
the CLI user saw it on stderr at best, the GUI user never.
"""

from __future__ import annotations

import os
import warnings
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest
from al_dic.core.data_structures import FrameTrackingStats, TrackingDiagnostics

from al_dic_3d import synthetic as syn
from al_dic_3d.matching.contracts import CorrespondenceSet
from al_dic_3d.matching.diagnostics import summarize_run, summary_lines, temporal_rows
from al_dic_3d.matching.engine_log import tracking_warnings
from al_dic_3d.matching.temporal import TemporalField


def _stats(frame: int, ref: int, n_far: int, n_tracked: int = 1000) -> FrameTrackingStats:
    return FrameTrackingStats(
        frame=frame,
        ref_frame=ref,
        n_queried=1000,
        n_extrapolated=n_far + 40,
        n_extrapolated_far=n_far,
        n_extrapolated_border=0,
        max_extrapolation_px=37.5,
        n_lost_parent_mask=0,
        n_lost_child_mask=1000 - n_tracked,
        n_lost_no_data=0,
        n_tracked=n_tracked,
        n_tracked_extrapolated=n_far,
    )


def _diag(*frames: FrameTrackingStats) -> TrackingDiagnostics:
    return TrackingDiagnostics(
        n_nodes=1000,
        n_never_material=0,
        far_extrapolation_px=16.0,
        measurable_box=(0, 500, 0, 500),
        has_later_references=True,
        frames=frames,
    )


def test_engine_warnings_are_read_from_the_pipeline_result():
    diag = _diag(_stats(1, 0, 0), _stats(2, 1, 25), _stats(3, 2, 30, n_tracked=300))
    found = {w["key"]: w for w in tracking_warnings(SimpleNamespace(tracking_diagnostics=diag))}
    assert set(found) == {"grid_miss", "material_loss"}
    miss = found["grid_miss"]
    assert (miss["frame"], miss["ref_frame"], miss["count"], miss["n_frames"]) == (3, 2, 30, 2)
    assert miss["far_px"] == 16.0
    loss = found["material_loss"]
    assert loss["count"] == 700 and loss["n_material"] == 1000


def test_a_clean_or_unreadable_record_gives_no_warning():
    assert tracking_warnings(SimpleNamespace(tracking_diagnostics=None)) == ()
    assert tracking_warnings(object()) == ()
    clean = _diag(_stats(1, 0, 0), _stats(2, 1, 1))
    assert tracking_warnings(SimpleNamespace(tracking_diagnostics=clean)) == ()
    assert tracking_warnings(SimpleNamespace(tracking_diagnostics="garbage")) == ()


def _summary_with(warnings_: tuple[dict, ...]):
    n_frames, n = 4, 20
    tf = TemporalField(
        ref_coords=np.zeros((n, 2)),
        u_accum=np.zeros((n_frames, n, 2)),
        valid=np.ones((n_frames, n), dtype=bool),
        engine_warnings=warnings_,
    )
    rows = temporal_rows("R", tf)
    cs = CorrespondenceSet(
        strategy="fake",
        xL=np.zeros((n_frames, n, 2)),
        xR=np.ones((n_frames, n, 2)),
        quality=np.zeros((n_frames, n)),
        source=np.zeros((n_frames, n), dtype=np.uint8),
        diagnostics=tuple(rows),
    )
    return summarize_run(cs)


GRID_MISS = {
    "key": "grid_miss",
    "frame": 3,
    "ref_frame": 2,
    "count": 30,
    "fraction": 0.03,
    "max_px": 37.5,
    "n_frames": 2,
    "far_px": 16.0,
    "n_material": 1000,
}


def test_the_cli_summary_words_the_engine_warning():
    s = _summary_with((GRID_MISS,))
    assert s.engine_warnings == ({**GRID_MISS, "cam": "R"},)
    assert s.to_meta()["engine_warnings"][0]["key"] == "grid_miss"
    level, text = next(line for line in summary_lines(s) if "may be wrong" in line[1])
    assert level == "warning"
    assert text.startswith("camera R: on frame 4, 30 points lay more than 16.0 px")
    assert "reference frame 3" in text
    assert not any("may be wrong" in t for _, t in summary_lines(_summary_with(())))


def test_the_gui_log_shows_the_engine_warning():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QObject
    from PySide6.QtWidgets import QApplication

    from al_dic_3d.gui.panels.run_summary import RunSummaryMixin

    QApplication.instance() or QApplication([])
    loss = {**GRID_MISS, "key": "material_loss", "count": 700, "fraction": 0.7}

    class _Log(RunSummaryMixin, QObject):
        def __init__(self) -> None:
            super().__init__()
            self.lines: list[tuple[str, str]] = []

        def _append_log(self, text: str, level: str = "info") -> None:
            self.lines.append((level, text))

    log = _Log()
    log._log_engine_warnings(_summary_with((GRID_MISS, loss, {"key": "unknown"})))
    assert [lvl for lvl, _ in log.lines] == ["warn", "warn"]
    assert (
        log.lines[0][1].startswith("Camera R: on frame 4, 30 points")
        and "may be wrong" in (log.lines[0][1])
    )
    assert log.lines[1][1].startswith("Camera R: 700 of 1000 points (70%)")


def test_an_engine_warning_reaches_the_run_summary_end_to_end(tmp_path, monkeypatch):
    """The real engine's record is read in the run: inject one finding into its assessment."""
    import al_dic.core.tracking_diagnostics as td

    from al_dic_3d.runner import load_config, run_pipeline

    real = td.assess_tracking
    seen: list[object] = []

    def _assess(diag):
        # The engine assesses its record itself (for its log) and the 3D layer
        # again; only the first record seen (the left camera's) gets the finding.
        seen.append(diag)
        found = real(diag)
        if diag is not seen[0]:
            return found
        return (
            td.TrackingFinding(
                key=td.FINDING_GRID_MISS,
                severity=td.SEVERITY_WARNING,
                frame=2,
                ref_frame=1,
                count=7,
                fraction=0.05,
                max_px=30.0,
                n_frames=1,
            ),
            *found,
        )

    monkeypatch.setattr(td, "assess_tracking", _assess)
    scene = syn.build_scene(tmp_path, img=320, n_frames=4)
    cfg = load_config(syn.write_config(tmp_path, scene, explicit_files=True))
    cfg = replace(cfg, output_dir=tmp_path / "out", reference_mode="incremental")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = run_pipeline(cfg)
    assert seen, "the engine returned no tracking record for an incremental run"
    s = summarize_run(result.correspondence)
    assert [w["cam"] for w in s.engine_warnings if w["count"] == 7] == ["L"]
    assert any("camera L: on frame 3, 7 points" in t for _, t in summary_lines(s))
    assert result.meta["summary"]["engine_warnings"][0]["count"] == 7
