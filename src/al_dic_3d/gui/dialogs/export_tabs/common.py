"""Shared machinery for the export dialog tabs (worker, rows, pickers).

Every heavy export runs in an :class:`ExportWorker` ``QThread`` with a
``threading.Event`` cooperative cancel and ``(done, total, label)`` progress —
the 2D ``ExportImagesWorker`` idiom — surfaced through a per-tab
:class:`ProgressRow` (thin bar + status + Cancel). :class:`ExportTabBase`
owns one worker per tab so the dialog can stay open, run tabs independently,
and join everything on close.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

from al_dic.gui.theme import COLORS
from PySide6.QtCore import QCoreApplication, QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.export import RESOLUTION_PRESETS, FieldImageConfig, VizExportHint

if TYPE_CHECKING:
    from al_dic_3d.gui.dialogs.export_dialog import ExportDialog

# Field id -> user-facing label (math notation, shared across tabs).
FIELD_LABELS = {
    "U": "U",
    "V": "V",
    "W": "W",
    "mag": "|D|",
    "exx": "εxx",
    "eyy": "εyy",
    "exy": "εxy",
    "e1": "ε₁",
    "e2": "ε₂",
    "max_shear": "γ max",
    "von_mises": "von Mises",
}

# Media-export defaults: displacement components enabled (spec: U, V, W).
MEDIA_DEFAULT_ENABLED = {"U", "V", "W"}

COLORMAPS = ["turbo", "viridis", "jet", "coolwarm", "plasma", "inferno", "RdBu_r"]


class ExportWorker(QThread):
    """Runs one Qt-free export job off the UI thread; cancellable."""

    progress = Signal(int, int, str)
    finished_ok = Signal(object)  # the job's return value (list of paths, ...)
    failed = Signal(str)

    def __init__(
        self,
        job: Callable[[Callable[[int, int, str], None], threading.Event], object],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._job = job
        self._stop_event = threading.Event()

    def request_stop(self) -> None:
        self._stop_event.set()

    @property
    def was_cancelled(self) -> bool:
        return self._stop_event.is_set()

    def run(self) -> None:  # QThread entry point (worker thread)
        try:
            out = self._job(self._emit_progress, self._stop_event)
            self.finished_ok.emit(out)
        except Exception as exc:  # noqa: BLE001 - report any failure to the UI
            self.failed.emit(f"{type(exc).__name__}: {exc}")

    def _emit_progress(self, done: int, total: int, label: str = "") -> None:
        self.progress.emit(int(done), int(total), str(label))


class ProgressRow(QWidget):
    """Thin progress bar + status label + Cancel button (one per tab)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(4)

        row = QHBoxLayout()
        row.setSpacing(6)
        self._bar = QProgressBar()
        self._bar.setRange(0, 1000)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(8)
        self._bar.setVisible(False)
        row.addWidget(self._bar, stretch=1)
        self._cancel_btn = QPushButton(self.tr("Cancel"))
        self._cancel_btn.setFixedHeight(24)
        self._cancel_btn.setVisible(False)
        row.addWidget(self._cancel_btn)
        layout.addLayout(row)

        self._status = QLabel("")
        self._status.setWordWrap(True)
        self._status.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(self._status)

    def begin(self) -> None:
        self._bar.setValue(0)
        self._bar.setVisible(True)
        self._cancel_btn.setEnabled(True)
        self._cancel_btn.setVisible(True)
        self._status.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 11px;")
        self._status.setText(self.tr("Exporting…"))

    def on_progress(self, done: int, total: int, label: str) -> None:
        self._bar.setValue(int(done / max(1, total) * 1000))
        self._status.setText(f"{done}/{total}  {label}")

    def finish(self, message: str, *, ok: bool = True) -> None:
        self._bar.setVisible(False)
        self._cancel_btn.setVisible(False)
        color = COLORS.SUCCESS if ok else COLORS.WARNING
        self._status.setStyleSheet(f"color: {color}; font-size: 11px;")
        self._status.setText(message)

    def set_note(self, message: str) -> None:
        self._status.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 11px;")
        self._status.setText(message)


