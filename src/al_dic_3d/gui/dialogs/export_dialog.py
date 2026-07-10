"""Export dialog — tabbed Data / Images / Animation / Preview / 3D View.

A shared OUTPUT FOLDER row (path + Browse + Open Folder) feeds the tabs
(:mod:`al_dic_3d.gui.dialogs.export_tabs`): field-selective data serialization,
rendered per-camera field images, streaming GIF/MP4 animations, a WYSIWYG
Preview & Colorbar tab (whose colorbar/margin style ALL image/animation
exports use), and offscreen pyvista 3D-view exports. Every export action is a
plain (non-accept) button — the dialog stays open — runs on its tab's own
worker thread with cooperative cancel, and mints a FRESH timestamp per click
so repeats never overwrite.

The :class:`~al_dic_3d.export.render.VizExportHint` snapshot (constructed at
BOTH call sites: the main right sidebar and the strain window) prefills
colormap / opacity / deformed mode / current field so the export opens showing
what the user was looking at.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.export import VizExportHint, make_prefix, make_timestamp
from al_dic_3d.gui.dialogs.export_tabs import (
    AnimationTab,
    DataTab,
    ImagesTab,
    PreviewTab,
    View3DTab,
)

if TYPE_CHECKING:
    from al_dic_3d.export import ColorbarStyle
    from al_dic_3d.project.draft import ProjectDraft
    from al_dic_3d.runner import RunResult

# Draft knobs recorded in the always-written parameters JSON (scalar fields
# only; arrays/sequences are summarised by the run's own meta instead).
_DRAFT_PARAM_FIELDS = (
    "strategy",
    "reference_mode",
    "winsize",
    "winstepsize",
    "winsize_min",
    "stereo_search",
    "fft_search",
    "use_global_step",
    "admm_max_iter",
    "quality_gate",
    "refine_inner",
    "refine_outer",
    "refinement_level",
    "strain_size",
    "calibration_file",
    "roi",
)


def draft_export_params(draft: ProjectDraft) -> dict:
    """The GUI draft's matching parameters, for :func:`export_params` extra."""
    return {name: getattr(draft, name) for name in _DRAFT_PARAM_FIELDS}


