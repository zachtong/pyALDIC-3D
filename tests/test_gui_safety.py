"""Offscreen tests for UX Batch G1 — safety & correctness guards.

G1.1 unsaved-changes guard, G1.2 close-during-run safety (main + strain
windows), G1.3 ROI wrong-view auto-switch, G1.4 minimum/initial window size,
G1.5 pair-list frame jump, G1.7 global exception hook. G1.6 (export Open
Folder guard) lives in ``test_export_tables.py``, which owns the heavy
RunResult fixture the export dialog needs.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import sys
import time

import numpy as np
import pytest

pytest.importorskip("PySide6")
cv2 = pytest.importorskip("cv2")

from PySide6.QtCore import QThread  # noqa: E402

from al_dic_3d.gui.app import create_app, install_excepthook  # noqa: E402
from al_dic_3d.gui.main_window import MainWindow3D, initial_window_size  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


@pytest.fixture(scope="module")
def images(tmp_path_factory):
    """Three tiny L/R image pairs — enough for view/draft logic, no pipeline run."""
    d = tmp_path_factory.mktemp("g1_images")
    rng = np.random.default_rng(3)
    files: dict[str, list[str]] = {"L": [], "R": []}
    for cam in ("L", "R"):
        for k in range(3):
            path = d / f"{cam}_{k:02d}.png"
            cv2.imwrite(str(path), rng.integers(0, 255, (48, 48), dtype=np.uint8))
            files[cam].append(str(path))
    return files


def _window(images) -> MainWindow3D:
    win = MainWindow3D()
    win.show()
    draft = win.controller.state.draft
    draft.left = list(images["L"])
    draft.right = list(images["R"])
    win._left.refresh_all()
    win.signals.images_changed.emit()
    return win


class _SlowStubWorker(QThread):
    """Runs until request_stop — a stand-in for a long pipeline run (G1.2)."""

    def __init__(self) -> None:
        super().__init__()
        self._stop = False

    def request_stop(self) -> None:
        self._stop = True

    def run(self) -> None:  # QThread entry point (worker thread)
        while not self._stop:
            time.sleep(0.005)


class _ShortWorker(QThread):
    """Finishes on its own after ~50 ms (cascade join path)."""

    def run(self) -> None:  # QThread entry point (worker thread)
        time.sleep(0.05)


# ---------------------------------------------------------------------------
# G1.1 — unsaved-changes guard
# ---------------------------------------------------------------------------


def test_new_project_prompt_cancel_aborts(qapp, images, monkeypatch):
    win = _window(images)
    win.controller.state.mark_dirty()
    prompts: list[int] = []

    def fake_prompt(self) -> str:
        prompts.append(1)
        return "cancel"

    monkeypatch.setattr(MainWindow3D, "_prompt_unsaved", fake_prompt)
    old_state = win.controller.state
    win._new_project()
    assert prompts  # the guard asked
    assert win.controller.state is old_state  # action aborted
    assert win.controller.state.draft.left  # nothing was dropped
    win.controller.state.dirty = False
    win.close()


def test_new_project_prompt_discard_proceeds(qapp, images, monkeypatch):
    win = _window(images)
    win.controller.state.mark_dirty()
    monkeypatch.setattr(MainWindow3D, "_prompt_unsaved", lambda self: "discard")
    old_state = win.controller.state
    win._new_project()
    assert win.controller.state is not old_state
    assert not win.controller.state.draft.left
    assert not win.controller.state.dirty  # fresh project starts clean
    win.close()


def test_prompt_save_routes_through_save_flow(qapp, images, tmp_path, monkeypatch):
    win = _window(images)
    win.controller.state.mark_dirty()
    monkeypatch.setattr(MainWindow3D, "_prompt_unsaved", lambda self: "save")
    target = tmp_path / "g1_guard.aldic3d"
    monkeypatch.setattr(
        "PySide6.QtWidgets.QFileDialog.getSaveFileName",
        staticmethod(lambda *_a, **_k: (str(target), "")),
    )
    win._new_project()
    assert target.exists()  # the save flow actually ran
    assert not win.controller.state.dirty
    assert not win.controller.state.draft.left  # then the action proceeded
    win.close()


def test_prompt_save_cancelled_dialog_aborts_action(qapp, images, monkeypatch):
    win = _window(images)
    win.controller.state.mark_dirty()
    monkeypatch.setattr(MainWindow3D, "_prompt_unsaved", lambda self: "save")
    monkeypatch.setattr(
        "PySide6.QtWidgets.QFileDialog.getSaveFileName",
        staticmethod(lambda *_a, **_k: ("", "")),  # user backs out of Save As
    )
    old_state = win.controller.state
    win._new_project()
    assert win.controller.state is old_state  # abort: nothing was saved or lost
    assert win.controller.state.dirty
    win.controller.state.dirty = False
    win.close()


def test_clean_or_empty_state_never_prompts(qapp, monkeypatch):
    def boom(self) -> str:
        raise AssertionError("prompt must not appear")

    monkeypatch.setattr(MainWindow3D, "_prompt_unsaved", boom)
    win = MainWindow3D()  # clean: dirty False
    win._new_project()
    win.controller.state.mark_dirty()  # dirty but nothing worth saving
    win._new_project()
    assert win.close()


def test_close_dirty_cancel_keeps_window_open(qapp, images, monkeypatch):
    win = _window(images)
    win.controller.state.mark_dirty()
    monkeypatch.setattr(MainWindow3D, "_prompt_unsaved", lambda self: "cancel")
    assert not win.close()
    assert win.isVisible()
    monkeypatch.setattr(MainWindow3D, "_prompt_unsaved", lambda self: "discard")
    assert win.close()


# ---------------------------------------------------------------------------
# G1.2 — close-during-run safety
# ---------------------------------------------------------------------------


def test_close_during_run_declined_keeps_window_open(qapp, images, monkeypatch):
    win = _window(images)
    worker = _SlowStubWorker()
    worker.start()
    win._right._worker = worker
    try:
        assert win._right.active_worker() is worker
        monkeypatch.setattr(MainWindow3D, "_confirm_cancel_run", lambda self: False)
        assert not win.close()
        assert win.isVisible()
        assert worker.isRunning()  # the run was left untouched
    finally:
        worker.request_stop()
        assert worker.wait(5_000)
    assert win.close()


def test_close_during_run_accepted_cancels_joins_and_closes(qapp, images, monkeypatch):
    win = _window(images)
    worker = _SlowStubWorker()
    worker.start()
    win._right._worker = worker
    monkeypatch.setattr(MainWindow3D, "_confirm_cancel_run", lambda self: True)
    assert win.close()
    assert not worker.isRunning()  # request_stop + join happened before close


def test_strain_window_close_declined_keeps_window_open(qapp, monkeypatch):
    from al_dic_3d.gui.controller import WorkflowController
    from al_dic_3d.gui.state import GuiSignals
    from al_dic_3d.gui.strain_window import StrainWindow3D

    sw = StrainWindow3D(WorkflowController(), GuiSignals())
    sw.show()
    worker = _SlowStubWorker()
    worker.start()
    sw._worker = worker
    try:
        monkeypatch.setattr(StrainWindow3D, "_confirm_close_during_compute", lambda self: False)
        assert not sw.close()
        assert sw.isVisible()
        assert worker.isRunning()
    finally:
        worker.request_stop()
        assert worker.wait(5_000)
    assert sw.close()


def test_cascade_close_joins_strain_worker_without_prompt(qapp, images, monkeypatch):
    from al_dic_3d.gui.strain_window import StrainWindow3D

    win = _window(images)
    sw = StrainWindow3D(win.controller, win.signals)
    win._strain_window = sw
    worker = _ShortWorker()
    worker.start()
    sw._worker = worker

    def boom(self) -> bool:
        raise AssertionError("cascade close must join, never prompt")

    monkeypatch.setattr(StrainWindow3D, "_confirm_close_during_compute", boom)
    assert win.close()  # joins the ~50 ms worker, then cascades
    assert not worker.isRunning()
    assert win._strain_window is None


# ---------------------------------------------------------------------------
# G1.3 — ROI wrong-view trap
# ---------------------------------------------------------------------------


def test_shape_tool_jumps_to_left_frame1(qapp, images):
    win = _window(images)
    logged: list[str] = []
    win.signals.log.connect(lambda m, _l: logged.append(m))
    win.signals.set_camera("R")
    win.signals.set_current_frame(2, 3)
    win._on_roi_draw_requested("rect", "add")
    assert win.signals.current_camera == "L"
    assert win.signals.current_frame == 0
    assert win._canvas_area.canvas._tool == "rect"  # the tool still armed
    assert any("Switched to left camera" in m for m in logged)
    win.close()


def test_refine_brush_jumps_to_left_frame1(qapp, images):
    win = _window(images)
    win.signals.set_camera("R")
    win.signals.set_current_frame(1, 3)
    win._on_brush_requested("paint", 10)
    assert win.signals.current_camera == "L"
    assert win.signals.current_frame == 0
    assert win._canvas_area.canvas._tool == "brush"
    win.close()


def test_left_frame1_view_arms_without_jump_or_log(qapp, images):
    win = _window(images)
    logged: list[str] = []
    win.signals.log.connect(lambda m, _l: logged.append(m))
    win._on_roi_draw_requested("circle", "add")  # already on L / frame 1
    assert win.signals.current_camera == "L" and win.signals.current_frame == 0
    assert not any("Switched to left camera" in m for m in logged)
    win.close()


# ---------------------------------------------------------------------------
# G1.4 — minimum / initial window size
# ---------------------------------------------------------------------------


def test_minimum_size_fits_1366x768_laptops(qapp):
    win = MainWindow3D()
    assert (win.minimumWidth(), win.minimumHeight()) == (1100, 700)
    win.close()


def test_initial_size_clamps_to_available_screen():
    assert initial_window_size(2560, 1440) == (1420, 860)  # big display: preferred
    assert initial_window_size(1366, 768) == (1326, 700)  # laptop: fits on screen
    assert initial_window_size(800, 600) == (1100, 700)  # floor = the minimum size


def test_three_columns_usable_at_minimum_size(qapp, images):
    from PySide6.QtWidgets import QApplication

    win = _window(images)
    win.resize(1100, 700)
    QApplication.processEvents()
    assert win._right.width() == 280  # fixed sidebar intact
    assert win._canvas_area.width() >= 450  # canvas keeps a usable share
    win.close()


# ---------------------------------------------------------------------------
# G1.5 — pair-list frame jump during an L/R count mismatch
# ---------------------------------------------------------------------------


def test_pair_list_jump_clamps_against_longer_list(qapp, images):
    win = _window(images)
    draft = win.controller.state.draft
    draft.left = list(images["L"])[:2]  # 2 left vs 3 right (mismatch)
    draft.right = list(images["R"])
    win._left.refresh_images()
    assert win._left._pair_list.topLevelItemCount() == 3
    win._left._pair_list.setCurrentItem(win._left._pair_list.topLevelItem(2))
    assert win.signals.current_frame == 2  # was clamped to len(left)-1 == 1 before G1.5
    win.close()


# ---------------------------------------------------------------------------
# G1.7 — global exception hook (2D port)
# ---------------------------------------------------------------------------


def test_excepthook_logs_crash_to_gui_console(qapp):
    from al_dic_3d.gui.state import GuiSignals

    signals = GuiSignals()
    records: list[tuple[str, str]] = []
    signals.log.connect(lambda m, lvl: records.append((m, lvl)))
    old_hook = sys.excepthook
    try:
        hook = install_excepthook(signals)
        assert sys.excepthook is hook  # installed globally
        try:
            raise ValueError("boom from a slot")
        except ValueError:
            sys.excepthook(*sys.exc_info())  # what Qt does for a crashed slot
    finally:
        sys.excepthook = old_hook
    assert ("CRASH: ValueError: boom from a slot", "error") in records


def test_excepthook_survives_a_crashing_log_sink(qapp):
    from al_dic_3d.gui.state import GuiSignals

    signals = GuiSignals()

    def bad_slot(_m: str, _lvl: str) -> None:
        raise RuntimeError("console is gone")

    signals.log.connect(bad_slot)
    old_hook = sys.excepthook
    try:
        hook = install_excepthook(signals)
        try:
            raise ValueError("boom")
        except ValueError:
            hook(*sys.exc_info())  # must not raise despite the broken sink
    finally:
        sys.excepthook = old_hook
