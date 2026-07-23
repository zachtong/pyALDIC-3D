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
from al_dic.gui.widgets.double_spin import LocaleSafeDoubleSpinBox
from PySide6.QtCore import Qt, QTime, QTimer, Signal
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

from al_dic_3d.gui.issue_text import issues_text
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


class RightSidebar3D(QWidget):
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

        layout = QVBoxLayout(self)
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
        self._vmin_spin = LocaleSafeDoubleSpinBox()
        self._vmax_spin = LocaleSafeDoubleSpinBox()
        for spin, tip in (
            (self._vmin_spin, self.tr("Lower color-range bound (only with Auto range off)")),
            (self._vmax_spin, self.tr("Upper color-range bound (only with Auto range off)")),
        ):
            spin.setDecimals(4)
            spin.setRange(-1e9, 1e9)
            spin.setSingleStep(0.01)
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
        self.signals.run_state_changed.connect(lambda _s: self._refresh_result_buttons())

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._update_elapsed)
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

        start = persistence.last_dir("log")
        suggested = str(Path(start) / "pyaldic3d_log.txt") if start else "pyaldic3d_log.txt"
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
        self._append_log(f"log saved to {path}", "success")

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
        issues = issues_text(self.controller.state.draft.issues())
        running = self.signals.run_state == "running"
        self._run_btn.setEnabled(not running)
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
        if running:
            self._ready_lbl.setText("")
        elif issues:
            self._ready_lbl.setText(self.tr("Not ready — {0}").format(issues))
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
        issues = self.controller.state.draft.issues()
        if issues:
            self._append_log(self.tr("Not ready: {0}").format(issues_text(issues)), "warn")
            return
        # G2.7: baseline the draft signature; the stale hint clears now and
        # only reappears if the user edits parameters after this run.
        self._run_hash = self.controller.state.draft.result_signature()
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
        self._progress_bar.setValue(int(fraction * 1000))
        self._progress_lbl.setText(f"{fraction * 100:.0f}%  —  {message}")
        self.signals.progress.emit(fraction, message)

    def _on_done(self) -> None:
        self._timer.stop()
        self._progress_bar.setRange(0, 1000)  # restore after a G2.6 cancel race
        self._progress_bar.setValue(1000)
        self._remaining_lbl.setText(self.tr("REMAINING  {0}").format("00:00"))
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

    def _log_run_summary(self) -> None:
        """F3.1: the post-run failure accounting, written into the log console.

        Mirrors :func:`al_dic_3d.matching.diagnostics.summary_lines` (the CLI
        wording) with tr()-wrapped templates: frame-1 stereo stats, honesty-gate
        kills with the reason, low-validity frames, quality-gate demotions, and
        a one-line verdict. An all-empty run logs an ERROR, never a quiet
        'complete'.
        """
        result = self.controller.state.result
        if result is None:
            self._append_log(self.tr("Analysis complete"), "success")
            return
        from al_dic_3d.matching.diagnostics import LOW_VALIDITY_FRAC, summarize_run

        s = summarize_run(result.correspondence, result.reconstruction.points)
        # R2 (engine 0.7 partial results): a cancelled-but-kept run announces
        # itself FIRST — one honest line saying how many frames survived.
        meta = result.meta or {}
        if meta.get("stopped_early"):
            k = int(meta.get("stopped_at_frame") or 0)
            self._append_log(
                self.tr(
                    "Stopped early at frame {0}/{1} — kept {2} computed frames "
                    "(later frames are empty)"
                ).format(k, s.n_frames, k),
                "warn",
            )
        elif meta.get("stop_reason"):
            self._append_log(self.tr("Run interrupted: {0}").format(meta["stop_reason"]), "warn")
        if s.stereo_n_pts:
            frac = s.stereo_n_valid / s.stereo_n_pts
            self._append_log(
                self.tr("Frame-1 stereo match: {0}/{1} points matched ({2}%)").format(
                    s.stereo_n_valid, s.stereo_n_pts, f"{frac * 100:.0f}"
                ),
                "warn" if frac < LOW_VALIDITY_FRAC else "info",
            )
        for cam, n in sorted(s.gated_by_cam.items()):
            self._append_log(
                self.tr(
                    "Camera {0}: validity gate removed {1} node-frames "
                    "(correlation vs frame 1 failed)"
                ).format(cam, n),
                "warn",
            )
        for k in s.low_frames:
            self._append_log(
                self.tr("Frame {0}: only {1}% of points valid").format(
                    k, f"{s.valid_frac[k] * 100:.0f}"
                ),
                "warn",
            )
        gates = result.meta.get("gates") or {}
        for key, template in (
            ("znssd_demoted", self.tr("Quality gate (ZNSSD) removed {0} positions")),
            ("reproj_demoted", self.tr("Reprojection gate removed {0} positions")),
            ("outliers_removed", self.tr("3D outlier filter removed {0} positions")),
        ):
            n = int(gates.get(key, 0))
            if n:
                self._append_log(template.format(n), "info")
        if s.all_empty:
            self._append_log(
                self.tr(
                    "No valid points in ANY frame — the run produced an empty "
                    "result. Check ROI, masks and seeding (details above)."
                ),
                "error",
            )
        else:
            self._append_log(
                self.tr(
                    "Analysis complete — {0} frames, median validity {1}%, "
                    "{2} frame(s) below {3}% (see above)"
                ).format(
                    s.n_frames,
                    f"{s.median_valid_frac * 100:.0f}",
                    len(s.low_frames),
                    f"{LOW_VALIDITY_FRAC * 100:.0f}",
                ),
                "success",
            )

    def _on_fail(self, message: str) -> None:
        self._timer.stop()
        self._progress_bar.setRange(0, 1000)  # restore after a G2.6 cancel race
        self._run_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._append_log(self.tr("Failed: {0}").format(message), "error")
        self.signals.set_run_state("failed")
        self.refresh_readiness()

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
        if self._export_dialog is not None:  # reuse the open dialog
            self._export_dialog.show()
            self._export_dialog.raise_()
            self._export_dialog.activateWindow()
            return
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
        )
        extra = draft_export_params(state.draft)
        dialog = ExportDialog(
            state.result, extra_params=extra, parent=self, draft=state.draft, hint=hint
        )
        # DeleteOnClose + destroyed-hook keeps the singleton reuse safe: the
        # reference is dropped the moment Qt tears the dialog down.
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        dialog.destroyed.connect(self._on_export_dialog_gone)
        self._export_dialog = dialog
        dialog.show()

    def _on_export_dialog_gone(self, *_a) -> None:
        self._export_dialog = None

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
