"""Export page — write the results to ``.npz`` + ``.mat``.

Mesh (PLY/VTU), screenshots, and animations are the Phase-5 export suite.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QLabel, QPushButton

from al_dic_3d.gui.pages.base import WorkflowPage


class ExportPage(WorkflowPage):
    def build(self) -> None:
        self._set(
            self.tr("Export"),
            self.tr(
                "Write the results to .npz + .mat (mesh / screenshot export lands in Phase 5)."
            ),
        )
        self._export_btn = QPushButton(self.tr("Export results (.npz + .mat)…"))
        self._status = QLabel(self)
        self._add(self._export_btn)
        self._add(self._status)
        self._export_btn.clicked.connect(self._on_export)
        self.refresh()

    def _on_export(self) -> None:
        state = self.controller.state
        if state.result is None or state.config is None:
            self._status.setText(self.tr("No results to export."))
            return
        directory = QFileDialog.getExistingDirectory(self, self.tr("Choose output folder"))
        if not directory:
            return
        from al_dic_3d.runner import write_results

        cfg = replace(state.config, output_dir=Path(directory))
        paths = write_results(state.result, cfg)
        self._status.setText(
            self.tr("Wrote {0} and {1}").format(paths["npz"].name, paths["mat"].name)
        )

    def refresh(self) -> None:
        self._export_btn.setEnabled(self.controller.state.has_results)
