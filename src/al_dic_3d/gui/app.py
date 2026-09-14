"""Qt application entry point for the pyALDIC-3D GUI.

``create_app`` builds (or reuses) the ``QApplication`` and installs the
translators; ``main`` shows the :class:`MainWindow3D`. Kept split so a headless
test can build the app (offscreen) without entering the event loop.

Operations layer (H2, a port of the 2D 0.8.0 one): the windowed frozen build
has no console -- ``sys.stderr`` is ``None`` -- so every printed traceback is
lost there. ``main`` therefore (1) sends logging to a per-user file and arms
:mod:`faulthandler` for native (VTK / driver) crashes, (2) installs the crash
hook BEFORE the main window is built, so a failure while building it is
reported instead of vanishing, and (3) once the window is up, compiles the JIT
kernels in the background (:mod:`al_dic_3d.gui.kernel_warmup`).
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path

logger = logging.getLogger(__name__)

APP_DIR_NAME = "pyALDIC-3D"
LOG_FILE_NAME = "pyALDIC-3D.log"
CRASH_LOG_NAME = "pyALDIC-3D-crash.log"
_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_LOG_MAX_BYTES = 2_000_000  # per file; the rotation keeps _LOG_BACKUPS older ones
_LOG_BACKUPS = 2
_CRASH_LOG_MAX_BYTES = 1_000_000  # the crash log starts over once it grows past this
# Qt platforms with no user to dismiss a modal dialog (tests, CI, the self-test).
_HEADLESS_PLATFORMS = frozenset({"offscreen", "minimal"})

# The log file once :func:`configure_logging` has opened it, else ``None``.
LOG_FILE: Path | None = None
_FILE_HANDLER: logging.Handler | None = None
# faulthandler writes to this file's descriptor from its fault handler, so the
# file object must stay open -- and referenced -- for the life of the process.
_CRASH_STREAM = None


def create_app(argv: list[str] | None = None):
    """Return a configured ``QApplication`` (reusing an existing instance)."""
    from PySide6.QtWidgets import QApplication

    from al_dic_3d.i18n import install_translators

    app = QApplication.instance() or QApplication(argv if argv is not None else [])
    app.setApplicationName("pyALDIC-3D")
    app.setOrganizationName("pyALDIC")
    _apply_theme(app)

    from PySide6.QtCore import QSettings

    saved = QSettings("pyALDIC", "pyALDIC-3D").value("language", None)
    install_translators(app, locale=str(saved) if saved else None)
    return app


def _apply_theme(app) -> None:
    """Apply the shared pyALDIC dark-navy theme (reused from the 2D repo)."""
    try:
        from al_dic.gui.theme import build_stylesheet
    except ImportError:
        return  # theme is cosmetic; run un-themed if the 2D theme is unavailable
    app.setStyle("Fusion")  # QSS renders correctly on the Fusion style
    app.setStyleSheet(build_stylesheet())


# --- logging + native crash log ------------------------------------------------


def user_data_dir() -> Path:
    """Per-user writable folder for the log and crash files.

    ``%LOCALAPPDATA%\\pyALDIC-3D`` on Windows, ``~/pyALDIC-3D`` elsewhere --
    deliberately not next to the executable, which is routinely installed
    where the user cannot write (Program Files, a network share).
    """
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return Path(base) / APP_DIR_NAME


class _SessionRotatingFileHandler(RotatingFileHandler):
    """``RotatingFileHandler`` that survives a rotation Windows refuses.

    Every running instance appends to the same per-user log. On Windows the
    rename in ``doRollover`` fails while another instance holds the file open,
    and the stock handler then drops every later record of this process (each
    emit retries the rollover and fails again) -- the crash reports included.
    Here a failed rotation turns rotation off for the rest of the session: the
    file grows past ``maxBytes`` until a later launch rotates it.
    """

    def doRollover(self) -> None:  # noqa: N802 (logging API name)
        try:
            super().doRollover()
        except OSError:
            self.maxBytes = 0
            if self.stream is None:
                self.stream = self._open()


def configure_logging(*, force: bool = False) -> Path | None:
    """Send logging to a per-user file when there is no console; return its path.

    Active when the app is frozen (``sys.frozen``) or ``sys.stderr`` is ``None``
    (``pythonw``, the windowed build), or when ``force`` is set. A development
    run from a terminal keeps Python's defaults, so tracebacks still print
    there. When active it also routes ``warnings`` and uncaught thread
    exceptions into the log and arms :mod:`faulthandler`. Idempotent.

    Returns ``None`` when inactive or when the log cannot be opened: a
    read-only profile is never a reason to refuse to start.
    """
    global LOG_FILE, _FILE_HANDLER
    if _FILE_HANDLER is not None:
        return LOG_FILE
    if not force and not (getattr(sys, "frozen", False) or sys.stderr is None):
        return None
    try:
        folder = user_data_dir() / "logs"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / LOG_FILE_NAME
        handler = _SessionRotatingFileHandler(
            path, maxBytes=_LOG_MAX_BYTES, backupCount=_LOG_BACKUPS, encoding="utf-8"
        )
    except OSError:
        return None
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root = logging.getLogger()
    root.addHandler(handler)
    if sys.stderr is not None:
        # A frozen app started from a console (``pyaldic3d-cli.exe gui``):
        # keep warnings and tracebacks visible there as well.
        console = logging.StreamHandler()
        console.setLevel(logging.WARNING)
        console.setFormatter(logging.Formatter(_LOG_FORMAT))
        root.addHandler(console)
    if root.getEffectiveLevel() > logging.INFO:
        root.setLevel(logging.INFO)
    logging.captureWarnings(True)  # warnings.warn() would print to the missing stderr
    threading.excepthook = _log_thread_exception
    _FILE_HANDLER, LOG_FILE = handler, path
    crash_log = _enable_faulthandler(folder)

    from al_dic_3d import __version__

    logger.info(
        "pyALDIC-3D %s starting (Python %s, %s, frozen=%s); crash log: %s",
        __version__,
        sys.version.split()[0],
        sys.platform,
        bool(getattr(sys, "frozen", False)),
        crash_log if crash_log is not None else "unavailable",
    )
    return path


def _enable_faulthandler(folder: Path) -> Path | None:
    """Arm :mod:`faulthandler` into ``folder/pyALDIC-3D-crash.log``.

    A native crash (VTK, an OpenGL driver, Qt) kills the process before any
    Python handler runs; faulthandler still writes every thread's Python stack.
    Each session appends a header line so a dump can be matched to its run.
    """
    global _CRASH_STREAM
    import faulthandler

    from al_dic_3d import __version__

    path = folder / CRASH_LOG_NAME
    stream = None
    try:
        oversized = path.exists() and path.stat().st_size > _CRASH_LOG_MAX_BYTES
        stream = open(path, "w" if oversized else "a", encoding="utf-8")  # noqa: SIM115 - lives for the process
        stream.write(
            f"--- pyALDIC-3D {__version__} session {time.strftime('%Y-%m-%d %H:%M:%S')} "
            f"(pid {os.getpid()}) ---\n"
        )
        stream.flush()
        faulthandler.enable(file=stream, all_threads=True)
    except (OSError, RuntimeError, ValueError):
        if stream is not None:
            stream.close()
        return None
    _CRASH_STREAM = stream
    return path


def _log_thread_exception(args) -> None:
    """``threading.excepthook`` for a console-less build: log instead of printing."""
    if args.exc_type is SystemExit:
        return
    name = getattr(args.thread, "name", "?")
    logger.critical(
        "Unhandled exception in thread %s",
        name,
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
    )


# --- crash reporting -------------------------------------------------------------


class CrashHook:
    """``sys.excepthook`` that reports instead of dying silently (G1.7, H2).

    An unhandled exception in a Qt slot would otherwise kill or zombify the GUI
    with nothing on screen. For every such exception the hook

    * logs the full traceback (the per-user log file in a frozen build, the
      terminal in a development run),
    * posts a one-line ``CRASH:`` message to the GUI console once the main
      window's ``signals`` are attached (``hook.signals = window.signals``), and
    * shows a modal error dialog: the traceback under *Show Details* plus the
      log-file path.

    An exception raised while a report is in progress (the console sink itself
    failing, or a slot failing under the open dialog) is logged only. The hook
    never raises.
    """

    def __init__(self, signals=None) -> None:
        self.signals = signals
        self._reporting = False

    def __call__(self, exc_type, exc_value, exc_tb) -> None:
        if issubclass(exc_type, SystemExit):  # a deliberate exit is no crash
            return
        if issubclass(exc_type, KeyboardInterrupt):  # nor is Ctrl+C in a terminal
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        try:
            logger.critical("Unhandled exception:\n%s", tb_str)
        except Exception:  # noqa: BLE001, S110 - the hook must never raise
            pass
        if self._reporting:
            return  # re-entrant: the reporting path itself (or a slot under the dialog) crashed
        self._reporting = True
        try:
            signals = self.signals
            if signals is not None:
                try:
                    signals.log.emit(f"CRASH: {exc_type.__name__}: {exc_value}", "error")
                except Exception:  # noqa: BLE001, S110 - the console may be gone
                    pass
            try:
                show_crash_dialog(exc_type, exc_value, tb_str)
            except Exception:  # noqa: BLE001 - never let the report itself escape
                logger.exception("Could not show the crash dialog")
        finally:
            self._reporting = False


def install_excepthook(signals=None) -> CrashHook:
    """Install and return a :class:`CrashHook` as ``sys.excepthook``.

    ``main`` installs it before any window exists and attaches the window's
    ``signals`` afterwards; passing ``signals`` here attaches them at once.
    """
    hook = CrashHook(signals)
    sys.excepthook = hook
    return hook


def _gui_application():
    """The running ``QApplication``, or ``None`` (none yet, or a core-only app)."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    return app if isinstance(app, QApplication) else None


