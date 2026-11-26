"""The run log numbers frames like the GUI and ignores frames a cancel never computed.

New-user audit (2026-11-25): the log said "Frame 2: only 0% valid" for the
third image (0-based, while the frame navigator counts from 1), and after a
cancel the frames never computed were reported as 0 % valid, followed by a
green "Analysis complete ... 1 frame below 70%".
"""

from __future__ import annotations

import os
from types import SimpleNamespace

import numpy as np
import pytest

from al_dic_3d.matching.contracts import CorrespondenceSet
from al_dic_3d.matching.diagnostics import computed_frames, summarize_run, summary_lines

N_PTS = 20


def _result(valid_per_frame: list[int], meta: dict | None = None):
    n_frames = len(valid_per_frame)
    points = np.full((n_frames, N_PTS, 3), np.nan)
    for k, n_valid in enumerate(valid_per_frame):
        points[k, :n_valid] = 1.0
    cs = CorrespondenceSet(
        strategy="fake",
        xL=np.zeros((n_frames, N_PTS, 2)),
        xR=np.ones((n_frames, N_PTS, 2)),
        quality=np.zeros((n_frames, N_PTS)),
        source=np.zeros((n_frames, N_PTS), dtype=np.uint8),
    )
    return SimpleNamespace(
        correspondence=cs, reconstruction=SimpleNamespace(points=points), meta=dict(meta or {})
    )


_STOPPED = {"stopped_early": True, "stopped_at_frame": 2, "stop_reason": "cancelled"}


def test_frames_past_the_stop_leave_the_summary():
    r = _result([20, 19, 0], _STOPPED)
    s = computed_frames(summarize_run(r.correspondence, r.reconstruction.points), r.meta)
    assert s.low_frames == () and len(s.valid_frac) == 2 and s.n_frames == 3
    assert s.median_valid_frac == pytest.approx(0.975)
    full = summarize_run(r.correspondence, r.reconstruction.points)
    assert computed_frames(full, {}) is full  # a complete run is untouched


def test_the_cli_summary_reports_a_partial_result_not_a_complete_one():
    r = _result([20, 19, 0], _STOPPED)
    lines = summary_lines(summarize_run(r.correspondence, r.reconstruction.points), stopped=r.meta)
    text = " | ".join(t for _, t in lines)
    assert "only 0%" not in text and "analysis complete" not in text
    assert ("warning", lines[-1][1]) == lines[-1] and "2 of 3 frames computed" in lines[-1][1]


def _gui_log(result) -> list[tuple[str, str]]:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QObject
    from PySide6.QtWidgets import QApplication

    from al_dic_3d.gui.panels.run_summary import RunSummaryMixin

    QApplication.instance() or QApplication([])

    class _Log(RunSummaryMixin, QObject):
        def __init__(self) -> None:
            super().__init__()
            self.controller = SimpleNamespace(state=SimpleNamespace(result=result))
            self.lines: list[tuple[str, str]] = []

        def _append_log(self, text: str, level: str = "info") -> None:
            self.lines.append((level, text))

    log = _Log()
    log._log_run_summary()
    return log.lines


def test_the_gui_log_numbers_frames_from_one():
    lines = _gui_log(_result([20, 19, 5]))
    text = " | ".join(t for _, t in lines)
    assert "Frame 3: only 25% of points valid" in text and "Frame 2:" not in text


def test_the_gui_log_after_a_cancel_skips_uncomputed_frames():
    lines = _gui_log(_result([20, 19, 0], _STOPPED))
    text = " | ".join(t for _, t in lines)
    assert "only 0%" not in text and "Analysis complete" not in text
    level, last = lines[-1]
    assert level == "warn" and "2 of 3 frames computed" in last
    assert not any(lvl == "success" for lvl, _ in lines)


def test_the_collapse_advice_names_the_first_deformed_frame_as_frame_2():
    lines = _gui_log(_result([20, 18, 1, 1], {"run_params": {"reference_mode": "accumulative"}}))
    advice = next(t for _, t in lines if t.startswith("Validity falls"))
    assert "(frame 2)" in advice
