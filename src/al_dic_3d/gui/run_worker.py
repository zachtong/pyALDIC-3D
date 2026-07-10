"""``RunWorker`` — the pipeline QThread behind the right sidebar's Run button.

Extracted from ``panels/right_sidebar.py`` (file-size discipline); re-exported
there for the existing import sites.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QThread, Signal

if TYPE_CHECKING:
    from al_dic_3d.gui.controller import WorkflowController


class RunWorker(QThread):
    """Runs the pipeline off the UI thread, relaying progress; cancellable."""

    progress = Signal(float, str)
    log = Signal(str, str)  # (message, level) — engine warnings forwarded live
    finished_ok = Signal()
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, controller: WorkflowController) -> None:
        super().__init__()
        self._controller = controller
        self._stop_requested = False

    def request_stop(self) -> None:
        """Ask the pipeline to stop at the next cooperative checkpoint."""
        self._stop_requested = True

    def run(self) -> None:  # QThread entry point (worker thread)
        import traceback
        import warnings

        def _forward(message, category, filename, lineno, file=None, line=None):  # noqa: ARG001
            # Engine run-time warnings (e.g. "Auto-scaled FFT search region:
            # 48 -> 26 (image 200x200)" from run_aldic's search clamp) would
            # otherwise die on stderr; surface them in the GUI console log.
            self.log.emit(str(message), "warning")

        try:
            # catch_warnings snapshots + restores the global filter/hook on
            # exit; only one pipeline run exists at a time, so hijacking
            # showwarning for the duration of the run is safe.
            with warnings.catch_warnings():
                warnings.simplefilter("always")
                warnings.showwarning = _forward
                self._controller.run(
                    progress=lambda f, m: self.progress.emit(f, m),
                    stop=lambda: self._stop_requested,
                )
            self.finished_ok.emit()
        except Exception as exc:  # noqa: BLE001 - report any failure to the UI
            if self._stop_requested:
                self.cancelled.emit()
            else:
                # F3.1: the user gets the exception TYPE + message in the log;
                # the full traceback goes to stderr for bug reports.
                traceback.print_exc()
                self.failed.emit(f"{type(exc).__name__}: {exc}")