class ExportTabBase(QWidget):
    """One tab = one worker: start/cancel/join plumbing shared by all tabs."""

    def __init__(self, dialog: ExportDialog, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dialog = dialog
        self._worker: ExportWorker | None = None
        self._export_btn: QPushButton | None = None
        self._progress = ProgressRow(self)
        self._progress._cancel_btn.clicked.connect(self._on_cancel)

    # -- lifecycle ---------------------------------------------------------

    def start_job(
        self,
        job: Callable[[Callable[[int, int, str], None], threading.Event], object],
    ) -> None:
        """Run *job* on a fresh worker; wire progress/finish back to this tab."""
        if self._worker is not None and self._worker.isRunning():
            return
        if self._export_btn is not None:
            self._export_btn.setEnabled(False)
        self._progress.begin()
        worker = ExportWorker(job, self)
        worker.progress.connect(self._progress.on_progress)
        worker.finished_ok.connect(self._on_job_done)
        worker.failed.connect(self._on_job_failed)
        self._worker = worker
        worker.start()

    def _on_cancel(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.request_stop()
            self._progress._cancel_btn.setEnabled(False)
            self._progress._status.setText(self.tr("Cancelling…"))

    def _on_job_done(self, out: object) -> None:
        if self._export_btn is not None:
            self._export_btn.setEnabled(True)
        cancelled = self._worker is not None and self._worker.was_cancelled
        n = len(out) if isinstance(out, (list, tuple)) else 0
        if cancelled:
            self._progress.finish(
                self.tr("Export cancelled — {0} file(s) kept").format(n), ok=False
            )
        else:
            self._progress.finish(self.describe_success(out))

    def _on_job_failed(self, message: str) -> None:
        if self._export_btn is not None:
            self._export_btn.setEnabled(True)
        self._progress.finish(self.tr("Error: {0}").format(message), ok=False)

    def describe_success(self, out: object) -> str:
        n = len(out) if isinstance(out, (list, tuple)) else 0
        return self.tr("Wrote {0} file(s)").format(n)

    # -- test/teardown support ----------------------------------------------

    def is_busy(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    def shutdown(self, timeout_ms: int = 10_000) -> None:
        """Request-stop and join the worker (dialog close)."""
        if self._worker is not None and self._worker.isRunning():
            self._worker.request_stop()
            self._worker.wait(timeout_ms)


# ---------------------------------------------------------------------------
# Shared pickers / rows
# ---------------------------------------------------------------------------


class FieldRow(QWidget):
    """One per-field row: enable + colormap + auto/fixed range + opacity.

    The row is the single source of truth for its field's appearance: the
    Preview tab reads it via :meth:`get_appearance` and writes back via
    :meth:`set_appearance` (signals blocked, 2D idiom). Any direct user edit
    on the row emits :attr:`appearance_changed` so the preview can follow.
    """

    appearance_changed = Signal()

    def __init__(
        self,
        field_id: str,
        hint: VizExportHint,
        *,
        has_data: bool,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._field_id = field_id

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 1, 0, 1)
        row.setSpacing(6)

        self._check = QCheckBox()
        self._check.setChecked(has_data and field_id in MEDIA_DEFAULT_ENABLED)
        self._check.setEnabled(has_data)
        row.addWidget(self._check)

        name_lbl = QLabel(FIELD_LABELS.get(field_id, field_id))
        name_lbl.setFixedWidth(72)
        name_lbl.setToolTip(field_id)
        name_lbl.setStyleSheet(
            f"color: {COLORS.TEXT_PRIMARY if has_data else COLORS.TEXT_MUTED}; font-size: 11px;"
        )
        row.addWidget(name_lbl)

        self._cmap_combo = QComboBox()
        self._cmap_combo.addItems(COLORMAPS)
        if hint.colormap in COLORMAPS:
            self._cmap_combo.setCurrentText(hint.colormap)
        self._cmap_combo.setEnabled(has_data)
        self._cmap_combo.setFixedWidth(92)
        row.addWidget(self._cmap_combo)

        self._auto_check = QCheckBox(self.tr("Auto"))
        self._auto_check.setToolTip(self.tr("Auto range"))
        self._auto_check.setChecked(True)
        self._auto_check.setEnabled(has_data)
        self._auto_check.toggled.connect(self._on_auto_changed)
        row.addWidget(self._auto_check)

        self._vmin_spin = QDoubleSpinBox()
        self._vmax_spin = QDoubleSpinBox()
        for spin, val in ((self._vmin_spin, hint.vmin), (self._vmax_spin, hint.vmax)):
            spin.setRange(-1e9, 1e9)
            spin.setDecimals(4)
            spin.setValue(val)
            spin.setFixedWidth(84)
            spin.setEnabled(False)
            row.addWidget(spin)

        opacity_lbl = QLabel(self.tr("Opacity"))
        opacity_lbl.setToolTip(self.tr("Field opacity (0 = transparent, 1 = fully opaque)"))
        opacity_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 11px;")
        row.addWidget(opacity_lbl)
        self._alpha_spin = QDoubleSpinBox()
        self._alpha_spin.setRange(0.0, 1.0)
        self._alpha_spin.setSingleStep(0.05)
        self._alpha_spin.setDecimals(2)
        self._alpha_spin.setValue(hint.overlay_alpha)
        self._alpha_spin.setFixedWidth(64)
        self._alpha_spin.setEnabled(has_data)
        row.addWidget(self._alpha_spin)
        row.addStretch()

        # Direct user edits notify listeners (the Preview tab's live sync).
        self._cmap_combo.currentIndexChanged.connect(self.appearance_changed)
        self._auto_check.toggled.connect(self.appearance_changed)
        self._vmin_spin.valueChanged.connect(self.appearance_changed)
        self._vmax_spin.valueChanged.connect(self.appearance_changed)
        self._alpha_spin.valueChanged.connect(self.appearance_changed)

    def _on_auto_changed(self, auto: bool) -> None:
        self._vmin_spin.setEnabled(not auto)
        self._vmax_spin.setEnabled(not auto)

    @property
    def field_id(self) -> str:
        return self._field_id

    def config(self) -> FieldImageConfig:
        return FieldImageConfig(
            field_id=self._field_id,
            enabled=self._check.isChecked() and self._check.isEnabled(),
            colormap=self._cmap_combo.currentText(),
            auto_range=self._auto_check.isChecked(),
            vmin=self._vmin_spin.value(),
            vmax=self._vmax_spin.value(),
            opacity=self._alpha_spin.value(),
        )

    def get_appearance(self) -> dict:
        """Colormap / range / opacity as a plain dict (for the preview panel)."""
        return dict(
            colormap=self._cmap_combo.currentText(),
            auto=self._auto_check.isChecked(),
            vmin=self._vmin_spin.value(),
            vmax=self._vmax_spin.value(),
            opacity=self._alpha_spin.value(),
        )

    def set_appearance(
        self,
        colormap: str | None = None,
        auto: bool | None = None,
        vmin: float | None = None,
        vmax: float | None = None,
        opacity: float | None = None,
    ) -> None:
        """Push values into the row's widgets, blocking signals to avoid loops.

        Lets the Preview tab edit a field's appearance while this row stays
        the single source of truth that export reads via :meth:`config`.
        """
        for widget, value in (
            (self._vmin_spin, vmin),
            (self._vmax_spin, vmax),
            (self._alpha_spin, opacity),
        ):
            if value is not None:
                widget.blockSignals(True)
                widget.setValue(value)
                widget.blockSignals(False)
        if colormap is not None:
            self._cmap_combo.blockSignals(True)
            self._cmap_combo.setCurrentText(colormap)
            self._cmap_combo.blockSignals(False)
        if auto is not None:
            self._auto_check.blockSignals(True)
            self._auto_check.setChecked(auto)
            self._auto_check.blockSignals(False)
            self._vmin_spin.setEnabled(not auto)
            self._vmax_spin.setEnabled(not auto)


class FieldRowsPanel(QWidget):
    """Rows for every exportable field (strain rows disabled without strain)."""

    def __init__(
        self,
        field_ids: Sequence[str],
        hint: VizExportHint,
        *,
        strain_available: bool,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        from al_dic_3d.export import STRAIN_IDS

        self._rows: list[FieldRow] = []
        for fid in field_ids:
            has_data = strain_available if fid in STRAIN_IDS else True
            row = FieldRow(fid, hint, has_data=has_data)
            layout.addWidget(row)
            self._rows.append(row)

    @property
    def rows(self) -> list[FieldRow]:
        return list(self._rows)

    def row_for(self, field_id: str) -> FieldRow | None:
        return next((r for r in self._rows if r.field_id == field_id), None)

    def configs(self) -> list[FieldImageConfig]:
        return [row.config() for row in self._rows]

    def enabled_configs(self) -> list[FieldImageConfig]:
        return [c for c in self.configs() if c.enabled]


class CameraRow(QWidget):
    """Camera selector: Left / Right / both -> tuple of camera ids."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        lbl = QLabel(self.tr("Camera"))
        lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        row.addWidget(lbl)
        self._combo = QComboBox()
        self._combo.addItem(self.tr("Left"), ("L",))
        self._combo.addItem(self.tr("Right"), ("R",))
        self._combo.addItem(self.tr("Left + Right"), ("L", "R"))
        row.addWidget(self._combo)
        row.addStretch()

    def cameras(self) -> tuple[str, ...]:
        return tuple(self._combo.currentData())


def make_resolution_combo(parent: QWidget | None = None) -> QComboBox:
    """Long-edge resolution presets; ``currentData() == 0`` = full resolution."""
    combo = QComboBox(parent)
    for px in sorted(p for p in RESOLUTION_PRESETS if p > 0):
        combo.addItem(f"{px} px", px)
    combo.addItem(QCoreApplication.translate("ExportTabs", "Full resolution"), 0)
    combo.setCurrentIndex(combo.findData(1024))
    return combo


class BackgroundRow(QWidget):
    """Reference vs deformed plot geometry (2D radio idiom)."""

    def __init__(self, hint: VizExportHint, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self._ref_radio = QRadioButton(self.tr("Original (frame 1 background)"))
        self._def_radio = QRadioButton(self.tr("Deformed (current frame background)"))
        (self._def_radio if hint.show_deformed else self._ref_radio).setChecked(True)
        layout.addWidget(self._ref_radio)
        layout.addWidget(self._def_radio)

    def show_deformed(self) -> bool:
        return self._def_radio.isChecked()


class FrameRangeRow(QWidget):
    """All frames, or an inclusive 1-based from/to range."""

    def __init__(self, n_frames: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        self._all_check = QCheckBox(self.tr("All frames"))
        self._all_check.setChecked(True)
        self._all_check.toggled.connect(self._on_all_toggled)
        row.addWidget(self._all_check)
        from_lbl = QLabel(self.tr("From frame"))
        from_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        row.addWidget(from_lbl)
        self._from_spin = QSpinBox()
        self._to_spin = QSpinBox()
        for spin in (self._from_spin, self._to_spin):
            spin.setRange(1, max(1, n_frames))
            spin.setEnabled(False)
        self._to_spin.setValue(max(1, n_frames))
        row.addWidget(self._from_spin)
        to_lbl = QLabel(self.tr("to"))
        to_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        row.addWidget(to_lbl)
        row.addWidget(self._to_spin)
        row.addStretch()

    def _on_all_toggled(self, all_frames: bool) -> None:
        self._from_spin.setEnabled(not all_frames)
        self._to_spin.setEnabled(not all_frames)

    def frame_range(self) -> tuple[int, int]:
        """(frame_start, frame_end) 0-based inclusive; (0, -1) = all frames."""
        if self._all_check.isChecked():
            return 0, -1
        start = self._from_spin.value() - 1
        end = self._to_spin.value() - 1
        return min(start, end), max(start, end)
