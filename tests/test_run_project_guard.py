"""Switching projects during a run must not leak the run's result (fix batch V, B5).

``WorkflowController.run`` read ``self.state`` only after ``run_pipeline``
returned, so a New/Open Project issued mid-run received the OLD run's result
(the empty new project reported ``has_results``), and New Project forced the
run state to idle while the worker kept running.
"""

from __future__ import annotations

import os
import threading
import time

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QCoreApplication  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

import al_dic_3d.runner as runner_mod  # noqa: E402
from al_dic_3d.gui.controller import ProjectSwitchedDuringRun, WorkflowController  # noqa: E402
from al_dic_3d.project import AppState3D  # noqa: E402


class _Sentinel:
    meta: dict = {}


def _slow_pipeline(started: threading.Event, seconds: float = 3.0, fail: bool = False):
    def fake(cfg, progress=None, stop=None):
        started.set()
        t0 = time.monotonic()
        while time.monotonic() - t0 < seconds:
            if stop is not None and stop():
                raise RuntimeError("cancelled")
            time.sleep(0.02)
        if fail:
            raise RuntimeError("synthetic failure")
        return _Sentinel()

    return fake


def test_controller_discards_a_result_whose_project_was_replaced(monkeypatch):
    started = threading.Event()
    monkeypatch.setattr(runner_mod, "run_pipeline", _slow_pipeline(started, 0.4))
    ctrl = WorkflowController(AppState3D())
    ctrl.state.config = object()  # skip build_config (the fake ignores it)
    ctrl.state.draft.left = []  # not ready -> uses the explicit config
    errors: list[BaseException] = []

    def run():
        try:
            ctrl.run()
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    t = threading.Thread(target=run)
    t.start()
    assert started.wait(5)
    ctrl.new_project()  # the user switched projects mid-run
    fresh = ctrl.state
    t.join(10)
    assert fresh.result is None and not fresh.has_results
    assert errors and isinstance(errors[0], ProjectSwitchedDuringRun)


@pytest.fixture()
def win(monkeypatch):
    import al_dic_3d.gui.main_window as mw

    app = QApplication.instance() or QApplication([])  # noqa: F841
    w = mw.MainWindow3D()
    w.show()
    yield w
    worker = w._right.active_worker()
    if worker is not None:
        worker.request_stop()
        worker.wait(10_000)
    w.close()


def _start_fake_run(win, monkeypatch, seconds: float = 3.0, fail: bool = False) -> threading.Event:
    started = threading.Event()
    monkeypatch.setattr(runner_mod, "run_pipeline", _slow_pipeline(started, seconds, fail))
    monkeypatch.setattr(type(win.controller.state.draft), "issues", lambda self: [])
    monkeypatch.setattr(type(win.controller.state.draft), "is_ready", lambda self: False)
    win.controller.state.config = object()
    win._right._on_run()
    assert started.wait(5)
    return started


def test_new_project_is_refused_while_running_when_the_user_declines(win, monkeypatch):
    import al_dic_3d.gui.main_window as mw

    _start_fake_run(win, monkeypatch)
    state = win.controller.state
    monkeypatch.setattr(mw.MainWindow3D, "_confirm_cancel_run_for_switch", lambda self: False)
    win._new_project()
    assert win.controller.state is state  # nothing switched
    assert win._right.active_worker() is not None  # run untouched
    assert win.signals.run_state == "running"


def test_new_project_cancels_the_run_first_when_the_user_agrees(win, monkeypatch):
    import al_dic_3d.gui.main_window as mw

    _start_fake_run(win, monkeypatch)
    monkeypatch.setattr(mw.MainWindow3D, "_confirm_cancel_run_for_switch", lambda self: True)
    win._new_project()
    QCoreApplication.processEvents()
    assert win._right.active_worker() is None  # joined before switching
    assert not win.controller.state.has_results
    assert win.signals.run_state != "running"


def test_project_actions_are_disabled_while_running(win, monkeypatch):
    _start_fake_run(win, monkeypatch, seconds=0.5, fail=True)
    assert not win._new_action.isEnabled()
    assert not win._open_action.isEnabled()
    assert not win._recent_menu.isEnabled()
    worker = win._right.active_worker()
    worker.wait(10_000)
    QCoreApplication.processEvents()
    assert win._new_action.isEnabled() and win._open_action.isEnabled()
