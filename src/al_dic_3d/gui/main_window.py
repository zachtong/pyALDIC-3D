"""``MainWindow3D`` — the application shell (Qt view over the workflow controller).

Same UX grammar as the 2D app (left workflow steps, central multi-page area,
bottom status) so 2D users transfer with zero learning cost, but the shell,
state, and controllers are 3D's own. This is the STRUCTURAL shell; the rich
per-page widgets are filled in during visual iteration.

All user-facing strings are literal ``self.tr(...)`` (i18n contract).
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFileDialog,
    QListWidget,
    QMainWindow,
    QSplitter,
    QStackedWidget,
    QWidget,
)

from al_dic_3d.gui.controller import WorkflowController
from al_dic_3d.gui.pages import PAGE_CLASSES


class MainWindow3D(QMainWindow):
    """The pyALDIC-3D main window: workflow steps + paged content."""

    def __init__(
        self, controller: WorkflowController | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.controller = controller or WorkflowController()
        self.setWindowTitle(self.tr("pyALDIC-3D"))

        self._steps = QListWidget()
        for name in self._step_names():
            self._steps.addItem(name)

        self._stack = QStackedWidget()
        self._pages = []
        for cls in PAGE_CLASSES:
            page = cls(self.controller)
            page.changed.connect(self._on_page_changed)
            self._pages.append(page)
            self._stack.addWidget(page)

        splitter = QSplitter()
        splitter.addWidget(self._steps)
        splitter.addWidget(self._stack)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([200, 800])
        self.setCentralWidget(splitter)

        self._steps.currentRowChanged.connect(self._on_step_changed)
        self._build_menu()
        self._sync_from_state()
        self.statusBar().showMessage(self.tr("Ready"))

    def _step_names(self) -> list[str]:
        # Short sidebar labels (literals so lupdate extracts them).
        return [
            self.tr("Project"),
            self.tr("Import"),
            self.tr("Calibration"),
            self.tr("ROI"),
            self.tr("Correspondence"),
            self.tr("Run"),
            self.tr("Results"),
            self.tr("Export"),
        ]

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu(self.tr("&File"))
        file_menu.addAction(self.tr("New Project")).triggered.connect(self._new_project)
        file_menu.addAction(self.tr("Open Project…")).triggered.connect(self._open_project)
        file_menu.addAction(self.tr("Save Project…")).triggered.connect(self._save_project)
        file_menu.addSeparator()
        file_menu.addAction(self.tr("Quit")).triggered.connect(self.close)

    # --- state sync ----------------------------------------------------------

    def _sync_from_state(self) -> None:
        step = self.controller.state.workflow_step
        self._steps.setCurrentRow(step)
        self._stack.setCurrentIndex(step)

    def _on_step_changed(self, row: int) -> None:
        if row < 0:
            return
        self.controller.goto(row)
        self._stack.setCurrentIndex(row)
        self._pages[row].refresh()

    def _on_page_changed(self) -> None:
        """A page mutated the state — re-sync the sidebar and refresh every page."""
        self._sync_from_state()
        for page in self._pages:
            page.refresh()

    # --- menu actions --------------------------------------------------------

    def _new_project(self) -> None:
        self.controller.new_project()
        self._on_page_changed()
        self.statusBar().showMessage(self.tr("New project created"))

    def _open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Open Project"), "", self.tr("pyALDIC-3D project (*.aldic3d)")
        )
        if not path:
            return
        try:
            self.controller.open_project(path)
        except Exception as exc:  # noqa: BLE001 - surface load errors to the user
            self.statusBar().showMessage(self.tr("Could not open project: {0}").format(exc))
            return
        self._on_page_changed()
        self.statusBar().showMessage(self.tr("Project opened"))

    def _save_project(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Save Project"), "", self.tr("pyALDIC-3D project (*.aldic3d)")
        )
        if not path:
            return
        self.controller.save_project(path)
        self.statusBar().showMessage(self.tr("Project saved"))
