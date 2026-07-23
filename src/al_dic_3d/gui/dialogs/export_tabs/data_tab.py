"""Data tab — field-selective NPZ / MAT / CSV / PLY / VTU export (Batch E1 UI).

The E1 dialog content (format checkboxes + displacement/strain field pickers)
moved here as one tab; the export itself now runs on the shared
:class:`ExportWorker` thread so a large VTU/PLY series never freezes the GUI.
"""

from __future__ import annotations

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

from al_dic_3d.export import DISPLACEMENT_IDS, STRAIN_IDS
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

        def job(progress_cb, stop_event) -> list[str]:
            return _run_data_export(out, prefix, ts, result, extra, fields, want)

        self.start_job(job)

    def describe_success(self, out: object) -> str:
        names = list(out) if isinstance(out, (list, tuple)) else []
        return self.tr("Wrote: {0}").format(", ".join(names))


def _run_data_export(
    out: Path,
    prefix: str,
    ts: str,
    result,
    extra: dict,
    fields: list[str],
    want: dict[str, bool],
) -> list[str]:
    """The Qt-free data export job (runs on the worker thread)."""
    from al_dic_3d.export import (
        export_csv_frames,
        export_mat,
        export_npz,
        export_params,
        export_ply_frames,
        export_vtu_series,
    )

    written: list[str] = [export_params(out, prefix, ts, result, extra).name]
    if want["npz"] or want["mat"]:
        # P3.3: build the field payload ONCE and hand it to both writers.
        from al_dic_3d.export import selected_arrays

        arrays = selected_arrays(result, fields)
        if want["npz"]:
            written.append(export_npz(result, fields, out, f"{prefix}_{ts}", arrays=arrays).name)
        if want["mat"]:
            written.append(export_mat(result, fields, out, f"{prefix}_{ts}", arrays=arrays).name)
    if want["csv"]:
        frames = export_csv_frames(result, fields, out, f"{prefix}_{ts}")
        written.append(f"{len(frames)} CSV")
    if want["ply"]:
        export_ply_frames(out, prefix, ts, result, fields)
        written.append(f"{prefix}_ply_{ts}/")
    if want["vtu"]:
        export_vtu_series(out, prefix, ts, result, fields)
        written.append(f"{prefix}_vtu_{ts}/")
    return written
