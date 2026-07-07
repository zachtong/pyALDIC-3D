"""Right sidebar — run controls, progress, field selection, visualization, log.

The 2D right-sidebar idiom (fixed 280 px, big primary Run button, outline-danger
Cancel, thin progress bar with ELAPSED / REMAINING, uppercase section labels,
console at the bottom) with 3D-DIC content: the run is the full stereo
correspondence + triangulation (+ strain) pipeline, and FIELD selects 3D
world-frame displacement components or surface-strain invariants.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from al_dic.gui.icons import icon_download, icon_play, icon_stop
from al_dic.gui.theme import COLORS
from al_dic.gui.widgets.console_log import ConsoleLog
from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.gui.state import GuiSignals
from al_dic_3d.gui.widgets.field_selector import FieldSelector3D

if TYPE_CHECKING:
    from al_dic_3d.gui.controller import WorkflowController

_COLORMAPS = ["turbo", "viridis", "jet", "coolwarm", "plasma", "inferno", "RdBu_r"]


class RunWorker(QThread):
    """Runs the pipeline off the UI thread, relaying progress."""

    progress = Signal(float, str)
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(self, controller: WorkflowController) -> None:
        super().__init__()
        self._controller = controller

    def run(self) -> None:  # QThread entry point (worker thread)
        try:
            self._controller.run(progress=lambda f, m: self.progress.emit(f, m))
            self.finished_ok.emit()
        except Exception as exc:  # noqa: BLE001 - report any failure to the UI
            self.failed.emit(str(exc))


class RightSidebar3D(QWidget):
    """Run controls + progress + field + visualization + log."""

    def __init__(
        self,
        controller: WorkflowController,
        signals: GuiSignals,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.controller = controller
        self.signals = signals
        self._worker: RunWorker | None = None
        self._run_started = 0.0
        self.setObjectName("rightSidebar")
        self.setFixedWidth(280)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # ---- Run controls ----
        self._run_btn = QPushButton(self.tr("Run 3D Analysis"))
        self._run_btn.setProperty("class", "btn-primary")
        self._run_btn.setFixedHeight(36)
        self._run_btn.setIcon(icon_play())
        self._run_btn.clicked.connect(self._on_run)
        layout.addWidget(self._run_btn)

        self._cancel_btn = QPushButton(self.tr("Cancel"))
        self._cancel_btn.setProperty("class", "btn-danger")
        self._cancel_btn.setFixedHeight(30)
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.setIcon(icon_stop())
        layout.addWidget(self._cancel_btn)

        self._export_btn = QPushButton(self.tr("Export Results"))
        self._export_btn.setFixedHeight(30)
        self._export_btn.setEnabled(False)
        self._export_btn.setIcon(icon_download())
        self._export_btn.clicked.connect(self._on_export)
        layout.addWidget(self._export_btn)

        self._ready_lbl = QLabel()
        self._ready_lbl.setWordWrap(True)
        self._ready_lbl.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 10px;")
        layout.addWidget(self._ready_lbl)

        # ---- PROGRESS ----
        self._section(layout, self.tr("PROGRESS"))
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 1000)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(8)
        layout.addWidget(self._progress_bar)

        self._progress_lbl = QLabel(self.tr("Ready"))
        self._progress_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(self._progress_lbl)

        stats = QHBoxLayout()
        self._elapsed_lbl = QLabel(self.tr("ELAPSED  --:--"))
        self._elapsed_lbl.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 10px;")
        stats.addWidget(self._elapsed_lbl)
        self._remaining_lbl = QLabel(self.tr("REMAINING  --:--"))
        self._remaining_lbl.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 10px;")
        stats.addWidget(self._remaining_lbl)
        layout.addLayout(stats)

        # ---- FIELD ----
        self._section(layout, self.tr("FIELD"))
        self._field_selector = FieldSelector3D(signals)
        layout.addWidget(self._field_selector)

        self._camera_row = QHBoxLayout()
        self._camera_row.setSpacing(4)
        cam_lbl = QLabel(self.tr("Camera"))
        cam_lbl.setFixedWidth(64)
        cam_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        self._camera_row.addWidget(cam_lbl)
        self._cam_left_btn = QPushButton(self.tr("Left"))
        self._cam_right_btn = QPushButton(self.tr("Right"))
        for btn in (self._cam_left_btn, self._cam_right_btn):
            btn.setCheckable(True)
            btn.setFixedHeight(26)
            self._camera_row.addWidget(btn)
        self._cam_left_btn.setChecked(True)
        self._cam_left_btn.clicked.connect(lambda: self._pick_camera("L"))
        self._cam_right_btn.clicked.connect(lambda: self._pick_camera("R"))
        from al_dic_3d.gui.widgets.field_selector import apply_toggle_style

        apply_toggle_style(self._cam_left_btn)
        apply_toggle_style(self._cam_right_btn)
        layout.addLayout(self._camera_row)

        # ---- VISUALIZATION ----
        self._section(layout, self.tr("VISUALIZATION"))
        cmap_row = QHBoxLayout()
        cmap_row.setSpacing(4)
        cmap_lbl = QLabel(self.tr("Colormap"))
        cmap_lbl.setFixedWidth(64)
        cmap_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        cmap_row.addWidget(cmap_lbl)
        self._cmap_combo = QComboBox()
        self._cmap_combo.addItems(_COLORMAPS)
        self._cmap_combo.currentTextChanged.connect(self._on_cmap)
        cmap_row.addWidget(self._cmap_combo, stretch=1)
        layout.addLayout(cmap_row)

        self._auto_range_cb = QCheckBox(self.tr("Auto range"))
        self._auto_range_cb.setChecked(True)
        self._auto_range_cb.toggled.connect(self._on_auto_range)
        layout.addWidget(self._auto_range_cb)

        opacity_row = QHBoxLayout()
        opacity_row.setSpacing(4)
        op_lbl = QLabel(self.tr("Opacity"))
        op_lbl.setFixedWidth(64)
        op_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        opacity_row.addWidget(op_lbl)
        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(0, 100)
        self._opacity_slider.setValue(int(signals.overlay_alpha * 100))
        self._opacity_slider.valueChanged.connect(self._on_opacity)
        opacity_row.addWidget(self._opacity_slider)
        layout.addLayout(opacity_row)

        # ---- LOG ----
        log_header = QHBoxLayout()
        log_lbl = QLabel(self.tr("LOG"))
        log_lbl.setStyleSheet(
            f"color: {COLORS.TEXT_SECONDARY}; font-size: 11px; "
            f"font-weight: bold; letter-spacing: 1px;"
        )
        log_header.addWidget(log_lbl)
        log_header.addStretch()
        clear_btn = QPushButton(self.tr("Clear"))
        clear_btn.setFixedSize(56, 20)
        clear_btn.setStyleSheet(f"font-size: 10px; color: {COLORS.TEXT_MUTED}; border: none;")
        clear_btn.clicked.connect(lambda: self._console.clear())
        log_header.addWidget(clear_btn)
        layout.addLayout(log_header)

        self._console = ConsoleLog()
        # ConsoleLog caps itself at 200 px; lift the cap so it absorbs the
        # leftover column space (otherwise the layout pads every section apart).
        self._console.setMaximumHeight(16_777_215)
        layout.addWidget(self._console, stretch=1)

        # ---- wiring ----
        self.signals.log.connect(self._console.append_log)
        for sig in (
            self.signals.images_changed,
            self.signals.roi_changed,
            self.signals.calibration_changed,
            self.signals.params_changed,
        ):
            sig.connect(self.refresh_readiness)

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._update_elapsed)
        self.refresh_readiness()

    # ---- helpers -------------------------------------------------------------

    def _section(self, layout: QVBoxLayout, text: str) -> None:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {COLORS.TEXT_SECONDARY}; font-size: 11px; "
            f"font-weight: bold; letter-spacing: 1px; margin-top: 8px;"
        )
        layout.addWidget(lbl)

    def refresh_readiness(self) -> None:
        issues = self.controller.state.draft.issues()
        running = self.signals.run_state == "running"
        self._run_btn.setEnabled(not running)
        if running:
            self._ready_lbl.setText("")
        elif issues:
            self._ready_lbl.setText(self.tr("Not ready — {0}").format("; ".join(issues)))
        else:
            self._ready_lbl.setText(self.tr("Ready to run."))
        self._export_btn.setEnabled(self.controller.state.has_results)

    # ---- run lifecycle ---------------------------------------------------------

    def _on_run(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        issues = self.controller.state.draft.issues()
        if issues:
            self._console.append_log(self.tr("Not ready: {0}").format("; ".join(issues)), "warning")
            return
        self.signals.set_run_state("running")
        self._run_btn.setEnabled(False)
        self._cancel_btn.setEnabled(False)  # cooperative cancel lands next
        self._progress_bar.setValue(0)
        self._run_started = time.perf_counter()
        self._timer.start()
        self._console.append_log(self.tr("Starting 3D analysis…"))
        self.refresh_readiness()

        self._worker = RunWorker(self.controller)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ok.connect(self._on_done)
        self._worker.failed.connect(self._on_fail)
        self._worker.start()

    def _on_progress(self, fraction: float, message: str) -> None:
        self._progress_bar.setValue(int(fraction * 1000))
        self._progress_lbl.setText(f"{fraction * 100:.0f}%  —  {message}")
        self.signals.progress.emit(fraction, message)

    def _on_done(self) -> None:
        self._timer.stop()
        self._progress_bar.setValue(1000)
        self._run_btn.setEnabled(True)
        result = self.controller.state.result
        self._field_selector.set_strain_available(result is not None and result.strain is not None)
        self._console.append_log(self.tr("Analysis complete"), "success")
        self.signals.set_run_state("done")
        self.signals.results_changed.emit()
        self.refresh_readiness()

    def _on_fail(self, message: str) -> None:
        self._timer.stop()
        self._run_btn.setEnabled(True)
        self._console.append_log(self.tr("Failed: {0}").format(message), "error")
        self.signals.set_run_state("failed")
        self.refresh_readiness()

    def _update_elapsed(self) -> None:
        elapsed = time.perf_counter() - self._run_started
        mins, secs = divmod(int(elapsed), 60)
        self._elapsed_lbl.setText(self.tr("ELAPSED  {0}").format(f"{mins:02d}:{secs:02d}"))
        frac = self._progress_bar.value() / 1000.0
        if frac > 0.01:
            remaining = elapsed / frac - elapsed
            r_mins, r_secs = divmod(int(max(0, remaining)), 60)
            self._remaining_lbl.setText(
                self.tr("REMAINING  {0}").format(f"{r_mins:02d}:{r_secs:02d}")
            )

    # ---- display -----------------------------------------------------------------

    def _pick_camera(self, cam: str) -> None:
        from al_dic_3d.gui.widgets.field_selector import apply_toggle_style

        self._cam_left_btn.setChecked(cam == "L")
        self._cam_right_btn.setChecked(cam == "R")
        apply_toggle_style(self._cam_left_btn)
        apply_toggle_style(self._cam_right_btn)
        self.signals.set_camera(cam)

    def _on_cmap(self, name: str) -> None:
        self.signals.colormap = name
        self.signals.display_changed.emit()

    def _on_auto_range(self, checked: bool) -> None:
        self.signals.color_auto = checked
        self.signals.display_changed.emit()

    def _on_opacity(self, value: int) -> None:
        self.signals.overlay_alpha = value / 100.0
        self.signals.display_changed.emit()

    # ---- export ----------------------------------------------------------------

    def _on_export(self) -> None:
        state = self.controller.state
        if state.result is None:
            return
        from al_dic_3d.gui.dialogs.export_dialog import ExportDialog

        dialog = ExportDialog(state.result, parent=self)
        dialog.exec()
