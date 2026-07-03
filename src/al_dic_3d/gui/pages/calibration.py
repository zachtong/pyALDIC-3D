"""Calibration page — import + immediate sanity preview (errors die here)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from al_dic_3d.calibration import IMPORTERS, load_calibration
from al_dic_3d.gui.pages.base import WorkflowPage


class CalibrationPage(WorkflowPage):
    def build(self) -> None:
        self._set(
            self.tr("Calibration"),
            self.tr("Import calibration and check the summary + baseline before continuing."),
        )
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(self.tr("Format:")))
        self._format = QComboBox()
        self._format.addItems(sorted(IMPORTERS))  # format identifiers, not user prose
        layout.addWidget(self._format)
        self._choose = QPushButton(self.tr("Choose calibration file…"))
        layout.addWidget(self._choose)
        layout.addStretch(1)
        self._add(row)

        self._file = QLabel(self)
        self._summary = QLabel(self)
        self._add(self._file)
        self._add(self._summary)

        self._format.currentTextChanged.connect(self._on_format)
        self._choose.clicked.connect(self._on_choose)
        self.refresh()

    def _on_format(self, fmt: str) -> None:
        self.draft.calibration_format = fmt
        self.controller.state.mark_dirty()
        self.changed.emit()

    def _on_choose(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Choose calibration file"),
            "",
            self.tr("Calibration files (*.xml *.yaml *.yml *.mat *.csv *.txt *.caldat)"),
        )
        if not path:
            return
        self.draft.calibration_file = Path(path)
        self._load_preview()
        self.controller.state.mark_dirty()
        self.changed.emit()
        self.refresh()

    def _load_preview(self) -> None:
        try:
            rig = load_calibration(self.draft.calibration_file, self.draft.calibration_format)
        except Exception as exc:  # noqa: BLE001 - the whole point is to catch it here
            self._summary.setText(self.tr("Calibration error: {0}").format(exc))
            return
        left, right = rig.cameras["L"], rig.cameras["R"]
        _, translation = rig.pose("R")
        baseline = float(np.linalg.norm(translation))
        self._summary.setText(
            self.tr(
                "L fx={0:.1f} fy={1:.1f} | R fx={2:.1f} fy={3:.1f} | baseline={4:.1f} mm"
            ).format(left.fx, left.fy, right.fx, right.fy, baseline)
        )

    def refresh(self) -> None:
        self._format.setCurrentText(self.draft.calibration_format)
        path = self.draft.calibration_file
        if path is not None:
            self._file.setText(self.tr("File: {0}").format(path))
        else:
            self._file.setText(self.tr("No calibration file selected"))