def build_crash_dialog(exc_type, exc_value, tb_str: str, log_file: Path | None = None):
    """The crash ``QMessageBox`` (not shown): message, log path, traceback details."""
    from PySide6.QtCore import QCoreApplication
    from PySide6.QtWidgets import QMessageBox

    box = QMessageBox(
        QMessageBox.Icon.Critical,
        QCoreApplication.translate("Application", "pyALDIC-3D has hit an error"),
        QCoreApplication.translate(
            "Application",
            "An unexpected error occurred. The application may not behave "
            "correctly from here on, so saving your project and restarting "
            "is recommended.",
        ),
    )
    path = LOG_FILE if log_file is None else log_file
    if path is not None:
        box.setInformativeText(
            QCoreApplication.translate("Application", "Details were written to {0}").format(
                str(path)
            )
        )
    box.setDetailedText(f"{exc_type.__name__}: {exc_value}\n\n{tb_str}")
    return box


def show_crash_dialog(exc_type, exc_value, tb_str: str) -> None:
    """Show the crash report modally -- a windowed build has no other channel.

    Skipped (the log still has it) without a ``QApplication``, off the GUI
    thread (widgets must not be created there), and on a headless platform
    where nobody could dismiss a modal dialog.
    """
    app = _gui_application()
    if app is None or threading.current_thread() is not threading.main_thread():
        return
    if app.platformName() in _HEADLESS_PLATFORMS:
        return
    build_crash_dialog(exc_type, exc_value, tb_str).exec()


