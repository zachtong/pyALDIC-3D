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

Off the GUI thread (fix batch V, low): the dense field is computed at the
camera's FULL resolution (it is the export path), ~1.1 s at 12 Mpx — which
froze the dialog on every edit. The debounced render now runs on the global
thread pool (one job at a time; edits made meanwhile coalesce into one
follow-up render, stale results are dropped by a generation tag). A persistent
renderer + decoded-background cache make colormap / range / opacity / style
edits recolour-only. The right camera uses the warped left ROI (M3) and the
backgrounds the canvas stretch (M6), exactly like the exports.
``_render_preview()`` stays a synchronous "render now" (tests, API).
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

import numpy as np
from al_dic.gui.theme import COLORS
from PySide6.QtCore import Qt, QThreadPool, QTimer
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
from al_dic_3d.gui.dialogs.export_tabs.common import (
    COLORMAPS,
    FIELD_LABELS,
    FieldRow,
    RangeSpinBox,
)
from al_dic_3d.gui.workers import PoolTask

if TYPE_CHECKING:
    from al_dic_3d.gui.dialogs.export_dialog import ExportDialog

# Long edge of the in-dialog preview render.
_PREVIEW_MAX_DIM = 512
# Decoded backgrounds kept for the preview (current + one neighbour).
_BG_CACHE_SIZE = 2


class _PreviewEngine:
    """Thread-safe preview compute state: one renderer + a small background cache.

    One lock serializes every render (the FieldmapRenderer caches are not
    thread-safe); the dense grids stay cached across colormap / range / style
    edits. The renderer is reset when the ROI (the render support) changes.
    """

    def __init__(self) -> None:
        from al_dic_3d.viz3d.fieldmap import FieldmapRenderer

        self.lock = threading.Lock()
        self.renderer = FieldmapRenderer()
        self.view_key: tuple | None = None  # (camera, frame, field, deformed) cached
        self._mask_key: tuple[Any, Any] | None = None
        self._bg: dict[str, np.ndarray | None] = {}

    def use_masks(self, left: Any, right: Any) -> None:
        """Drop cached support/crack products when a mask changed (caller holds lock)."""
        key = (left, right)
        old = self._mask_key
        if old is None or any(a is not b for a, b in zip(key, old, strict=True)):
            self.renderer.clear_all()
            self._mask_key = key

    def background(self, path: str) -> np.ndarray | None:
        """Canvas-identical background, decoded once (caller holds lock)."""
        if path not in self._bg:
            from al_dic_3d.viz3d.background import load_display_gray

            if len(self._bg) >= _BG_CACHE_SIZE:
                self._bg.pop(next(iter(self._bg)))
            self._bg[path] = load_display_gray(path)
        return self._bg[path]


