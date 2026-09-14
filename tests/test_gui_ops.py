"""Frozen-application operations (H2): log file, faulthandler, crash dialog, hook order.

A windowed frozen build has ``sys.stderr is None``: every traceback printed
there is lost. These tests pin the replacement channels -- the per-user log
file, the crash log for native faults, the modal crash dialog -- and that the
crash hook is live BEFORE the main window is built.
"""

from __future__ import annotations

import faulthandler
import logging
import os
import subprocess
import sys
import textwrap
import threading
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from al_dic_3d.gui import app as app_mod  # noqa: E402  (after importorskip guard)

_REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def qapp():
    return app_mod.create_app([])


@pytest.fixture
def isolated_logging(monkeypatch, tmp_path):
    """Per-test profile folder, a recording faulthandler, and a clean root logger after."""
    root = logging.getLogger()
    handlers_before = list(root.handlers)
    level_before = root.level
    thread_hook_before = threading.excepthook
    monkeypatch.setattr(app_mod, "user_data_dir", lambda: tmp_path / "profile" / "pyALDIC-3D")
    monkeypatch.setattr(app_mod, "LOG_FILE", None)
    monkeypatch.setattr(app_mod, "_FILE_HANDLER", None)
    monkeypatch.setattr(app_mod, "_CRASH_STREAM", None)
    armed: list[tuple[object, bool]] = []

    def record(file=None, all_threads=True):
        armed.append((file, all_threads))

    monkeypatch.setattr(faulthandler, "enable", record)
    yield armed
    for handler in list(root.handlers):
        if handler not in handlers_before:
            root.removeHandler(handler)
            handler.close()
    root.setLevel(level_before)
    logging.captureWarnings(False)
    threading.excepthook = thread_hook_before
    if app_mod._CRASH_STREAM is not None:
        app_mod._CRASH_STREAM.close()


def _log_text(path: Path) -> str:
    for handler in logging.getLogger().handlers:
        handler.flush()
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# configure_logging / faulthandler
# ---------------------------------------------------------------------------


def test_dev_run_keeps_the_console_defaults(isolated_logging, monkeypatch, tmp_path):
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert sys.stderr is not None
    assert app_mod.configure_logging() is None
    assert not (tmp_path / "profile").exists()
    assert isolated_logging == []  # faulthandler untouched