# --- background kernel warm-up ------------------------------------------------------


def start_kernel_warmup(window, parent=None):
    """Compile the JIT kernels in the background, shortly after first paint.

    See :mod:`al_dic_3d.gui.kernel_warmup` for why: without it the first *Run
    3D Analysis* of an installation stalls for tens of seconds with nothing to
    explain it. The GUI console says so only when it is actually slow: the
    notice appears once the warm-up has run for ``REPORT_THRESHOLD_S`` and the
    "ready" line follows it; a warm cache stays silent. Returns the
    :class:`~al_dic_3d.gui.kernel_warmup.KernelWarmup` (parented to ``parent``,
    default the window, so it lives exactly as long).
    """
    from PySide6.QtCore import QCoreApplication, QTimer

    from al_dic_3d.gui import kernel_warmup as kw

    warmup = kw.KernelWarmup(window if parent is None else parent)
    log = window.signals.log
    announced = [False]

    def _announce_if_running() -> None:
        if warmup.is_running():
            announced[0] = True
            log.emit(
                QCoreApplication.translate(
                    "Application", "Preparing compute kernels in the background…"
                ),
                "info",
            )

    def _start() -> None:
        warmup.start()
        QTimer.singleShot(int(kw.REPORT_THRESHOLD_S * 1000), warmup, _announce_if_running)

    def _report(seconds: float) -> None:
        if announced[0]:
            log.emit(
                QCoreApplication.translate("Application", "Compute kernels ready ({0} s).").format(
                    f"{seconds:.0f}"
                ),
                "info",
            )

    warmup.compiled.connect(_report)  # queued: emitted from the warm-up thread
    # The timers carry ``warmup`` as their context: closing the window first
    # deletes it and cancels them.
    QTimer.singleShot(kw.START_DELAY_MS, warmup, _start)
    return warmup


# --- entry point --------------------------------------------------------------------


def session_path_from_argv(argv: list[str] | None) -> str | None:
    """The first existing ``.aldic3d`` path in ``argv`` (Q6), or None.

    2D port (``al_dic.gui.app._session_path_from_argv``): the CLI's ``gui
    SESSION`` positional and the Windows double-click association both land
    here, so the app boots straight into the given project.
    """
    for arg in argv or []:
        if arg and arg.lower().endswith(".aldic3d") and Path(arg).exists():
            return arg
    return None


def main(argv: list[str] | None = None) -> int:
    """Launch the GUI (blocks in the Qt event loop). Returns the exit code."""
    configure_logging()  # H2: before anything can fail
    hook = install_excepthook()  # H2: live BEFORE the main window is built
    try:
        app = create_app(argv)
        from al_dic_3d.gui.main_window import MainWindow3D

        window = MainWindow3D()  # sizes itself to the available screen (G1.4)
    except Exception:  # noqa: BLE001 - a windowed build has no other way to say why
        hook(*sys.exc_info())
        return 1
    hook.signals = window.signals  # G1.7: crashes also land in the GUI console
    window.show()
    start_kernel_warmup(window)
    session = session_path_from_argv(argv)
    if session is not None:
        # Defer until the event loop runs so the load-progress dialog and
        # worker behave normally (2D pattern).
        from PySide6.QtCore import QTimer

        QTimer.singleShot(0, lambda: window._open_project_path(session))
    return int(app.exec())