class PreviewTab(QWidget):
    """WYSIWYG preview of one exported frame + the shared colorbar style."""

    _worker = None  # duck-types the ExportTabBase surface (no export worker here)

    def __init__(self, dialog: ExportDialog, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dialog = dialog
        self._engine = _PreviewEngine()
        self._generation = 0  # bumped per request; stale results are dropped
        self._inflight = False
        self._pending = False
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

        # Debounced re-render so rapid setting changes coalesce (2D idiom); the
        # render itself runs on the thread pool.
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(220)
        self._preview_timer.timeout.connect(self._request_preview)

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

        self._vmin_spin = RangeSpinBox()
        self._vmax_spin = RangeSpinBox()
        for spin in (self._vmin_spin, self._vmax_spin):
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
        refresh_btn.clicked.connect(self._request_preview)
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
        return False  # a preview never blocks closing the dialog

    def shutdown(self, timeout_ms: int = 0) -> None:
        self._preview_timer.stop()
        self._generation += 1  # a render still in flight is dropped on arrival
        self._pending = False

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
        if not auto and row.seed_range_if_needed():
            # First manual range for this field: start from its data range.
            seeded = row.get_appearance()
            for spin, key in ((self._vmin_spin, "vmin"), (self._vmax_spin, "vmax")):
                spin.blockSignals(True)
                spin.setValue(seeded[key])
                spin.blockSignals(False)
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

    def _preview_request(self) -> dict | str:
        """Everything one render needs, read on the GUI thread (or a message)."""
        field = self._field_combo.currentData()
        row = self._selected_row()
        if field is None or row is None:
            return self.tr("Enable a field on the Images tab to preview.")
        dialog = self._dialog
        result = dialog.result
        n_frames = int(result.reconstruction.n_frames)
        frame_k = max(0, min(self._frame_spin.value() - 1, n_frames - 1))
        cam = str(self._camera_combo.currentData())
        show_deformed = dialog._images_tab.show_deformed()
        files = list(dialog.image_files.get(cam) or [])
        bg_path = None
        if files:
            bg_path = files[min(frame_k, len(files) - 1) if show_deformed else 0]
        return dict(
            result=result,
            field=field,
            cfg=row.config(),
            frame_k=frame_k,
            cam=cam,
            show_deformed=show_deformed,
            bg_path=bg_path,
            mesh_step=dialog.mesh_step,
            roi=dialog.roi_mask,
            right_mask=dialog.right_roi_mask,  # warps (once) on the worker thread
            include_colorbar=dialog._images_tab.include_colorbar(),
            style=self.colorbar_style(),
            margin=(self.margin_ratio(), self.margin_color()),
        )

    def _compose(self, req: dict) -> np.ndarray | None:
        """Render one preview frame (any thread); None = no data to draw.

        The export functions are looked up on the package at call time, so the
        preview always runs exactly what the exports run.
        """
        import al_dic_3d.export as export_api
        from al_dic_3d.export.render import crack_barrier

        result, cam, roi = req["result"], req["cam"], req["roi"]
        right = req["right_mask"]() if (cam == "R" and roi is not None) else None
        cfg = req["cfg"]
        engine = self._engine
        with engine.lock:
            engine.use_masks(roi, right)
            view_key = (cam, req["frame_k"], req["field"], req["show_deformed"])
            if engine.view_key != view_key:
                engine.renderer.clear_frame_caches()  # keep one frame's grids only
                engine.view_key = view_key
            bg = engine.background(req["bg_path"]) if req["bg_path"] else None
            # Item 4 WYSIWYG: crack-bridging cells are blanked exactly like the
            # image export (the drawn L ROI doubles as the barrier when crack-aware).
            rendered = export_api.render_field_frame(
                result,
                cam,
                req["field"],
                req["frame_k"],
                bg,
                cfg,
                mesh_step=req["mesh_step"],
                roi_mask=roi if cam == "L" else right,
                show_deformed=req["show_deformed"],
                output_max_dim=_PREVIEW_MAX_DIM,
                renderer=engine.renderer,
                barrier_mask=crack_barrier(result, roi) if cam == "L" else None,
            )
        if rendered is None:
            return None
        img, vmin, vmax = rendered
        if req["include_colorbar"]:
            img = export_api.attach_colorbar(
                img, req["style"], cfg.colormap, vmin, vmax, cfg.colorbar_text()
            )
        return export_api.add_margin(img, *req["margin"])

    def _request_preview(self) -> None:
        """Debounced entry: render on the thread pool, newest settings win."""
        if self._dialog._tabs.currentWidget() is not self:
            return  # an Images-tab edit while hidden: activate() renders on show
        req = self._preview_request()
        if isinstance(req, str):
            self._preview_label.setText(req)
            return
        self._generation += 1
        if self._inflight:
            self._pending = True  # re-render with the latest settings afterwards
            return
        self._inflight = True
        task = PoolTask(self._compose, req, tag=self._generation)
        task.signals.done.connect(self._on_preview_done)
        task.signals.failed.connect(self._on_preview_failed)
        QThreadPool.globalInstance().start(task)

    def _on_preview_done(self, generation: int, img: object) -> None:
        self._inflight = False
        if generation == self._generation or self._pending:
            self._show_preview(img)
        if self._pending:
            self._pending = False
            self._request_preview()

    def _on_preview_failed(self, generation: int, message: str) -> None:
        self._inflight = False
        if generation == self._generation or self._pending:
            self._preview_label.setText(self.tr("Preview failed: ") + message)
        if self._pending:
            self._pending = False
            self._request_preview()

    def _render_preview(self) -> None:
        """Render NOW on the calling thread (tests / API); errors show in the canvas."""
        try:
            req = self._preview_request()
            if isinstance(req, str):
                self._preview_label.setText(req)
                return
            self._show_preview(self._compose(req))
        except Exception as exc:  # never let a preview error break the dialog
            self._preview_label.setText(self.tr("Preview failed: ") + str(exc))

    def _show_preview(self, img: object) -> None:
        if img is None:
            self._preview_label.setText(self.tr("No data for this field/frame."))
            return
        rgb = np.ascontiguousarray(np.asarray(img)[:, :, ::-1])
        h, w = rgb.shape[:2]
        qimg = QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888).copy()
        pix = QPixmap.fromImage(qimg).scaled(
            self._preview_label.width(),
            self._preview_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._preview_label.setPixmap(pix)
