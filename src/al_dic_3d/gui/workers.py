"""Shared background-work machinery for the GUI (performance batch P2).

Three tools with one rule — heavy work leaves the GUI thread, results come
back through queued signal delivery:

``JobWorker``
    The cancellable ``QThread`` generalized from the export tabs (still
    importable there as ``ExportWorker``): one Qt-free job, cooperative
    ``threading.Event`` cancel, ``(done, total, label)`` progress.

``PoolTask`` / ``TaskSignals``
    A plain function wrapped for ``QThreadPool``. Connect ``signals.done`` /
    ``signals.failed`` to **bound methods of GUI-thread QObjects** so the
    auto-connection queues delivery back to the GUI thread (connecting bare
    lambdas would run them on the worker thread).

``run_with_progress``
    Runs one job on a ``JobWorker`` behind an application-modal indeterminate
    progress dialog while KEEPING the caller synchronous via a local event
    loop. This is the simplest design that preserves the G1/G2 guard contract
    (``MainWindow3D._save_project() -> bool`` must stay a plain call the close
    guard can branch on) while the heavy payload runs off the GUI thread.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QEventLoop, QObject, QRunnable, Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import QProgressDialog, QWidget

# Delay before the modal progress dialog becomes visible: fast saves/loads
# finish silently instead of flashing a dialog for a few milliseconds.
PROGRESS_DIALOG_DELAY_MS = 300


class JobWorker(QThread):
    """Runs one Qt-free job off the UI thread; cancellable (2D export idiom)."""

    progress = Signal(int, int, str)
    finished_ok = Signal(object)  # the job's return value (list of paths, ...)
    failed = Signal(str)

    def __init__(
        self,
        job: Callable[[Callable[[int, int, str], None], threading.Event], object],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._job = job
        self._stop_event = threading.Event()

    def request_stop(self) -> None:
        self._stop_event.set()

    @property
    def was_cancelled(self) -> bool:
        return self._stop_event.is_set()

    def run(self) -> None:  # QThread entry point (worker thread)
        try:
            out = self._job(self._emit_progress, self._stop_event)
            self.finished_ok.emit(out)
        except Exception as exc:  # noqa: BLE001 - report any failure to the UI
            self.failed.emit(f"{type(exc).__name__}: {exc}")

    def _emit_progress(self, done: int, total: int, label: str = "") -> None:
        self.progress.emit(int(done), int(total), str(label))


class TaskSignals(QObject):
    """Cross-thread result channel for one :class:`PoolTask`."""

    done = Signal(object, object)  # (tag, result)
    failed = Signal(object, str)  # (tag, "ErrorType: message")


class PoolTask(QRunnable):
    """One function call on a ``QThreadPool``, results via :class:`TaskSignals`.

    ``tag`` is echoed back with the result so receivers can drop stale
    deliveries (generation counters, path keys). Create the task on the GUI
    thread and connect its signals to bound methods of GUI-thread QObjects
    BEFORE ``pool.start`` — delivery is then queued to the GUI thread.
    """

    def __init__(self, fn: Callable[..., Any], *args: Any, tag: Any = None) -> None:
        super().__init__()
        self.signals = TaskSignals()
        self._fn = fn
        self._args = args
        self._tag = tag

    def run(self) -> None:  # QRunnable entry point (worker thread)
        try:
            out = self._fn(*self._args)
        except Exception as exc:  # noqa: BLE001 - surface any failure to the GUI
            self._emit(self.signals.failed, f"{type(exc).__name__}: {exc}")
            return
        self._emit(self.signals.done, out)

    def _emit(self, sig: Signal, payload: Any) -> None:
        try:
            sig.emit(self._tag, payload)
        except RuntimeError:  # app teardown deleted the signal proxy
            pass


def run_with_progress(
    parent: QWidget | None,
    label: str,
    job: Callable[[], Any],
    *,
    delay_ms: int = PROGRESS_DIALOG_DELAY_MS,
) -> tuple[bool, Any]:
    """Run ``job()`` on a worker behind a modal progress dialog; block until done.

    Returns ``(True, result)`` or ``(False, error_message)`` synchronously.
    The local event loop keeps the GUI repainting; the application-modal
    dialog (no Cancel — a half-written ``.aldic3d`` must never exist) blocks
    every window, including the parentless strain window, from mutating state
    mid-save/load. The dialog only appears when the job outlives ``delay_ms``.
    """
    dialog = QProgressDialog(label, "", 0, 0, parent)  # range (0, 0) = indeterminate
    dialog.setWindowTitle(label)
    dialog.setCancelButton(None)
    dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
    dialog.setMinimumDuration(2**31 - 1)  # never auto-show; the timer below decides

    outcome: dict[str, Any] = {}
    loop = QEventLoop(parent)
    worker = JobWorker(lambda _progress, _stop: job(), parent)
    worker.finished_ok.connect(lambda out: outcome.setdefault("ok", out))
    worker.failed.connect(lambda msg: outcome.setdefault("err", msg))
    worker.finished.connect(loop.quit)

    timer = QTimer(dialog)
    timer.setSingleShot(True)
    timer.setInterval(max(0, int(delay_ms)))
    timer.timeout.connect(dialog.show)
    timer.start()

    worker.start()
    loop.exec()
    worker.wait()  # fully joined — never leak a finishing QThread past this call
    timer.stop()
    dialog.reset()
    dialog.deleteLater()
    if "err" in outcome:
        return False, outcome["err"]
    return True, outcome.get("ok")
