"""``MainWindow3D`` — three-column main window (2D UX grammar, 3D content).

Left sidebar (import / calibration / workflow / ROI / parameters) | central
canvas (frames + result overlays + playback) | right sidebar (run / progress /
field / visualization / log) — the same layout language as the 2D app so users
transfer with zero learning cost, over the 3D backend (``WorkflowController`` /
``ProjectDraft`` / ``RunResult``).
"""

from __future__ import annotations

from al_dic.gui.window_chrome import enable_dark_title_bar
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QWidget,
)

from al_dic_3d.gui import persistence
from al_dic_3d.gui.controller import WorkflowController
from al_dic_3d.gui.main_menu import MainMenuMixin
from al_dic_3d.gui.panels.canvas_area import CanvasArea3D
from al_dic_3d.gui.panels.left_sidebar import LeftSidebar3D
from al_dic_3d.gui.panels.right_sidebar import RightSidebar3D
from al_dic_3d.gui.state import GuiSignals

# G1.2: bound on joining a cancelled pipeline worker at window close. The
# stop is honoured at the next frame head, so the wait is the rest of the
# frame in flight -- seconds, or tens of seconds at 24 Mpx or during the first
# run's JIT compile. The wait keeps the GUI painting (fix batch V: it used to
# give up after 10 s and let Qt destroy the still-running QThread).
_WORKER_JOIN_TIMEOUT_MS = 180_000

# Smallest window (H5, fix batch V): fits 1366x768 laptops and 1920x1080 at
# 150 % (1280x672 logical px usable); the sidebars scroll below their natural
# height instead of squeezing their buttons.
MIN_WINDOW_SIZE = (960, 600)


def initial_window_size(avail_width: int, avail_height: int) -> tuple[int, int]:
    """Clamp the preferred 1420x860 default to the usable screen area (G1.4).

    Same pattern as the strain window's clamp: a 1366x768 laptop must get a
    window that fits fully on screen (the old fixed 1420x800 minimum could
    not), while large displays still open at the comfortable three-column
    size. The margins keep the whole frame, title bar included, on screen.
    """
    return (
        max(MIN_WINDOW_SIZE[0], min(1420, avail_width - 40)),
        max(MIN_WINDOW_SIZE[1], min(860, avail_height - 80)),
    )


