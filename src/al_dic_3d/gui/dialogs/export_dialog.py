"""Export dialog — output folder + formats + field selection (2D dialog idiom).

Mirrors the 2D Export Results window: an OUTPUT FOLDER row (path + Browse + Open
Folder), FORMAT checkboxes (NumPy / MATLAB / per-frame CSV), and DISPLACEMENT /
STRAIN field groups with All / None pickers. Exports run through the Qt-free
:mod:`al_dic_3d.export` module.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from al_dic.gui.theme import COLORS
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.export import DISPLACEMENT_IDS, STRAIN_IDS

if TYPE_CHECKING:
    from al_dic_3d.runner import RunResult

_FIELD_LABELS = {
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


class ExportDialog(QDialog):
    """Field-selective export of a completed run."""

    def __init__(self, result: RunResult, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._result = result
        self.setWindowTitle(self.tr("Export Results"))
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # ---- OUTPUT FOLDER ----
        layout.addWidget(self._section_label(self.tr("OUTPUT FOLDER")))
        folder_row = QHBoxLayout()
        self._folder_edit = QLineEdit()
        self._folder_edit.setPlaceholderText(self.tr("Select output folder…"))
        folder_row.addWidget(self._folder_edit, stretch=1)
        browse_btn = QPushButton(self.tr("Browse…"))
        browse_btn.clicked.connect(self._on_browse)
        folder_row.addWidget(browse_btn)
        self._open_btn = QPushButton(self.tr("Open Folder"))
        self._open_btn.clicked.connect(self._on_open_folder)
        folder_row.addWidget(self._open_btn)
        layout.addLayout(folder_row)

        # ---- FORMAT ----
        fmt_group = QGroupBox(self.tr("Format"))
        fmt_layout = QVBoxLayout(fmt_group)
        self._npz_cb = QCheckBox(self.tr("NumPy archive (.npz)"))
        self._npz_cb.setChecked(True)
        self._mat_cb = QCheckBox(self.tr("MATLAB (.mat)"))
        self._mat_cb.setChecked(True)
        self._csv_cb = QCheckBox(self.tr("CSV (one file per frame)"))
        for cb in (self._npz_cb, self._mat_cb, self._csv_cb):
            fmt_layout.addWidget(cb)
        layout.addWidget(fmt_group)

        # ---- DISPLACEMENT ----
        self._disp_checks = self._field_group(
            layout, self.tr("Displacement"), DISPLACEMENT_IDS, checked=True
        )

        # ---- STRAIN ----
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

        # ---- actions ----
        self._status = QLabel("")
        self._status.setStyleSheet(f"color: {COLORS.SUCCESS}; font-size: 11px;")
        layout.addWidget(self._status)

        buttons = QHBoxLayout()
        buttons.addStretch()
        self._export_btn = QPushButton(self.tr("Export Data"))
        self._export_btn.setProperty("class", "btn-primary")
        self._export_btn.setFixedHeight(32)
        self._export_btn.clicked.connect(self._on_export)
        buttons.addWidget(self._export_btn)
        close_btn = QPushButton(self.tr("Close"))
        close_btn.setFixedHeight(32)
        close_btn.clicked.connect(self.accept)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

    # ---- helpers ---------------------------------------------------------------

    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {COLORS.TEXT_SECONDARY}; font-size: 11px; "
            f"font-weight: bold; letter-spacing: 1px;"
        )
        return lbl

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
            cb = QCheckBox(_FIELD_LABELS.get(field_id, field_id))
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
        fields += [f for f, cb in self._strain_checks.items() if cb.isChecked() and cb.isEnabled()]
        return fields

    # ---- actions ----------------------------------------------------------------

    def _on_browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, self.tr("Choose output folder"))
        if folder:
            self._folder_edit.setText(folder)

    def _on_open_folder(self) -> None:
        folder = self._folder_edit.text().strip()
        if folder:
            import os

            os.startfile(folder)  # noqa: S606 - open the user's own folder

    def _on_export(self) -> None:
        folder = self._folder_edit.text().strip()
        if not folder:
            self._status.setText(self.tr("Choose an output folder first."))
            self._status.setStyleSheet(f"color: {COLORS.WARNING}; font-size: 11px;")
            return
        from al_dic_3d.export import export_csv_frames, export_mat, export_npz

        out = Path(folder)
        fields = self.selected_fields()
        written: list[str] = []
        if self._npz_cb.isChecked():
            written.append(export_npz(self._result, fields, out, "results").name)
        if self._mat_cb.isChecked():
            written.append(export_mat(self._result, fields, out, "results").name)
        if self._csv_cb.isChecked():
            frames = export_csv_frames(self._result, fields, out, "results")
            written.append(self.tr("{0} CSV frames").format(len(frames)))
        self._status.setStyleSheet(f"color: {COLORS.SUCCESS}; font-size: 11px;")
        self._status.setText(self.tr("Wrote: {0}").format(", ".join(written)))
