"""A camera that moved after calibration is named in the run log (new-user audit).

A right camera rotated 1.5 deg after calibration gave a frame-1 median
epipolar residual of 0.8 px with only 207 of 4444 links rejected, so the
log showed an info line while |D| was 8.6 % off; the warning needed 20 %
rejected links or a median above 2 px. Healthy real runs measure 0.02-0.25 px.
"""

from __future__ import annotations

import os

import numpy as np
import pytest

from al_dic_3d.matching.contracts import CorrespondenceSet, DisparityField
from al_dic_3d.matching.diagnostics import (
    EPIPOLAR_DRIFT_PX,
    stereo_check_advice,
    stereo_rows,
    summarize_run,
    summary_lines,
)

# Measured on real data (frame-1 median epipolar residual, px): the worst
# healthy run (GitHub issue #1 rig) and the audit's bumped camera.
HEALTHY_MAX_PX = 0.251
BUMPED_PX = 0.8


def _summary(n: int, n_valid: int, rejected: tuple[int, int], median: float):
    valid = np.zeros(n, dtype=bool)
    valid[:n_valid] = True
    disp = DisparityField(
        frame_idx=0, left_pts=np.zeros((n, 2)), d=np.zeros((n, 2)), znssd=np.zeros(n), valid=valid
    )
    rows = stereo_rows(disp, rejected=rejected, epipolar_median_px=median)
    cs = CorrespondenceSet(
        strategy="fake",
        xL=np.zeros((2, n, 2)),
        xR=np.ones((2, n, 2)),
        quality=np.zeros((2, n)),
        source=np.zeros((2, n), dtype=np.uint8),
        diagnostics=tuple(rows),
    )
    return summarize_run(cs)


def test_the_threshold_keeps_a_clear_margin_above_healthy_runs():
    assert EPIPOLAR_DRIFT_PX >= 1.9 * HEALTHY_MAX_PX  # about twice the worst healthy run
    assert EPIPOLAR_DRIFT_PX < BUMPED_PX


def test_a_bumped_camera_gets_the_recalibrate_warning():
    s = _summary(4542, 4214, (23, 207), BUMPED_PX)  # the audit's numbers
    assert stereo_check_advice(s) == "recalibrate"
    level, text = next(line for line in summary_lines(s) if "recalibrate" in line[1])
    assert level == "warning" and "0.8 px" in text and "moved" in text


def test_healthy_runs_stay_quiet():
    assert stereo_check_advice(_summary(30228, 30163, (1, 0), 0.042)) is None
    assert stereo_check_advice(_summary(1139, 1105, (10, 0), 0.087)) is None
    # The issue #1 rig keeps its weak-correlation advice, not a calibration one.
    assert stereo_check_advice(_summary(2008, 990, (810, 12), 0.222)) == "raise_znssd"


def test_the_gui_log_says_to_recalibrate():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QObject
    from PySide6.QtWidgets import QApplication

    from al_dic_3d.gui.panels.run_summary import RunSummaryMixin

    QApplication.instance() or QApplication([])

    class _Log(RunSummaryMixin, QObject):
        def __init__(self) -> None:
            super().__init__()
            self.lines: list[tuple[str, str]] = []

        def _append_log(self, text: str, level: str = "info") -> None:
            self.lines.append((level, text))

    log = _Log()
    log._log_stereo_check(_summary(4542, 4214, (23, 207), BUMPED_PX), {})
    warn = [t for lvl, t in log.lines if lvl == "warn"]
    assert len(warn) == 1 and "Recalibrate" in warn[0] and "0.8 px" in warn[0]
