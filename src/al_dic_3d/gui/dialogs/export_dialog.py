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
colormap / opacity / deformed mode / current field / range so the export opens
showing what the user was looking at, and carries the canvas's display unit and
frame rate so rendered exports scale and label values like the canvas (M1).

The dialog describes the RESULT it was built for (fix batch V, H1/H3/H6): the
node step comes from the run (:func:`~al_dic_3d.export.run_mesh_step`), the
parameters JSON prefers what the run recorded, and :meth:`ExportDialog.matches`
lets the singleton owners detect a stale dialog after a rerun, a strain
recompute or a project switch and rebuild it.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

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

from al_dic_3d.export import (
    VELOCITY_ID,
    VizExportHint,
    camera_roi_masks,
    field_color_range,
    make_prefix,
    make_timestamp,
    run_mesh_step,
)
from al_dic_3d.gui.dialogs.export_tabs import (
    AnimationTab,
    DataTab,
    ImagesTab,
    PreviewTab,
    View3DTab,
)

if TYPE_CHECKING:
    from al_dic_3d.export import CameraTuple, ColorbarStyle
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
    """The GUI draft's matching parameters, for :func:`export_params` extra.

    The draft is LIVE (it may have been edited after the run): the parameters
    JSON keeps every value the run itself recorded (``result.meta`` /
    ``run_params``) and uses these only for keys the run did not record.
    """
    return {name: getattr(draft, name) for name in _DRAFT_PARAM_FIELDS}


def _camera_tuple(cam: Any) -> CameraTuple | None:
    """A pyvista camera position (or any 3x3 sequence) as plain float tuples."""
    try:
        parts = tuple(tuple(float(v) for v in part) for part in cam)
    except (TypeError, ValueError):
        return None
    if len(parts) != 3 or any(len(p) != 3 for p in parts):
        return None
    return parts  # type: ignore[return-value]


