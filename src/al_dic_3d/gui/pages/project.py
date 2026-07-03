"""Project page — new / open / save a ``.aldic3d`` project."""

from __future__ import annotations

from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QPushButton, QWidget

from al_dic_3d.gui.pages.base import WorkflowPage


class ProjectPage(WorkflowPage):
    def build(self) -> None:
        self._set(
            self.tr("New / Open Project"),
            self.tr("Create a new .aldic3d project or open an existing one to resume it."),
        )
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        self._new_btn = QPushButton(self.tr("New Project"))
        self._open_btn = QPushButton(self.tr("Open Project…"))
        self._save_btn = QPushButton(self.tr("Save Project As…"))
        for btn in (self._new_btn, self._open_btn, self._save_btn):
            layout.addWidget(btn)
        layout.addStretch(1)
        self._add(row)

        self._status = QLabel(self)
        self._add(self._status)

        self._new_btn.clicked.connect(self._on_new)
        self._open_btn.clicked.connect(self._on_open)
        self._save_btn.clicked.connect(self._on_save)
        self.refresh()

    def _on_new(self) -> None:
        self.controller.new_project()
        self.changed.emit()
        self.refresh()

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Open Project"), "", self.tr("pyALDIC-3D project (*.aldic3d)")
        )
        if not path:
            return
        try:
            self.controller.open_project(path)
        except Exception as exc:  # noqa: BLE001 - surface load errors to the user
            self._status.setText(self.tr("Open failed: {0}").format(exc))
            return
        self.changed.emit()
        self.refresh()

    def _on_save(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save Project"),
            "project.aldic3d",
            self.tr("pyALDIC-3D project (*.aldic3d)"),
        )
        if not path:
            return
        self.controller.save_project(path)
        self.refresh()

    def refresh(self) -> None:
        state = self.controller.state
        if state.project_path is not None:
            self._status.setText(self.tr("Project: {0}").format(state.project_path))
        else:
            self._status.setText(self.tr("Unsaved project"))
