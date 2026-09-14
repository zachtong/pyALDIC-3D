"""Shared machinery for the export dialog tabs (worker, rows, pickers).

Every heavy export runs in an :class:`ExportWorker` ``QThread`` with a
``threading.Event`` cooperative cancel and ``(done, total, label)`` progress —
the 2D ``ExportImagesWorker`` idiom — surfaced through a per-tab
:class:`ProgressRow` (thin bar + status + Cancel). :class:`ExportTabBase`
owns one worker per tab so the dialog can stay open, run tabs independently,
and join everything on close.

Honest status (fix batch V): the tab reads the job's
:class:`~al_dic_3d.export.outcome.ExportOutcome` — "cancelled" only when the
job really stopped early, zero written files is a red failure (never a green
"Wrote 0 file(s)"), and frames without data / fields without data / a missing
right-camera ROI are spelled out in amber.

The worker itself was generalized into :class:`al_dic_3d.gui.workers.JobWorker`
(the session save/load flow reuses it, P2.5); ``ExportWorker`` stays the
importable name here for the existing tab/test import sites.
"""

from __future__ import annotations

import re
import threading
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

from al_dic.gui.theme import COLORS
from al_dic.gui.widgets.double_spin import LocaleSafeDoubleSpinBox
from PySide6.QtCore import QCoreApplication, Signal
from PySide6.QtGui import QValidator
from PySide6.QtWidgets import (
    QAbstractSpinBox,
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

from al_dic_3d.export import (
    DISPLACEMENT_IDS,
    RESOLUTION_PRESETS,
    STRAIN_IDS,
    VELOCITY_ID,
    FieldImageConfig,
    VizExportHint,
)
from al_dic_3d.export.outcome import WARN_RIGHT_ROI
from al_dic_3d.gui.workers import JobWorker as ExportWorker

if TYPE_CHECKING:
    from al_dic_3d.gui.dialogs.export_dialog import ExportDialog

# Field id -> user-facing label (math notation, shared across tabs).
FIELD_LABELS = {
    "U": "U",
    "V": "V",
    "W": "W",
    "mag": "|D|",
    VELOCITY_ID: "|V|",
    "exx": "εxx",
    "eyy": "εyy",
    "exy": "εxy",
    "e1": "ε₁",
    "e2": "ε₂",
    "max_shear": "γ max",
    "von_mises": "von Mises",
}

# Fields the rendered-media tabs offer (the canvas's fields, velocity included).
MEDIA_FIELD_IDS = (*DISPLACEMENT_IDS, VELOCITY_ID, *STRAIN_IDS)

# Media-export defaults: displacement components enabled (spec: U, V, W).
MEDIA_DEFAULT_ENABLED = {"U", "V", "W"}

COLORMAPS = ["turbo", "viridis", "jet", "coolwarm", "plasma", "inferno", "RdBu_r"]

# How many labels of skipped frames / empty passes the status line lists.
_MAX_LISTED = 3

# A number being typed: sign, digits, one dot, optional exponent.
_PARTIAL_NUMBER = re.compile(r"[+-]?(\d+\.?\d*|\.\d*)?([eE][+-]?\d*)?")


class RangeSpinBox(LocaleSafeDoubleSpinBox):
    """Colour-range Min/Max box that keeps strain-sized values exact.

    ``QDoubleSpinBox`` rounds its VALUE to ``decimals()``: with 4 decimals a
    strain range of 1.2e-5 snapped to 0 (fix batch V, low). This box keeps 12
    decimals and shows up to 6 significant digits (``1.234e-05``, ``150.25``),
    accepts typed exponents and a comma decimal (the 2D locale-safe base), and
    steps adaptively (one step in the last shown digit).

    Pattern for the other colour-range boxes (right sidebar / strain window):
    ``setDecimals(12)`` + this ``textFromValue`` / ``valueFromText`` /
    ``validate`` trio + ``AdaptiveDecimalStepType``.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setDecimals(12)
        self.setRange(-1e9, 1e9)
        self.setStepType(QAbstractSpinBox.StepType.AdaptiveDecimalStepType)

    def textFromValue(self, value: float) -> str:  # noqa: N802 - Qt override
        return self.locale().toString(float(value), "g", 6)

    def valueFromText(self, text: str) -> float:  # noqa: N802 - Qt override
        value, ok = self.locale().toDouble(text.replace(",", ".").strip())
        return float(value) if ok else self.value()

    def validate(self, text: str, pos: int) -> object:
        s = text.replace(",", ".").strip()
        if s in ("", "+", "-"):
            return QValidator.State.Intermediate, text, pos
        value, ok = self.locale().toDouble(s)
        if ok:
            state = (
                QValidator.State.Acceptable
                if self.minimum() <= value <= self.maximum()
                else QValidator.State.Intermediate
            )
            return state, text.replace(",", "."), pos
        if _PARTIAL_NUMBER.fullmatch(s):
            return QValidator.State.Intermediate, text, pos
        return QValidator.State.Invalid, text, pos

    def fixup(self, text: str) -> str:
        return text.replace(",", ".")


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

    def finish(self, message: str, *, ok: bool = True, error: bool = False) -> None:
        """Final status: green (ok), amber (``ok=False``) or red (``error``)."""
        self._bar.setVisible(False)
        self._cancel_btn.setVisible(False)
        color = COLORS.DANGER if error else (COLORS.SUCCESS if ok else COLORS.WARNING)
        self._status.setStyleSheet(f"color: {color}; font-size: 11px;")
        self._status.setText(message)

    def set_note(self, message: str) -> None:
        self._status.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 11px;")
        self._status.setText(message)


# Workers still running when their dialog closed (see ExportTabBase.shutdown).
# Holding the Python reference keeps the QThread alive until it finishes.
_ORPHANED_WORKERS: list = []


def _prune_orphans() -> None:
    """Drop detached workers that have finished."""
    alive = []
    for worker in _ORPHANED_WORKERS:
        try:
            running = worker.isRunning()
        except RuntimeError:  # C++ object already gone
            running = False
        if running:
            alive.append(worker)
    _ORPHANED_WORKERS[:] = alive


def _listed(items: Sequence[str]) -> str:
    """First few labels, comma-joined, with an ellipsis when there are more."""
    shown = ", ".join(items[:_MAX_LISTED])
    return shown + (", …" if len(items) > _MAX_LISTED else "")


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
        # "Cancelled" only when the job REALLY stopped early: a stop requested
        # after its last file changes nothing (fix batch V). Jobs without
        # bookkeeping fall back to the stop flag.
        cancelled = getattr(out, "cancelled", None)
        if cancelled is None:
            cancelled = self._worker is not None and self._worker.was_cancelled
        n = len(out) if isinstance(out, (list, tuple)) else 0
        if cancelled:
            self._progress.finish(self.describe_cancelled(out), ok=False)
            return
        if n == 0:
            self._progress.finish(self.describe_nothing_written(out), error=True)
            return
        problems = self.describe_problems(out)
        message = self.describe_success(out)
        if problems:
            self._progress.finish(message + " — " + problems, ok=False)
        else:
            self._progress.finish(message)

    def _on_job_failed(self, message: str) -> None:
        if self._export_btn is not None:
            self._export_btn.setEnabled(True)
        self._progress.finish(self.tr("Error: {0}").format(message), error=True)

    def describe_success(self, out: object) -> str:
        n = len(out) if isinstance(out, (list, tuple)) else 0
        return self.tr("Wrote {0} file(s)").format(n)

    def describe_cancelled(self, out: object) -> str:
        """Amber status of an export that stopped early on Cancel."""
        n = len(out) if isinstance(out, (list, tuple)) else 0
        message = self.tr("Export cancelled — {0} file(s) kept").format(n)
        if getattr(out, "discarded", None):
            message += " " + self.tr("(the unfinished animation was deleted)")
        return message

    def describe_nothing_written(self, out: object) -> str:
        """Red status for an export that finished without writing anything."""
        unavailable = list(getattr(out, "unavailable", []) or [])
        if unavailable:
            return self.tr("Nothing was written: no data to draw for {0}.").format(
                _listed(unavailable)
            )
        return self.tr("Nothing was written — the export produced no files.")

    def describe_problems(self, out: object) -> str:
        """Amber notes for a partly successful export ('' when there are none)."""
        notes: list[str] = []
        skipped = list(getattr(out, "skipped", []) or [])
        if skipped:
            notes.append(
                self.tr("{0} frame(s) had no data to draw ({1})").format(
                    len(skipped), _listed(skipped)
                )
            )
        unavailable = list(getattr(out, "unavailable", []) or [])
        if unavailable:
            notes.append(self.tr("no data for {0}").format(_listed(unavailable)))
        for code in getattr(out, "warnings", []) or []:
            if code == WARN_RIGHT_ROI:
                notes.append(
                    self.tr("the right-camera ROI could not be derived; the tracked area was used")
                )
            else:
                notes.append(str(code))
        return "; ".join(notes)

    # -- test/teardown support ----------------------------------------------

    def is_busy(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    def shutdown(self, timeout_ms: int = 10_000) -> None:
        """Request-stop and join the worker (dialog close).

        A worker that outlives the join (a job that does not poll its stop
        event quickly) is DETACHED rather than left for Qt to destroy: deleting
        a running ``QThread`` aborts the whole process (the 2D 0.7.2 crash). The
        detached worker keeps a module-level reference until it finishes.
        """
        _prune_orphans()
        worker = self._worker
        if worker is None or not worker.isRunning():
            return
        worker.request_stop()
        if worker.wait(timeout_ms):
            return
        for signal in (worker.progress, worker.finished_ok, worker.failed):
            try:
                signal.disconnect()
            except (RuntimeError, TypeError):
                pass
        worker.setParent(None)
        _ORPHANED_WORKERS.append(worker)
        self._worker = None


# ---------------------------------------------------------------------------
# Shared pickers / rows
# ---------------------------------------------------------------------------


class FieldRow(QWidget):
    """One per-field row: enable + colormap + auto/fixed range + opacity.

    The row is the single source of truth for its field's appearance: the
    Preview tab reads it via :meth:`get_appearance` and writes back via
    :meth:`set_appearance` (signals blocked, 2D idiom). Any direct user edit
    on the row emits :attr:`appearance_changed` so the preview can follow.

    Units (fix batch V, M1): ``value_scale`` / ``label`` put the field in the
    canvas's display unit, so the range spins hold display-unit values. Only
    the row of the canvas's CURRENT field is prefilled with the canvas range
    and follows its Auto setting; the others start on Auto and seed their
    Min/Max from the data (``seed_range``) the first time Auto is unticked.
    """

    appearance_changed = Signal()

    def __init__(
        self,
        field_id: str,
        hint: VizExportHint,
        *,
        has_data: bool,
        parent: QWidget | None = None,
        value_scale: float = 1.0,
        label: str | None = None,
        seed_range: Callable[[str], tuple[float, float]] | None = None,
    ) -> None:
        super().__init__(parent)
        self._field_id = field_id
        self._value_scale = float(value_scale)
        self._label = label
        self._seed_range = seed_range
        prefill = field_id == hint.current_field
        self._range_seeded = prefill  # the canvas range IS this field's range
        auto = bool(hint.auto_range) if prefill else True

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 1, 0, 1)
        row.setSpacing(6)

        self._check = QCheckBox()
        self._check.setChecked(has_data and field_id in MEDIA_DEFAULT_ENABLED)
        self._check.setEnabled(has_data)
        row.addWidget(self._check)

        name_lbl = QLabel(FIELD_LABELS.get(field_id, field_id))
        name_lbl.setFixedWidth(72)
        name_lbl.setToolTip(label or field_id)
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
        self._auto_check.setChecked(auto)
        self._auto_check.setEnabled(has_data)
        self._auto_check.toggled.connect(self._on_auto_changed)
        row.addWidget(self._auto_check)

        self._vmin_spin = RangeSpinBox()
        self._vmax_spin = RangeSpinBox()
        values = (hint.vmin, hint.vmax) if prefill else (0.0, 1.0)
        for spin, val in zip((self._vmin_spin, self._vmax_spin), values, strict=True):
            spin.setValue(float(val))
            spin.setFixedWidth(84)
            spin.setEnabled(has_data and not auto)
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
        for spin in (self._vmin_spin, self._vmax_spin):
            spin.valueChanged.connect(self._on_range_edited)
            spin.valueChanged.connect(self.appearance_changed)
        self._alpha_spin.valueChanged.connect(self.appearance_changed)

    def _on_auto_changed(self, auto: bool) -> None:
        if not auto:
            self.seed_range_if_needed()
        self._vmin_spin.setEnabled(not auto)
        self._vmax_spin.setEnabled(not auto)

    def _on_range_edited(self, _value: float) -> None:
        self._range_seeded = True  # the user's own numbers: never overwrite

    def seed_range_if_needed(self) -> bool:
        """Fill Min/Max from the data once (display units); True when it did."""
        if self._range_seeded or self._seed_range is None:
            return False
        self._range_seeded = True
        try:
            lo, hi = self._seed_range(self._field_id)
        except Exception:  # noqa: BLE001 - a seed is a convenience, never fatal
            return False
        for spin, val in ((self._vmin_spin, lo), (self._vmax_spin, hi)):
            spin.blockSignals(True)
            spin.setValue(float(val))
            spin.blockSignals(False)
        return True

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
            value_scale=self._value_scale,
            label=self._label,
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
        if vmin is not None or vmax is not None:
            self._range_seeded = True
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
    """Rows for every exportable field (rows without data are disabled).

    ``display(field_id) -> (value_scale, label)`` supplies each row's display
    unit (the dialog's canvas unit); ``seed_range(field_id) -> (lo, hi)`` the
    data range a row adopts when its Auto box is first unticked.
    """

    def __init__(
        self,
        field_ids: Sequence[str],
        hint: VizExportHint,
        *,
        strain_available: bool,
        velocity_available: bool = True,
        display: Callable[[str], tuple[float, str | None]] | None = None,
        seed_range: Callable[[str], tuple[float, float]] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._rows: list[FieldRow] = []
        for fid in field_ids:
            if fid in STRAIN_IDS:
                has_data = strain_available
            elif fid == VELOCITY_ID:
                has_data = velocity_available
            else:
                has_data = True
            scale, label = display(fid) if display is not None else (1.0, None)
            row = FieldRow(
                fid, hint, has_data=has_data, value_scale=scale, label=label, seed_range=seed_range
            )
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
