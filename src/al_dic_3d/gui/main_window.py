"""``MainWindow3D`` — three-column main window (2D UX grammar, 3D content).

Left sidebar (import / calibration / workflow / ROI / parameters) | central
canvas (frames + result overlays + playback) | right sidebar (run / progress /
field / visualization / log) — the same layout language as the 2D app so users
transfer with zero learning cost, over the 3D backend (``WorkflowController`` /
``ProjectDraft`` / ``RunResult``).
"""

from __future__ import annotations

from al_dic.gui.window_chrome import enable_dark_title_bar
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QMainWindow, QWidget

from al_dic_3d.gui.controller import WorkflowController
from al_dic_3d.gui.panels.canvas_area import CanvasArea3D
from al_dic_3d.gui.panels.left_sidebar import LeftSidebar3D
from al_dic_3d.gui.panels.right_sidebar import RightSidebar3D
from al_dic_3d.gui.state import GuiSignals


class MainWindow3D(QMainWindow):
    """Left sidebar | canvas | right sidebar."""

    def __init__(
        self, controller: WorkflowController | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.controller = controller or WorkflowController()
        self.signals = GuiSignals()
        self._strain_window = None  # lazy singleton (Batch C post-processing)
        self.setWindowTitle(self.tr("pyALDIC-3D"))
        self.setMinimumSize(1420, 800)
        enable_dark_title_bar(self)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._left = LeftSidebar3D(self.controller, self.signals)
        layout.addWidget(self._left, stretch=0)

        self._canvas_area = CanvasArea3D(self.controller, self.signals)
        layout.addWidget(self._canvas_area, stretch=1)

        self._right = RightSidebar3D(self.controller, self.signals)
        layout.addWidget(self._right, stretch=0)

        # ROI toolbox <-> canvas drawing tools (2D toolbar idiom): a shape
        # selection arms a one-shot canvas tool; the commit/cancel resets the
        # toolbar highlight via drawing_finished. The "+ Refine" menu drives
        # the freehand refinement brush on the same canvas.
        toolbar = self._left.roi_toolbar
        toolbar.draw_requested.connect(self._on_roi_draw_requested)
        toolbar.clear_requested.connect(self._canvas_area.roi_clear)
        toolbar.invert_requested.connect(self._canvas_area.roi_invert)
        toolbar.import_requested.connect(self._canvas_area.roi_import)
        toolbar.save_requested.connect(self._canvas_area.roi_save)
        toolbar.brush_requested.connect(self._on_brush_requested)
        toolbar.brush_radius_changed.connect(self._canvas_area.set_brush_radius)
        toolbar.brush_clear_requested.connect(self._canvas_area.clear_brush)
        self._canvas_area.canvas.drawing_finished.connect(toolbar.deactivate)

        # INITIAL GUESS (F2): the "Place point…" toggle arms the one-shot seed
        # click tool on the canvas; commit / Esc resets the toggle through
        # drawing_finished (same lifecycle as the ROI shape tools).
        init_w = self._left.init_guess_widget
        init_w.place_seed_toggled.connect(self._on_place_seed_toggled)
        init_w.clear_seed_requested.connect(self._canvas_area.clear_seed)
        self._canvas_area.canvas.drawing_finished.connect(
            lambda: init_w.set_seed_mode_active(False, emit=False)
        )

        # Strain window lifecycle: the sidebar button opens/raises it, and a
        # completed run auto-opens it (2D idiom — non-modal, zero friction).
        self._right.open_strain_window_requested.connect(self._open_strain_window)
        self.signals.run_state_changed.connect(self._on_run_state_changed)

        self._build_menu()
        self.signals.log.emit("pyALDIC-3D ready", "info")

    # ---- strain window (lazy singleton) -----------------------------------------

    def _open_strain_window(self) -> None:
        """Show the strain post-processing window; refuse (and log) without results."""
        if not self.controller.state.has_results:
            self.signals.log.emit("run an analysis first — no results to post-process", "warning")
            return
        if self._strain_window is None:
            from al_dic_3d.gui.strain_window import StrainWindow3D

            self._strain_window = StrainWindow3D(self.controller, self.signals, parent=None)
        self._strain_window.show()
        self._strain_window.raise_()
        self._strain_window.activateWindow()

    def _on_run_state_changed(self, new_state: str) -> None:
        """Auto-open the strain window when a run completes (2D auto-open idiom)."""
        if new_state == "done" and self.controller.state.has_results:
            self._open_strain_window()

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        # Cascade close: the strain window is a parentless top-level we own, so
        # it must close with the main window to keep lifecycle parity.
        if self._strain_window is not None:
            self._strain_window.close()
            self._strain_window = None
        super().closeEvent(event)

    def _on_roi_draw_requested(self, shape: str, mode: str) -> None:
        if not self._canvas_area.canvas.has_image:
            self.signals.log.emit(
                "load images first before drawing a Region of Interest", "warning"
            )
            self._left.roi_toolbar.deactivate()
            return
        self._canvas_area.start_shape_tool(shape, mode)

    def _on_place_seed_toggled(self, active: bool) -> None:
        if not active:
            self._canvas_area.cancel_seed_tool()
            return
        if not self._canvas_area.canvas.has_image:
            self.signals.log.emit("load images first before placing a starting point", "warning")
            self._left.init_guess_widget.set_seed_mode_active(False, emit=False)
            return
        # The seed lives on the LEFT camera, frame 1 — jump there so the click
        # lands on the reference view (2D init_mode_user_changed idiom).
        draft = self.controller.state.draft
        self.signals.set_camera("L")
        self.signals.set_current_frame(0, max(len(draft.left), 1))
        self._canvas_area.start_seed_tool()

    def _on_brush_requested(self, mode: str, radius: int) -> None:
        if not self._canvas_area.canvas.has_image:
            self.signals.log.emit("load images first before using the brush", "warning")
            self._left.roi_toolbar.deactivate()
            return
        self._canvas_area.set_refine_brush(mode, radius)

    # ---- menu ----------------------------------------------------------------

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu(self.tr("&File"))

        new_action = QAction(self.tr("New Project"), self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)

        open_action = QAction(self.tr("Open Project…"), self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)

        save_action = QAction(self.tr("Save Project…"), self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._save_project)
        file_menu.addAction(save_action)

        file_menu.addSeparator()
        quit_action = QAction(self.tr("Quit"), self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Settings > Language (8-locale contract; catalogs compile via tools/i18n.py).
        settings_menu = self.menuBar().addMenu(self.tr("&Settings"))
        language_menu = settings_menu.addMenu(self.tr("Language"))
        from al_dic_3d.i18n import LOCALES

        names = {
            "en": "English",
            "zh_CN": "简体中文",
            "zh_TW": "繁體中文",
            "ja": "日本語",
            "ko": "한국어",
            "de": "Deutsch",
            "fr": "Français",
            "es": "Español",
        }
        from PySide6.QtCore import QSettings

        current = str(QSettings("pyALDIC", "pyALDIC-3D").value("language", "en"))
        for code in LOCALES:
            act = QAction(names.get(code, code), self)
            act.setCheckable(True)
            act.setChecked(code == current)
            act.triggered.connect(lambda _c=False, code=code: self._on_language(code))
            language_menu.addAction(act)

    def _on_language(self, code: str) -> None:
        """Persist the language preference; applied on next launch (2D phase-1 strategy)."""
        from PySide6.QtCore import QSettings

        QSettings("pyALDIC", "pyALDIC-3D").setValue("language", code)
        self.signals.log.emit(f"language preference: {code} (applies on restart)", "info")

    # ---- project lifecycle -------------------------------------------------------

    def _resync_all(self) -> None:
        """Full view resync after new/open project."""
        self._left.refresh_all()
        self.signals.images_changed.emit()
        self.signals.roi_changed.emit()
        self.signals.params_changed.emit()
        if self.controller.state.has_results:
            self.signals.results_changed.emit()
        self._right.refresh_readiness()

    def _new_project(self) -> None:
        self.controller.new_project()
        self.signals.set_run_state("idle")
        self._resync_all()
        self.signals.log.emit("new project", "info")

    def _open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Open Project"), "", self.tr("pyALDIC-3D project (*.aldic3d)")
        )
        if not path:
            return
        try:
            self.controller.open_project(path)
        except Exception as exc:  # noqa: BLE001 - surface load errors to the user
            self.signals.log.emit(f"open failed: {exc}", "error")
            return
        self._resync_all()
        self.signals.log.emit(f"opened {path}", "success")

    def _save_project(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save Project"),
            "project.aldic3d",
            self.tr("pyALDIC-3D project (*.aldic3d)"),
        )
        if not path:
            return
        self.controller.save_project(path)
        self.signals.log.emit(f"saved {path}", "success")
