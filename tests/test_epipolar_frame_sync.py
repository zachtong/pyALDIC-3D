"""A left/right frame offset is named in the run summary (robustness audit 2026-11-26).

One right image missing and the rest renumbered put every later stereo pair out
of step: the run reported 100 % valid with a 3D error of 1.0 mm instead of
0.05 mm, because the frame-1 stereo check only looks at frame 1. The median
epipolar residual of the tracked pairs is the tell: 0.023-0.026 px on the
healthy frames, 0.31-0.38 px (0.35 mm/frame motion) or 2.1-2.3 px (larger
motion) on the out-of-step ones. Real data stay flat: the quickstart D
specimen measures 0.087 / 0.078 / 0.089 px over its three frames.
"""

from __future__ import annotations

import os
import shutil
import time
import warnings
from dataclasses import replace

import numpy as np
import pytest

from al_dic_3d import synthetic as syn
from al_dic_3d.matching.contracts import CorrespondenceSet
from al_dic_3d.matching.diagnostics import (
    EPIPOLAR_JUMP_PX,
    EPIPOLAR_ROW_CAM,
    epipolar_rows,
    frame_row,
    frame_sync_frames,
    summarize_run,
    summary_lines,
)

# Per-frame medians (px) the audit measured on its 640 px synthetic scenes.
HEALTHY = (0.006, 0.023, 0.023, 0.026, 0.026, 0.025)
DROPPED_SLOW = (0.006, 0.023, 0.376, 0.345, 0.306)
DROPPED_FAST = (0.006, 0.019, 2.258, 2.143, 2.242)
REAL_QUICKSTART = (0.0866, 0.078, 0.0892)
SWAPPED = (4.2, 4.21, 4.25)  # left and right swapped: the frame-1 advice speaks


def _summary(medians) -> object:
    n_frames, n = len(medians), 50
    rows = [
        {**frame_row(k, EPIPOLAR_ROW_CAM, n, n), "epipolar_median_px": m}
        for k, m in enumerate(medians)
    ]
    cs = CorrespondenceSet(
        strategy="fake",
        xL=np.zeros((n_frames, n, 2)),
        xR=np.ones((n_frames, n, 2)),
        quality=np.zeros((n_frames, n)),
        source=np.zeros((n_frames, n), dtype=np.uint8),
        diagnostics=tuple(rows),
    )
    return summarize_run(cs)


def test_healthy_and_real_runs_stay_quiet():
    assert frame_sync_frames(_summary(HEALTHY)) == ()
    assert frame_sync_frames(_summary(REAL_QUICKSTART)) == ()
    assert max(REAL_QUICKSTART) - REAL_QUICKSTART[0] < 0.1 * EPIPOLAR_JUMP_PX


def test_an_out_of_step_pair_is_flagged_from_its_first_frame():
    assert frame_sync_frames(_summary(DROPPED_SLOW)) == (2, 3, 4)
    assert frame_sync_frames(_summary(DROPPED_FAST)) == (2, 3, 4)


def test_a_calibration_off_from_frame_1_is_left_to_the_frame_1_advice():
    assert frame_sync_frames(_summary(SWAPPED)) == ()


def test_a_result_saved_before_the_check_has_no_medians():
    s = _summary(())
    assert s.epipolar_by_frame == () and frame_sync_frames(s) == ()
    assert "epipolar_by_frame" in s.to_meta()


def test_the_cli_summary_names_the_first_frame_and_the_causes():
    lines = summary_lines(_summary(DROPPED_SLOW))
    level, text = next(line for line in lines if "epipolar lines" in line[1])
    assert level == "warning"
    assert text.startswith("frame 3 is the first of 3 frames")
    assert "0.38 px" in text and "missing" in text and "unsynchronised" in text
    assert not any("epipolar lines" in t for _, t in summary_lines(_summary(HEALTHY)))


