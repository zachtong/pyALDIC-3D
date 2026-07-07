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

        # ROI draw toggle <-> canvas rubber-band mode; a completed drawing
        # releases the toggle (2D toolbar deactivate idiom).
        self._left.roi_draw_button.toggled.connect(self._canvas_area.set_roi_edit_mode)
        self._canvas_area.canvas.roi_changed.connect(
            lambda _roi: self._left.roi_draw_button.setChecked(False)
        )

        # Refinement brush toggle — mutually exclusive with ROI drawing (both
        # claim the left mouse button on the canvas).
        self._left.brush_button.toggled.connect(self._on_brush_toggled)
        self._left.roi_draw_button.toggled.connect(
            lambda on: on and self._left.brush_button.setChecked(False)
        )
        self._left.brush_clear_button.clicked.connect(self._canvas_area.clear_brush)

        self._build_menu()
        self.signals.log.emit("pyALDIC-3D ready", "info")

    def _on_brush_toggled(self, active: bool) -> None:
        if active:
            self._left.roi_draw_button.setChecked(False)
        self._canvas_area.set_brush_mode(active)

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