def test_frozen_build_logs_to_a_per_user_file(isolated_logging, monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    path = app_mod.configure_logging()
    expected = tmp_path / "profile" / "pyALDIC-3D" / "logs" / "pyALDIC-3D.log"
    assert path == expected and app_mod.LOG_FILE == expected
    logging.getLogger("al_dic_3d.test_ops").warning("héllo 试样")
    text = _log_text(path)
    assert "héllo 试样" in text and "starting" in text
    # faulthandler armed into the crash log, whose file object stays alive
    ((stream, all_threads),) = isolated_logging
    assert all_threads and stream is app_mod._CRASH_STREAM and not stream.closed
    assert Path(stream.name) == expected.parent / "pyALDIC-3D-crash.log"
    # idempotent: a second call adds no second file handler
    n_files = sum(isinstance(h, logging.FileHandler) for h in logging.getLogger().handlers)
    assert app_mod.configure_logging() == path
    assert sum(isinstance(h, logging.FileHandler) for h in logging.getLogger().handlers) == n_files


def test_missing_stderr_turns_the_file_log_on(isolated_logging, monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)
    monkeypatch.setattr(sys, "stderr", None)
    path = app_mod.configure_logging()
    assert path is not None and path.name == "pyALDIC-3D.log"
    logging.getLogger("al_dic_3d.test_ops").error("no console here")
    assert "no console here" in _log_text(path)


def test_read_only_profile_never_blocks_startup(isolated_logging, monkeypatch, tmp_path):
    blocker = tmp_path / "not-a-folder"
    blocker.write_text("x", encoding="utf-8")
    monkeypatch.setattr(app_mod, "user_data_dir", lambda: blocker / "pyALDIC-3D")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    assert app_mod.configure_logging() is None
    assert app_mod.LOG_FILE is None


def test_a_faulthandler_failure_keeps_the_log(isolated_logging, monkeypatch):
    def refuse(file=None, all_threads=True):  # noqa: ARG001
        raise RuntimeError("fd not usable")

    monkeypatch.setattr(faulthandler, "enable", refuse)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    assert app_mod.configure_logging() is not None
    assert app_mod._CRASH_STREAM is None


def test_a_failed_rotation_keeps_logging(tmp_path):
    """A second running instance holding the log open blocks the Windows rename.

    The stock RotatingFileHandler then drops every later record; this one
    stops rotating for the session and keeps appending.
    """
    path = tmp_path / "pyALDIC-3D.log"
    handler = app_mod._SessionRotatingFileHandler(
        path, maxBytes=200, backupCount=2, encoding="utf-8"
    )

    def blocked(source, dest):  # noqa: ARG001 - what os.rename does on Windows here
        raise PermissionError(32, "The process cannot access the file")

    handler.rotate = blocked
    log = logging.getLogger("al_dic_3d.test_rotation")
    log.addHandler(handler)
    log.propagate = False
    try:
        for i in range(40):
            log.warning("record %03d with some padding to cross maxBytes quickly", i)
    finally:
        log.removeHandler(handler)
        log.propagate = True
        handler.close()
    text = path.read_text(encoding="utf-8")
    assert all(f"record {i:03d}" in text for i in range(40))  # nothing dropped
    assert handler.maxBytes == 0  # rotation off for the rest of this session


def test_rotation_still_rotates_when_it_can(tmp_path):
    path = tmp_path / "pyALDIC-3D.log"
    handler = app_mod._SessionRotatingFileHandler(
        path, maxBytes=200, backupCount=2, encoding="utf-8"
    )
    log = logging.getLogger("al_dic_3d.test_rotation_ok")
    log.addHandler(handler)
    log.propagate = False
    try:
        for i in range(40):
            log.warning("record %03d with some padding to cross maxBytes quickly", i)
    finally:
        log.removeHandler(handler)
        log.propagate = True
        handler.close()
    assert (tmp_path / "pyALDIC-3D.log.1").is_file() and handler.maxBytes == 200


def test_thread_crashes_reach_the_log(isolated_logging, monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    path = app_mod.configure_logging()

    def work():
        raise ValueError("thread went down")

    t = threading.Thread(target=work, name="doomed")
    t.start()
    t.join()
    text = _log_text(path)
    assert "doomed" in text and "ValueError: thread went down" in text


# ---------------------------------------------------------------------------
# CrashHook / crash dialog
# ---------------------------------------------------------------------------


@pytest.fixture
def shown(monkeypatch):
    calls: list[tuple] = []
    monkeypatch.setattr(app_mod, "show_crash_dialog", lambda t, v, tb: calls.append((t, v, tb)))
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)  # restored after the test
    return calls


def _raise_into(hook, exc: BaseException) -> None:
    try:
        raise exc
    except BaseException:  # noqa: BLE001
        hook(*sys.exc_info())


def test_crash_hook_logs_the_console_and_the_dialog(qapp, shown, caplog):
    from al_dic_3d.gui.state import GuiSignals

    signals = GuiSignals()
    records: list[tuple[str, str]] = []
    signals.log.connect(lambda m, lvl: records.append((m, lvl)))
    hook = app_mod.install_excepthook(signals)
    assert sys.excepthook is hook
    with caplog.at_level(logging.CRITICAL):
        _raise_into(hook, ValueError("boom from a slot"))
    assert records == [("CRASH: ValueError: boom from a slot", "error")]
    assert len(shown) == 1 and shown[0][0] is ValueError
    assert "ValueError: boom from a slot" in shown[0][2] and "Traceback" in shown[0][2]
    assert any("boom from a slot" in r.getMessage() for r in caplog.records)


def test_crash_hook_without_signals_still_reports(qapp, shown):
    hook = app_mod.install_excepthook()  # installed before any window exists
    assert hook.signals is None
    _raise_into(hook, RuntimeError("startup failure"))
    assert len(shown) == 1 and shown[0][0] is RuntimeError


def test_crash_during_the_report_is_logged_not_nested(qapp, monkeypatch, caplog):
    calls: list[str] = []
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)
    hook = app_mod.install_excepthook()

    def dialog(t, v, tb):  # noqa: ARG001 - a slot crashes while the dialog is open
        calls.append(str(v))
        _raise_into(hook, KeyError("inner"))

    monkeypatch.setattr(app_mod, "show_crash_dialog", dialog)
    with caplog.at_level(logging.CRITICAL):
        _raise_into(hook, ValueError("outer"))
    assert calls == ["outer"]  # no second dialog
    messages = " ".join(r.getMessage() for r in caplog.records)
    assert "outer" in messages and "inner" in messages  # both tracebacks logged
    _raise_into(hook, ValueError("later"))  # the guard resets afterwards
    assert calls == ["outer", "later"]