def test_the_gui_log_warns_about_the_frame_offset():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from types import SimpleNamespace

    from PySide6.QtCore import QObject
    from PySide6.QtWidgets import QApplication

    from al_dic_3d.gui.panels.run_summary import RunSummaryMixin

    QApplication.instance() or QApplication([])
    s = _summary(DROPPED_FAST)
    n_frames = len(DROPPED_FAST)
    cs = CorrespondenceSet(
        strategy="fake",
        xL=np.zeros((n_frames, 50, 2)),
        xR=np.ones((n_frames, 50, 2)),
        quality=np.zeros((n_frames, 50)),
        source=np.zeros((n_frames, 50), dtype=np.uint8),
        diagnostics=tuple(
            {**frame_row(k, EPIPOLAR_ROW_CAM, 50, 50), "epipolar_median_px": m}
            for k, m in enumerate(DROPPED_FAST)
        ),
    )
    assert s.epipolar_by_frame == DROPPED_FAST
    result = SimpleNamespace(
        correspondence=cs,
        reconstruction=SimpleNamespace(points=np.zeros((n_frames, 50, 3))),
        meta={},
    )

    class _Log(RunSummaryMixin, QObject):
        def __init__(self) -> None:
            super().__init__()
            self.lines: list[tuple[str, str]] = []
            self.controller = SimpleNamespace(state=SimpleNamespace(result=result))

        def _append_log(self, text: str, level: str = "info") -> None:
            self.lines.append((level, text))

    log = _Log()
    log._log_run_summary()
    warn = [t for lvl, t in log.lines if lvl == "warn" and "epipolar lines" in t]
    assert len(warn) == 1 and warn[0].startswith("Frame 3 is the first of 3 frames")
    assert "2.26 px" in warn[0]


def test_epipolar_rows_measure_the_pairs_and_sample_large_meshes():
    _, _, _, _, rig = syn.cameras(320)
    rng = np.random.default_rng(3)
    xl = rng.uniform(80, 240, size=(1, 6000, 2))
    # Pairs ON their epipolar lines: back-project each left point onto a plane
    # and project it into the right camera.
    from al_dic_3d.calibration import undistort_points

    nl = undistort_points(xl[0], rig.cameras["L"])
    X = np.column_stack([nl, np.ones(len(nl))]) * syn.Z0
    R, T = rig.pose("R")
    Xr = X @ R.T + T
    import cv2

    intr = rig.cameras["R"]
    K = np.array([[intr.fx, 0, intr.cx], [0, intr.fy, intr.cy], [0, 0, 1]])
    dist = np.array([intr.k1, intr.k2, intr.p1, intr.p2, intr.k3])
    pr, _ = cv2.projectPoints(Xr, np.zeros(3), np.zeros(3), K, dist)
    xr = pr.reshape(1, -1, 2)
    # Frame 2: the right points shifted 1 px vertically (across the lines).
    xL = np.concatenate([xl, xl])
    xR = np.concatenate([xr, xr + np.array([0.0, 1.0])])
    xR[0, :10] = np.nan
    t0 = time.perf_counter()
    rows = epipolar_rows(rig, xL, xR)
    elapsed = time.perf_counter() - t0
    assert [r["cam"] for r in rows] == [EPIPOLAR_ROW_CAM] * 2
    assert rows[0]["n_valid"] == 5990 and rows[0]["epipolar_median_px"] < 0.01
    assert 0.8 < rows[1]["epipolar_median_px"] < 1.05  # 1 px, scaled by the distortion
    assert elapsed < 0.5  # milliseconds per frame, sampled
    few = epipolar_rows(rig, xL[:, :5], xR[:, :5])
    assert "epipolar_median_px" not in few[0]


def _run(cfg):
    from al_dic_3d.runner import run_pipeline

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return run_pipeline(cfg)


def test_a_missing_right_image_warns_end_to_end(tmp_path):
    from al_dic_3d.runner import load_config

    scene = syn.build_scene(tmp_path, img=320, n_frames=5)
    cfg = load_config(syn.write_config(tmp_path, scene, explicit_files=True))
    cfg = replace(cfg, output_dir=tmp_path / "out")
    base = _run(cfg)
    assert frame_sync_frames(summarize_run(base.correspondence)) == ()
    # Right image 2 is lost and the later ones renumbered: 4 frames, 2-3 out of step.
    right = []
    for j, i in enumerate((0, 1, 3, 4)):
        name = f"Rr_{j:03d}.png"
        shutil.copyfile(tmp_path / scene["right"][i], tmp_path / name)
        right.append(name)
    dropped = _run(replace(cfg, left=tuple(scene["left"][:4]), right=tuple(right)))
    s = summarize_run(dropped.correspondence)
    assert frame_sync_frames(s) == (2, 3)
    assert any("frame 3 is the first of 2 frames" in t for _, t in summary_lines(s))
    assert dropped.meta["summary"]["epipolar_by_frame"][2] > EPIPOLAR_JUMP_PX
