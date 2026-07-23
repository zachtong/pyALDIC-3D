"""3D View tab — offscreen pyvista exports of the reconstructed surface.

One selected field colors the deforming surface. Modes: a per-frame image
sequence and/or a deforming-sequence animation, and/or a turntable orbit of
the CURRENT frame (the frame the calling window was showing, carried in the
``VizExportHint``). Drives the Qt-free :mod:`al_dic_3d.export.render3d`
entry points on the shared worker thread; pyvista is imported lazily inside
the job, so opening this tab costs nothing when the extra is missing.
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

from al_dic_3d.export import DISPLACEMENT_IDS, STRAIN_IDS, VIEW3D_RESOLUTIONS
from al_dic_3d.gui.dialogs.export_tabs.common import (
    COLORMAPS,
    FIELD_LABELS,
    ExportTabBase,
    FrameRangeRow,
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
        for fid in (*DISPLACEMENT_IDS, *STRAIN_IDS):
            if fid in STRAIN_IDS and not strain_available:
                continue
            self._field_combo.addItem(FIELD_LABELS.get(fid, fid), fid)
        idx = self._field_combo.findData(hint.current_field)
        if idx >= 0:
            self._field_combo.setCurrentIndex(idx)
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
        result = self._dialog.result
        field_id = str(self._field_combo.currentData())
        window_size = tuple(self._resolution_combo.currentData())
        cmap = self._cmap_combo.currentText()
        fmt = str(self._format_combo.currentData())
        fps = self._fps_spin.value()
        frame_step = self._step_spin.value()
        frame_start, frame_end = self._range_row.frame_range()
        frame_k = self._dialog.hint.current_frame
        n_orbit = self._orbit_spin.value()
        # The drawn LEFT ROI mask doubles as the crack barrier on crack-aware runs
        # (item 4): cells bridging the crack are dropped from the exported surface.
        roi_mask = self._dialog.roi_mask

        def job(progress_cb, stop_event):
            from al_dic_3d.export import export_view3d_frames, export_view3d_turntable

            paths = []
            if write_frames or want_anim:
                paths += export_view3d_frames(
                    out,
                    prefix,
                    ts,
                    result,
                    field_id,
                    frame_start=frame_start,
                    frame_end=frame_end,
                    window_size=window_size,
                    cmap=cmap,
                    write_frames=write_frames,
                    animation_format=fmt if want_anim else None,
                    fps=fps,
                    frame_step=frame_step,
                    roi_mask=roi_mask,
                    stop_event=stop_event,
                    progress_cb=progress_cb,
                )
            if want_turntable and not stop_event.is_set():
                paths += export_view3d_turntable(
                    out,
                    prefix,
                    ts,
                    result,
                    field_id,
                    frame_k=frame_k,
                    n_orbit=n_orbit,
                    window_size=window_size,
                    cmap=cmap,
                    animation_format=fmt,
                    fps=fps,
                    roi_mask=roi_mask,
                    stop_event=stop_event,
                    progress_cb=progress_cb,
                )
            return paths

        self.start_job(job)
