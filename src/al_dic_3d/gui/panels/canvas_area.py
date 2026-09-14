"""Central canvas — toolbar, layered image canvas, overlays, playback bar.

The 2D ``CanvasArea`` idiom: a 36 px toolbar (Fit / 100% / zoom, view toggles on
the right), the zoomable canvas with a top-left config card and a right-edge
colorbar (both reused/mirrored from 2D), and the 36 px frame navigator at the
bottom. 3D content: the background is the CURRENT CAMERA's frame; results render
as a DENSE continuous full-field overlay (2D-app idiom): the tracked
correspondence points are interpolated onto a regular image-space grid by the
shared :class:`VizController3D`, masked to the reference ROI (or the valid-node
support), and colormapped.

ROI toolbox: this panel owns the :class:`ROIController` mask engine behind the
sidebar's ROI toolbar — shape commits, invert/clear/import/save all funnel into
:meth:`commit_roi_mask`, which persists the mask on the draft and mirrors its
bounding box into ``draft.roi``. It also drives the live mesh PREVIEW overlay:
the debounced preview calls the runner's :func:`build_reference_mesh` with the
draft's exact parameters, so preview == pipeline.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from al_dic.gui.icons import icon_maximize, icon_zoom_in, icon_zoom_out
from al_dic.gui.theme import COLORS
from al_dic.gui.widgets.colorbar_overlay import ColorbarOverlay
from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.gui.controllers.roi_controller import ROIController
from al_dic_3d.gui.panels.canvas_render import CanvasRenderMixin
from al_dic_3d.gui.panels.canvas_tools import CanvasToolsMixin
from al_dic_3d.gui.panels.mesh_preview import MeshPreviewBuilder, snapshot_preview_params
from al_dic_3d.gui.state import GuiSignals
from al_dic_3d.gui.widgets.config_overlay import ConfigOverlay3D
from al_dic_3d.gui.widgets.frame_navigator import FrameNavigator3D
from al_dic_3d.gui.widgets.image_view import ImageCanvas3D
from al_dic_3d.gui.widgets.mesh_appearance import MeshAppearanceControls
from al_dic_3d.gui.widgets.mesh_overlay import MeshOverlay
from al_dic_3d.gui.widgets.view3d import View3D
from al_dic_3d.viz3d.lru import LRUCache

if TYPE_CHECKING:
    from al_dic_3d.gui.controller import WorkflowController

_MAG_CACHE_SIZE = 32  # per-frame |D| / |ΔD| vectors (P2.6/Q2); results-scoped


class CanvasArea3D(CanvasRenderMixin, CanvasToolsMixin, QWidget):
    """Toolbar + canvas (+ overlays) + frame navigator.

    The seed-point / refinement-brush relays live in :class:`CanvasToolsMixin`
    and result rendering (frames, dense overlay, 3D view — off the GUI thread
    when heavy, V-view) in :class:`CanvasRenderMixin` (split for the 800-line
    file cap).
    """

    def __init__(
        self,
        controller: WorkflowController,
        signals: GuiSignals,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.controller = controller
        self.signals = signals

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ---- toolbar ----
        toolbar = QWidget()
        toolbar.setFixedHeight(36)
        toolbar.setStyleSheet(
            f"background: {COLORS.BG_PANEL}; border-bottom: 1px solid {COLORS.BORDER};"
        )
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(8, 2, 8, 2)
        tb.setSpacing(4)

        btn_fit = QPushButton(self.tr("Fit"))
        btn_fit.setFixedWidth(60)
        btn_fit.setIcon(icon_maximize())
        btn_fit.setToolTip(self.tr("Fit the image to the viewport (Ctrl+0)"))
        # G2.4: the "100%" button doubles as a live zoom readout — its label
        # follows the current zoom percent; clicking still resets to 100 %.
        self._zoom_btn = QPushButton("100%")
        self._zoom_btn.setFixedWidth(60)
        self._zoom_btn.setToolTip(
            self.tr(
                "Current zoom — click to reset to 100% (1:1 pixels).\n"
                "Wheel: zoom · Right/middle drag: pan · Space: pan mode"
            )
        )
        btn_in = QPushButton()
        btn_in.setFixedWidth(28)
        btn_in.setIcon(icon_zoom_in())
        btn_in.setToolTip(self.tr("Zoom in (Ctrl+=)"))
        btn_out = QPushButton()
        btn_out.setFixedWidth(28)
        btn_out.setIcon(icon_zoom_out())
        btn_out.setToolTip(self.tr("Zoom out (Ctrl+-)"))
        for b in (btn_fit, self._zoom_btn, btn_in, btn_out):
            tb.addWidget(b)
        tb.addStretch()

        self._grid_cb = QCheckBox(self.tr("Show Grid"))
        self._grid_cb.setToolTip(
            self.tr(
                "Show the computational mesh preview on the reference view\n"
                "(left camera, frame 1). Rebuilt live from the current Subset\n"
                "Step / refinement settings — what you see is the run's mesh.\n"
                "Default on; turn off to declutter the canvas."
            )
        )
        self._grid_cb.setChecked(True)
        self._grid_cb.toggled.connect(self._on_grid_toggled)
        tb.addWidget(self._grid_cb)

        self._subset_cb = QCheckBox(self.tr("Show Subset"))
        self._subset_cb.setToolTip(
            self.tr(
                "Hovering a mesh node shows its correlation subset window\n"
                "(the Subset Size box). Needs Show Grid. Use it to judge\n"
                "whether the subset spans enough speckle texture."
            )
        )
        self._subset_cb.setChecked(False)
        self._subset_cb.toggled.connect(self._on_subset_toggled)
        tb.addWidget(self._subset_cb)

        # F3.2: a view TOGGLE like Show Grid / Show Subset, not a button.
        self._view3d_cb = QCheckBox(self.tr("3D View"))
        self._view3d_cb.setToolTip(
            self.tr(
                "Switch the canvas to the reconstructed 3D surface (colored by\n"
                "the selected field, with the camera frusta). Uncheck to return\n"
                "to the 2D image view. Requires results."
            )
        )
        self._view3d_cb.setChecked(False)
        self._view3d_cb.toggled.connect(self._on_view_mode)
        tb.addWidget(self._view3d_cb)

        # Q8: mesh-overlay appearance (color swatch + width) beside the grid
        # toggle it styles; values live on GuiSignals / view_state.
        self._mesh_appearance = MeshAppearanceControls(signals)
        tb.addWidget(self._mesh_appearance)
        layout.addWidget(toolbar)

        # ---- canvas (2D) / 3D view stack + overlays ----
        self._canvas = ImageCanvas3D()
        self._view3d = View3D()
        self._stack = QStackedWidget()
        self._stack.addWidget(self._canvas)
        self._stack.addWidget(self._view3d)
        layout.addWidget(self._stack, stretch=1)

        self._colorbar = ColorbarOverlay(self._canvas.viewport())
        self._config_overlay = ConfigOverlay3D(controller, self._canvas.viewport())
        self._mesh_overlay = MeshOverlay(self._canvas.viewport())
        # F3.1 empty-result guard: when a run yields NO valid point anywhere,
        # the result panel must say so — never silently render nothing.
        self._empty_notice = QLabel(self._canvas.viewport())
        self._empty_notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_notice.setWordWrap(True)
        self._empty_notice.setStyleSheet(
            f"color: {COLORS.DANGER}; background: rgba(0, 0, 0, 150); "
            f"font-size: 13px; padding: 12px;"
        )
        self._empty_notice.setVisible(False)
        self._result_empty = False
        self._init_empty_hint()  # G3.3: quick-start text until the first image
        self._canvas.viewport().installEventFilter(self)
        self._rig_cache = None  # loaded lazily for the 3D frusta
        # Dense renderer + frame prefetcher (P2.2) + V-view presenters.
        self._init_render_pipeline()
        # P2.6: per-frame |D| magnitude + drawn-ROI-as-bool caches.
        self._mag_cache: LRUCache[int, np.ndarray] = LRUCache(_MAG_CACHE_SIZE)
        # Q2: per-frame |D_k − D_{k−1}| in mm/frame — frame-rate applied at
        # read time, so a frame-rate edit never invalidates this cache.
        self._vel_cache: LRUCache[int, np.ndarray] = LRUCache(_MAG_CACHE_SIZE)
        self._roi_bool_cache: tuple[np.ndarray, np.ndarray] | None = None

        # ROI mask engine (created lazily once an image defines the shape).
        self._roi_ctrl: ROIController | None = None
        self._synced_roi_src: np.ndarray | None = None  # draft array last pushed

        # RIGHT-camera ROI support (F2.3): the left mask warped through the
        # frame-1 correspondence — a compute-once value resolved off the GUI
        # thread by heavy renders; rebuilt on ROI edits / new results.
        self._right_mask_lazy = None
        self._right_mask_dirty = True

        # Mesh preview (P2.3): debounced background build; hover lookup arrays.
        self._mesh_builder = MeshPreviewBuilder(self._mesh_snapshot, self)
        self._mesh_builder.built.connect(self._apply_preview_mesh)
        self._mesh_builder.hidden.connect(self._hide_mesh_overlay)
        self._hover_coords: np.ndarray | None = None
        self._hover_valid: np.ndarray | None = None

        # ---- frame navigator ----
        self._frame_nav = FrameNavigator3D(signals)
        layout.addWidget(self._frame_nav)

        # ---- wiring ----
        btn_fit.clicked.connect(self._canvas.fit_to_view)
        self._zoom_btn.clicked.connect(self._canvas.zoom_to_100)
        btn_in.clicked.connect(self._canvas.zoom_in)
        btn_out.clicked.connect(self._canvas.zoom_out)
        self._canvas.view_changed.connect(self._update_zoom_readout)

        self._canvas.roi_mask_edited.connect(self.commit_roi_mask)
        self._canvas.seed_clicked.connect(self._on_seed_clicked)
        self._canvas.seed_remove_requested.connect(self._on_seed_remove)
        self._canvas.context_menu_requested.connect(self._on_canvas_menu)  # G3.1b
        self._canvas.notice.connect(signals.log)
        self._canvas.brush_changed.connect(self._on_brush_changed)
        self._canvas.view_changed.connect(self._sync_mesh_view_transform)
        self._canvas.scene_hover.connect(self._on_scene_hover)
        self._canvas.hover_left.connect(lambda: self._mesh_overlay.set_hover_node(None))
        signals.frame_changed.connect(self._on_frame_or_camera)
        signals.camera_changed.connect(self._on_frame_or_camera)
        signals.display_changed.connect(self.render)
        signals.results_changed.connect(self._on_results)
        signals.images_changed.connect(self._on_images)
        signals.roi_changed.connect(self._on_roi_changed)
        signals.params_changed.connect(self._on_params_changed)
        signals.calibration_changed.connect(self._invalidate_rig)

    @property
    def canvas(self) -> ImageCanvas3D:
        return self._canvas

    def _update_zoom_readout(self) -> None:
        """G2.4: the '100%' button label follows the live zoom level."""
        self._zoom_btn.setText(f"{self._canvas.zoom_level * 100:.0f}%")

    def view3d_camera(self):
        """The interactive 3D view's camera, for the 3D export (None: not shown)."""
        return self._view3d.camera_position()

    def toggle_playback(self) -> None:
        """Space shortcut relay (G2.5): play/pause the frame navigator."""
        self._frame_nav.toggle_playback()

    # ---- ROI toolbox --------------------------------------------------------------

    @property
    def roi_ctrl(self) -> ROIController | None:
        """The mask engine (None until an image defines the canvas shape)."""
        self._ensure_roi_ctrl()
        return self._roi_ctrl

    def _ensure_roi_ctrl(self) -> None:
        """(Re)create the ROI controller to match the current image shape."""
        if not self._canvas.has_image:
            return
        rect = self._canvas.scene().sceneRect()
        shape = (int(rect.height()), int(rect.width()))
        if self._roi_ctrl is None or self._roi_ctrl.shape != shape:
            self._roi_ctrl = ROIController(shape)
            self._synced_roi_src = None
            mask = self.controller.state.draft.roi_mask_array
            if mask is not None and np.asarray(mask).shape == shape:
                self._roi_ctrl.mask = np.asarray(mask) > 0
                self._synced_roi_src = mask
            self._canvas.set_roi_controller(self._roi_ctrl)
            self._canvas.update_roi_overlay()

    def start_shape_tool(self, shape: str, mode: str) -> None:
        """Arm a one-shot ROI drawing tool on the canvas (from the toolbar)."""
        self._ensure_roi_ctrl()
        self._canvas.set_tool(shape, mode)

    def commit_roi_mask(self) -> None:
        """Persist the controller mask on the draft; mirror its bbox into roi."""
        ctrl = self._roi_ctrl
        if ctrl is None:
            return
        draft = self.controller.state.draft
        mask = ctrl.mask
        if mask.any():
            draft.roi_mask_array = mask.copy()
            ys, xs = np.nonzero(mask)
            draft.roi = (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()))
        else:
            draft.roi_mask_array = None
            draft.roi = None
        self._synced_roi_src = draft.roi_mask_array  # ctrl already holds this mask
        self._canvas.update_roi_overlay()
        self.controller.state.mark_dirty()
        self.signals.roi_changed.emit()

    def roi_clear(self) -> None:
        ctrl = self.roi_ctrl
        if ctrl is None:
            return
        ctrl.clear()
        self.commit_roi_mask()

    def roi_invert(self) -> None:
        ctrl = self.roi_ctrl
        if ctrl is None:
            return
        ctrl.invert()
        self.commit_roi_mask()

    def roi_import(self, path: str) -> None:
        ctrl = self.roi_ctrl
        if ctrl is None:
            self.signals.log.emit(self.tr("Load images before importing an ROI mask"), "warning")
            return
        try:
            ctrl.import_mask(path)
        except Exception as exc:  # noqa: BLE001 - surface bad files to the user log
            self.signals.log.emit(self.tr("Could not import the mask: {0}").format(exc), "error")
            return
        self.commit_roi_mask()
        self.signals.log.emit(self.tr("ROI mask imported from {0}").format(path), "info")

    def roi_save(self) -> None:
        ctrl = self.roi_ctrl
        if ctrl is None or not ctrl.mask.any():
            self.signals.log.emit(self.tr("No ROI mask to save — draw one first"), "warning")
            return
        from al_dic_3d.gui import persistence

        left = self.controller.state.draft.left
        near = left[0] if left else None  # the images' folder, else the last one
        start = persistence.suggested_save_path("roi_mask.png", "mask", near=near)
        path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Save Mask"), start, self.tr("PNG image (*.png)")
        )
        if not path:
            return
        try:
            ctrl.save_mask(path)
        except Exception as exc:  # noqa: BLE001 - surface IO errors to the user log
            self.signals.log.emit(self.tr("Could not save the mask: {0}").format(exc), "error")
            return
        persistence.set_last_dir("mask", path)
        self.signals.log.emit(self.tr("ROI mask saved to {0}").format(path), "success")

    def _on_roi_changed(self) -> None:
        """ROI edits change the dense-field support: drop mask-derived caches."""
        self._viz_ctrl.invalidate_masks()
        self._right_mask_dirty = True
        self._sync_roi()
        if self.controller.state.result is not None:
            self.render()

    def _sync_roi(self) -> None:
        """Draft -> view: mask overlay and the mesh preview (mask fill IS the ROI display).

        Runs on every render (frame scrubs included), so the push into the
        ROI controller — and the full-image RGBA overlay rebuild it forces —
        only happens when the draft's mask ARRAY actually changed (P2.6: the
        old unconditional path rebuilt an (H, W, 4) pixmap per frame change).
        """
        draft = self.controller.state.draft
        if self._roi_ctrl is not None:
            mask = draft.roi_mask_array
            changed = False
            if mask is None:
                self._synced_roi_src = None
                if self._roi_ctrl.mask.any():
                    self._roi_ctrl.clear()
                    changed = True
            elif (
                np.asarray(mask).shape == self._roi_ctrl.shape and mask is not self._synced_roi_src
            ):
                self._roi_ctrl.mask = np.asarray(mask) > 0
                self._synced_roi_src = mask
                changed = True
            if changed:
                self._canvas.update_roi_overlay()
        self._schedule_mesh_preview()

    # ---- mesh preview + subset hover ------------------------------------------------

    def _on_grid_toggled(self, checked: bool) -> None:
        self._subset_cb.setEnabled(checked)
        if not checked:
            self._subset_cb.setChecked(False)
            self._mesh_builder.stop()
            self._mesh_overlay.setVisible(False)
        else:
            self._schedule_mesh_preview()

    def _on_subset_toggled(self, checked: bool) -> None:
        if not checked:
            self._mesh_overlay.set_hover_node(None)

    def _on_params_changed(self) -> None:
        self._config_overlay.refresh()
        self._schedule_mesh_preview()

    def _on_frame_or_camera(self, _v) -> None:
        self.render()
        self._schedule_mesh_preview()

    def _schedule_mesh_preview(self) -> None:
        """Debounced preview rebuild (params/ROI edits arrive in bursts)."""
        if self._grid_cb.isChecked():
            self._mesh_builder.schedule()

    def _mesh_preview_applicable(self) -> bool:
        """Preview shows frame-1 LEFT reference geometry only on that view."""
        draft = self.controller.state.draft
        return (
            self._stack.currentIndex() == 0
            and self.signals.current_camera == "L"
            and self.signals.current_frame == 0
            and self._canvas.has_image
            and draft.roi is not None
            and draft.roi[0] < draft.roi[1]
            and draft.roi[2] < draft.roi[3]
        )

    def _mesh_snapshot(self) -> dict | None:
        """GUI-thread param capture for the background build (None = hide)."""
        if not self._grid_cb.isChecked() or not self._mesh_preview_applicable():
            return None
        rect = self._canvas.scene().sceneRect()
        return snapshot_preview_params(
            self.controller.state.draft, int(rect.height()), int(rect.width())
        )

    def _generate_preview_mesh(self) -> None:
        """Start a background preview build with the current params (P2.3)."""
        self._mesh_builder.kick_now()

    def wait_mesh_preview(self, timeout_ms: int = 30_000) -> bool:
        """Join in-flight preview builds and deliver results (tests)."""
        return self._mesh_builder.wait_idle(timeout_ms)

    def _apply_preview_mesh(self, coords, elements, valid) -> None:
        """A background build landed — re-check the view state, then show it."""
        if not self._grid_cb.isChecked() or not self._mesh_preview_applicable():
            self._hide_mesh_overlay()
            return
        self._hover_coords = coords
        self._hover_valid = valid
        self._mesh_overlay.set_mesh(coords, elements, valid)
        self._mesh_overlay.set_view_transform(self._canvas.viewportTransform())
        self._mesh_overlay.setVisible(True)

    def _hide_mesh_overlay(self) -> None:
        self._mesh_overlay.set_mesh(None, None)
        self._mesh_overlay.setVisible(False)
        self._hover_coords = None
        self._hover_valid = None

    def _sync_mesh_view_transform(self) -> None:
        """Lightweight pan/zoom sync — transform only, no path rebuild."""
        if self._mesh_overlay.isVisible():
            self._mesh_overlay.set_view_transform(self._canvas.viewportTransform())

    def _on_scene_hover(self, sx: float, sy: float) -> None:
        """Snap the hover subset window to the nearest valid preview node."""
        if not self._subset_cb.isChecked() or self._hover_coords is None:
            return
        coords = self._hover_coords
        dist_sq = (coords[:, 0] - sx) ** 2 + (coords[:, 1] - sy) ** 2
        mask = ~np.isnan(dist_sq)
        if self._hover_valid is not None:
            mask &= self._hover_valid
        if not np.any(mask):
            self._mesh_overlay.set_hover_node(None)
            return
        dist_sq = np.where(mask, dist_sq, np.inf)
        min_idx = int(np.argmin(dist_sq))
        threshold = float(self.controller.state.draft.winstepsize) * 1.5
        if dist_sq[min_idx] > threshold * threshold:
            self._mesh_overlay.set_hover_node(None)
            return
        self._mesh_overlay.set_hover_node(min_idx, float(self.controller.state.draft.winsize))

    # ---- view mode ---------------------------------------------------------------

    def _on_view_mode(self, use_3d: bool) -> None:
        self._stack.setCurrentIndex(1 if use_3d else 0)
        self.render()
        self._schedule_mesh_preview()

    def _invalidate_rig(self) -> None:
        self._rig_cache = None

    def _load_rig(self):
        """Lazily load the stereo rig for the 3D frusta (None if unavailable)."""
        if self._rig_cache is not None:
            return self._rig_cache
        draft = self.controller.state.draft
        if draft.calibration_file is None:
            return None
        try:
            from al_dic_3d.calibration import load_calibration

            self._rig_cache = load_calibration(draft.calibration_file, draft.calibration_format)
        except Exception:  # noqa: BLE001 - frusta are decoration only
            self._rig_cache = None
        return self._rig_cache

    # ---- data-driven refresh ------------------------------------------------------

    def _on_images(self) -> None:
        draft = self.controller.state.draft
        n = max(len(draft.left), len(draft.right))
        self._frame_nav.set_frame_count(n)
        self._config_overlay.refresh()
        self._cancel_render_work()  # queued renders/decodes belong to old images
        self._viz_ctrl.clear_all()  # image size may have changed
        self._prefetcher.invalidate()  # decoded frames are stale by definition
        self._mag_cache.clear()
        self._vel_cache.clear()
        self.render()
        self._ensure_roi_ctrl()
        self._sync_brush_from_draft()  # Z1: restored refinement zones -> canvas
        self._schedule_mesh_preview()

    def _on_results(self) -> None:
        result = self.controller.state.result
        # F3.1: an all-invalid run must be called out on the canvas itself.
        self._result_empty = result is not None and not bool(
            np.isfinite(result.reconstruction.points).any()
        )
        self._empty_notice.setText(
            self.tr("Analysis produced no valid points — nothing to display. See the log.")
        )
        self._cancel_render_work()  # in-flight overlays belong to the old result
        self._run_step_memo = None
        self._viz_ctrl.clear_all()
        self._mag_cache.clear()
        self._vel_cache.clear()
        self._right_mask_dirty = True
        # P2.4: new results are the ONLY event that re-frames the 3D camera.
        self._view3d.request_camera_reset()
        self.render()

    # ---- rendering: see CanvasRenderMixin (canvas_render.py) --------------------

    # ---- overlay geometry ------------------------------------------------------------

    def eventFilter(self, obj, event) -> bool:  # noqa: N802 (Qt override)
        if obj is self._canvas.viewport() and event.type() == QEvent.Type.Resize:
            self._colorbar.setGeometry(0, 0, obj.width(), obj.height())
            self._mesh_overlay.setGeometry(0, 0, obj.width(), obj.height())
            self._empty_notice.setGeometry(0, obj.height() // 2 - 40, obj.width(), 80)
            self._update_empty_hint()  # keep the quick-start text centered (G3.3)
            self._config_overlay.reposition()
        return super().eventFilter(obj, event)
