"""Data tab — field-selective NPZ / MAT / CSV / PLY / VTU export (Batch E1 UI).

The E1 dialog content (format checkboxes + displacement/strain field pickers)
moved here as one tab; the export itself runs on the shared
:class:`ExportWorker` thread so a large VTU/PLY series never freezes the GUI.

Progress + cancel (fix batch V, M5): the job forwards the worker's progress
callback and stop event into every writer — one bar segment per format, NPZ
and MAT per array chunk / variable, CSV / PLY / VTU per frame — stops between
arrays / frames, never leaves a truncated NPZ/MAT (temporary file + replace),
and reports "cancelled" only when it really stopped early.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from al_dic.gui.theme import COLORS
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.export import DISPLACEMENT_IDS, STRAIN_IDS, ExportCancelled, ExportOutcome
from al_dic_3d.gui.dialogs.export_tabs.common import FIELD_LABELS, ExportTabBase

if TYPE_CHECKING:
    from al_dic_3d.gui.dialogs.export_dialog import ExportDialog


class DataTab(ExportTabBase):
    """Formats + field selection + the (threaded) data export action."""

    def __init__(self, dialog: ExportDialog, parent: QWidget | None = None) -> None:
        super().__init__(dialog, parent)
        result = dialog.result

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # ---- FORMAT ----
        fmt_group = QGroupBox(self.tr("Format"))
        fmt_layout = QVBoxLayout(fmt_group)
        self._npz_cb = QCheckBox(self.tr("NumPy archive (.npz)"))
        self._npz_cb.setChecked(True)
        self._mat_cb = QCheckBox(self.tr("MATLAB (.mat)"))
        self._mat_cb.setChecked(True)
        self._csv_cb = QCheckBox(self.tr("CSV (one file per frame)"))
        self._ply_cb = QCheckBox(self.tr("PLY point clouds (per frame)"))
        self._vtu_cb = QCheckBox(self.tr("VTU mesh series (ParaView)"))
        for cb in (self._npz_cb, self._mat_cb, self._csv_cb, self._ply_cb, self._vtu_cb):
            fmt_layout.addWidget(cb)
        params_note = QLabel(self.tr("✓ Parameters file (JSON) always exported"))
        params_note.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 11px;")
        fmt_layout.addWidget(params_note)
        layout.addWidget(fmt_group)

        # ---- DISPLACEMENT / STRAIN field pickers ----
        self._disp_checks = self._field_group(
            layout, self.tr("Displacement"), DISPLACEMENT_IDS, checked=True
        )
        strain_available = result.strain is not None
        self._strain_checks = self._field_group(
            layout, self.tr("Strain"), STRAIN_IDS, checked=strain_available
        )
        if not strain_available:
            for cb in self._strain_checks.values():
                cb.setEnabled(False)

        note = QLabel(
            self.tr("3D points, reprojection error, and source flags are always exported.")
        )
        note.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 10px;")
        layout.addWidget(note)
        layout.addStretch()

        # ---- action + progress ----
        buttons = QHBoxLayout()
        buttons.addStretch()
        self._export_btn = QPushButton(self.tr("Export Data"))
        self._export_btn.setProperty("class", "btn-primary")
        self._export_btn.setFixedHeight(32)
        self._export_btn.clicked.connect(self.start_export)
        buttons.addWidget(self._export_btn)
        layout.addLayout(buttons)
        layout.addWidget(self._progress)

    # ---- helpers ---------------------------------------------------------------

    def _field_group(
        self, layout: QVBoxLayout, title: str, ids: tuple, *, checked: bool
    ) -> dict[str, QCheckBox]:
        group = QGroupBox(title)
        outer = QVBoxLayout(group)
        picker = QHBoxLayout()
        picker.setSpacing(4)
        pick_lbl = QLabel(self.tr("Select:"))
        pick_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        picker.addWidget(pick_lbl)
        all_btn = QPushButton(self.tr("All"))
        none_btn = QPushButton(self.tr("None"))
        for b in (all_btn, none_btn):
            b.setFixedSize(64, 24)
            picker.addWidget(b)
        picker.addStretch()
        outer.addLayout(picker)

        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        checks: dict[str, QCheckBox] = {}
        for i, field_id in enumerate(ids):
            cb = QCheckBox(FIELD_LABELS.get(field_id, field_id))
            cb.setChecked(checked)
            grid.addWidget(cb, i // 4, i % 4)
            checks[field_id] = cb
        outer.addWidget(grid_host)
        layout.addWidget(group)

        all_btn.clicked.connect(lambda: [cb.setChecked(True) for cb in checks.values()])
        none_btn.clicked.connect(lambda: [cb.setChecked(False) for cb in checks.values()])
        return checks

    def selected_fields(self) -> list[str]:
        fields = [f for f, cb in self._disp_checks.items() if cb.isChecked()]
        strain = [f for f, cb in self._strain_checks.items() if cb.isChecked() and cb.isEnabled()]
        fields += strain
        # C3: carry the strain validity mask whenever strain is exported and it
        # exists, matching the headless runner (write_results / _arrays). Without
        # it a downstream tool averaging the dense strain silently includes the
        # trimmed one-sided-gauge nodes with no way to filter them.
        result = self._dialog.result
        if (
            strain
            and result.strain is not None
            and getattr(result.strain, "strain_valid", None) is not None
        ):
            fields.append("strain_valid")
        return fields

    @property
    def status_label(self):
        return self._progress._status

    # ---- export ----------------------------------------------------------------

    def start_export(self) -> None:
        target = self._dialog.export_target()
        if target is None:
            self._progress.finish(self.tr("Choose an output folder first."), ok=False)
            return
        out, prefix, ts = target
        fields = self.selected_fields()
        want = {
            "npz": self._npz_cb.isChecked(),
            "mat": self._mat_cb.isChecked(),
            "csv": self._csv_cb.isChecked(),
            "ply": self._ply_cb.isChecked(),
            "vtu": self._vtu_cb.isChecked(),
        }
        result = self._dialog.result
        extra = self._dialog.extra_params

        def job(progress_cb, stop_event) -> ExportOutcome:
            return _run_data_export(
                out,
                prefix,
                ts,
                result,
                extra,
                fields,
                want,
                progress_cb=progress_cb,
                stop_event=stop_event,
            )

        self.start_job(job)

    def describe_success(self, out: object) -> str:
        names = list(out) if isinstance(out, (list, tuple)) else []
        return self.tr("Wrote: {0}").format(", ".join(names))

    def describe_cancelled(self, out: object) -> str:
        names = list(out) if isinstance(out, (list, tuple)) else []
        return self.tr("Export cancelled — kept: {0}").format(", ".join(names))


# Resolution of each format's segment of the progress bar (Qt ints are 32-bit:
# byte counts of multi-GB arrays must never reach the signal).
_STAGE_UNITS = 1000


def _remove_empty_dir(folder: Path) -> None:
    """Delete *folder* only if it is empty (a format cancelled before frame 1)."""
    try:
        folder.rmdir()
    except OSError:  # not empty / already gone: keep it
        pass


class _StageProgress:
    """Maps each writer's own progress onto one bar: one segment per format."""

    def __init__(self, emit: Callable[[int, int, str], None] | None, n_stages: int) -> None:
        self._emit = emit
        self._total = max(1, n_stages) * _STAGE_UNITS
        self._stage = 0
        self._label = ""

    def begin(self, label: str) -> None:
        self._label = label
        self._report(0.0, "")

    def end(self) -> None:
        self._report(1.0, "")
        self._stage += 1

    def fraction(self, done: float, total: float, detail: str = "") -> None:
        self._report(float(done) / max(float(total), 1.0), detail)

    def _report(self, frac: float, detail: str) -> None:
        if self._emit is None:
            return
        frac = min(max(frac, 0.0), 1.0)
        done = self._stage * _STAGE_UNITS + int(round(frac * _STAGE_UNITS))
        # PLY / VTU messages already start with their format name.
        label = detail if detail.startswith(self._label) else f"{self._label} {detail}".strip()
        self._emit(min(done, self._total), self._total, label)


