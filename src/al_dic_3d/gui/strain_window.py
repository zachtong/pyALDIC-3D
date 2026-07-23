"""``StrainWindow3D`` — the strain post-processing window (2D StrainWindow clone).

Independent ``QMainWindow`` over a completed :class:`~al_dic_3d.runner.RunResult`:
runs :class:`StrainController3D` on demand and renders the strain fields as a
DENSE continuous full-field overlay on the LEFT-camera image (the strain gauge
is defined on the left/frame-1 mesh, so the left view is the natural canvas; a
camera toggle is deliberately out of scope — keep it simple). Rendering shares
:class:`VizController3D` with the main canvas, namespaced ``strain_window:<field>``
(the 2D idiom), through a PRIVATE controller instance.

Decoupling contracts (mirroring the 2D window, enforced by tests):

* Owns a PRIVATE current-frame index — never touches ``GuiSignals.current_frame``.
* Owns its own field selector / colormap / range / opacity — never reads or
  writes the main window's display state on ``GuiSignals``.
* Reads ``controller.state.result`` and writes back ONLY through
  :class:`StrainController3D` (``dataclasses.replace`` on the frozen result),
  then emits ``signals.results_changed``.

The coordinate-system control (surface tangent plane / left camera frame /
custom 3-point specimen frame) is the key 3D addition; the 3-point pick flow
arms a click mode on this window's own canvas and snaps each click to the
nearest valid node of the reference mesh.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from al_dic.gui.icons import icon_download
from al_dic.gui.theme import COLORS
from al_dic.gui.widgets.collapsible_section import CollapsibleSection
from al_dic.gui.widgets.colorbar_overlay import ColorbarOverlay
from al_dic.gui.widgets.console_log import ConsoleLog
from al_dic.gui.window_chrome import enable_dark_title_bar
from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QColor, QGuiApplication, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.gui.controllers.strain_controller import StrainController3D
from al_dic_3d.gui.controllers.viz_controller import VizController3D
from al_dic_3d.gui.state import GuiSignals
from al_dic_3d.gui.strain_render import prepare_strain_render, trim_count
from al_dic_3d.gui.widgets.strain_field_selector import (
    STRAIN_FIELD_LABELS,
    StrainFieldSelector3D,
)
from al_dic_3d.gui.widgets.strain_navigator import StrainNavigator3D
from al_dic_3d.gui.widgets.strain_param_panel import StrainParamPanel3D
from al_dic_3d.gui.widgets.strain_support import PickCanvas, StrainWorker, ZoomBar
from al_dic_3d.gui.widgets.strain_viz_panel import StrainVizPanel3D

if TYPE_CHECKING:
    from al_dic_3d.gui.controller import WorkflowController
    from al_dic_3d.strain3d.model import StrainResult3D

# Pick-marker colors for the 3-point specimen frame: Origin / +X / +Y.
_PICK_COLORS = (QColor("#3b82f6"), QColor("#ef4444"), QColor("#22c55e"))


def initial_window_size(avail_width: int, avail_height: int) -> tuple[int, int]:
    """Clamp the preferred 1280x800 default to the usable screen area.

    Same rationale as the 2D strain window: a fixed 800 px height overflows
    small laptop screens, and a window whose bottom edge opens off-screen can
    be impossible to shrink. The margins keep the whole frame on screen.
    """
    return (
        max(640, min(1280, avail_width - 40)),
        max(480, min(800, avail_height - 80)),
    )


class StrainWindow3D(QMainWindow):
    """Independent strain post-processing window (full 2D clone, 3D data)."""

    def __init__(
        self,
        controller: WorkflowController,
        signals: GuiSignals,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.controller = controller
        self.signals = signals
        self._strain_ctrl = StrainController3D(controller)
        self._worker: StrainWorker | None = None
        self._export_dialog = None  # G3.12: non-modal singleton

        # PRIVATE display state — never mirrored to GuiSignals.
        self._frame = 0
        self._viz_ctrl = VizController3D()  # private dense renderer + caches
        self._last_rendered: tuple[float, float] = (0.0, 1.0)
        self._recon_id: int | None = None  # detects a NEW run vs a strain writeback

        # 3-point specimen pick state.
        self._pick_nodes: list[int] = []
        self._pick_items: list = []  # QGraphicsItems (markers + labels)

        self.setWindowTitle(self.tr("Strain Post-Processing"))
        enable_dark_title_bar(self)
        screen = self.screen() or QGuiApplication.primaryScreen()
        avail = screen.availableGeometry()
        self.resize(*initial_window_size(avail.width(), avail.height()))
        from al_dic_3d.gui import persistence

        persistence.restore_window_state(self, "strain_window")  # G3.2

        central = QWidget(self)
        root = QHBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # ---- left pane: zoom toolbar + canvas + colorbar + navigator ----
        left = QVBoxLayout()
        left.setSpacing(0)

        self._canvas = PickCanvas()
        zoom_bar = ZoomBar(self._canvas)  # extracted toolbar (P3.5 file-size)
        self._zoom_btn = zoom_bar.zoom_btn  # historical alias
        left.addWidget(zoom_bar)
        left.addWidget(self._canvas, stretch=1)
        self._colorbar = ColorbarOverlay(self._canvas.viewport())
        self._canvas.viewport().installEventFilter(self)
        self._canvas.point_picked.connect(self._on_point_picked)

        self._nav = StrainNavigator3D()
        self._nav.frame_changed.connect(self._on_frame_nav)
        left.addWidget(self._nav)
        root.addLayout(left, 1)

        # ---- right pane: 340 px scrollable column of collapsible sections ----
        right_container = QWidget()
        right_container.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        right = QVBoxLayout(right_container)
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(6)

        self._params_section = CollapsibleSection(self.tr("STRAIN PARAMETERS"), expanded=True)
        self._param_panel = StrainParamPanel3D(winstepsize=controller.state.draft.winstepsize)
        self._param_panel.params_dirty.connect(self._on_params_dirty)
        self._param_panel.pick_requested.connect(self._start_pick)
        self._params_section.add_widget(self._param_panel)
        right.addWidget(self._params_section)

        # Action buttons stay OUTSIDE collapsible sections (2D idiom) so users
        # can trigger Compute / Export even when STRAIN PARAMETERS is folded.
        self._compute_btn = QPushButton(self.tr("Compute Strain"))
        self._compute_btn.setProperty("class", "btn-primary")
        self._compute_btn.setFixedHeight(40)
        self._compute_btn.clicked.connect(self._on_compute_clicked)
        right.addWidget(self._compute_btn)

        self._export_btn = QPushButton(self.tr("Export Results"))
        self._export_btn.setFixedHeight(30)
        self._export_btn.setIcon(icon_download())
        self._export_btn.setToolTip(
            self.tr("Export displacement and strain results to NPZ / MAT / CSV")
        )
        self._export_btn.setEnabled(False)
        self._export_btn.clicked.connect(self._on_export)
        right.addWidget(self._export_btn)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)  # P3.5: real per-frame progress
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(8)
        self._progress.setVisible(False)
        right.addWidget(self._progress)

        self._progress_lbl = QLabel("")
        self._progress_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 11px;")
        self._progress_lbl.setVisible(False)
        right.addWidget(self._progress_lbl)

        # P3.5: cooperative cancel — visible only while a compute runs.
        self._cancel_btn = QPushButton(self.tr("Cancel"))
        self._cancel_btn.setFixedHeight(26)
        self._cancel_btn.setToolTip(self.tr("Stop the strain computation at the next frame."))
        self._cancel_btn.setVisible(False)
        self._cancel_btn.clicked.connect(self._on_cancel_clicked)
        right.addWidget(self._cancel_btn)

        self._stale_lbl = QLabel("")
        self._stale_lbl.setStyleSheet("color: #fbbf24; font-size: 11px; font-style: italic;")
        right.addWidget(self._stale_lbl)

        self._field_section = CollapsibleSection(self.tr("FIELD"), expanded=True)
        self._field_selector = StrainFieldSelector3D()
        self._field_selector.field_changed.connect(lambda _f: self._render())
        self._field_section.add_widget(self._field_selector)
        right.addWidget(self._field_section)

        self._viz_section = CollapsibleSection(self.tr("VISUALIZATION"), expanded=True)
        self._viz_section.add_widget(self._build_viz_panel())
        right.addWidget(self._viz_section)

        self._log_section = CollapsibleSection(self.tr("LOG"), expanded=False)
        self._console = ConsoleLog()
        self._log_section.add_widget(self._console)
        right.addWidget(self._log_section)

        right.addStretch(1)

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        right_scroll.setFrameShape(QFrame.Shape.NoFrame)
        right_scroll.setWidget(right_container)
        right_scroll.setFixedWidth(340)
        root.addWidget(right_scroll, 0)

        self.setCentralWidget(central)

        self._connect_signals()
        self._refresh_from_result()
        self._render()

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------

    def _build_viz_panel(self) -> QWidget:
        # Widgets live in the extracted (behavior-free) panel; ALL wiring stays
        # here so the window keeps owning its private display state. Aliases
        # preserve the historical attribute names (tests, export hint).
        panel = StrainVizPanel3D()
        self._deformed_cb = panel.deformed_cb
        self._cmap_combo = panel.cmap_combo
        self._auto_range_cb = panel.auto_range_cb
        self._vmin_spin = panel.vmin_spin
        self._vmax_spin = panel.vmax_spin
        self._opacity_slider = panel.opacity_slider

        self._deformed_cb.toggled.connect(lambda _c: self._render())
        self._cmap_combo.currentTextChanged.connect(lambda _t: self._render())
        self._auto_range_cb.toggled.connect(self._on_auto_range)
        self._vmin_spin.valueChanged.connect(lambda _v: self._render())
        self._vmax_spin.valueChanged.connect(lambda _v: self._render())
        self._opacity_slider.valueChanged.connect(lambda _v: self._render())
        return panel

    # ------------------------------------------------------------------
    # Signal lifecycle (2D Bug-B idiom: reconnect on show, disconnect on close)
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        if not getattr(self, "_signals_connected", False):
            self.signals.results_changed.connect(self._on_results_changed)
            self._signals_connected = True

    def showEvent(self, event) -> None:  # noqa: N802 (Qt override)
        super().showEvent(event)
        self._connect_signals()
        # 2D idiom: clear the viz cache on show so a previous session's
        # overlay never bleeds through after the data changed while hidden.
        self._viz_ctrl.clear_all()
        self._param_panel.set_winstepsize(self.controller.state.draft.winstepsize)
        self._refresh_from_result()
        self._render()

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        # G1.2: a live compute QThread must be joined before the window goes
        # (Qt otherwise destroys a running thread). The cascade path (main
        # window closing) calls join_worker() BEFORE close(), so this prompt
        # only ever appears for a user-initiated close. P3.5: with the
        # cooperative cancel hook the prompt now offers to CANCEL the compute;
        # confirming stops it at the next frame and joins the (short) tail.
        if self._worker is not None and self._worker.isRunning():
            if not self._confirm_close_during_compute():
                event.ignore()
                return
            self._worker.request_stop()
            self.join_worker()
        # G3.12: a non-modal export dialog may hold live workers — close it
        # through its own running-export guard first.
        if self._export_dialog is not None and not self._export_dialog.close():
            event.ignore()
            return
        if getattr(self, "_signals_connected", False):
            self.signals.results_changed.disconnect(self._on_results_changed)
            self._signals_connected = False
        self._cancel_pick()
        from al_dic_3d.gui import persistence

        persistence.save_window_state(self, "strain_window")  # G3.2
        super().closeEvent(event)

    def join_worker(self, timeout_ms: int = 10_000) -> None:
        """Join a running strain worker under a busy cursor (close/cascade, G1.2).

        P3.5: the compute is cancelled first so the join is bounded by one
        frame's work, not the whole remaining sequence.
        """
        if self._worker is None or not self._worker.isRunning():
            return
        from PySide6.QtWidgets import QApplication

        self._worker.request_stop()
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self._worker.wait(timeout_ms)
        finally:
            QApplication.restoreOverrideCursor()

    def _confirm_close_during_compute(self) -> bool:
        """Yes/No prompt when the user closes while a compute runs (G1.2).

        P3.5: the worker now has a cooperative cancel hook, so the honest
        offer is to CANCEL the compute (it stops at the next frame) and close.
        """
        from PySide6.QtWidgets import QMessageBox

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(self.tr("Computation Running"))
        box.setText(self.tr("A strain computation is running — cancel it and close?"))
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)
        # Qt's own qtbase button catalogs are not shipped — set the texts
        # explicitly so the 8-locale contract covers the buttons too.
        box.button(QMessageBox.StandardButton.Yes).setText(self.tr("Yes"))
        box.button(QMessageBox.StandardButton.No).setText(self.tr("No"))
        return box.exec() == QMessageBox.StandardButton.Yes

    def eventFilter(self, obj, event) -> bool:  # noqa: N802 (Qt override)
        if obj is self._canvas.viewport() and event.type() == QEvent.Type.Resize:
            self._colorbar.setGeometry(0, 0, obj.width(), obj.height())
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        """←/→ = prev/next strain frame, Space = play/pause (G2.5).

        Reached only when the focused child did not consume the key, so spin
        boxes keep their arrow keys and the pick canvas keeps Space pan mode.
        """
        key = event.key()
        if key in (Qt.Key.Key_Left, Qt.Key.Key_Right):
            self._nav.step(-1 if key == Qt.Key.Key_Left else 1)
            event.accept()
            return
        if key == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._nav.toggle_playback()
            event.accept()
            return
        super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # Public accessors (tests + integration)
    # ------------------------------------------------------------------

    def strain_current_frame(self) -> int:
        return self._frame

    def set_strain_frame(self, idx: int) -> None:
        n = self._frame_count()
        clamped = max(0, min(idx, max(0, n - 1)))
        if clamped == self._frame:
            return
        self._frame = clamped
        self._nav.set_state(n, clamped)
        self._render()

    def current_field(self) -> str:
        return self._field_selector.current_field()

    def set_current_field(self, name: str) -> None:
        self._field_selector.set_current_field(name)

    def is_stale(self) -> bool:
        return self._param_panel.is_dirty()

    def param_panel(self) -> StrainParamPanel3D:
        return self._param_panel

    def trigger_compute(self) -> None:
        """Synchronous compute — the tests' blocking path (no worker thread)."""
        if self.controller.state.result is None:
            return
        try:
            self._strain_ctrl.compute_and_store(self._param_panel.get_override())
        except Exception as exc:  # noqa: BLE001 - surface compute errors in the log
            self._log(self.tr("Strain compute failed: {0}").format(exc), "error")
            return
        self._viz_ctrl.clear_all()
        self.signals.results_changed.emit()
        self._after_compute_success()

    # ------------------------------------------------------------------
    # Compute flow
    # ------------------------------------------------------------------

    def _on_compute_clicked(self) -> None:
        if self.controller.state.result is None:
            self._log(self.tr("Run 3D analysis first — no results to post-process."), "warning")
            return
        if not self._param_panel.compute_allowed():
            self._log(self.tr("Click Origin, then +X, then +Y on the image"), "warning")
            return
        if self._worker is not None and self._worker.isRunning():
            return
        self._compute_btn.setEnabled(False)
        self._progress.setValue(0)
        self._progress.setVisible(True)
        self._progress_lbl.setText(self.tr("Computing strain…"))
        self._progress_lbl.setVisible(True)
        self._cancel_btn.setEnabled(True)
        self._cancel_btn.setVisible(True)

        self._worker = StrainWorker(self._strain_ctrl, self._param_panel.get_override())
        self._worker.progress.connect(self._on_worker_progress)
        self._worker.finished_ok.connect(self._on_worker_finished)
        self._worker.failed.connect(self._on_worker_failed)
        self._worker.cancelled.connect(self._on_worker_cancelled)
        self._worker.start()

    def _on_cancel_clicked(self) -> None:
        """P3.5: trip the worker's cooperative stop; it aborts at the next frame."""
        if self._worker is None or not self._worker.isRunning():
            return
        self._cancel_btn.setEnabled(False)
        self._progress_lbl.setText(self.tr("Cancelling…"))
        self._worker.request_stop()

    def _on_worker_progress(self, frac: float, _msg: str) -> None:
        self._progress.setValue(int(round(frac * 100)))
        self._progress_lbl.setText(self.tr("Computing strain… {0}%").format(int(frac * 100)))

    def _hide_compute_feedback(self) -> None:
        self._progress.setVisible(False)
        self._progress_lbl.setVisible(False)
        self._cancel_btn.setVisible(False)

    def _on_worker_finished(self, strain: StrainResult3D) -> None:
        # Writeback on the main thread (frozen replace + one notification).
        self._strain_ctrl.apply(strain)
        self._viz_ctrl.clear_all()
        self.signals.results_changed.emit()
        self._progress_lbl.setText(self.tr("Complete"))
        self._cancel_btn.setVisible(False)
        self._compute_btn.setEnabled(True)
        self._after_compute_success()
        QTimer.singleShot(2000, self._hide_compute_feedback)

    def _on_worker_failed(self, message: str) -> None:
        self._hide_compute_feedback()
        self._compute_btn.setEnabled(True)
        self._log(self.tr("Strain compute failed: {0}").format(message), "error")

    def _on_worker_cancelled(self) -> None:
        self._hide_compute_feedback()
        self._compute_btn.setEnabled(True)
        self._log(self.tr("Strain computation cancelled."), "info")

    def _after_compute_success(self) -> None:
        self._param_panel.mark_clean()
        self._stale_lbl.setText("")
        self._log(self.tr("Strain computation complete."), "success")
        self._refresh_from_result()
        self._render()

    def _on_params_dirty(self) -> None:
        self._stale_lbl.setText(self.tr("⚠ Params changed -- click Compute Strain"))
        self._compute_btn.setEnabled(self._param_panel.compute_allowed())
        self._refresh_action_tooltips()

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _on_export(self) -> None:
        result = self.controller.state.result
        if result is None:
            return
        if self._export_dialog is not None:  # G3.12: reuse the open dialog
            self._export_dialog.show()
            self._export_dialog.raise_()
            self._export_dialog.activateWindow()
            return
        from al_dic_3d.export import VizExportHint
        from al_dic_3d.gui.dialogs.export_dialog import ExportDialog, draft_export_params

        # Snapshot of THIS window's private display state (never GuiSignals):
        # the export dialog opens prefilled with what the user is looking at.
        hint = VizExportHint(
            colormap=self._cmap_combo.currentText(),
            show_deformed=self._deformed_cb.isChecked(),
            overlay_alpha=self._opacity_slider.value() / 100.0,
            current_field=self._field_selector.current_field(),
            auto_range=self._auto_range_cb.isChecked(),
            vmin=float(self._vmin_spin.value()),
            vmax=float(self._vmax_spin.value()),
            current_frame=self._frame,
        )
        extra = draft_export_params(self.controller.state.draft)
        dialog = ExportDialog(
            result,
            extra_params=extra,
            parent=self,
            draft=self.controller.state.draft,
            hint=hint,
        )
        # G3.12: non-modal — keep scrubbing frames while exports run.
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        dialog.destroyed.connect(lambda *_a: setattr(self, "_export_dialog", None))
        self._export_dialog = dialog
        dialog.show()

    # ------------------------------------------------------------------
    # 3-point specimen pick flow
    # ------------------------------------------------------------------

    def _start_pick(self) -> None:
        if self.controller.state.result is None:
            self._log(self.tr("Run 3D analysis first — no results to post-process."), "warning")
            return
        self._clear_pick_markers()
        self._pick_nodes = []
        self._param_panel.set_specimen_R(None)
        # Picks live on the frame-1 reference image: jump there and show
        # reference geometry so clicks land on the mesh the frame is built on.
        self._frame = 0
        self._nav.set_state(self._frame_count(), 0)
        self._deformed_cb.setChecked(False)
        self._canvas.set_pick_mode(True)
        self._param_panel.set_pick_status(self.tr("Click Origin, then +X, then +Y on the image"))
        self._render()

    def _cancel_pick(self) -> None:
        self._canvas.set_pick_mode(False)
        self._pick_nodes = []
        self._clear_pick_markers()

    def _on_point_picked(self, x: float, y: float) -> None:
        idx = self._strain_ctrl.nearest_valid_node(x, y)
        if idx is None:
            self._log("no valid node near the click — run/inspect the result first", "warning")
            return
        self._pick_nodes.append(idx)
        n = len(self._pick_nodes)
        result = self.controller.state.result
        nx, ny = result.ref_coords[idx]
        self._add_pick_marker(float(nx), float(ny), n - 1)
        self._param_panel.set_pick_status(self.tr("Picked {0}/3 points").format(n))
        if n < 3:
            return
        self._canvas.set_pick_mode(False)
        try:
            r, _t = self._strain_ctrl.specimen_frame_from_nodes(self._pick_nodes)
        except Exception as exc:  # noqa: BLE001 - degenerate picks must not crash
            self._log(self.tr("Strain compute failed: {0}").format(exc), "error")
            self._param_panel.set_pick_status(
                self.tr("Click Origin, then +X, then +Y on the image")
            )
            self._pick_nodes = []
            self._clear_pick_markers()
            return
        self._param_panel.set_specimen_R(r)
        axes = tuple(np.round(r[:, i], 3).tolist() for i in range(3))
        self._param_panel.set_pick_status(
            self.tr("Picked {0}/3 points").format(3)
            + "\n"
            + self.tr("x→{0}  y→{1}  z→{2}").format(*axes)
        )
        self._compute_btn.setEnabled(True)

    def _add_pick_marker(self, x: float, y: float, order: int) -> None:
        scene = self._canvas.scene()
        r = max(3.0, self.controller.state.draft.winstepsize * 0.35)
        pen = QPen(_PICK_COLORS[order], 2)
        pen.setCosmetic(True)
        dot = scene.addEllipse(x - r, y - r, 2 * r, 2 * r, pen)
        dot.setZValue(30)
        labels = (self.tr("O"), self.tr("+X"), self.tr("+Y"))
        text = scene.addSimpleText(labels[order])
        text.setBrush(_PICK_COLORS[order])
        text.setPos(x + r + 2, y - r)
        text.setZValue(30)
        self._pick_items += [dot, text]

    def _clear_pick_markers(self) -> None:
        scene = self._canvas.scene()
        for item in self._pick_items:
            scene.removeItem(item)
        self._pick_items = []

    # ------------------------------------------------------------------
    # Data-driven refresh
    # ------------------------------------------------------------------

    def _on_results_changed(self) -> None:
        result = self.controller.state.result
        self._viz_ctrl.clear_all()
        recon_id = None if result is None else id(result.reconstruction)
        if recon_id != self._recon_id:
            # A genuinely new run (not our strain writeback): picked nodes and
            # the specimen frame belong to the old mesh — drop them.
            self._recon_id = recon_id
            self._cancel_pick()
            self._param_panel.set_specimen_R(None)
            self._param_panel.set_pick_status("")
            self._param_panel.mark_clean()
            self._stale_lbl.setText("")
            self._frame = 0
        self._nav.stop_playback()
        self._refresh_from_result()
        self._render()

    def _refresh_from_result(self) -> None:
        result = self.controller.state.result
        has_strain = result is not None and result.strain is not None
        self._field_selector.set_fields_available(has_strain)
        # R1.2 (2D 01ed129): Export follows RESULTS, not strain — the shared
        # dialog exports displacement too (session reload / pre-compute).
        self._export_btn.setEnabled(result is not None)
        self._compute_btn.setEnabled(result is not None and self._param_panel.compute_allowed())
        # R1.4: physical node spacing feeds the panel's VSG size readout.
        self._param_panel.set_node_spacing_mm(self._strain_ctrl.node_spacing_mm())
        self._refresh_action_tooltips()
        if self._recon_id is None and result is not None:
            self._recon_id = id(result.reconstruction)
        n = self._frame_count()
        self._frame = max(0, min(self._frame, max(0, n - 1)))
        self._nav.set_state(n, self._frame)

    def _refresh_action_tooltips(self) -> None:
        """G2.1 stateful tooltips: disabled Compute / Export explain themselves."""
        result = self.controller.state.result
        if result is None:
            self._compute_btn.setToolTip(
                self.tr("Run a 3D analysis first — strain needs displacement results.")
            )
        elif not self._param_panel.compute_allowed():
            self._compute_btn.setToolTip(
                self.tr("Pick the 3 specimen-frame points first (Origin, +X, +Y).")
            )
        else:
            self._compute_btn.setToolTip(
                self.tr(
                    "Compute Green-Lagrange surface strain from the displacement "
                    "field with the parameters above."
                )
            )
        if result is not None:
            self._export_btn.setToolTip(
                self.tr("Export displacement and strain results to NPZ / MAT / CSV")
            )
        else:
            self._export_btn.setToolTip(
                self.tr("Run an analysis first — there are no results yet.")
            )

    def _frame_count(self) -> int:
        result = self.controller.state.result
        return 0 if result is None else int(result.reconstruction.n_frames)

    def _on_frame_nav(self, value: int) -> None:
        self._frame = int(value)
        self._render()

    def _on_auto_range(self, checked: bool) -> None:
        self._vmin_spin.setEnabled(not checked)
        self._vmax_spin.setEnabled(not checked)
        if not checked:
            # Populate the spinboxes with the last rendered range (2D idiom).
            vmin, vmax = self._last_rendered
            for spin, val in ((self._vmin_spin, vmin), (self._vmax_spin, vmax)):
                spin.blockSignals(True)
                spin.setValue(val)
                spin.blockSignals(False)
        self._render()

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _try_load_background(self, img_idx: int) -> None:
        """Best-effort LEFT-camera background fetch — silent on failure."""
        files = self.controller.state.draft.left
        if not files:
            return
        try:
            self._canvas.set_image_file(files[min(img_idx, len(files) - 1)])
        except Exception:  # noqa: BLE001 - a bad frame must not crash the canvas
            pass

    def _clear_overlay(self) -> None:
        self._canvas.set_overlay_pixmap(None)
        self._colorbar.setVisible(False)

    def _render(self) -> None:
        result = self.controller.state.result
        show_deformed = self._deformed_cb.isChecked()
        if result is None:
            self._clear_overlay()
            self._try_load_background(0)
            return

        k = max(0, min(self._frame, result.reconstruction.n_frames - 1))
        self._try_load_background(k if show_deformed else 0)

        strain = result.strain
        if strain is None:
            self._clear_overlay()
            return

        field = self._field_selector.current_field()
        # Q4: live 'Trimmed: N nodes' readout — derived from strain_valid after a
        # reload where n_trimmed did not persist (C3-3), so it never blanks.
        self._param_panel.set_trim_readout(trim_count(strain, k), int(strain.n_pts))
        crack_aware = bool(result.meta.get("crack_aware", False))  # item 5 indicator
        self._param_panel.set_crack_aware(crack_aware)
        # Geometry follows the deformed toggle; values stay those of frame k.
        deformed = bool(show_deformed) and k > 0

        # The drawn LEFT reference mask (if any) bounds the field; else the
        # renderer falls back to the valid-node hull support.
        roi_mask = None
        drawn = self.controller.state.draft.roi_mask_array
        if drawn is not None:
            roi_mask = np.asarray(drawn) > 0

        # Display mask + geometry + range prep (Qt-free helper): shares the WYSIWYG
        # display mask and the crack-barrier blank with the export paths (C3/C4).
        rd = prepare_strain_render(
            result,
            field,
            k,
            deformed=deformed,
            roi_mask=roi_mask,
            crack_aware=crack_aware,
            auto_range_on=self._auto_range_cb.isChecked(),
            manual_vmin=self._vmin_spin.value(),
            manual_vmax=self._vmax_spin.value(),
        )
        self._last_rendered = (rd.vmin, rd.vmax)

        rect = self._canvas.scene().sceneRect()
        w, h = int(rect.width()), int(rect.height())
        if w <= 0 or h <= 0:
            self._clear_overlay()
            return

        try:
            pixmap, xg, yg, out_step = self._viz_ctrl.render_field(
                k,
                f"strain_window:{field}",
                rd.pts,
                rd.vals,
                img_shape=(h, w),
                mesh_step=int(self.controller.state.draft.winstepsize),
                cmap=self._cmap_combo.currentText(),
                vmin=rd.vmin,
                vmax=rd.vmax,
                roi_mask=roi_mask,
                deformed=deformed,
                ref_uv=rd.ref_uv,
                ref_pts=rd.ref_pts,
                barrier_mask=rd.barrier_mask,
            )
        except Exception as exc:  # noqa: BLE001 - a render bug must not kill the window
            self._log(f"render failed: {type(exc).__name__}: {exc}", "error")
            self._clear_overlay()
            return
        if pixmap is None:
            self._clear_overlay()
            return
        self._canvas.set_overlay_pixmap(pixmap)
        self._canvas.set_overlay_geometry(float(out_step), float(xg.min()), float(yg.min()))
        self._canvas.set_overlay_opacity(self._opacity_slider.value() / 100.0)
        vp = self._canvas.viewport()
        self._colorbar.setGeometry(0, 0, vp.width(), vp.height())
        self._colorbar.update_params(
            self._cmap_combo.currentText(), rd.vmin, rd.vmax, STRAIN_FIELD_LABELS.get(field, field)
        )
        self._colorbar.setVisible(True)

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _log(self, message: str, level: str = "info") -> None:
        # 'warning' is an alias ConsoleLog does not color; errors force the
        # collapsed LOG section open so a failed compute is never invisible.
        self._console.append_log(message, "warn" if level == "warning" else level)
        if level == "error":
            self._log_section.set_expanded(True)