def test_keyboard_interrupt_is_not_reported_as_a_crash(qapp, shown):
    hook = app_mod.install_excepthook()
    _raise_into(hook, KeyboardInterrupt())
    assert shown == []


def test_system_exit_is_not_reported_as_a_crash(qapp, shown, caplog):
    hook = app_mod.install_excepthook()
    with caplog.at_level(logging.CRITICAL):
        _raise_into(hook, SystemExit(0))
    assert shown == [] and not caplog.records


def test_crash_dialog_content(qapp):
    from PySide6.QtWidgets import QMessageBox

    log = Path("C:/Users/someone/AppData/Local/pyALDIC-3D/logs/pyALDIC-3D.log")
    tb = "Traceback (most recent call last):\n  ...\nValueError: bad value\n"
    box = app_mod.build_crash_dialog(ValueError, ValueError("bad value"), tb, log_file=log)
    try:
        assert box.icon() == QMessageBox.Icon.Critical
        assert box.windowTitle() == "pyALDIC-3D has hit an error"
        assert "unexpected error" in box.text()
        assert str(log) in box.informativeText()
        assert box.detailedText().startswith("ValueError: bad value")
        assert tb in box.detailedText()
    finally:
        box.deleteLater()


def test_crash_dialog_without_a_log_file(qapp, monkeypatch):
    monkeypatch.setattr(app_mod, "LOG_FILE", None)
    box = app_mod.build_crash_dialog(ValueError, ValueError("x"), "tb")
    try:
        assert box.informativeText() == ""
    finally:
        box.deleteLater()


class _RecordingBox:
    def __init__(self, calls):
        self._calls = calls

    def exec(self):
        self._calls.append("exec")
        return 0