def _run_data_export(
    out: Path,
    prefix: str,
    ts: str,
    result,
    extra: dict,
    fields: list[str],
    want: dict[str, bool],
    *,
    progress_cb: Callable[[int, int, str], None] | None = None,
    stop_event=None,
) -> ExportOutcome:
    """The Qt-free data export job (runs on the worker thread).

    Returns the written names as an :class:`ExportOutcome`; ``cancelled`` is set
    only when a stop left formats (or frames) unwritten. A cancelled NPZ/MAT
    leaves no file (the writers remove their temporary file); CSV / PLY / VTU
    keep the complete frames written before the stop.
    """
    from al_dic_3d.export import (
        export_csv_frames,
        export_mat,
        export_npz,
        export_params,
        export_ply_frames,
        export_vtu_series,
        selected_arrays,
    )
    from al_dic_3d.export.outcome import stop_requested

    written = ExportOutcome([export_params(out, prefix, ts, result, extra).name])
    stages = [name for name in ("npz", "mat", "csv", "ply", "vtu") if want.get(name)]
    bar = _StageProgress(progress_cb, len(stages))
    arrays = None
    try:
        for stage in stages:
            if stop_requested(stop_event):
                written.cancelled = True
                break
            bar.begin(stage.upper())
            if stage in ("npz", "mat"):
                if arrays is None:  # P3.3: build the payload ONCE for both writers
                    arrays = selected_arrays(result, fields)
                writer = export_npz if stage == "npz" else export_mat
                path = writer(
                    result,
                    fields,
                    out,
                    f"{prefix}_{ts}",
                    arrays=arrays,
                    progress_cb=bar.fraction,
                    stop_event=stop_event,
                )
                written.append(path.name)
            elif stage == "csv":
                # Own sub-folder, like the CLI (`<prefix>_csv_<ts>`): hundreds of
                # per-frame CSVs no longer flood the chosen output folder.
                csv_dir = out / f"{prefix}_csv_{ts}"
                frames = export_csv_frames(
                    result,
                    fields,
                    csv_dir,
                    prefix,
                    progress_cb=bar.fraction,
                    stop_event=stop_event,
                )
                if frames:
                    written.append(f"{len(frames)} CSV")
                else:
                    _remove_empty_dir(csv_dir)
                written.cancelled = written.cancelled or frames.cancelled
            else:
                export = export_ply_frames if stage == "ply" else export_vtu_series
                files = export(
                    out,
                    prefix,
                    ts,
                    result,
                    fields,
                    progress_cb=lambda frac, msg: bar.fraction(frac, 1.0, msg),
                    stop_event=stop_event,
                )
                stopped = bool(getattr(files, "cancelled", False))
                frame_files = [p for p in files if Path(p).suffix != ".pvd"]
                if frame_files:
                    written.append(f"{prefix}_{stage}_{ts}/")
                elif stopped:  # cancelled before the first frame: leave nothing behind
                    for p in files:
                        Path(p).unlink(missing_ok=True)
                    _remove_empty_dir(out / f"{prefix}_{stage}_{ts}")
                written.cancelled = written.cancelled or stopped
            if written.cancelled:
                break
            bar.end()
    except ExportCancelled:
        written.cancelled = True  # the NPZ/MAT writer already removed its temp file
    return written
