"""Right sidebar — run controls, progress, field selection, visualization, log.

The 2D right-sidebar idiom (fixed 280 px, big primary Run button, outline-danger
Cancel, thin progress bar with ELAPSED / REMAINING, uppercase section labels,
console at the bottom) with 3D-DIC content: the run is the full stereo
correspondence + triangulation (+ strain) pipeline, and FIELD selects 3D
world-frame displacement components or surface-strain invariants.
"""

from __future__ import annotations

import time
from collections import deque
from typing import TYPE_CHECKING

from al_dic.gui.icons import icon_download, icon_play, icon_stop
from al_dic.gui.theme import COLORS
from al_dic.gui.widgets.collapsible_section import CollapsibleSection
from PySide6.QtCore import Qt, QTime, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.gui.issue_text import issues_text
from al_dic_3d.gui.panels.run_summary import RunSummaryMixin
from al_dic_3d.gui.run_worker import RunWorker
from al_dic_3d.gui.state import GuiSignals
from al_dic_3d.gui.widgets.console_log3d import ConsoleLog3D
from al_dic_3d.gui.widgets.field_selector import FieldSelector3D, apply_toggle_style
from al_dic_3d.gui.widgets.units_section import UnitsSection3D

if TYPE_CHECKING:
    from al_dic_3d.gui.controller import WorkflowController

_COLORMAPS = ["turbo", "viridis", "jet", "coolwarm", "plasma", "inferno", "RdBu_r"]

# G3.5: retained log entries (level, timestamp, text) behind the severity
# filter — re-rendering history must keep the original timestamps.
_LOG_CAPACITY = 2000
_LOG_FILTERS: dict[str, frozenset[str] | None] = {
    "all": None,  # no filtering
    "info": frozenset({"info", "success"}),
    "warn": frozenset({"warn", "error"}),
    "error": frozenset({"error"}),
}