def test_show_crash_dialog_runs_modally_on_a_real_platform(qapp, monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(app_mod, "_HEADLESS_PLATFORMS", frozenset())
    monkeypatch.setattr(app_mod, "build_crash_dialog", lambda *a, **k: _RecordingBox(calls))
    app_mod.show_crash_dialog(ValueError, ValueError("x"), "tb")
    assert calls == ["exec"]


def test_show_crash_dialog_is_skipped_headless(qapp, monkeypatch):
    assert qapp.platformName() in app_mod._HEADLESS_PLATFORMS  # nobody could click OK
    monkeypatch.setattr(app_mod, "build_crash_dialog", lambda *a, **k: pytest.fail("built"))
    app_mod.show_crash_dialog(ValueError, ValueError("x"), "tb")


def test_show_crash_dialog_is_skipped_off_the_gui_thread(qapp, monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(app_mod, "_HEADLESS_PLATFORMS", frozenset())
    monkeypatch.setattr(app_mod, "build_crash_dialog", lambda *a, **k: _RecordingBox(calls))
    t = threading.Thread(target=app_mod.show_crash_dialog, args=(ValueError, ValueError(), "tb"))
    t.start()
    t.join()
    assert calls == []


def test_show_crash_dialog_is_skipped_without_an_application(monkeypatch):
    monkeypatch.setattr(app_mod, "_gui_application", lambda: None)
    monkeypatch.setattr(app_mod, "build_crash_dialog", lambda *a, **k: pytest.fail("built"))
    app_mod.show_crash_dialog(ValueError, ValueError("x"), "tb")


# ---------------------------------------------------------------------------
# main(): hook order, startup failure
# ---------------------------------------------------------------------------


def _fake_main_window(monkeypatch, seen: dict, *, fail: Exception | None = None):
    from al_dic_3d.gui import main_window as mw
    from al_dic_3d.gui.state import GuiSignals

    class FakeWindow:
        def __init__(self):
            seen["hook_at_construction"] = sys.excepthook
            if fail is not None:
                raise fail
            self.signals = GuiSignals()

        def show(self):
            seen["shown"] = True

    monkeypatch.setattr(mw, "MainWindow3D", FakeWindow)
    monkeypatch.setattr(app_mod, "configure_logging", lambda: None)
    monkeypatch.setattr(app_mod, "start_kernel_warmup", lambda w: seen.setdefault("warm", w))
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)


def test_main_installs_the_crash_hook_before_the_window(qapp, monkeypatch, shown):
    from PySide6.QtCore import QTimer

    seen: dict = {}
    _fake_main_window(monkeypatch, seen)
    QTimer.singleShot(0, lambda: qapp.exit(0))  # leave the event loop at once
    assert app_mod.main([]) == 0
    hook = seen["hook_at_construction"]
    assert isinstance(hook, app_mod.CrashHook)
    assert seen["shown"] and hook.signals is seen["warm"].signals  # console attached
    assert shown == []


def test_main_reports_a_startup_failure(qapp, monkeypatch, shown, caplog):
    seen: dict = {}
    _fake_main_window(monkeypatch, seen, fail=RuntimeError("no OpenGL 3.2 context"))
    with caplog.at_level(logging.CRITICAL):
        assert app_mod.main([]) == 1
    assert isinstance(seen["hook_at_construction"], app_mod.CrashHook)
    assert len(shown) == 1 and shown[0][0] is RuntimeError
    assert any("no OpenGL 3.2 context" in r.getMessage() for r in caplog.records)
    assert "warm" not in seen


# ---------------------------------------------------------------------------
# RunWorker: the traceback goes through logging
# ---------------------------------------------------------------------------


class _Boom:
    def run(self, progress=None, stop=None):  # noqa: ARG002
        raise ValueError("boom: bad calibration matrix")


def test_run_worker_failure_is_logged_with_its_traceback(qapp, caplog):
    from al_dic_3d.gui.run_worker import RunWorker

    worker = RunWorker(_Boom())
    got: list[str] = []
    worker.failed.connect(got.append)
    with caplog.at_level(logging.ERROR, logger="al_dic_3d.gui.run_worker"):
        worker.run()  # synchronous: the error path needs no thread
    assert got == ["ValueError: boom: bad calibration matrix"]
    rec = next(r for r in caplog.records if r.name == "al_dic_3d.gui.run_worker")
    assert rec.levelno == logging.ERROR and rec.exc_info[0] is ValueError


def test_run_worker_survives_a_missing_stderr(qapp, monkeypatch, caplog):
    from al_dic_3d.gui.run_worker import RunWorker

    monkeypatch.setattr(sys, "stderr", None)  # the windowed frozen build
    worker = RunWorker(_Boom())
    got: list[str] = []
    worker.failed.connect(got.append)
    with caplog.at_level(logging.ERROR):
        worker.run()
    assert got == ["ValueError: boom: bad calibration matrix"]
    assert any(r.exc_info for r in caplog.records)


def test_run_worker_traceback_still_reaches_a_console(tmp_path):
    """Without any logging setup (a terminal run) the traceback prints to stderr."""
    script = textwrap.dedent(
        """
        from al_dic_3d.gui.run_worker import RunWorker

        class Boom:
            def run(self, progress=None, stop=None):
                raise ValueError("boom: bad calibration matrix")

        RunWorker(Boom()).run()
        """
    )
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=_REPO,
        env=env,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "Traceback" in proc.stderr and "ValueError: boom: bad calibration matrix" in proc.stderr
