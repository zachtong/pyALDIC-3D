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
from al_dic.gui.icons import icon_download, icon_maximize, icon_zoom_in, icon_zoom_out
from al_dic.gui.theme import COLORS
from al_dic.gui.widgets.collapsible_section import CollapsibleSection
from al_dic.gui.widgets.colorbar_overlay import ColorbarOverlay
from al_dic.gui.widgets.console_log import ConsoleLog
from al_dic.gui.window_chrome import enable_dark_title_bar
from PySide6.QtCore import QEvent, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QColor, QGuiApplication, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.gui.controllers.strain_controller import StrainController3D
from al_dic_3d.gui.controllers.viz_controller import VizController3D, visible_values
from al_dic_3d.gui.state import GuiSignals
from al_dic_3d.gui.widgets.image_view import ImageCanvas3D
from al_dic_3d.gui.widgets.strain_field_selector import (
    STRAIN_FIELD_LABELS,
    StrainFieldSelector3D,
)
from al_dic_3d.gui.widgets.strain_navigator import StrainNavigator3D
from al_dic_3d.gui.widgets.strain_param_panel import StrainParamPanel3D

if TYPE_CHECKING:
    from al_dic_3d.gui.controller import WorkflowController
    from al_dic_3d.strain3d.model import StrainResult3D

_COLORMAPS = ["turbo", "viridis", "jet", "coolwarm", "plasma", "inferno", "RdBu_r"]

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


