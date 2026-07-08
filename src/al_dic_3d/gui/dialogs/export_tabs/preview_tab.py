"""Preview & Colorbar tab — WYSIWYG single-frame preview + shared export style.

Renders ONE frame through the EXACT export code path
(:func:`al_dic_3d.export.render_field_frame` -> ``attach_colorbar`` ->
``add_margin``) at a ~512 px long edge, debounced by a 220 ms single-shot
timer (2D dialog idiom) so dragging a spinbox stays smooth. The COLORBAR
STYLE + margin controls here ARE the style every Images / Animation export
uses — the dialog exposes them via ``colorbar_style()`` / ``margin_ratio()``
/ ``margin_color()`` and the tabs pass them to their Qt-free workers. The
FIELD APPEARANCE panel two-way syncs with the previewed field's row on the
Images tab, which stays the single source of truth that export reads.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from al_dic.gui.theme import COLORS
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.export import ColorbarStyle
from al_dic_3d.gui.dialogs.export_tabs.common import COLORMAPS, FIELD_LABELS, FieldRow

if TYPE_CHECKING:
    from al_dic_3d.gui.dialogs.export_dialog import ExportDialog

# Long edge of the in-dialog preview render (small = fast, in-thread is fine).
_PREVIEW_MAX_DIM = 512


class PreviewTab(QWidget):
    """WYSIWYG preview of one exported frame + the shared colorbar style."""

    _worker = None  # duck-types the ExportTabBase surface (no worker here)

    def __init__(self, dialog: ExportDialog, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dialog = dialog
        n_frames = int(dialog.result.reconstruction.n_frames)

        layout = QHBoxLayout(self)
        layout.setSpacing(10)

        # ---- left: preview canvas + field / frame / camera pickers ----
        left = QVBoxLayout()
        self._preview_label = QLabel(self.tr("Open this tab to render a preview."))
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setMinimumSize(420, 340)
        self._preview_label.setStyleSheet("background:#111; color:#888; border:1px solid #333;")
        left.addWidget(self._preview_label, stretch=1)

        pick_row = QHBoxLayout()
        pick_row.setSpacing(6)
        field_lbl = QLabel(self.tr("Field"))
        field_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        pick_row.addWidget(field_lbl)
        self._field_combo = QComboBox()
        self._field_combo.currentIndexChanged.connect(self._on_field_changed)
        pick_row.addWidget(self._field_combo, stretch=1)

        frame_lbl = QLabel(self.tr("Frame"))
        frame_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        pick_row.addWidget(frame_lbl)
        self._frame_spin = QSpinBox()
        self._frame_spin.setRange(1, max(1, n_frames))
        self._frame_spin.setValue(min(max(1, dialog.hint.current_frame + 1), max(1, n_frames)))
        self._frame_spin.valueChanged.connect(self._schedule_preview)
        pick_row.addWidget(self._frame_spin)

        cam_lbl = QLabel(self.tr("Camera"))
        cam_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        pick_row.addWidget(cam_lbl)
        self._camera_combo = QComboBox()
        self._camera_combo.addItem(self.tr("Left"), "L")
        self._camera_combo.addItem(self.tr("Right"), "R")
        self._camera_combo.currentIndexChanged.connect(self._schedule_preview)
        pick_row.addWidget(self._camera_combo)
        left.addLayout(pick_row)
        layout.addLayout(left, stretch=1)

        # ---- right: field appearance (synced) + colorbar style ----
        right = QVBoxLayout()
        right.addWidget(self._build_appearance_group())
        right.addWidget(self._build_style_group())
        right.addStretch()
        layout.addLayout(right)

        # Debounced re-render so rapid setting changes coalesce (2D idiom).
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(220)
        self._preview_timer.timeout.connect(self._render_preview)

        # Live sync FROM the Images tab rows (the source of truth) into the
        # appearance panel whenever the previewed field's row is edited.
        for row in self._image_rows():
            row.appearance_changed.connect(self._on_row_appearance_changed)

        self._refresh_fields()
        self._load_appearance()

    # ---- widget builders ---------------------------------------------------------

    def _build_appearance_group(self) -> QGroupBox:
        group = QGroupBox(self.tr("FIELD APPEARANCE"))
        form = QFormLayout(group)
        self._cmap_combo = QComboBox()
        self._cmap_combo.addItems(COLORMAPS)
        self._cmap_combo.currentIndexChanged.connect(self._on_appearance_changed)
        form.addRow(self.tr("Colormap"), self._cmap_combo)

        self._auto_check = QCheckBox(self.tr("Auto"))
        self._auto_check.setToolTip(self.tr("Auto range"))
        self._auto_check.setChecked(True)
        self._auto_check.toggled.connect(self._on_appearance_changed)
        form.addRow(self.tr("Range"), self._auto_check)

        self._vmin_spin = QDoubleSpinBox()
        self._vmax_spin = QDoubleSpinBox()
        for spin in (self._vmin_spin, self._vmax_spin):
            spin.setRange(-1e9, 1e9)
            spin.setDecimals(4)
            spin.valueChanged.connect(self._on_appearance_changed)
        form.addRow(self.tr("Min"), self._vmin_spin)
        form.addRow(self.tr("Max"), self._vmax_spin)

        self._opacity_spin = QDoubleSpinBox()
        self._opacity_spin.setRange(0.0, 1.0)
        self._opacity_spin.setSingleStep(0.05)
        self._opacity_spin.setDecimals(2)
        self._opacity_spin.valueChanged.connect(self._on_appearance_changed)
        form.addRow(self.tr("Opacity"), self._opacity_spin)

        self._apply_all_btn = QPushButton(self.tr("Apply to all fields"))
        self._apply_all_btn.setToolTip(
            self.tr(
                "Apply this field's colormap, opacity and auto-range to every "
                "enabled field (each field keeps its own min/max)."
            )
        )
        self._apply_all_btn.clicked.connect(self._apply_appearance_to_all)
        form.addRow(self._apply_all_btn)
        return group

    def _build_style_group(self) -> QGroupBox:
        default = ColorbarStyle()
        group = QGroupBox(self.tr("COLORBAR STYLE"))
        form = QFormLayout(group)

        self._pos_combo = QComboBox()
        for lbl, val in (
            (self.tr("Right"), "right"),
            (self.tr("Left"), "left"),
            (self.tr("Top"), "top"),
            (self.tr("Bottom"), "bottom"),
        ):
            self._pos_combo.addItem(lbl, val)
        self._pos_combo.currentIndexChanged.connect(self._schedule_preview)
        form.addRow(self.tr("Position"), self._pos_combo)

        self._font_spin = QSpinBox()
        self._font_spin.setRange(6, 32)
        self._font_spin.setValue(int(default.font_size))
        self._font_spin.valueChanged.connect(self._schedule_preview)
        form.addRow(self.tr("Font size"), self._font_spin)

        self._font_combo = QComboBox()
        for fam in ColorbarStyle.FONT_FAMILIES:  # generic family names stay literal
            self._font_combo.addItem(fam, fam)
        self._font_combo.currentIndexChanged.connect(self._schedule_preview)
        form.addRow(self.tr("Font family"), self._font_combo)

        self._width_spin = QDoubleSpinBox()
        self._width_spin.setRange(0.02, 0.25)
        self._width_spin.setSingleStep(0.01)
        self._width_spin.setDecimals(2)
        self._width_spin.setValue(default.width_ratio)
        self._width_spin.valueChanged.connect(self._schedule_preview)
        form.addRow(self.tr("Bar thickness"), self._width_spin)

        self._bg_combo = QComboBox()
        for lbl, val in ((self.tr("Black"), "black"), (self.tr("White"), "white")):
            self._bg_combo.addItem(lbl, val)
        self._bg_combo.currentIndexChanged.connect(self._schedule_preview)
        form.addRow(self.tr("Background"), self._bg_combo)

        self._margin_spin = QDoubleSpinBox()
        self._margin_spin.setRange(0.0, 0.30)
        self._margin_spin.setSingleStep(0.01)
        self._margin_spin.setDecimals(2)
        self._margin_spin.setToolTip(
            self.tr(
                "Add a blank border around the exported content, as a fraction "
                "of the long edge (0 = none)."
            )
        )
        self._margin_spin.valueChanged.connect(self._schedule_preview)
        form.addRow(self.tr("Margin"), self._margin_spin)

        self._margin_color_combo = QComboBox()
        for lbl, val in ((self.tr("White"), "white"), (self.tr("Black"), "black")):
            self._margin_color_combo.addItem(lbl, val)
        self._margin_color_combo.currentIndexChanged.connect(self._schedule_preview)
        form.addRow(self.tr("Margin color"), self._margin_color_combo)

        refresh_btn = QPushButton(self.tr("Refresh preview"))
        refresh_btn.clicked.connect(self._render_preview)
        form.addRow(refresh_btn)
        return group

    # ---- shared style consumed by the Images / Animation exports ----------------

    def colorbar_style(self) -> ColorbarStyle:
        """The COLORBAR STYLE panel as the Qt-free style object exports take."""
        return ColorbarStyle(
            position=self._pos_combo.currentData(),
            font_size=float(self._font_spin.value()),
            width_ratio=float(self._width_spin.value()),
            background=self._bg_combo.currentData(),
            font_family=self._font_combo.currentData(),
        )

    def margin_ratio(self) -> float:
        return float(self._margin_spin.value())

    def margin_color(self) -> str:
        return str(self._margin_color_combo.currentData())

    # ---- dialog lifecycle (duck-types the worker-tab surface) --------------------

    def activate(self) -> None:
        """Tab became current: repopulate fields, resync, render (2D idiom)."""
        self._refresh_fields()
        self._load_appearance()
        self._schedule_preview()

    def is_busy(self) -> bool:
        return False

    def shutdown(self, timeout_ms: int = 0) -> None:
        self._preview_timer.stop()

    # ---- field list + two-way appearance sync ------------------------------------

    def _image_rows(self) -> list[FieldRow]:
        return self._dialog._images_tab.field_rows

    def _selected_row(self) -> FieldRow | None:
        """The Images-tab row for the field currently being previewed."""
        field = self._field_combo.currentData()
        if field is None:
            return None
        return next((r for r in self._image_rows() if r.field_id == field), None)

    def _refresh_fields(self) -> None:
        """Repopulate the picker from the enabled Images-tab fields."""
        prev = self._field_combo.currentData()
        if prev is None:
            prev = self._dialog.hint.current_field
        self._field_combo.blockSignals(True)
        self._field_combo.clear()
        for row in self._image_rows():
            cfg = row.config()
            if cfg.enabled:
                self._field_combo.addItem(
                    FIELD_LABELS.get(cfg.field_id, cfg.field_id), cfg.field_id
                )
        i = self._field_combo.findData(prev)
        if i >= 0:
            self._field_combo.setCurrentIndex(i)
        self._field_combo.blockSignals(False)

    def _on_field_changed(self) -> None:
        self._load_appearance()
        self._schedule_preview()

    def _load_appearance(self) -> None:
        """Load the selected field's colormap/range/opacity into the panel."""
        row = self._selected_row()
        if row is None:
            return
        a = row.get_appearance()
        widgets = (
            self._cmap_combo,
            self._auto_check,
            self._vmin_spin,
            self._vmax_spin,
            self._opacity_spin,
        )
        for w in widgets:
            w.blockSignals(True)
        self._cmap_combo.setCurrentText(a["colormap"])
        self._auto_check.setChecked(a["auto"])
        self._vmin_spin.setValue(a["vmin"])
        self._vmax_spin.setValue(a["vmax"])
        self._opacity_spin.setValue(a["opacity"])
        for w in widgets:
            w.blockSignals(False)
        self._vmin_spin.setEnabled(not a["auto"])
        self._vmax_spin.setEnabled(not a["auto"])

    def _on_appearance_changed(self) -> None:
        """Push the panel's appearance edits back to the Images-tab row."""
        row = self._selected_row()
        if row is None:
            return
        auto = self._auto_check.isChecked()
        row.set_appearance(
            colormap=self._cmap_combo.currentText(),
            auto=auto,
            vmin=self._vmin_spin.value(),
            vmax=self._vmax_spin.value(),
            opacity=self._opacity_spin.value(),
        )
        self._vmin_spin.setEnabled(not auto)
        self._vmax_spin.setEnabled(not auto)
        self._schedule_preview()

    def _on_row_appearance_changed(self) -> None:
        """An Images-tab row was edited directly — follow it if previewed."""
        if self.sender() is self._selected_row():
            self._load_appearance()
            self._schedule_preview()

    def _apply_appearance_to_all(self) -> None:
        """Push colormap / opacity / auto-range to every enabled field row on
        the Images AND Animation tabs. Per-field min/max stay untouched —
        different fields have different value scales (2D idiom)."""
        cmap = self._cmap_combo.currentText()
        auto = self._auto_check.isChecked()
        opacity = self._opacity_spin.value()
        for rows in (self._image_rows(), self._dialog._animation_tab.field_rows):
            for row in rows:
                if row.config().enabled:
                    row.set_appearance(colormap=cmap, auto=auto, opacity=opacity)
        self._schedule_preview()

    # ---- rendering ---------------------------------------------------------------

    def _schedule_preview(self) -> None:
        self._preview_timer.start()

    def _render_preview(self) -> None:
        """Render one frame with the exact export path, at a small size."""
        try:
            self._render_preview_impl()
        except Exception as exc:  # never let a preview error break the dialog
            self._preview_label.setText(self.tr("Preview failed: ") + str(exc))

    def _render_preview_impl(self) -> None:
        import cv2

        from al_dic_3d.export import add_margin, attach_colorbar, colorbar_label
        from al_dic_3d.export import render_field_frame as render_frame

        field = self._field_combo.currentData()
        row = self._selected_row()
        if field is None or row is None:
            self._preview_label.setText(self.tr("Enable a field on the Images tab to preview."))
            return
        cfg = row.config()

        dialog = self._dialog
        result = dialog.result
        n_frames = int(result.reconstruction.n_frames)
        frame_k = max(0, min(self._frame_spin.value() - 1, n_frames - 1))
        cam = str(self._camera_combo.currentData())
        show_deformed = dialog._images_tab.show_deformed()

        files = list(dialog.image_files.get(cam) or [])
        bg = None
        if files:
            idx = min(frame_k, len(files) - 1) if show_deformed else 0
            bg = cv2.imread(str(files[idx]), cv2.IMREAD_GRAYSCALE)

        rendered = render_frame(
            result,
            cam,
            field,
            frame_k,
            bg,
            cfg,
            mesh_step=dialog.mesh_step,
            roi_mask=dialog.roi_mask if cam == "L" else None,
            show_deformed=show_deformed,
            output_max_dim=_PREVIEW_MAX_DIM,
        )
        if rendered is None:
            self._preview_label.setText(self.tr("No data for this field/frame."))
            return
        img, vmin, vmax = rendered

        if dialog._images_tab.include_colorbar():
            img = attach_colorbar(
                img, self.colorbar_style(), cfg.colormap, vmin, vmax, colorbar_label(field)
            )
        img = add_margin(img, self.margin_ratio(), self.margin_color())

        rgb = np.ascontiguousarray(img[:, :, ::-1])
        h, w = rgb.shape[:2]
        qimg = QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888).copy()
        pix = QPixmap.fromImage(qimg).scaled(
            self._preview_label.width(),
            self._preview_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._preview_label.setPixmap(pix)