class RightSidebar3D(RunSummaryMixin, QWidget):
    """Run controls + progress + field + visualization + log."""

    open_strain_window_requested = Signal()

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
        self._export_dialog = None  # G3.12: non-modal singleton
        self._log_entries: deque[tuple[str, str, str]] = deque(maxlen=_LOG_CAPACITY)
        self.setObjectName("rightSidebar")
        self.setFixedWidth(280)
        self._pending_hash = None  # draft signature of the run in flight (G2.7)

        # H5 (fix batch V): the sidebar needs ~900 px of height. On a 1366x768
        # laptop or 1080p at 150 % the window is shorter, and the FIELD buttons
        # used to collapse to a sliver; the content now scrolls instead.
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        scroll.setWidget(content)
        outer.addWidget(scroll)
        self._scroll = scroll
        layout = QVBoxLayout(content)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # ---- Run controls ----
        self._run_btn = QPushButton(self.tr("Run 3D Analysis"))
        self._run_btn.setProperty("class", "btn-primary")
        self._run_btn.setFixedHeight(36)
        self._run_btn.setIcon(icon_play())
        self._run_btn.setToolTip(
            self.tr(
                "Run the full stereo correspondence + triangulation pipeline "
                "on the loaded image pairs (F5)."
            )
        )
        self._run_btn.clicked.connect(self._on_run)
        layout.addWidget(self._run_btn)

        self._cancel_btn = QPushButton(self.tr("Cancel"))
        self._cancel_btn.setProperty("class", "btn-danger")
        self._cancel_btn.setFixedHeight(30)
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.setToolTip(
            self.tr(
                "Cancel the current analysis. Frames computed so far are kept "
                "as a partial result; only when nothing was computed yet does "
                "the run return to IDLE."
            )
        )
        self._cancel_btn.setIcon(icon_stop())
        self._cancel_btn.clicked.connect(self._on_cancel)
        layout.addWidget(self._cancel_btn)

        self._export_btn = QPushButton(self.tr("Export Results"))
        self._export_btn.setFixedHeight(30)
        self._export_btn.setEnabled(False)
        self._export_btn.setIcon(icon_download())
        self._export_btn.clicked.connect(self._on_export)
        layout.addWidget(self._export_btn)

        # Strain is post-processing (Batch C): its own window, opened here.
        self._strain_window_btn = QPushButton(self.tr("Open Strain Window"))
        self._strain_window_btn.setFixedHeight(30)
        self._strain_window_btn.setEnabled(False)
        self._strain_window_btn.clicked.connect(self.open_strain_window_requested.emit)
        layout.addWidget(self._strain_window_btn)

        self._ready_lbl = QLabel()
        self._ready_lbl.setWordWrap(True)
        self._ready_lbl.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 10px;")
        layout.addWidget(self._ready_lbl)

        # G2.7: amber staleness hint — the on-screen result no longer matches
        # the draft parameters. Hash-driven; see _refresh_stale.
        self._stale_lbl = QLabel(self.tr("Parameters changed since this result — re-run to update"))
        self._stale_lbl.setWordWrap(True)
        self._stale_lbl.setStyleSheet("color: #fbbf24; font-size: 10px; font-style: italic;")
        self._stale_lbl.setVisible(False)
        layout.addWidget(self._stale_lbl)
        self._run_hash: str | None = None  # draft signature at run start (G2.7)

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

        # Deformed vs reference frame toggle (2D idiom): controls WHERE the
        # field is plotted (geometry), so it lives in FIELD, not VISUALIZATION.
        self._deformed_cb = QCheckBox(self.tr("Show on deformed frame"))
        self._deformed_cb.setChecked(True)
        self._deformed_cb.setToolTip(
            self.tr(
                "When checked, overlay results on the deformed (current) frame "
                "instead of the reference frame"
            )
        )
        self._deformed_cb.toggled.connect(self.signals.set_show_deformed)
        layout.addWidget(self._deformed_cb)

        self._camera_row = QHBoxLayout()
        self._camera_row.setSpacing(4)
        cam_lbl = QLabel(self.tr("Camera"))
        cam_lbl.setFixedWidth(64)
        cam_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        self._camera_row.addWidget(cam_lbl)
        self._cam_left_btn = QPushButton(self.tr("Left"))
        self._cam_left_btn.setToolTip(
            self.tr(
                "Show the LEFT camera's images (the reference view: ROI, seed "
                "and mesh live here). Default."
            )
        )
        self._cam_right_btn = QPushButton(self.tr("Right"))
        self._cam_right_btn.setToolTip(
            self.tr(
                "Show the RIGHT camera's images with the field warped onto "
                "them — a cross-check that the stereo match is sound."
            )
        )
        for btn in (self._cam_left_btn, self._cam_right_btn):
            btn.setCheckable(True)
            btn.setFixedHeight(26)
            self._camera_row.addWidget(btn)
        self._cam_left_btn.setChecked(True)
        self._cam_left_btn.clicked.connect(lambda: self._pick_camera("L"))
        self._cam_right_btn.clicked.connect(lambda: self._pick_camera("R"))
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
        self._cmap_combo.setToolTip(
            self.tr(
                "Colormap for the field overlay and the 3D surface. Default "
                "turbo (perceptually ordered, high contrast); pick RdBu_r or "
                "coolwarm for signed fields centered on zero."
            )
        )
        self._cmap_combo.currentTextChanged.connect(self._on_cmap)
        cmap_row.addWidget(self._cmap_combo, stretch=1)
        layout.addLayout(cmap_row)

        self._auto_range_cb = QCheckBox(self.tr("Auto range"))
        self._auto_range_cb.setChecked(True)
        self._auto_range_cb.setToolTip(
            self.tr(
                "Rescale the color range to each frame's data range "
                "(2–98 percentile of the visible values). Default on; uncheck "
                "to type fixed Min/Max bounds that hold across frames."
            )
        )
        self._auto_range_cb.toggled.connect(self._on_auto_range)
        layout.addWidget(self._auto_range_cb)

        # G2.2: manual Min/Max bounds — enabled when Auto is off, seeded from
        # the live (percentile) range so editing starts from what is shown.
        range_row = QHBoxLayout()
        range_row.setSpacing(4)
        range_row.addWidget(QLabel(self.tr("Min")))
        # Fix batch V: the export dialog's RangeSpinBox keeps strain-sized
        # values exact (4 decimals snapped a 1.2e-5 range to 0).
        from al_dic_3d.gui.dialogs.export_tabs.common import RangeSpinBox

        self._vmin_spin = RangeSpinBox()
        self._vmax_spin = RangeSpinBox()
        for spin, tip in (
            (self._vmin_spin, self.tr("Lower color-range bound (only with Auto range off)")),
            (self._vmax_spin, self.tr("Upper color-range bound (only with Auto range off)")),
        ):
            spin.setEnabled(False)  # disabled while Auto range is on
            spin.setToolTip(tip)
            spin.valueChanged.connect(self._on_manual_range)
        range_row.addWidget(self._vmin_spin, stretch=1)
        range_row.addWidget(QLabel(self.tr("Max")))
        range_row.addWidget(self._vmax_spin, stretch=1)
        layout.addLayout(range_row)

        opacity_row = QHBoxLayout()
        opacity_row.setSpacing(4)
        op_lbl = QLabel(self.tr("Opacity"))
        op_lbl.setFixedWidth(64)
        op_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        opacity_row.addWidget(op_lbl)
        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(0, 100)
        self._opacity_slider.setValue(int(signals.overlay_alpha * 100))
        self._opacity_slider.setToolTip(self.tr("Overlay opacity (0 = transparent, 100 = opaque)"))
        self._opacity_slider.valueChanged.connect(self._on_opacity)
        opacity_row.addWidget(self._opacity_slider)
        layout.addLayout(opacity_row)

        # ---- UNITS (Q1: display-layer conversion + frame rate) ----
        self._units = UnitsSection3D(signals)
        units_section = CollapsibleSection(self.tr("UNITS"), expanded=False)
        units_section.add_widget(self._units)
        layout.addWidget(units_section)

        # ---- LOG ----
        log_header = QHBoxLayout()
        log_header.setSpacing(4)
        log_lbl = QLabel(self.tr("LOG"))
        log_lbl.setStyleSheet(
            f"color: {COLORS.TEXT_SECONDARY}; font-size: 11px; "
            f"font-weight: bold; letter-spacing: 1px;"
        )
        log_header.addWidget(log_lbl)
        log_header.addStretch()
        # G3.5: severity filter — re-renders history from the retained entries.
        self._log_filter = QComboBox()
        self._log_filter.addItem(self.tr("All messages"), "all")
        self._log_filter.addItem(self.tr("Info"), "info")
        self._log_filter.addItem(self.tr("Warnings + errors"), "warn")
        self._log_filter.addItem(self.tr("Errors only"), "error")
        self._log_filter.setFixedHeight(20)
        self._log_filter.setStyleSheet(f"font-size: 10px; color: {COLORS.TEXT_MUTED};")
        self._log_filter.setToolTip(self.tr("Show only log messages of this severity"))
        self._log_filter.currentIndexChanged.connect(self._rerender_log)
        log_header.addWidget(self._log_filter)
        save_btn = QPushButton(self.tr("Save…"))
        save_btn.setFixedSize(52, 20)
        save_btn.setStyleSheet(
            f"font-size: 10px; color: {COLORS.TEXT_MUTED}; border: none; padding: 0px;"
        )
        save_btn.setToolTip(self.tr("Save the full log to a text file"))
        save_btn.clicked.connect(self._on_save_log)
        log_header.addWidget(save_btn)
        clear_btn = QPushButton(self.tr("Clear"))
        clear_btn.setFixedSize(52, 20)
        clear_btn.setStyleSheet(
            f"font-size: 10px; color: {COLORS.TEXT_MUTED}; border: none; padding: 0px;"
        )
        clear_btn.setToolTip(self.tr("Clear the log console (messages are not recoverable)"))
        clear_btn.clicked.connect(self._on_clear_log)
        log_header.addWidget(clear_btn)
        layout.addLayout(log_header)

        self._console = ConsoleLog3D()
        # ConsoleLog caps itself at 200 px; lift the cap so it absorbs the
        # leftover column space (otherwise the layout pads every section apart).
        self._console.setMaximumHeight(16_777_215)
        self._console.save_requested.connect(self._on_save_log)  # G3.1c menu
        self._console.clear_requested.connect(self._on_clear_log)
        layout.addWidget(self._console, stretch=1)

        # ---- wiring ----
        self.signals.log.connect(self._append_log)
        for sig in (
            self.signals.images_changed,
            self.signals.roi_changed,
            self.signals.calibration_changed,
            self.signals.params_changed,
        ):
            sig.connect(self.refresh_readiness)
        # Results-driven buttons must ALSO react to results_changed and to the
        # run-state transitions: refresh_readiness alone missed the
        # project-open path (results appear without any input signal firing).
        self.signals.results_changed.connect(self._refresh_result_buttons)
        self.signals.results_changed.connect(self._refresh_stale)
        self.signals.results_changed.connect(self._close_stale_export_dialog)
        self._view3d_camera_provider = None
        self.signals.run_state_changed.connect(lambda _s: self._refresh_result_buttons())

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._update_elapsed)
        # While Auto range is on, the (disabled) Min/Max boxes show the range
        # the canvas is actually using instead of 0.0000 (fix batch V).
        self._range_timer = QTimer(self)
        self._range_timer.setInterval(300)
        self._range_timer.timeout.connect(self._mirror_auto_range)
        self._range_timer.start()
        self.refresh_readiness()

    # ---- log console (G3.5: retained entries + filter + save) -----------------

    def _append_log(self, message: str, level: str = "info") -> None:
        """Console sink — maps the 'warning' alias onto ConsoleLog's 'warn' color.

        Half the code base emits level 'warning'; ConsoleLog only colors
        'warn', so those messages silently rendered as info-grey (part of the
        F3.1 'failures are invisible' complaint). Every entry lands in the
        retained ring buffer; the console shows only what passes the filter.
        """
        level = "warn" if level == "warning" else level
        timestamp = QTime.currentTime().toString("HH:mm:ss")
        self._log_entries.append((level, timestamp, message))
        if self._log_passes(level):
            self._console.append_entry(timestamp, message, level)

    def _log_passes(self, level: str) -> bool:
        allowed = _LOG_FILTERS.get(self._log_filter.currentData() or "all")
        return allowed is None or level in allowed

    def _rerender_log(self) -> None:
        """Filter change: replay the retained entries with original timestamps."""
        self._console.clear()
        for level, timestamp, message in self._log_entries:
            if self._log_passes(level):
                self._console.append_entry(timestamp, message, level)

    def _on_clear_log(self) -> None:
        """Clear console AND buffer — a filter switch must not resurrect lines."""
        self._log_entries.clear()
        self._console.clear()

    def _on_save_log(self) -> None:
        """Write the FULL retained log (unfiltered) to a text file."""
        from pathlib import Path

        from PySide6.QtWidgets import QFileDialog

        from al_dic_3d.gui import persistence

        suggested = persistence.suggested_save_path("pyaldic3d_log.txt", "log")
        path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Save log"), suggested, self.tr("Text files (*.txt)")
        )
        if not path:
            return
        try:
            lines = [f"{ts} [{lvl}] {msg}" for lvl, ts, msg in self._log_entries]
            Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
        except OSError as exc:
            self._append_log(self.tr("Failed: {0}").format(exc), "error")
            return
        persistence.set_last_dir("log", path)
        self._append_log(self.tr("Log saved to {0}").format(path), "success")

    # ---- helpers -------------------------------------------------------------

    def _section(self, layout: QVBoxLayout, text: str) -> None:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {COLORS.TEXT_SECONDARY}; font-size: 11px; "
            f"font-weight: bold; letter-spacing: 1px; margin-top: 8px;"
        )
        layout.addWidget(lbl)

    def refresh_readiness(self) -> None:
        # G3.8: draft.issues() codes are English-by-contract — translate here.
        draft = self.controller.state.draft
        issues = issues_text(draft.readiness_issues())
        running = self.signals.run_state == "running"
        # M9 (fix batch V): Run is enabled only when the project is ready; the
        # tooltip and the label below it say what is missing.
        self._run_btn.setEnabled(not running and not issues)
        # Stateful tooltip (2D idiom): a disabled/blocked Run explains itself.
        if issues and not running:
            self._run_btn.setToolTip(self.tr("Not ready — {0}").format(issues))
        else:
            self._run_btn.setToolTip(
                self.tr(
                    "Run the full stereo correspondence + triangulation pipeline "
                    "on the loaded image pairs (F5)."
                )
            )
        from al_dic_3d.gui.fft_activity import effective_init_guess

        no_point = draft.init_guess == "seed" and effective_init_guess(draft) == "fft"
        colour = COLORS.WARNING if (issues or no_point) and not running else COLORS.TEXT_MUTED
        self._ready_lbl.setStyleSheet(f"color: {colour}; font-size: 10px;")
        if running:
            self._ready_lbl.setText("")
        elif issues:
            self._ready_lbl.setText(self.tr("Not ready — {0}").format(issues))
        elif no_point:
            self._ready_lbl.setText(
                self.tr(
                    "Ready to run. No starting point: the stereo offset is found "
                    "automatically and frame 1 is seeded by FFT."
                )
            )
        else:
            self._ready_lbl.setText(self.tr("Ready to run."))
        self._refresh_result_buttons()
        self._refresh_stale()

    def _refresh_stale(self) -> None:
        """G2.7: show the amber hint when the draft diverged from the result.

        The baseline hash is taken at run start; a project opened with results
        adopts the loaded draft as its baseline (nothing changed yet). Cleared
        whenever results disappear (new project) or a new run starts.
        """
        state = self.controller.state
        if not state.has_results:
            self._run_hash = None
            self._stale_lbl.setVisible(False)
            return
        if self._run_hash is None:
            self._run_hash = state.draft.result_signature()
        self._stale_lbl.setVisible(state.draft.result_signature() != self._run_hash)

    def _refresh_result_buttons(self) -> None:
        """Enable Export / Open Strain Window whenever results exist.

        Driven by results_changed AND run_state_changed so the buttons work
        both after a run completes (state -> done) and after a project open
        (results restored, no run) — the latter was a known enablement bug.
        """
        has_results = self.controller.state.has_results
        running = self.signals.run_state == "running"
        self._export_btn.setEnabled(has_results and not running)
        self._strain_window_btn.setEnabled(has_results and not running)
        self._field_selector.set_velocity_enabled(has_results)  # Q2
        # Stateful tooltips (2D idiom): disabled buttons explain themselves.
        if has_results and not running:
            self._export_btn.setToolTip(
                self.tr("Export displacement and strain results to NPZ / MAT / CSV")
            )
            self._strain_window_btn.setToolTip(
                self.tr(
                    "Compute and visualize strain in a separate post-processing "
                    "window. Requires displacement results from a completed Run."
                )
            )
        else:
            reason = (
                self.tr("Available after the running analysis finishes.")
                if running
                else self.tr("Run an analysis first — there are no results yet.")
            )
            self._export_btn.setToolTip(reason)
            self._strain_window_btn.setToolTip(reason)

    # ---- run lifecycle ---------------------------------------------------------

    def active_worker(self) -> RunWorker | None:
        """The live pipeline worker, or None (the main window's close guard, G1.2)."""
        if self._worker is not None and self._worker.isRunning():
            return self._worker
        return None

    def _on_run(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        issues = self.controller.state.draft.readiness_issues()
        if issues:
            self._append_log(self.tr("Not ready: {0}").format(issues_text(issues)), "warn")
            return
        # G2.7: remember the signature of THIS run; it becomes the baseline of
        # the stale hint only when the run delivers results (fix batch V: a
        # failed or cancelled run used to hide the hint while the OLD results
        # stayed on screen).
        self._pending_hash = self.controller.state.draft.result_signature()
        self._stale_lbl.setVisible(False)
        self.signals.set_run_state("running")
        self._run_btn.setEnabled(False)
        self._cancel_btn.setEnabled(True)
        self._progress_bar.setRange(0, 1000)
        self._progress_bar.setValue(0)
        self._run_started = time.perf_counter()
        self._elapsed_lbl.setText(self.tr("ELAPSED  {0}").format("00:00"))
        self._remaining_lbl.setText(self.tr("REMAINING  {0}").format("--:--"))
        self._timer.start()
        self._append_log(self.tr("Starting 3D analysis…"))
        self.refresh_readiness()

        self._worker = RunWorker(self.controller)
        self._worker.progress.connect(self._on_progress)
        self._worker.log.connect(self.signals.log)
        self._worker.finished_ok.connect(self._on_done)
        self._worker.failed.connect(self._on_fail)
        self._worker.cancelled.connect(self._on_cancelled)
        self._worker.start()

    def _on_cancel(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.request_stop()
            self._cancel_btn.setEnabled(False)
            # G2.6: honest cancel feedback — the pipeline stops at the next
            # cooperative checkpoint, so the bar goes indeterminate and the
            # label says what is actually happening until the worker returns.
            self._progress_bar.setRange(0, 0)
            self._progress_lbl.setText(self.tr("Cancelling — finishing current frame…"))
            self._append_log(self.tr("Cancelling…"), "warn")

    def _on_progress(self, fraction: float, message: str) -> None:
        from al_dic_3d.gui.progress_text import progress_text

        self._progress_bar.setValue(int(fraction * 1000))
        # M10 (fix batch V): plain-language, translated text, not the raw
        # compute strings ("track_both frame 3/40", engine section codes).
        self._progress_lbl.setText(f"{fraction * 100:.0f}%  —  {progress_text(message)}")
        self.signals.progress.emit(fraction, message)

    def _on_done(self) -> None:
        self._update_elapsed()  # the final elapsed time, even for a sub-second run
        self._timer.stop()
        self._run_hash = self._pending_hash
        self._progress_bar.setRange(0, 1000)  # restore after a G2.6 cancel race
        self._progress_bar.setValue(1000)
        self._remaining_lbl.setText(self.tr("REMAINING  {0}").format("00:00"))
        self._progress_lbl.setText(self.tr("Analysis complete"))
        self._run_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        result = self.controller.state.result
        if result is not None and (result.meta or {}).get("stopped_early"):
            # R2: a cancelled-but-kept run must not leave the G2.6 "Cancelling…"
            # label behind — say what actually happened.
            self._progress_lbl.setText(self.tr("Stopped early — partial results kept"))
        self._log_run_summary()
        self.signals.set_run_state("done")
        self.signals.results_changed.emit()
        self.refresh_readiness()

    def _on_fail(self, message: str) -> None:
        self._timer.stop()
        self._progress_bar.setRange(0, 1000)  # restore after a G2.6 cancel race
        self._run_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._progress_lbl.setText(self.tr("Analysis failed"))
        self._append_log(self.tr("Failed: {0}").format(message), "error")
        self.signals.set_run_state("failed")
        self.refresh_readiness()
        self._show_error(
            self.tr("Analysis Failed"),
            self.tr(
                "The analysis stopped with an error:\n\n{0}\n\nThe log has the details."
            ).format(message),
        )

    def _show_error(self, title: str, message: str) -> None:
        """Modal error box (fix batch V: run failures were log-only). Stubbed in tests."""
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.critical(self, title, message)

    def _on_cancelled(self) -> None:
        self._timer.stop()
        self._progress_bar.setRange(0, 1000)  # back from the G2.6 indeterminate bar
        self._run_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._progress_bar.setValue(0)
        self._progress_lbl.setText(self.tr("Ready"))
        self._elapsed_lbl.setText(self.tr("ELAPSED  {0}").format("--:--"))
        self._remaining_lbl.setText(self.tr("REMAINING  {0}").format("--:--"))
        self._append_log(self.tr("Run cancelled"), "warn")
        self.signals.set_run_state("idle")
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
        self._vmin_spin.setEnabled(not checked)
        self._vmax_spin.setEnabled(not checked)
        if not checked:
            # G2.2: seed the manual bounds from the live (auto-computed
            # percentile) range so editing starts from what is on screen.
            for spin, val in (
                (self._vmin_spin, self.signals.color_min),
                (self._vmax_spin, self.signals.color_max),
            ):
                spin.blockSignals(True)
                spin.setValue(val)
                spin.blockSignals(False)
        self.signals.display_changed.emit()

    def _mirror_auto_range(self) -> None:
        if not self.signals.color_auto:
            return
        for spin, val in (
            (self._vmin_spin, self.signals.color_min),
            (self._vmax_spin, self.signals.color_max),
        ):
            if val is not None and abs(spin.value() - float(val)) > 1e-12:
                spin.blockSignals(True)
                spin.setValue(float(val))
                spin.blockSignals(False)

    def _on_manual_range(self) -> None:
        """G2.2: push the typed Min/Max to the shared display state."""
        if self.signals.color_auto:
            return  # spins are display-only while Auto is on
        self.signals.color_min = float(self._vmin_spin.value())
        self.signals.color_max = float(self._vmax_spin.value())
        self.signals.display_changed.emit()

    def _on_opacity(self, value: int) -> None:
        self.signals.overlay_alpha = value / 100.0
        self.signals.display_changed.emit()

    # ---- export (G3.12: non-modal — scrub frames while exports run) -------------

    def _on_export(self) -> None:
        state = self.controller.state
        if state.result is None:
            return
        dlg = self._export_dialog
        if dlg is not None:
            # Reuse the open dialog only while it exports THIS result (fix batch
            # V: a rerun, a strain recompute or a project switch used to leave
            # it exporting the old one); a busy stale dialog stays up.
            if dlg.matches(state.result) or not dlg.close():
                dlg.show()
                dlg.raise_()
                dlg.activateWindow()
                return
            self._export_dialog = None
        from al_dic_3d.export import VizExportHint
        from al_dic_3d.gui.dialogs.export_dialog import ExportDialog, draft_export_params

        # Snapshot of the live view so the export dialog opens showing what
        # the user is looking at (colormap, deformed mode, field, frame).
        hint = VizExportHint(
            colormap=self.signals.colormap,
            show_deformed=self.signals.show_deformed,
            overlay_alpha=self.signals.overlay_alpha,
            current_field=self.signals.display_field,
            auto_range=self.signals.color_auto,
            vmin=self.signals.color_min,
            vmax=self.signals.color_max,
            current_frame=self.signals.current_frame,
            display_unit=self.signals.display_unit,
            frame_rate=self.signals.frame_rate,
            frame_rate_known=self.signals.frame_rate_known,
        )
        extra = draft_export_params(state.draft)
        dialog = ExportDialog(
            state.result,
            extra_params=extra,
            parent=self,
            draft=state.draft,
            hint=hint,
            camera_provider=self._view3d_camera_provider,
        )
        # DeleteOnClose + destroyed-hook keeps the singleton reuse safe: the
        # reference is dropped the moment Qt tears the dialog down -- but only
        # if it still names THAT dialog (a late destroy of a replaced one must
        # not drop its successor).
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        dialog.destroyed.connect(lambda *_a, d=dialog: self._on_export_dialog_gone(d))
        self._export_dialog = dialog
        dialog.show()

    def _on_export_dialog_gone(self, dialog=None) -> None:
        if dialog is None or self._export_dialog is dialog:
            self._export_dialog = None

    def _close_stale_export_dialog(self) -> None:
        """New results: an idle dialog still showing the old ones is closed."""
        dlg = self._export_dialog
        if dlg is not None and not dlg.matches(self.controller.state.result) and not dlg.is_busy():
            dlg.close()

    def set_view3d_camera_provider(self, provider) -> None:
        """``provider() -> camera | None``: the 3D view's camera for 3D exports."""
        self._view3d_camera_provider = provider

    def close_export_dialog(self) -> bool:
        """Close the non-modal export dialog if open (main-window close cascade).

        False = the user kept it open (an export was running and they declined).
        """
        if self._export_dialog is None:
            return True
        return bool(self._export_dialog.close())

    # ---- view-state persistence (G3.10) ------------------------------------------

    def apply_view_state(self, vs: dict, n_frames: int) -> None:
        """Push a saved ``view_state`` dict into GuiSignals AND this panel's
        widgets (signals blocked), then emit one display_changed. The
        string-free sync logic lives in :mod:`al_dic_3d.gui.view_state`."""
        from al_dic_3d.gui.view_state import apply_to_sidebar

        apply_to_sidebar(self, vs, n_frames)
