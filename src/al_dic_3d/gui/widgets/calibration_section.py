"""CALIBRATION sidebar section — the three D12 entry modes + the QC funnel.

Extracted from ``LeftSidebar3D`` (file-size discipline): built-in calibrator
(primary), file import (alternative), manual parameters (fallback). All three
converge on an opencv_yaml file previewed by the same status funnel, which
shows fx / fy and the stereo baseline as a sanity check.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from al_dic.gui.theme import COLORS
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.calibration import IMPORTERS, load_calibration
from al_dic_3d.gui.state import GuiSignals

if TYPE_CHECKING:
    from al_dic_3d.gui.controller import WorkflowController


class CalibrationSection3D(QWidget):
    """Calibrate-from-images / Format / Import / Manual + status preview."""

    def __init__(
        self,
        controller: WorkflowController,
        signals: GuiSignals,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.controller = controller
        self.signals = signals

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 8)
        layout.setSpacing(6)

        self.calibrate_btn = QPushButton(self.tr("Calibrate from images…"))
        self.calibrate_btn.setProperty("class", "btn-primary")
        self.calibrate_btn.setToolTip(
            self.tr(
                "Run the built-in stereo calibrator on your target photos\n"
                "(checkerboard / ChArUco / dot grid). Writes an opencv_yaml\n"
                "file and loads it — the recommended path when you have\n"
                "calibration images."
            )
        )
        self.calibrate_btn.clicked.connect(self._on_calibrate_dialog)
        layout.addWidget(self.calibrate_btn)

        row = QHBoxLayout()
        row.setSpacing(4)
        lbl = QLabel(self.tr("Format"))
        lbl.setFixedWidth(88)
        lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        row.addWidget(lbl)
        self.format_combo = QComboBox()
        self.format_combo.addItems(sorted(IMPORTERS))
        self.format_combo.setCurrentText("opencv_yaml")
        self.format_combo.setToolTip(
            self.tr(
                "File format of the calibration to import. Default opencv_yaml\n"
                "(written by the built-in calibrator). Pick the format matching\n"
                "your source: dice (DICe XML), matchid (MatchID .caldat),\n"
                "opencorr (OpenCorr CSV), mmc (MultiDIC/MMC .mat), matlabcv\n"
                "(MATLAB stereoParams .mat)."
            )
        )
        self.format_combo.currentTextChanged.connect(self._on_calib_format)
        row.addWidget(self.format_combo, stretch=1)
        layout.addLayout(row)

        self.import_btn = QPushButton(self.tr("Import calibration…"))
        self.import_btn.setToolTip(
            self.tr(
                "Load an existing stereo calibration file in the selected\n"
                "Format. The status line below shows fx / fy and the baseline\n"
                "as a sanity check."
            )
        )
        self.import_btn.clicked.connect(self._on_calib_browse)
        layout.addWidget(self.import_btn)

        self.manual_btn = QPushButton(self.tr("Manual parameters…"))
        self.manual_btn.setToolTip(
            self.tr(
                "Type intrinsics and extrinsics by hand (fx, fy, cx, cy,\n"
                "distortion, R, T) — the fallback when no calibration file\n"
                "exists. Writes an opencv_yaml file and loads it."
            )
        )
        self.manual_btn.clicked.connect(self._on_manual_dialog)
        layout.addWidget(self.manual_btn)

        self.status_label = QLabel(self.tr("No calibration loaded"))
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(self.status_label)

    # ---- entry modes ---------------------------------------------------------

    def _on_calibrate_dialog(self) -> None:
        from al_dic_3d.gui.dialogs.calibration_dialog import CalibrationDialog

        dlg = CalibrationDialog(self)
        if dlg.exec() and dlg.saved_path:
            self._adopt_calibration_file(dlg.saved_path)

    def _on_manual_dialog(self) -> None:
        from al_dic_3d.gui.dialogs.manual_params_dialog import ManualParamsDialog

        dlg = ManualParamsDialog(self)
        if dlg.exec() and dlg.saved_path:
            self._adopt_calibration_file(dlg.saved_path)

    def _adopt_calibration_file(self, path) -> None:
        """Route a freshly written opencv_yaml through the shared QC funnel."""
        draft = self.controller.state.draft
        draft.calibration_file = Path(path)
        draft.calibration_format = "opencv_yaml"
        self.format_combo.setCurrentText("opencv_yaml")
        self.controller.state.mark_dirty()
        self.preview()
        self.signals.calibration_changed.emit()

    def _on_calib_format(self, fmt: str) -> None:
        self.controller.state.draft.calibration_format = fmt
        self.controller.state.mark_dirty()
        self.signals.calibration_changed.emit()

    def _on_calib_browse(self) -> None:
        from al_dic_3d.gui import persistence

        path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Choose calibration file"),
            persistence.last_dir("calibration"),  # G3.2
            self.tr("Calibration files (*.xml *.yaml *.yml *.mat *.csv *.txt *.caldat)"),
        )
        if not path:
            return
        persistence.set_last_dir("calibration", path)
        self.controller.state.draft.calibration_file = Path(path)
        self.controller.state.mark_dirty()
        self.preview()
        self.signals.calibration_changed.emit()

    # ---- QC funnel -------------------------------------------------------------

    def preview(self) -> None:
        """Load + summarize the draft's calibration file on the status line."""
        draft = self.controller.state.draft
        try:
            rig = load_calibration(draft.calibration_file, draft.calibration_format)
        except Exception as exc:  # noqa: BLE001 - calibration errors must die HERE
            self.status_label.setText(self.tr("Error: {0}").format(exc))
            self.status_label.setStyleSheet(f"color: {COLORS.DANGER}; font-size: 11px;")
            self.signals.log.emit(str(exc), "error")
            return
        left = rig.cameras["L"]
        _, t = rig.pose("R")
        baseline = float(np.linalg.norm(t))
        self.status_label.setText(
            self.tr("{0}\nfx {1:.0f}  fy {2:.0f}  |  baseline {3:.1f} mm").format(
                Path(str(draft.calibration_file)).name, left.fx, left.fy, baseline
            )
        )
        self.status_label.setStyleSheet(f"color: {COLORS.SUCCESS}; font-size: 11px;")
        self.signals.log.emit(f"calibration loaded: baseline {baseline:.1f} mm", "success")
