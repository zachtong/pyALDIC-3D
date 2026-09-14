"""3D View tab — offscreen pyvista exports of the reconstructed surface.

One selected field colors the deforming surface. Modes: a per-frame image
sequence and/or a deforming-sequence animation, and/or a turntable orbit of
the CURRENT frame (the frame the calling window was showing, carried in the
``VizExportHint``). Drives the Qt-free :mod:`al_dic_3d.export.render3d`
entry points on the shared worker thread; pyvista is imported lazily inside
the job, so opening this tab costs nothing when the extra is missing.

Consistency with the interactive 3D view (fix batch V, M4): Auto range is the
view's per-frame 2nd-98th percentile over the nodes inside the ROI, a fixed
range can be typed (prefilled from the canvas when this is the canvas field),
the surface honours the drawn ROI, values and the scalar-bar title follow the
canvas's display unit, and the camera is the user's current 3D view when the
main window supplies one (the isometric default otherwise).
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

from al_dic_3d.export import (
    GIF_MAX_FPS,
    STRAIN_IDS,
    VELOCITY_ID,
    VIEW3D_RESOLUTIONS,
    ExportOutcome,
    animation_fps,
)
from al_dic_3d.gui.dialogs.export_tabs.common import (
    COLORMAPS,
    FIELD_LABELS,
    MEDIA_FIELD_IDS,
    ExportTabBase,
    FrameRangeRow,
    RangeSpinBox,
)

if TYPE_CHECKING:
    from al_dic_3d.gui.dialogs.export_dialog import ExportDialog


class View3DTab(ExportTabBase):
    """Offscreen 3D surface renders: sequence, animation, turntable."""

    def __init__(self, dialog: ExportDialog, parent: QWidget | None = None) -> None:
        super().__init__(dialog, parent)
        result = dialog.result
        hint = dialog.hint
        n_frames = int(result.reconstruction.n_frames)
        strain_available = result.strain is not None

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # ---- field + colormap + resolution ----
        opts = QHBoxLayout()
        opts.setSpacing(6)
        field_lbl = QLabel(self.tr("Field"))
        field_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        opts.addWidget(field_lbl)
        self._field_combo = QComboBox()
        for fid in MEDIA_FIELD_IDS:
            if fid in STRAIN_IDS and not strain_available:
                continue
            if fid == VELOCITY_ID and n_frames < 2:
                continue
            self._field_combo.addItem(FIELD_LABELS.get(fid, fid), fid)
        opts.addWidget(self._field_combo)

        cmap_lbl = QLabel(self.tr("Colormap"))
        cmap_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        opts.addWidget(cmap_lbl)
        self._cmap_combo = QComboBox()
        self._cmap_combo.addItems(COLORMAPS)
        if hint.colormap in COLORMAPS:
            self._cmap_combo.setCurrentText(hint.colormap)
        opts.addWidget(self._cmap_combo)

        res_lbl = QLabel(self.tr("Resolution"))
        res_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        opts.addWidget(res_lbl)
        self._resolution_combo = QComboBox()
        for w, h in VIEW3D_RESOLUTIONS:
            self._resolution_combo.addItem(f"{w} × {h}", (w, h))
        opts.addWidget(self._resolution_combo)
        opts.addStretch()
        layout.addLayout(opts)

        # ---- colour range (the interactive view's rule, or a fixed range) ----
        range_row = QHBoxLayout()
        range_row.setSpacing(6)
        self._auto_check = QCheckBox(self.tr("Auto range"))
        self._auto_check.setToolTip(
            self.tr(
                "Like the 3D view: each frame's 2–98 percentile of the values inside "
                "the ROI. Untick to use a fixed Min/Max for every frame."
            )
        )
        self._auto_check.setChecked(True)
        self._auto_check.toggled.connect(self._on_auto_toggled)
        range_row.addWidget(self._auto_check)
        min_lbl = QLabel(self.tr("Min"))
        min_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        range_row.addWidget(min_lbl)
        self._vmin_spin = RangeSpinBox()
        self._vmin_spin.setFixedWidth(96)
        range_row.addWidget(self._vmin_spin)
        max_lbl = QLabel(self.tr("Max"))
        max_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        range_row.addWidget(max_lbl)
        self._vmax_spin = RangeSpinBox()
        self._vmax_spin.setFixedWidth(96)
        range_row.addWidget(self._vmax_spin)
        self._unit_lbl = QLabel("")
        self._unit_lbl.setStyleSheet(f"color: {COLORS.TEXT_MUTED};")
        range_row.addWidget(self._unit_lbl)
        range_row.addStretch()
        layout.addLayout(range_row)

        # ---- sequence mode ----
        seq_group = QGroupBox(self.tr("Frame sequence"))
        seq_layout = QVBoxLayout(seq_group)
        seq_layout.setContentsMargins(8, 4, 8, 4)
        self._frames_check = QCheckBox(self.tr("Per-frame image sequence (PNG)"))
        self._frames_check.setChecked(True)
        seq_layout.addWidget(self._frames_check)
        anim_row = QHBoxLayout()
        anim_row.setSpacing(6)
        self._anim_check = QCheckBox(self.tr("Animation"))
        self._anim_check.setChecked(True)
        anim_row.addWidget(self._anim_check)
        self._format_combo = QComboBox()
        self._format_combo.addItem("MP4", "mp4")
        self._format_combo.addItem("GIF", "gif")
        anim_row.addWidget(self._format_combo)
        fps_lbl = QLabel(self.tr("Frames per second"))
        fps_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        anim_row.addWidget(fps_lbl)
        self._fps_spin = QSpinBox()
        self._fps_spin.setRange(1, 120)
        self._fps_spin.setValue(10)
        anim_row.addWidget(self._fps_spin)
        step_lbl = QLabel(self.tr("Frame step"))
        step_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        anim_row.addWidget(step_lbl)
        self._step_spin = QSpinBox()
        self._step_spin.setRange(1, max(1, n_frames))
        self._step_spin.setValue(1)
        anim_row.addWidget(self._step_spin)
        anim_row.addStretch()
        seq_layout.addLayout(anim_row)
        self._range_row = FrameRangeRow(n_frames)
        seq_layout.addWidget(self._range_row)
        layout.addWidget(seq_group)

        # ---- turntable mode ----
        turn_group = QGroupBox(self.tr("Turntable"))
        turn_layout = QHBoxLayout(turn_group)
        turn_layout.setContentsMargins(8, 4, 8, 4)
        turn_layout.setSpacing(6)
        self._turntable_check = QCheckBox(
            self.tr("Turntable (360° orbit at frame {0})").format(hint.current_frame + 1)
        )
        turn_layout.addWidget(self._turntable_check)
        orbit_lbl = QLabel(self.tr("Orbit frames"))
        orbit_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        turn_layout.addWidget(orbit_lbl)
        self._orbit_spin = QSpinBox()
        self._orbit_spin.setRange(4, 360)
        self._orbit_spin.setValue(36)
        turn_layout.addWidget(self._orbit_spin)
        turn_layout.addStretch()
        layout.addWidget(turn_group)

        self._gif_note = QLabel()
        self._gif_note.setWordWrap(True)
        self._gif_note.setStyleSheet(f"color: {COLORS.WARNING}; font-size: 11px;")
        layout.addWidget(self._gif_note)
        for signal in (
            self._format_combo.currentIndexChanged,
            self._fps_spin.valueChanged,
            self._step_spin.valueChanged,
        ):
            signal.connect(self._update_gif_note)
        layout.addStretch()

        # ---- action + progress ----
        buttons = QHBoxLayout()
        buttons.addStretch()
        self._export_btn = QPushButton(self.tr("Export 3D View"))
        self._export_btn.setProperty("class", "btn-primary")
        self._export_btn.setFixedHeight(32)
        self._export_btn.clicked.connect(self.start_export)
        buttons.addWidget(self._export_btn)
        layout.addLayout(buttons)
        layout.addWidget(self._progress)

        self._range_seeded = False
        self._field_combo.currentIndexChanged.connect(self._on_field_changed)
        idx = self._field_combo.findData(hint.current_field)
        if idx >= 0:
            self._field_combo.setCurrentIndex(idx)
        self._on_field_changed()
        self._update_gif_note()

    # ---- range + unit follow the selected field ----------------------------------

    def _field(self) -> str:
        return str(self._field_combo.currentData())

    def _on_field_changed(self, *_args) -> None:
        """Prefill the canvas range for the canvas field; Auto otherwise."""
        hint = self._dialog.hint
        field = self._field()
        _scale, label = self._dialog.field_display(field)
        self._unit_lbl.setText(label or "")
        prefill = field == hint.current_field
        self._range_seeded = prefill
        auto = bool(hint.auto_range) if prefill else True
        values = (hint.vmin, hint.vmax) if prefill else (0.0, 1.0)
        for spin, val in ((self._vmin_spin, values[0]), (self._vmax_spin, values[1])):
            spin.blockSignals(True)
            spin.setValue(float(val))
            spin.blockSignals(False)
        self._auto_check.blockSignals(True)
        self._auto_check.setChecked(auto)
        self._auto_check.blockSignals(False)
        self._vmin_spin.setEnabled(not auto)
        self._vmax_spin.setEnabled(not auto)

    def _on_auto_toggled(self, auto: bool) -> None:
        if not auto and not self._range_seeded:
            self._range_seeded = True
            try:
                lo, hi = self._dialog.seed_range(self._field())
            except Exception:  # noqa: BLE001 - a seed is a convenience only
                lo, hi = self._vmin_spin.value(), self._vmax_spin.value()
            self._vmin_spin.setValue(lo)
            self._vmax_spin.setValue(hi)
        self._vmin_spin.setEnabled(not auto)
        self._vmax_spin.setEnabled(not auto)

    def _update_gif_note(self, *_args) -> None:
        _step, playback = animation_fps(self._fps_spin.value(), self._step_spin.value())
        too_fast = self._format_combo.currentData() == "gif" and playback > GIF_MAX_FPS
        self._gif_note.setText(
            self.tr(
                "GIF timing has 1/100 s steps: {0} fps will play at {1} fps. "
                "Choose MP4 for faster playback."
            ).format(playback, GIF_MAX_FPS)
            if too_fast
            else ""
        )
        self._gif_note.setVisible(too_fast)

    # ---- export ----------------------------------------------------------------

    def start_export(self) -> None:
        target = self._dialog.export_target()
        if target is None:
            self._progress.finish(self.tr("Choose an output folder first."), ok=False)
            return
        write_frames = self._frames_check.isChecked()
        want_anim = self._anim_check.isChecked()
        want_turntable = self._turntable_check.isChecked()
        if not (write_frames or want_anim or want_turntable):
            self._progress.finish(self.tr("Nothing selected to export."), ok=False)
            return
        out, prefix, ts = target
        dialog = self._dialog
        result = dialog.result
        field_id = self._field()
        value_scale, field_label = dialog.field_display(field_id)
        common = dict(
            window_size=tuple(self._resolution_combo.currentData()),
            cmap=self._cmap_combo.currentText(),
            auto_range=self._auto_check.isChecked(),
            vmin=float(self._vmin_spin.value()),
            vmax=float(self._vmax_spin.value()),
            fps=self._fps_spin.value(),
            # The drawn LEFT ROI bounds the surface like the 3D view and, on a
            # crack-aware run, doubles as the crack barrier (item 4).
            roi_mask=dialog.roi_mask,
            camera=dialog.view3d_camera(),
            value_scale=value_scale,
            field_label=field_label,
        )
        fmt = str(self._format_combo.currentData())
        frame_step = self._step_spin.value()
        frame_start, frame_end = self._range_row.frame_range()
        frame_k = dialog.hint.current_frame
        n_orbit = self._orbit_spin.value()

        def job(progress_cb, stop_event):
            import al_dic_3d.export as export_api

            outcome = ExportOutcome()
            if write_frames or want_anim:
                outcome.absorb(
                    export_api.export_view3d_frames(
                        out,
                        prefix,
                        ts,
                        result,
                        field_id,
                        frame_start=frame_start,
                        frame_end=frame_end,
                        write_frames=write_frames,
                        animation_format=fmt if want_anim else None,
                        frame_step=frame_step,
                        stop_event=stop_event,
                        progress_cb=progress_cb,
                        **common,
                    )
                )
            if want_turntable and not stop_event.is_set():
                outcome.absorb(
                    export_api.export_view3d_turntable(
                        out,
                        prefix,
                        ts,
                        result,
                        field_id,
                        frame_k=frame_k,
                        n_orbit=n_orbit,
                        animation_format=fmt,
                        stop_event=stop_event,
                        progress_cb=progress_cb,
                        **common,
                    )
                )
            elif want_turntable:
                outcome.cancelled = True  # the turntable never ran
            return outcome

        self.start_job(job)