class MainWindow3D(MainMenuMixin, QMainWindow):
    """Left sidebar | canvas | right sidebar."""

    def __init__(
        self, controller: WorkflowController | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.controller = controller or WorkflowController()
        self.signals = GuiSignals()
        self._strain_window = None  # lazy singleton (Batch C post-processing)
        self._strain_auto_opened = False  # G3.6: auto-open only once per session
        self._update_window_title()  # G2.8: '<project>[*] — pyALDIC-3D' + dirty star
        # G1.4 / H5: the minimum fits small laptop screens (sidebars 320+280
        # leave the canvas ~360 px); the initial size is clamped to the screen.
        self.setMinimumSize(*MIN_WINDOW_SIZE)
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is not None:
            avail = screen.availableGeometry()
            self.resize(*initial_window_size(avail.width(), avail.height()))
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
        # The 3D export frames the surface the way the 3D view shows it.
        self._right.set_view3d_camera_provider(self._canvas_area.view3d_camera)

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
        init_w.auto_place_requested.connect(self._on_auto_place_seed)
        self._canvas_area.canvas.drawing_finished.connect(
            lambda: init_w.set_seed_mode_active(False, emit=False)
        )

        # Strain window lifecycle: the sidebar button opens/raises it, and a
        # completed run auto-opens it (2D idiom — non-modal, zero friction).
        self._right.open_strain_window_requested.connect(self._open_strain_window)
        self.signals.run_state_changed.connect(self._on_run_state_changed)

        # G2.8: every mark_dirty site emits one of these signals right after,
        # so the title's modified-star tracks the state without polling.
        for sig in (
            self.signals.images_changed,
            self.signals.roi_changed,
            self.signals.params_changed,
            self.signals.calibration_changed,
            self.signals.results_changed,
        ):
            sig.connect(self._update_window_title)

        self._build_menu()
        self._build_shortcuts()
        # G3.2: the saved geometry (if any) overrides the screen-clamp default.
        persistence.restore_window_state(self, "main_window")
        self.signals.log.emit(self.tr("pyALDIC-3D ready"), "info")

    # ---- keyboard shortcuts (G2.5) ------------------------------------------------

    def _build_shortcuts(self) -> None:
        """Window-level accelerators. Frame keys (←/→/Space) go through
        keyPressEvent instead so focused widgets (spin boxes, the canvas's
        Space pan mode, buttons) keep their native key handling."""
        QShortcut(QKeySequence("F5"), self, activated=self._right._on_run)
        QShortcut(QKeySequence("Ctrl+0"), self, activated=self._canvas_area.canvas.fit_to_view)
        QShortcut(QKeySequence("Ctrl+="), self, activated=self._canvas_area.canvas.zoom_in)
        QShortcut(QKeySequence("Ctrl++"), self, activated=self._canvas_area.canvas.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, activated=self._canvas_area.canvas.zoom_out)

    def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        """←/→ = prev/next frame, Space = play/pause (G2.5).

        Reached only when the focused child did NOT consume the key, which is
        exactly the wanted guard: arrows in a spin box edit the value, Space on
        the canvas drives pan mode, Space on a button clicks it.
        """
        key = event.key()
        if key in (Qt.Key.Key_Left, Qt.Key.Key_Right):
            draft = self.controller.state.draft
            n = max(len(draft.left), len(draft.right))
            step = -1 if key == Qt.Key.Key_Left else 1
            self.signals.set_current_frame(self.signals.current_frame + step, n)
            event.accept()
            return
        if key == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._canvas_area.toggle_playback()
            event.accept()
            return
        super().keyPressEvent(event)

    # ---- strain window (lazy singleton) -----------------------------------------

    def _open_strain_window(self) -> None:
        """Show the strain post-processing window; refuse (and log) without results."""
        if not self.controller.state.has_results:
            self.signals.log.emit(
                self.tr("Run an analysis first — there are no results to post-process"), "warning"
            )
            return
        if self._strain_window is None:
            from al_dic_3d.gui.strain_window import StrainWindow3D

            self._strain_window = StrainWindow3D(self.controller, self.signals, parent=None)
        self._strain_window.show()
        self._strain_window.raise_()
        self._strain_window.activateWindow()

    def _on_run_state_changed(self, new_state: str) -> None:
        """Auto-open the strain window on the FIRST completed run only (G3.6).

        The 2D auto-open idiom, once per app session: later runs would steal
        focus mid-iteration, so they just log where to find the window.
        """
        # Fix batch V: switching projects mid-run is disabled (and guarded in the
        # handlers) — a run's result belongs to the project that started it.
        running = new_state == "running"
        for action in (getattr(self, "_new_action", None), getattr(self, "_open_action", None)):
            if action is not None:
                action.setEnabled(not running)
        if getattr(self, "_recent_menu", None) is not None:
            self._recent_menu.setEnabled(not running)
        if new_state != "done" or not self.controller.state.has_results:
            return
        if not self._strain_auto_opened:
            self._strain_auto_opened = True
            self._open_strain_window()
        else:
            self.signals.log.emit(
                self.tr("Strain window available — open it from the sidebar"), "info"
            )

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        # G1.2: never let Qt destroy a live pipeline QThread ("QThread:
        # Destroyed while thread is still running") — ask first, then cancel
        # and join under a busy cursor before the window may go.
        if getattr(self, "_closing", False):
            event.ignore()  # a second close request while the run is stopping
            return
        worker = self._right.active_worker()
        if worker is not None and not self._confirm_cancel_run():
            event.ignore()
            return
        # G3.12: a non-modal export dialog may hold live export workers — close
        # it through its own guard (prompts if an export is still running).
        if not self._right.close_export_dialog():
            event.ignore()
            return
        # G1.1: unsaved-changes guard (Save / Discard / Cancel).
        if not self._confirm_unsaved():
            event.ignore()
            return
        # Only now is the close certain (fix batch V, M7): cancelling the
        # unsaved-changes prompt used to leave the app open with the run
        # already stopped.
        if worker is not None:
            worker.request_stop()
            self._closing = True
            try:
                self._join_worker(worker)
            finally:
                self._closing = False
        # Cascade close: the strain window is a parentless top-level we own, so
        # it must close with the main window to keep lifecycle parity. Join its
        # compute worker first so its own closeEvent never re-prompts (G1.2).
        if self._strain_window is not None:
            self._strain_window.join_worker()
            self._strain_window.close()
            self._strain_window = None
        persistence.save_window_state(self, "main_window")  # G3.2
        super().closeEvent(event)

    @staticmethod
    def _join_worker(worker) -> None:
        """Wait for a stopping worker under a busy cursor, GUI still painting (G1.2)."""
        import time

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        deadline = time.monotonic() + _WORKER_JOIN_TIMEOUT_MS / 1000.0
        try:
            while not worker.wait(100) and time.monotonic() < deadline:
                QApplication.processEvents()
        finally:
            QApplication.restoreOverrideCursor()

    # ---- close / discard guards (G1.1 / G1.2) ----------------------------------

    def _confirm_cancel_run(self) -> bool:
        """Yes/No prompt before killing a running analysis on close (G1.2)."""
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(self.tr("Analysis Running"))
        box.setText(self.tr("An analysis is running — cancel it and quit?"))
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)
        # Qt's own qtbase button catalogs are not shipped — set the texts
        # explicitly so the 8-locale contract covers the buttons too.
        box.button(QMessageBox.StandardButton.Yes).setText(self.tr("Yes"))
        box.button(QMessageBox.StandardButton.No).setText(self.tr("No"))
        return box.exec() == QMessageBox.StandardButton.Yes

    def _show_error(self, title: str, message: str) -> None:
        """Modal error box (fix batch V: failures were log-only). Stubbed in tests."""
        QMessageBox.critical(self, title, message)

    def _confirm_cancel_run_for_switch(self) -> bool:
        """Yes/No prompt before cancelling a run to switch projects (fix batch V)."""
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(self.tr("Analysis Running"))
        box.setText(self.tr("An analysis is running — cancel it and switch projects?"))
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)
        box.button(QMessageBox.StandardButton.Yes).setText(self.tr("Yes"))
        box.button(QMessageBox.StandardButton.No).setText(self.tr("No"))
        return box.exec() == QMessageBox.StandardButton.Yes

    def _stop_run_before_switch(self) -> bool:
        """True when no run is active, or the user agreed and it was stopped."""
        worker = self._right.active_worker()
        if worker is None:
            return True
        if not self._confirm_cancel_run_for_switch():
            return False
        worker.request_stop()
        self._join_worker(worker)
        QApplication.processEvents()  # deliver the worker's cancelled/done slots
        return self._right.active_worker() is None

    def _confirm_unsaved(self) -> bool:
        """True = proceed (clean, saved, or discarded); False = abort (G1.1)."""
        state = self.controller.state
        worth_saving = bool(state.draft.left or state.draft.right or state.has_results)
        if not (state.dirty and worth_saving):
            return True
        choice = self._prompt_unsaved()
        if choice == "save":
            return self._save_project()
        return choice == "discard"

    def _prompt_unsaved(self) -> str:
        """Modal Save / Discard / Cancel prompt (split out so tests can stub it)."""
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(self.tr("Unsaved Changes"))
        box.setText(self.tr("The project has unsaved changes. Save them before continuing?"))
        box.setStandardButtons(
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel
        )
        box.setDefaultButton(QMessageBox.StandardButton.Save)
        box.button(QMessageBox.StandardButton.Save).setText(self.tr("Save"))
        box.button(QMessageBox.StandardButton.Discard).setText(self.tr("Discard"))
        box.button(QMessageBox.StandardButton.Cancel).setText(self.tr("Cancel"))
        ret = box.exec()
        if ret == QMessageBox.StandardButton.Save:
            return "save"
        return "discard" if ret == QMessageBox.StandardButton.Discard else "cancel"

    # ---- ROI tools -------------------------------------------------------------

    def _ensure_roi_reference_view(self) -> None:
        """G1.3: ROI edits land on the LEFT frame-1 mask — jump the view there.

        Same idiom as seed placement: arming a shape tool or the refine brush
        while viewing the RIGHT camera or a later frame would silently stamp
        the drawn region onto the wrong image (the mask always belongs to the
        left camera, frame 1).
        """
        if self.signals.current_camera == "L" and self.signals.current_frame == 0:
            return
        draft = self.controller.state.draft
        self.signals.set_camera("L")
        self.signals.set_current_frame(0, max(len(draft.left), 1))
        self.signals.log.emit(self.tr("Switched to left camera, frame 1 for ROI editing"), "info")

    def _on_roi_draw_requested(self, shape: str, mode: str) -> None:
        if not self._canvas_area.canvas.has_image:
            self.signals.log.emit(
                self.tr("Load images first, then draw the region of interest"), "warning"
            )
            self._left.roi_toolbar.deactivate()
            return
        self._ensure_roi_reference_view()
        self._canvas_area.start_shape_tool(shape, mode)

    def _on_place_seed_toggled(self, active: bool) -> None:
        if not active:
            self._canvas_area.cancel_seed_tool()
            return
        if not self._canvas_area.canvas.has_image:
            self.signals.log.emit(
                self.tr("Load images first, then place a starting point"), "warning"
            )
            self._left.init_guess_widget.set_seed_mode_active(False, emit=False)
            return
        # The seed lives on the LEFT camera, frame 1 — jump there so the click
        # lands on the reference view (2D init_mode_user_changed idiom).
        draft = self.controller.state.draft
        self.signals.set_camera("L")
        self.signals.set_current_frame(0, max(len(draft.left), 1))
        self._canvas_area.start_seed_tool()

    def _on_auto_place_seed(self) -> None:
        """Place one Starting Point deep inside the ROI (fix batch V, H2)."""
        from al_dic_3d.matching.seed import central_seed_point

        draft = self.controller.state.draft
        if draft.seed_points:
            self.signals.log.emit(
                self.tr("Starting points are already placed; clear them to auto-place"), "info"
            )
            return
        point = central_seed_point(draft.roi, getattr(draft, "roi_mask_array", None))
        if point is None:
            self.signals.log.emit(
                self.tr("Draw the ROI first: the point is placed inside it"), "warning"
            )
            return
        draft.seed_points = [point]
        draft.seed_point = point
        self.controller.state.mark_dirty()
        self.signals.log.emit(
            self.tr("Starting point placed automatically at ({0:.0f}, {1:.0f})").format(*point),
            "info",
        )
        self._canvas_area._sync_seed_marker()
        self.signals.params_changed.emit()

    def _on_brush_requested(self, mode: str, radius: int) -> None:
        if not self._canvas_area.canvas.has_image:
            self.signals.log.emit(self.tr("Load images first, then use the brush"), "warning")
            self._left.roi_toolbar.deactivate()
            return
        self._ensure_roi_reference_view()
        self._canvas_area.set_refine_brush(mode, radius)

    # ---- menu ----------------------------------------------------------------

    # ---- project lifecycle -------------------------------------------------------

    def _update_window_title(self) -> None:
        """G2.8: '<project file>[*] — pyALDIC-3D'; the star shows unsaved work.

        Qt substitutes the ``[*]`` placeholder with '*' when
        ``isWindowModified()`` is true and removes it otherwise.
        """
        state = self.controller.state
        name = state.project_path.name if state.project_path else self.tr("Untitled")
        self.setWindowTitle(self.tr("{0}[*] — pyALDIC-3D").format(name))
        self.setWindowModified(bool(state.dirty))

    def _resync_all(self) -> None:
        """Full view resync after new/open project."""
        self._left.refresh_all()
        self.signals.images_changed.emit()
        self.signals.roi_changed.emit()
        self.signals.params_changed.emit()
        # G3.10: restore the saved display state (field/colormap/range/camera…)
        # BEFORE results_changed so the first result render uses it.
        view_state = self.controller.state.view_state
        if view_state:
            from al_dic_3d.gui.view_state import apply_to_canvas

            draft = self.controller.state.draft
            self._right.apply_view_state(view_state, max(len(draft.left), len(draft.right)))
            # Z2: the canvas toolbar toggles (Show Grid / Show Subset / 3D View),
            # applied after the sidebar so the 3D page — if that was the saved
            # view — renders with the restored field and colormap.
            apply_to_canvas(self._canvas_area, view_state)
        if self.controller.state.has_results:
            self.signals.results_changed.emit()
        self._right.refresh_readiness()

    def _capture_view_state(self) -> dict:
        """Snapshot the display state for persistence (G3.10 / Z2).

        Single-sourced in :func:`al_dic_3d.gui.view_state.capture` (keys =
        ``VIEW_STATE_KEYS``) so the save side cannot drift away from the restore
        side in ``_resync_all``.
        """
        from al_dic_3d.gui.view_state import capture

        return capture(self.signals, self._canvas_area)

    def _new_project(self) -> None:
        if not self._stop_run_before_switch():
            return
        if not self._confirm_unsaved():  # G1.1: dirty work is never silently dropped
            return
        self.controller.new_project()  # fresh AppState3D: dirty is False again
        self.signals.set_run_state("idle")
        self._resync_all()
        self._update_window_title()
        self.signals.log.emit(self.tr("New project"), "info")

    def _open_project(self) -> None:
        if not self._stop_run_before_switch():
            return
        if not self._confirm_unsaved():  # G1.1: dirty work is never silently dropped
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Open Project"),
            persistence.last_dir("project"),  # G3.2
            self.tr("pyALDIC-3D project (*.aldic3d)"),
        )
        if not path:
            return
        self._open_project_path(path)

    def _open_project_path(self, path: str) -> None:
        """Load ``path`` (Open dialog or Recent menu); caller handled G1.1."""
        # P2.5: parse + array reconstruction run on a worker behind a modal
        # progress dialog; the loaded state is applied HERE on the GUI thread.
        from al_dic_3d.gui.workers import run_with_progress
        from al_dic_3d.project.session import load_session

        ok, out = run_with_progress(self, self.tr("Loading project…"), lambda: load_session(path))
        if not ok:
            self.signals.log.emit(self.tr("Could not open the project: {0}").format(out), "error")
            self._show_error(
                self.tr("Open Project"),
                self.tr("Could not open the project:\n{0}\n\n{1}").format(path, out),
            )
            return
        # R1.1: relocate moved image sequences BEFORE adopting the state so a
        # cancelled locate-prompt leaves the current project untouched.
        if not self._relocate_session_images(out, path):
            return
        self.controller.adopt_state(out)  # loaded state: dirty only if relocated
        persistence.add_recent_project(path)  # G3.2
        persistence.set_last_dir("project", path)
        self._resync_all()
        self._update_window_title()
        self.signals.log.emit(self.tr("Opened {0}").format(path), "success")

    def _relocate_session_images(self, state, path: str) -> bool:
        """R1.1: auto-relocate moved images (prompting as last resort).

        Rewrites ``state.draft`` in place and marks the state dirty so the next
        save persists the corrected paths. False = the user cancelled the
        locate prompt — the caller must abort the open.
        """
        from al_dic_3d.project.relocate import (
            RelocationCancelled,
            relocate_calibration,
            relocate_draft_images,
        )

        try:
            moves = relocate_draft_images(
                state.draft, path, locate_dir_cb=self._prompt_locate_images
            )
        except RelocationCancelled as exc:
            # Fix batch V (M8): results stay viewable and exportable without
            # the images, so offer to open anyway instead of refusing outright.
            if not self._confirm_open_without_images():
                self.signals.log.emit(self.tr("Open cancelled: {0}").format(exc), "warn")
                return False
            moves = relocate_draft_images(state.draft, path, None, allow_missing=True)
        for m in moves:
            if m.new_dir is None:
                self.signals.log.emit(
                    self.tr(
                        "Camera {0}: {1} image(s) not found (was {2}). Results stay "
                        "viewable and exportable; running again needs the images."
                    ).format(m.camera, m.n_files, m.old_dir),
                    "warn",
                )
            else:
                self.signals.log.emit(
                    self.tr("Relocated {0} camera-{1} images: {2} -> {3}").format(
                        m.n_files, m.camera, m.old_dir, m.new_dir
                    ),
                    "info",
                )
        calib = relocate_calibration(state.draft, path)
        if calib is not None:
            self.signals.log.emit(self.tr("Calibration file found at {0}").format(calib), "info")
        for note in getattr(state, "open_notes", []):
            prefix = "calibration restored from the project file: "
            if note.startswith(prefix):
                note = self.tr(
                    "The calibration file was not found; using the copy saved in the project: {0}"
                ).format(note[len(prefix) :])
            self.signals.log.emit(note, "info")
        if any(m.new_dir is not None for m in moves) or calib is not None:
            state.mark_dirty()  # the rewritten draft should reach the next save
        return True

    def _confirm_open_without_images(self) -> bool:
        """Yes/No: open a project whose images cannot be found (stubbed in tests)."""
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(self.tr("Images Not Found"))
        box.setText(
            self.tr(
                "Some of this project's images cannot be found. Open it anyway? "
                "Results stay viewable and exportable; running again needs the images."
            )
        )
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.Yes)
        box.button(QMessageBox.StandardButton.Yes).setText(self.tr("Open anyway"))
        box.button(QMessageBox.StandardButton.No).setText(self.tr("Cancel"))
        return box.exec() == QMessageBox.StandardButton.Yes

    def _prompt_locate_images(self, camera: str, old_dir: str, is_retry: bool) -> str | None:
        """Directory picker for images that could not be auto-relocated (R1.1)."""
        if is_retry:
            QMessageBox.warning(
                self,
                self.tr("Locate Images"),
                self.tr(
                    "The selected folder does not contain this project's "
                    "camera {0} frames. Pick the folder holding the original "
                    "image files, or cancel to abort opening."
                ).format(camera),
            )
        else:
            QMessageBox.information(
                self,
                self.tr("Locate Images"),
                self.tr(
                    "The image folder saved with this project was not found:\n"
                    "{0}\n\nSelect the folder that now contains the camera {1} "
                    "frames (file names must match)."
                ).format(old_dir, camera),
            )
        folder = QFileDialog.getExistingDirectory(
            self,
            self.tr("Locate images for camera {0}").format(camera),
            persistence.last_dir("images"),
        )
        if folder:
            persistence.set_last_dir("images", folder)
        return folder or None

    def _save_project(self) -> bool:
        """G2.8 Save (Ctrl+S): write to the bound project file, no dialog.

        Falls through to Save As when the project has never been saved.
        False = cancelled or failed (the G1.1 close guard relies on this).
        """
        path = self.controller.state.project_path
        if path is None:
            return self._save_project_as()
        return self._write_project(path)

    def _save_project_as(self) -> bool:
        """Save As (Ctrl+Shift+S): always ask for a target file."""
        from pathlib import Path

        start_dir = persistence.last_dir("project")  # G3.2
        suggested = str(Path(start_dir) / "project.aldic3d") if start_dir else "project.aldic3d"
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save Project"),
            suggested,
            self.tr("pyALDIC-3D project (*.aldic3d)"),
        )
        if not path:
            return False
        return self._write_project(path)

    def _prompt_include_results(self, estimate: str) -> str:
        """Q7 modal Yes/No/Cancel: include the computed results in the save?

        Split out so offscreen tests can stub it (conftest pattern). Returns
        "yes" | "no" | "cancel".
        """
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle(self.tr("Include Results?"))
        box.setText(self.tr("Include the analysis results in this project file?"))
        box.setInformativeText(
            self.tr(
                "Including results (about {0} uncompressed) lets you reopen "
                "the project without recomputing. Choose No to save a small "
                "configuration-only file for sharing."
            ).format(estimate)
        )
        box.setStandardButtons(
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel
        )
        box.setDefaultButton(QMessageBox.StandardButton.Yes)
        box.button(QMessageBox.StandardButton.Yes).setText(self.tr("Yes"))
        box.button(QMessageBox.StandardButton.No).setText(self.tr("No"))
        box.button(QMessageBox.StandardButton.Cancel).setText(self.tr("Cancel"))
        ret = box.exec()
        if ret == QMessageBox.StandardButton.Yes:
            return "yes"
        return "no" if ret == QMessageBox.StandardButton.No else "cancel"

    def _write_project(self, path) -> bool:
        """Serialize on a worker behind a modal progress dialog (P2.5).

        ``run_with_progress`` blocks with a local event loop, so this still
        RETURNS bool synchronously — the G1.1 close guard's contract. The
        application-modal dialog prevents any state mutation mid-save.
        """
        from al_dic_3d.gui.workers import run_with_progress

        # Q7: with results present, offer Yes (full) / No (config-only) /
        # Cancel before writing; the estimate is the raw array nbytes.
        include_results = True
        state = self.controller.state
        if state.result is not None:
            from al_dic_3d.project.session import estimated_result_nbytes

            try:
                est = f"{estimated_result_nbytes(state.result) / 1e6:.0f} MB"
            except Exception:  # noqa: BLE001 - the estimate is informational only
                est = self.tr("unknown size")
            choice = self._prompt_include_results(est)
            if choice == "cancel":
                return False
            include_results = choice == "yes"

        # G3.10: the display state rides along in the project file.
        self.controller.state.view_state = self._capture_view_state()
        ok, out = run_with_progress(
            self,
            self.tr("Saving project…"),
            lambda: self.controller.save_project(path, include_results=include_results),
        )
        if not ok:
            self.signals.log.emit(self.tr("Could not save the project: {0}").format(out), "error")
            self._show_error(
                self.tr("Save Project"),
                self.tr(
                    "Could not save the project:\n{0}\n\n{1}\n\n"
                    "The previous version of the file, if any, is unchanged."
                ).format(path, out),
            )
            return False
        persistence.add_recent_project(path)  # G3.2
        persistence.set_last_dir("project", path)
        self._update_window_title()  # clean now; star disappears
        self.signals.log.emit(self.tr("Saved {0}").format(path), "success")
        return True
