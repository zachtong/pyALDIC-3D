"""Run page — execute the pipeline in a worker thread with progress + console.

Reuses the 2D ``ConsoleLog`` widget (see docs/DEPENDS_ON_2D.md). The heavy run
happens off the UI thread (the 2D worker pattern) so the window stays responsive.
"""

from __future__ import annotations

from al_dic.gui.widgets.console_log import ConsoleLog
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QProgressBar, QPushButton

from al_dic_3d.gui.controller import WorkflowController
from al_dic_3d.gui.pages.base import WorkflowPage


class RunWorker(QThread):
    """Runs ``controller.run`` off the UI thread, relaying progress."""

    progress = Signal(float, str)
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(self, controller: WorkflowController) -> None:
        super().__init__()
        self._controller = controller

    def run(self) -> None:  # QThread entry point (worker thread)
        try:
            self._controller.run(progress=lambda frac, msg: self.progress.emit(frac, msg))
            self.finished_ok.emit()
        except Exception as exc:  # noqa: BLE001 - report any failure to the UI
            self.failed.emit(str(exc))


class RunPage(WorkflowPage):
    def build(self) -> None:
        self._set(
            self.tr("Run"),
            self.tr("Execute the pipeline; results open when it finishes."),
        )
        self._run_btn = QPushButton(self.tr("Run pipeline"))
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._console = ConsoleLog()
        self._add(self._run_btn)
        self._add(self._progress)
        self._add(self._console)

        self._worker: RunWorker | None = None
        self._run_btn.clicked.connect(self._on_run)
        self.refresh()

    def _on_run(self) -> None:
        if not self.controller.can_run():
            self._console.append_log(
                self.tr("Not ready: {0}").format("; ".join(self.draft.issues())), "warning"
            )
            return
        self._run_btn.setEnabled(False)
        self._progress.setValue(0)
        self._console.append_log(self.tr("Running…"))
        self._worker = RunWorker(self.controller)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ok.connect(self._on_done)
        self._worker.failed.connect(self._on_fail)
        self._worker.start()

    def _on_progress(self, frac: float, msg: str) -> None:
        self._progress.setValue(int(frac * 100))
        self._console.append_log(msg)

    def _on_done(self) -> None:
        self._progress.setValue(100)
        self._run_btn.setEnabled(True)
        self._console.append_log(self.tr("Done."))
        self.changed.emit()  # results available -> refresh navigation

    def _on_fail(self, msg: str) -> None:
        self._run_btn.setEnabled(True)
        self._console.append_log(self.tr("Failed: {0}").format(msg), "error")

    def refresh(self) -> None:
        self._run_btn.setEnabled(self.controller.can_run())
