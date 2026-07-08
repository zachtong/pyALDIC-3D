"""Images tab — per-camera rendered field frames (PNG/JPEG/TIFF batch).

Per-field rows (enable + colormap + auto/fixed range + opacity), a camera
selector (L / R / both), format + JPEG quality, a long-edge resolution preset,
the include-colorbar toggle, reference/deformed background radios, and a frame
range — driving the Qt-free :func:`al_dic_3d.export.export_image_frames` on
the shared worker thread.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from al_dic.gui.theme import COLORS
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.export import DISPLACEMENT_IDS, STRAIN_IDS
from al_dic_3d.gui.dialogs.export_tabs.common import (
    BackgroundRow,
    CameraRow,
    ExportTabBase,
    FieldRowsPanel,
    FrameRangeRow,
    make_resolution_combo,
)

if TYPE_CHECKING:
    from al_dic_3d.gui.dialogs.export_dialog import ExportDialog


class ImagesTab(ExportTabBase):
    """Rendered per-camera field images."""

    def __init__(self, dialog: ExportDialog, parent: QWidget | None = None) -> None:
        super().__init__(dialog, parent)
        result = dialog.result
        hint = dialog.hint
        n_frames = int(result.reconstruction.n_frames)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # ---- fields ----
        fields_group = QGroupBox(self.tr("Fields"))
        fg_layout = QVBoxLayout(fields_group)
        fg_layout.setContentsMargins(8, 4, 8, 4)
        self._rows = FieldRowsPanel(
            [*DISPLACEMENT_IDS, *STRAIN_IDS],
            hint,
            strain_available=result.strain is not None,
        )
        fg_layout.addWidget(self._rows)
        layout.addWidget(fields_group)

        # ---- camera + format + resolution ----
        self._camera_row = CameraRow()
        layout.addWidget(self._camera_row)

        opts = QHBoxLayout()
        opts.setSpacing(6)
        fmt_lbl = QLabel(self.tr("Format"))
        fmt_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        opts.addWidget(fmt_lbl)
        self._format_combo = QComboBox()
        self._format_combo.addItem("PNG", "png")
        self._format_combo.addItem("JPEG", "jpeg")
        self._format_combo.addItem("TIFF", "tiff")
        self._format_combo.currentIndexChanged.connect(self._on_format_changed)
        opts.addWidget(self._format_combo)
        self._quality_lbl = QLabel(self.tr("JPEG quality"))
        self._quality_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        opts.addWidget(self._quality_lbl)
        self._quality_spin = QSpinBox()
        self._quality_spin.setRange(10, 100)
        self._quality_spin.setValue(92)
        opts.addWidget(self._quality_spin)
        res_lbl = QLabel(self.tr("Resolution (long edge)"))
        res_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        opts.addWidget(res_lbl)
        self._resolution_combo = make_resolution_combo(self)
        opts.addWidget(self._resolution_combo)
        opts.addStretch()
        layout.addLayout(opts)
        self._on_format_changed()

        self._colorbar_check = QCheckBox(self.tr("Include colorbar"))
        self._colorbar_check.setChecked(True)
        layout.addWidget(self._colorbar_check)

        # ---- background + frame range ----
        bg_group = QGroupBox(self.tr("Background"))
        bg_layout = QVBoxLayout(bg_group)
        bg_layout.setContentsMargins(8, 4, 8, 4)
        self._background_row = BackgroundRow(hint)
        bg_layout.addWidget(self._background_row)
        layout.addWidget(bg_group)

        self._range_row = FrameRangeRow(n_frames)
        layout.addWidget(self._range_row)
        layout.addStretch()

        # ---- action + progress ----
        buttons = QHBoxLayout()
        buttons.addStretch()
        self._export_btn = QPushButton(self.tr("Export Images"))
        self._export_btn.setProperty("class", "btn-primary")
        self._export_btn.setFixedHeight(32)
        self._export_btn.clicked.connect(self.start_export)
        buttons.addWidget(self._export_btn)
        layout.addLayout(buttons)
        layout.addWidget(self._progress)

        if not dialog.image_files["L"]:
            self._export_btn.setEnabled(False)
            self._progress.set_note(
                self.tr("Load an image sequence first (open the project in the main window).")
            )

    def _on_format_changed(self) -> None:
        is_jpeg = self._format_combo.currentData() == "jpeg"
        self._quality_lbl.setVisible(is_jpeg)
        self._quality_spin.setVisible(is_jpeg)

    # ---- export ----------------------------------------------------------------

    def start_export(self) -> None:
        target = self._dialog.export_target()
        if target is None:
            self._progress.finish(self.tr("Choose an output folder first."), ok=False)
            return
        configs = self._rows.configs()
        if not any(c.enabled for c in configs):
            self._progress.finish(self.tr("No fields enabled."), ok=False)
            return
        out, prefix, ts = target
        result = self._dialog.result
        image_files = self._dialog.image_files
        kwargs = dict(
            cameras=self._camera_row.cameras(),
            mesh_step=self._dialog.mesh_step,
            roi_mask=self._dialog.roi_mask,
            show_deformed=self._background_row.show_deformed(),
            image_format=str(self._format_combo.currentData()),
            jpeg_quality=self._quality_spin.value(),
            output_max_dim=int(self._resolution_combo.currentData()),
            include_colorbar=self._colorbar_check.isChecked(),
        )
        kwargs["frame_start"], kwargs["frame_end"] = self._range_row.frame_range()

        def job(progress_cb, stop_event):
            from al_dic_3d.export import export_image_frames

            return export_image_frames(
                out,
                prefix,
                ts,
                result,
                image_files,
                configs,
                stop_event=stop_event,
                progress_cb=progress_cb,
                **kwargs,
            )

        self.start_job(job)
