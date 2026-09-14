"""Animation tab — streaming MP4/GIF export of rendered field frames.

Same per-field rows / camera / resolution / background / range controls as the
Images tab plus format (MP4 or GIF), timeline fps, and a frame-step decimator
(the playback fps scales down by the same factor so the real duration is
preserved). Drives the Qt-free :func:`al_dic_3d.export.export_animation` on
the shared worker thread — frames stream straight into the encoder (GIFs too:
one frame in memory, see :mod:`al_dic_3d.export.gifstream`). A note explains
that a GIF cannot play faster than 50 fps.
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

from al_dic_3d.export import GIF_MAX_FPS, animation_fps
from al_dic_3d.gui.dialogs.export_tabs.common import (
    MEDIA_FIELD_IDS,
    BackgroundRow,
    CameraRow,
    ExportTabBase,
    FieldRowsPanel,
    FrameRangeRow,
    make_resolution_combo,
)

if TYPE_CHECKING:
    from al_dic_3d.gui.dialogs.export_dialog import ExportDialog


class AnimationTab(ExportTabBase):
    """One MP4/GIF per enabled (camera, field) pair."""

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
            MEDIA_FIELD_IDS,
            hint,
            strain_available=result.strain is not None,
            velocity_available=n_frames > 1,
            display=dialog.field_display,
            seed_range=dialog.seed_range,
        )
        fg_layout.addWidget(self._rows)
        layout.addWidget(fields_group)

        # ---- camera + format + fps + step + resolution ----
        self._camera_row = CameraRow()
        layout.addWidget(self._camera_row)

        opts = QHBoxLayout()
        opts.setSpacing(6)
        fmt_lbl = QLabel(self.tr("Format"))
        fmt_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        opts.addWidget(fmt_lbl)
        self._format_combo = QComboBox()
        self._format_combo.addItem("MP4", "mp4")
        self._format_combo.addItem("GIF", "gif")
        opts.addWidget(self._format_combo)
        fps_lbl = QLabel(self.tr("Frames per second"))
        fps_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        opts.addWidget(fps_lbl)
        self._fps_spin = QSpinBox()
        self._fps_spin.setRange(1, 120)
        self._fps_spin.setValue(10)
        opts.addWidget(self._fps_spin)
        step_lbl = QLabel(self.tr("Frame step"))
        step_lbl.setToolTip(self.tr("Keep every Nth frame (1 = all)"))
        step_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        opts.addWidget(step_lbl)
        self._step_spin = QSpinBox()
        self._step_spin.setRange(1, max(1, n_frames))
        self._step_spin.setValue(1)
        opts.addWidget(self._step_spin)
        res_lbl = QLabel(self.tr("Resolution (long edge)"))
        res_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        opts.addWidget(res_lbl)
        self._resolution_combo = make_resolution_combo(self)
        opts.addWidget(self._resolution_combo)
        opts.addStretch()
        layout.addLayout(opts)

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
        self._update_gif_note()

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
        self._export_btn = QPushButton(self.tr("Export Animation"))
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

    def _update_gif_note(self) -> None:
        """GIF delays are 1/100 s: faster than 50 fps plays at 50 fps (say so)."""
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

    # ---- surface consumed by the Preview & Colorbar tab -------------------------

    @property
    def field_rows(self):
        """Per-field rows (targets of the preview's Apply-to-all button)."""
        return self._rows.rows

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
            fmt=str(self._format_combo.currentData()),
            fps=self._fps_spin.value(),
            frame_step=self._step_spin.value(),
            mesh_step=self._dialog.mesh_step,
            roi_mask=self._dialog.roi_mask,
            right_roi_mask=self._dialog.right_roi_mask(compute=False),
            show_deformed=self._background_row.show_deformed(),
            output_max_dim=int(self._resolution_combo.currentData()),
            include_colorbar=self._colorbar_check.isChecked(),
            colorbar_style=self._dialog.colorbar_style(),
            margin_ratio=self._dialog.margin_ratio(),
            margin_color=self._dialog.margin_color(),
        )
        kwargs["frame_start"], kwargs["frame_end"] = self._range_row.frame_range()

        def job(progress_cb, stop_event):
            from al_dic_3d.export import export_animation

            return export_animation(
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