class _PickCanvas(ImageCanvas3D):
    """Read-only canvas with an optional 3-point pick mode (no ROI tools armed)."""

    point_picked = Signal(float, float)  # scene (x, y) of a left click in pick mode

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._pick_mode = False

    def set_pick_mode(self, on: bool) -> None:
        self._pick_mode = bool(on)
        self.setCursor(Qt.CursorShape.CrossCursor if on else Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if self._pick_mode and event.button() == Qt.MouseButton.LeftButton:
            sp = self.mapToScene(event.position().toPoint())
            self.point_picked.emit(sp.x(), sp.y())
            return
        super().mousePressEvent(event)


class _StrainWorker(QThread):
    """Background strain compute; state writeback happens in the window's slot."""

    finished_ok = Signal(object)  # StrainResult3D
    failed = Signal(str)

    def __init__(self, ctrl: StrainController3D, override: dict) -> None:
        super().__init__()
        self._ctrl = ctrl
        self._override = override

    def run(self) -> None:  # QThread entry point (worker thread)
        try:
            self.finished_ok.emit(self._ctrl.compute(self._override))
        except Exception as exc:  # noqa: BLE001 - report any failure to the UI
            import traceback

            traceback.print_exc()  # full traceback to stderr (F3.1)
            self.failed.emit(f"{type(exc).__name__}: {exc}")


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
        self._worker: _StrainWorker | None = None

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

        central = QWidget(self)
        root = QHBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # ---- left pane: zoom toolbar + canvas + colorbar + navigator ----
        left = QVBoxLayout()
        left.setSpacing(0)

        zoom_bar = QWidget()
        zoom_bar.setFixedHeight(36)
        zoom_bar.setStyleSheet(
            f"background: {COLORS.BG_PANEL}; border-bottom: 1px solid {COLORS.BORDER};"
        )
        zl = QHBoxLayout(zoom_bar)
        zl.setContentsMargins(8, 2, 8, 2)
        zl.setSpacing(4)
        btn_fit = QPushButton(self.tr("Fit"))
        btn_fit.setToolTip(self.tr("Fit image to viewport"))
        btn_fit.setFixedWidth(60)
        btn_fit.setIcon(icon_maximize())
        btn_100 = QPushButton("100%")
        btn_100.setToolTip(self.tr("Zoom to 100% (1:1)"))
        btn_100.setFixedWidth(60)
        btn_in = QPushButton()
        btn_in.setToolTip(self.tr("Zoom in"))
        btn_in.setFixedWidth(28)
        btn_in.setIcon(icon_zoom_in())
        btn_out = QPushButton()
        btn_out.setToolTip(self.tr("Zoom out"))
        btn_out.setFixedWidth(28)
        btn_out.setIcon(icon_zoom_out())
        for b in (btn_fit, btn_100, btn_in, btn_out):
            zl.addWidget(b)
        zl.addStretch()
        left.addWidget(zoom_bar)

        self._canvas = _PickCanvas()
        left.addWidget(self._canvas, stretch=1)
        self._colorbar = ColorbarOverlay(self._canvas.viewport())
        self._canvas.viewport().installEventFilter(self)
        self._canvas.point_picked.connect(self._on_point_picked)

        btn_fit.clicked.connect(self._canvas.fit_to_view)
        btn_100.clicked.connect(self._canvas.zoom_to_100)
        btn_in.clicked.connect(self._canvas.zoom_in)
        btn_out.clicked.connect(self._canvas.zoom_out)

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
        self._progress.setRange(0, 0)  # busy: the compute API has no per-frame hook
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(8)
        self._progress.setVisible(False)
        right.addWidget(self._progress)

        self._progress_lbl = QLabel("")
        self._progress_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 11px;")
        self._progress_lbl.setVisible(False)
        right.addWidget(self._progress_lbl)

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
        host = QWidget()
        form = QFormLayout(host)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(6)

        self._deformed_cb = QCheckBox(self.tr("Show on deformed frame"))
        self._deformed_cb.setChecked(True)
        self._deformed_cb.toggled.connect(lambda _c: self._render())
        form.addRow(self._deformed_cb)

        self._cmap_combo = QComboBox()
        self._cmap_combo.addItems(_COLORMAPS)
        self._cmap_combo.currentTextChanged.connect(lambda _t: self._render())
        form.addRow(self.tr("Colormap"), self._cmap_combo)

        self._auto_range_cb = QCheckBox(self.tr("Auto range"))
        self._auto_range_cb.setChecked(True)
        self._auto_range_cb.toggled.connect(self._on_auto_range)
        form.addRow(self._auto_range_cb)

        self._vmin_spin = QDoubleSpinBox()
        self._vmax_spin = QDoubleSpinBox()
        for spin in (self._vmin_spin, self._vmax_spin):
            spin.setDecimals(6)
            spin.setRange(-1e9, 1e9)
            spin.setSingleStep(1e-3)
            spin.setEnabled(False)
            spin.valueChanged.connect(lambda _v: self._render())
        minmax = QHBoxLayout()
        minmax.setSpacing(4)
        minmax.setContentsMargins(0, 0, 0, 0)
        minmax.addWidget(QLabel(self.tr("Min")))
        minmax.addWidget(self._vmin_spin, 1)
        minmax.addWidget(QLabel(self.tr("Max")))
        minmax.addWidget(self._vmax_spin, 1)
        minmax_host = QWidget()
        minmax_host.setLayout(minmax)
        form.addRow(minmax_host)

        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(0, 100)
        self._opacity_slider.setValue(85)
        self._opacity_slider.valueChanged.connect(lambda _v: self._render())
        form.addRow(self.tr("Opacity"), self._opacity_slider)
        return host

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
        # only ever appears for a user-initiated close.
        if self._worker is not None and self._worker.isRunning():
            if not self._confirm_close_during_compute():
                event.ignore()
                return
            self.join_worker()
        if getattr(self, "_signals_connected", False):
            self.signals.results_changed.disconnect(self._on_results_changed)
            self._signals_connected = False
        self._cancel_pick()
        super().closeEvent(event)

    def join_worker(self, timeout_ms: int = 10_000) -> None:
        """Join a running strain worker under a busy cursor (close/cascade, G1.2)."""
        if self._worker is None or not self._worker.isRunning():
            return
        from PySide6.QtWidgets import QApplication

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self._worker.wait(timeout_ms)
        finally:
            QApplication.restoreOverrideCursor()

    def _confirm_close_during_compute(self) -> bool:
        """Yes/No prompt when the user closes while a compute runs (G1.2).

        The strain worker has no cooperative cancel hook, so the honest offer
        is to WAIT for it (bounded by :meth:`join_worker`), not to cancel it.
        """
        from PySide6.QtWidgets import QMessageBox

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(self.tr("Computation Running"))
        box.setText(self.tr("A strain computation is running — wait for it and close?"))
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
        self._progress.setVisible(True)
        self._progress_lbl.setText(self.tr("Computing strain…"))
        self._progress_lbl.setVisible(True)

        self._worker = _StrainWorker(self._strain_ctrl, self._param_panel.get_override())
        self._worker.finished_ok.connect(self._on_worker_finished)
        self._worker.failed.connect(self._on_worker_failed)
        self._worker.start()

    def _on_worker_finished(self, strain: StrainResult3D) -> None:
        # Writeback on the main thread (frozen replace + one notification).
        self._strain_ctrl.apply(strain)
        self._viz_ctrl.clear_all()
        self.signals.results_changed.emit()
        self._progress_lbl.setText(self.tr("Complete"))
        self._compute_btn.setEnabled(True)
        self._after_compute_success()
        QTimer.singleShot(
            2000,
            lambda: (self._progress.setVisible(False), self._progress_lbl.setVisible(False)),
        )

    def _on_worker_failed(self, message: str) -> None:
        self._progress.setVisible(False)
        self._progress_lbl.setVisible(False)
        self._compute_btn.setEnabled(True)
        self._log(self.tr("Strain compute failed: {0}").format(message), "error")

    def _after_compute_success(self) -> None:
        self._param_panel.mark_clean()
        self._stale_lbl.setText("")
        self._log(self.tr("Strain computation complete."), "success")
        self._refresh_from_result()
        self._render()

    def _on_params_dirty(self) -> None:
        self._stale_lbl.setText(self.tr("⚠ Params changed -- click Compute Strain"))
        self._compute_btn.setEnabled(self._param_panel.compute_allowed())

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _on_export(self) -> None:
        result = self.controller.state.result
        if result is None:
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
        ExportDialog(
            result,
            extra_params=extra,
            parent=self,
            draft=self.controller.state.draft,
            hint=hint,
        ).exec()

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
        self._export_btn.setEnabled(has_strain)
        self._compute_btn.setEnabled(result is not None and self._param_panel.compute_allowed())
        if self._recon_id is None and result is not None:
            self._recon_id = id(result.reconstruction)
        n = self._frame_count()
        self._frame = max(0, min(self._frame, max(0, n - 1)))
        self._nav.set_state(n, self._frame)

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
        vals = getattr(strain, field)[k]
        cs = result.correspondence
        # Geometry follows the deformed toggle; values stay those of frame k.
        deformed = bool(show_deformed) and k > 0
        pts = cs.xL[k] if deformed else cs.xL[0]
        ref_pts = cs.xL[0]
        ref_uv = None
        if deformed:
            d = cs.xL[k] - cs.xL[0]  # 2D ref_uv contract: x_k - x_1 per node
            ref_uv = (d[:, 0], d[:, 1])

        # The strain gauge lives on the LEFT/frame-1 mesh, so the drawn LEFT
        # reference mask (if any) bounds the field; otherwise the renderer
        # falls back to the valid-node hull support.
        roi_mask = None
        drawn = self.controller.state.draft.roi_mask_array
        if drawn is not None:
            roi_mask = np.asarray(drawn) > 0

        # Auto range from VISIBLE nodes of THIS frame only (2D visible_values
        # contract): the colorbar must match what the dense render shows.
        if self._auto_range_cb.isChecked():
            vis = visible_values(vals, ref_pts, roi_mask)
            finite = vis[np.isfinite(vis)]
            if finite.size:
                vmin, vmax = float(finite.min()), float(finite.max())
            else:
                vmin, vmax = 0.0, 1.0
        else:
            vmin, vmax = float(self._vmin_spin.value()), float(self._vmax_spin.value())
        self._last_rendered = (vmin, vmax)

        rect = self._canvas.scene().sceneRect()
        w, h = int(rect.width()), int(rect.height())
        if w <= 0 or h <= 0:
            self._clear_overlay()
            return

        try:
            pixmap, xg, yg, out_step = self._viz_ctrl.render_field(
                k,
                f"strain_window:{field}",
                pts,
                vals,
                img_shape=(h, w),
                mesh_step=int(self.controller.state.draft.winstepsize),
                cmap=self._cmap_combo.currentText(),
                vmin=vmin,
                vmax=vmax,
                roi_mask=roi_mask,
                deformed=deformed,
                ref_uv=ref_uv,
                ref_pts=ref_pts,
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
            self._cmap_combo.currentText(), vmin, vmax, STRAIN_FIELD_LABELS.get(field, field)
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