class ExportDialog(QDialog):
    """Field-selective data + rendered-media export of a completed run.

    Public surface for the singleton owners (right sidebar, strain window):
    :attr:`result` (read-only) and :meth:`matches` — rebuild the dialog when
    ``not dialog.matches(state.result)``; :meth:`is_busy` tells whether an
    export is still running. ``camera_provider`` (optional) returns the
    interactive 3D view's current camera, read at export time.
    """

    def __init__(
        self,
        result: RunResult,
        extra_params: dict | None = None,
        parent: QWidget | None = None,
        *,
        draft: ProjectDraft | None = None,
        hint: VizExportHint | None = None,
        camera_provider: Callable[[], Any] | None = None,
    ) -> None:
        super().__init__(parent)
        self._result = result
        self.extra_params = extra_params or {}
        self.draft = draft
        self.hint = hint if hint is not None else VizExportHint()
        self._camera_provider = camera_provider
        self._mask_lock = threading.Lock()
        self._roi_cache: tuple[object, np.ndarray] | None = None  # (source array, bool)
        self._right_cache: tuple[object, np.ndarray | None] | None = None
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
                    "Offscreen renders of the 3D surface as images, a deforming "
                    "animation or a turntable, from your current 3D view."
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

    # ---- the result this dialog exports (owners rebuild it when stale) --------------

    @property
    def result(self) -> RunResult:
        """The result this dialog was built for (read-only)."""
        return self._result

    def matches(self, result: object) -> bool:
        """True when this dialog exports exactly *result* (identity).

        A rerun, a strain recompute (``dataclasses.replace``) and a project
        switch all produce a NEW result object, so ``not matches(state.result)``
        means the dialog is stale and must be rebuilt.
        """
        return result is not None and result is self._result

    def is_busy(self) -> bool:
        """True while any tab's export worker is running."""
        return any(tab.is_busy() for tab in self._all_tabs())

    # ---- shared context consumed by the tabs -------------------------------------

    @property
    def image_files(self) -> dict[str, list[str]]:
        """Camera id -> background image paths (empty lists without a draft)."""
        if self.draft is None:
            return {"L": [], "R": []}
        return {"L": list(self.draft.left), "R": list(self.draft.right)}

    @property
    def mesh_step(self) -> int:
        """The node step the RESULT was computed with — never the edited draft (H3)."""
        fallback = int(self.draft.winstepsize) if self.draft is not None else 16
        return run_mesh_step(self._result, default=fallback)

    @property
    def roi_mask(self) -> np.ndarray | None:
        """Drawn LEFT reference ROI mask as bool, or None (cached per mask edit).

        Every ROI edit stores a fresh array on the draft, so the source array's
        identity keys the cache (a reference is held, so the id cannot be
        recycled). Thread-safe: the Preview worker reads it too.
        """
        drawn = None if self.draft is None else self.draft.roi_mask_array
        if drawn is None:
            return None
        with self._mask_lock:
            if self._roi_cache is None or self._roi_cache[0] is not drawn:
                self._roi_cache = (drawn, np.asarray(drawn) > 0)
            return self._roi_cache[1]

    def right_roi_mask(self, *, compute: bool = True) -> np.ndarray | None:
        """The left ROI warped into the RIGHT camera (the canvas's support, M3).

        Cached per (ROI edit, result); ``compute=False`` only returns an
        already-warped mask (the export jobs then warp in their worker thread
        instead of on the GUI thread). Thread-safe.
        """
        roi = self.roi_mask
        if roi is None:
            return None
        with self._mask_lock:
            cached = self._right_cache
            if cached is not None and cached[0] is roi:
                return cached[1]
            if not compute:
                return None
        masks, _warnings = camera_roi_masks(self._result, ("R",), roi, self.image_files)
        with self._mask_lock:
            self._right_cache = (roi, masks["R"])
        return masks["R"]

    # ---- display units (M1): what the canvas shows --------------------------------

    def field_display(self, field_id: str) -> tuple[float, str | None]:
        """(value scale, colorbar label) of a field in the canvas's display unit.

        Velocity follows the canvas: mm/frame x frame rate -> unit/s once a
        frame rate was given, per frame (labelled so) until then.
        """
        from al_dic_3d.gui.display_units import field_display_factor, field_label

        unit = self.hint.display_unit or "mm"
        scale = float(field_display_factor(field_id, unit))
        if field_id != VELOCITY_ID:
            return scale, field_label(field_id, unit)
        if self.hint.frame_rate_known:
            return scale * float(self.hint.frame_rate), field_label(field_id, unit)
        try:
            return scale, field_label(field_id, unit, per_frame=True)
        except TypeError:  # a display_units without the per-frame label
            return scale, f"|V| ({unit}/frame)"

    def seed_range(self, field_id: str) -> tuple[float, float]:
        """A starting fixed range for *field_id* (display units).

        The canvas's auto range at the hint frame; when that is empty (the
        reference frame has zero displacement) the last frame's range instead.
        """
        n_frames = int(self._result.reconstruction.n_frames)
        scale, _label = self.field_display(field_id)
        k_hint = max(0, min(int(self.hint.current_frame), n_frames - 1))
        lo, hi = 0.0, 1.0
        for k in dict.fromkeys((k_hint, n_frames - 1)):
            lo, hi = field_color_range(
                self._result,
                "L",
                field_id,
                k,
                self.roi_mask,
                deformed=bool(self.hint.show_deformed) and k > 0,
                value_scale=scale,
            )
            if hi > lo:
                break
        return lo, hi

    def view3d_camera(self) -> CameraTuple | None:
        """The interactive 3D view's camera now (provider), else the hint's snapshot."""
        if self._camera_provider is not None:
            try:
                live = self._camera_provider()
            except Exception:  # noqa: BLE001 - no 3D view: isometric default
                live = None
            cam = _camera_tuple(live) if live is not None else None
            if cam is not None:
                return cam
        snap = self.hint.view3d_camera
        return _camera_tuple(snap) if snap is not None else None

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
        if self.is_busy():
            if not self._confirm_close_during_export():
                event.ignore()
                return
        for tab in self._all_tabs():
            tab.shutdown()
        # Accept directly. QDialog.closeEvent calls reject() — overridden above
        # to call close() — and that nested close is refused while this one is
        # in flight, so the base handler IGNORED the event: Close, Esc and the
        # window X all did nothing, and the main window could not quit either
        # (fix batch V; every public release through 1.1.0 was affected).
        event.accept()

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