class ExportDialog(QDialog):
    """Field-selective data + rendered-media export of a completed run."""

    def __init__(
        self,
        result: RunResult,
        extra_params: dict | None = None,
        parent: QWidget | None = None,
        *,
        draft: ProjectDraft | None = None,
        hint: VizExportHint | None = None,
    ) -> None:
        super().__init__(parent)
        self.result = result
        self.extra_params = extra_params or {}
        self.draft = draft
        self.hint = hint if hint is not None else VizExportHint()
        self.setWindowTitle(self.tr("Export Results"))
        self.setMinimumWidth(640)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # ---- shared OUTPUT FOLDER row ----
        layout.addWidget(self._section_label(self.tr("OUTPUT FOLDER")))
        folder_row = QHBoxLayout()
        self._folder_edit = QLineEdit()
        self._folder_edit.setPlaceholderText(self.tr("Select output folder…"))
        folder_row.addWidget(self._folder_edit, stretch=1)
        browse_btn = QPushButton(self.tr("Browse…"))
        browse_btn.setToolTip(self.tr("Choose the folder all exports are written into"))
        browse_btn.clicked.connect(self._on_browse)
        folder_row.addWidget(browse_btn)
        self._open_btn = QPushButton(self.tr("Open Folder"))
        self._open_btn.setToolTip(self.tr("Open the output folder in the file explorer"))
        self._open_btn.clicked.connect(self._on_open_folder)
        folder_row.addWidget(self._open_btn)
        layout.addLayout(folder_row)

        # ---- tabs ----
        self._tabs = QTabWidget()
        self._data_tab = DataTab(self)
        self._images_tab = ImagesTab(self)
        self._animation_tab = AnimationTab(self)
        self._preview_tab = PreviewTab(self)  # after Images/Animation: reads their rows
        self._view3d_tab = View3DTab(self)
        self._tabs.addTab(self._data_tab, self.tr("Data"))
        self._tabs.addTab(self._images_tab, self.tr("Images"))
        self._tabs.addTab(self._animation_tab, self.tr("Animation"))
        self._tabs.addTab(self._preview_tab, self.tr("Preview & Colorbar"))
        self._tabs.addTab(self._view3d_tab, self.tr("3D View"))
        for idx, tip in enumerate(
            (
                self.tr(
                    "Numeric results: field-selective NPZ / MAT / CSV tables "
                    "plus PLY / VTU meshes for external tools."
                ),
                self.tr(
                    "Rendered per-camera field overlays as PNG images, one per "
                    "frame, using the Preview & Colorbar style."
                ),
                self.tr(
                    "GIF / MP4 animations of the field overlay across frames, "
                    "using the Preview & Colorbar style."
                ),
                self.tr(
                    "WYSIWYG style source: the colorbar and margins configured "
                    "here are used by every Images / Animation export."
                ),
                self.tr(
                    "Offscreen renders of the 3D surface view (camera frusta "
                    "included) as images or turntable animations."
                ),
            )
        ):
            self._tabs.setTabToolTip(idx, tip)
        self._tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self._tabs, stretch=1)

        # ---- close ----
        buttons = QHBoxLayout()
        buttons.addStretch()
        close_btn = QPushButton(self.tr("Close"))
        close_btn.setFixedHeight(32)
        # G3.12: route through close() (NOT accept/done) so closeEvent always
        # runs — it owns the running-export guard and the worker shutdown.
        close_btn.clicked.connect(self.close)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

    # ---- shared context consumed by the tabs -------------------------------------

    @property
    def image_files(self) -> dict[str, list[str]]:
        """Camera id -> background image paths (empty lists without a draft)."""
        if self.draft is None:
            return {"L": [], "R": []}
        return {"L": list(self.draft.left), "R": list(self.draft.right)}

    @property
    def mesh_step(self) -> int:
        return int(self.draft.winstepsize) if self.draft is not None else 16

    @property
    def roi_mask(self) -> np.ndarray | None:
        """Drawn LEFT reference ROI mask as bool, or None."""
        if self.draft is None or self.draft.roi_mask_array is None:
            return None
        return np.asarray(self.draft.roi_mask_array) > 0

    def export_target(self) -> tuple[Path, str, str] | None:
        """(folder, prefix, FRESH timestamp) for one export click, or None."""
        folder = self._folder_edit.text().strip()
        if not folder:
            return None
        base_dir = self.result.meta.get("base_dir")
        prefix = make_prefix(Path(base_dir) if base_dir else None)
        return Path(folder), prefix, make_timestamp()

    # ---- shared colorbar/margin style (Preview & Colorbar tab = source) ----------

    def colorbar_style(self) -> ColorbarStyle:
        """The style every Images / Animation export uses (WYSIWYG preview)."""
        return self._preview_tab.colorbar_style()

    def margin_ratio(self) -> float:
        return self._preview_tab.margin_ratio()

    def margin_color(self) -> str:
        return self._preview_tab.margin_color()

    def _on_tab_changed(self, index: int) -> None:
        if self._tabs.widget(index) is self._preview_tab:
            self._preview_tab.activate()

    # ---- Batch-E1 compatibility surface (tests + callers) -------------------------

    @property
    def _npz_cb(self):
        return self._data_tab._npz_cb

    @property
    def _mat_cb(self):
        return self._data_tab._mat_cb

    @property
    def _csv_cb(self):
        return self._data_tab._csv_cb

    @property
    def _ply_cb(self):
        return self._data_tab._ply_cb

    @property
    def _vtu_cb(self):
        return self._data_tab._vtu_cb

    @property
    def _status(self):
        return self._data_tab.status_label

    def selected_fields(self) -> list[str]:
        return self._data_tab.selected_fields()

    def _on_export(self) -> None:
        """Trigger the Data tab export (kept for the E1 entry-point name)."""
        self._data_tab.start_export()

    # ---- worker lifecycle ----------------------------------------------------------

    def _all_tabs(self):
        # PreviewTab duck-types the worker surface (is_busy/shutdown/_worker).
        return (
            self._data_tab,
            self._images_tab,
            self._animation_tab,
            self._preview_tab,
            self._view3d_tab,
        )

    def wait_for_export(self, timeout_ms: int = 120_000) -> bool:
        """Join all running tab workers, pumping queued signals (tests)."""
        import time

        deadline = time.monotonic() + timeout_ms / 1000.0
        while any(tab.is_busy() for tab in self._all_tabs()):
            QCoreApplication.processEvents()
            if time.monotonic() > deadline:
                return False
            for tab in self._all_tabs():
                worker = tab._worker
                if worker is not None:
                    worker.wait(50)
        # Fully join every worker (``isRunning()`` can drop a beat before the
        # native thread is joinable) so no worker thread outlives this call,
        # THEN pump once more to deliver the queued finished_ok/failed slots.
        for tab in self._all_tabs():
            worker = tab._worker
            if worker is not None:
                worker.wait()
        QCoreApplication.processEvents()
        return True

    def reject(self) -> None:  # noqa: D102 - Qt override (Esc key)
        # Esc would otherwise call done() directly, skipping closeEvent's
        # running-export guard and worker shutdown (G3.12).
        self.close()

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        # G3.12 close guard (G1 idiom): never silently kill a running export.
        if any(tab.is_busy() for tab in self._all_tabs()):
            if not self._confirm_close_during_export():
                event.ignore()
                return
        for tab in self._all_tabs():
            tab.shutdown()
        super().closeEvent(event)

    def _confirm_close_during_export(self) -> bool:
        """Yes/No prompt when closing while an export runs (stubbed in tests)."""
        from PySide6.QtWidgets import QMessageBox

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(self.tr("Export Running"))
        box.setText(self.tr("An export is still running — cancel it and close?"))
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)
        box.button(QMessageBox.StandardButton.Yes).setText(self.tr("Yes"))
        box.button(QMessageBox.StandardButton.No).setText(self.tr("No"))
        return box.exec() == QMessageBox.StandardButton.Yes

    # ---- helpers ---------------------------------------------------------------

    def _section_label(self, text: str):
        from al_dic.gui.theme import COLORS
        from PySide6.QtWidgets import QLabel

        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {COLORS.TEXT_SECONDARY}; font-size: 11px; "
            f"font-weight: bold; letter-spacing: 1px;"
        )
        return lbl

    # ---- actions ----------------------------------------------------------------

    def _on_browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, self.tr("Choose output folder"))
        if folder:
            self._folder_edit.setText(folder)

    def _on_open_folder(self) -> None:
        folder = self._folder_edit.text().strip()
        if not folder:
            return
        if not Path(folder).is_dir():
            # G1.6: os.startfile raises on a nonexistent path — report on the
            # current tab's status row instead of crashing the dialog.
            tab = self._tabs.currentWidget()
            progress = getattr(tab, "_progress", None) or self._data_tab._progress
            progress.finish(self.tr("Folder does not exist: {0}").format(folder), ok=False)
            return
        import os

        os.startfile(folder)  # noqa: S606 - open the user's own folder
