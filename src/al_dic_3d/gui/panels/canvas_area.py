"""Central canvas — toolbar, layered image canvas, overlays, playback bar.

The 2D ``CanvasArea`` idiom: a 36 px toolbar (Fit / 100% / zoom, view toggles on
the right), the zoomable canvas with a top-left config card and a right-edge
colorbar (both reused/mirrored from 2D), and the 36 px frame navigator at the
bottom. 3D content: the background is the CURRENT CAMERA's frame; results render
as a DENSE continuous full-field overlay (2D-app idiom): the tracked
correspondence points are interpolated onto a regular image-space grid by the
shared :class:`VizController3D`, masked to the reference ROI (or the valid-node
support), and colormapped. "Show Points" optionally draws small node dots on
top of the dense field.

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
from PySide6.QtCore import QEvent, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.gui.controllers.roi_controller import ROIController
from al_dic_3d.gui.controllers.viz_controller import VizController3D, visible_values
from al_dic_3d.gui.rendering import scatter_field_pixmap
from al_dic_3d.gui.state import GuiSignals
from al_dic_3d.gui.widgets.config_overlay import ConfigOverlay3D
from al_dic_3d.gui.widgets.frame_navigator import FrameNavigator3D
from al_dic_3d.gui.widgets.image_view import ImageCanvas3D
from al_dic_3d.gui.widgets.mesh_overlay import MeshOverlay
from al_dic_3d.gui.widgets.view3d import View3D

if TYPE_CHECKING:
    from al_dic_3d.gui.controller import WorkflowController

# Field id -> colorbar label (math notation, not translated prose).
_FIELD_LABELS = {
    "U": "U (mm)",
    "V": "V (mm)",
    "W": "W (mm)",
    "mag": "|D| (mm)",
    "exx": "εxx",
    "eyy": "εyy",
    "exy": "εxy",
    "e1": "ε₁",
    "e2": "ε₂",
    "max_shear": "γ max",
    "von_mises": "von Mises",
}
_STRAIN_IDS = ("exx", "eyy", "exy", "e1", "e2", "max_shear", "von_mises")

_MESH_PREVIEW_DEBOUNCE_MS = 300


class CanvasArea3D(QWidget):
    """Toolbar + canvas (+ overlays) + frame navigator."""

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
        btn_100 = QPushButton("100%")
        btn_100.setFixedWidth(60)
        btn_in = QPushButton()
        btn_in.setFixedWidth(28)
        btn_in.setIcon(icon_zoom_in())
        btn_out = QPushButton()
        btn_out.setFixedWidth(28)
        btn_out.setIcon(icon_zoom_out())
        for b in (btn_fit, btn_100, btn_in, btn_out):
            tb.addWidget(b)
        tb.addStretch()

        self._grid_cb = QCheckBox(self.tr("Show Grid"))
        self._grid_cb.setToolTip(self.tr("Show/hide computational mesh grid"))
        self._grid_cb.setChecked(True)
        self._grid_cb.toggled.connect(self._on_grid_toggled)
        tb.addWidget(self._grid_cb)

        self._subset_cb = QCheckBox(self.tr("Show Subset"))
        self._subset_cb.setToolTip(self.tr("Show subset window on hover (requires Grid)"))
        self._subset_cb.setChecked(False)
        self._subset_cb.toggled.connect(self._on_subset_toggled)
        tb.addWidget(self._subset_cb)

        self._view3d_btn = QPushButton(self.tr("3D View"))
        self._view3d_btn.setCheckable(True)
        self._view3d_btn.setFixedWidth(76)
        self._view3d_btn.toggled.connect(self._on_view_mode)
        tb.addWidget(self._view3d_btn)

        # The dense field is always the base layer; "Show Points" (default
        # OFF) additionally draws small node dots on top of it.
        self._show_points_cb = QCheckBox(self.tr("Show Points"))
        self._show_points_cb.setChecked(False)
        self._show_points_cb.toggled.connect(lambda _c: self.render())
        tb.addWidget(self._show_points_cb)
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
        self._canvas.viewport().installEventFilter(self)
        self._rig_cache = None  # loaded lazily for the 3D frusta
        self._viz_ctrl = VizController3D()  # dense field renderer + caches

        # ROI mask engine (created lazily once an image defines the shape).
        self._roi_ctrl: ROIController | None = None

        # Mesh preview state (debounced rebuild; hover lookup arrays).
        self._mesh_timer = QTimer(self)
        self._mesh_timer.setSingleShot(True)
        self._mesh_timer.setInterval(_MESH_PREVIEW_DEBOUNCE_MS)
        self._mesh_timer.timeout.connect(self._generate_preview_mesh)
        self._hover_coords: np.ndarray | None = None
        self._hover_valid: np.ndarray | None = None

        # ---- frame navigator ----
        self._frame_nav = FrameNavigator3D(signals)
        layout.addWidget(self._frame_nav)

        # ---- wiring ----
        btn_fit.clicked.connect(self._canvas.fit_to_view)
        btn_100.clicked.connect(self._canvas.zoom_to_100)
        btn_in.clicked.connect(self._canvas.zoom_in)
        btn_out.clicked.connect(self._canvas.zoom_out)

        self._canvas.roi_mask_edited.connect(self.commit_roi_mask)
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
            mask = self.controller.state.draft.roi_mask_array
            if mask is not None and np.asarray(mask).shape == shape:
                self._roi_ctrl.mask = np.asarray(mask) > 0
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
            self.signals.log.emit("load images first before importing a ROI mask", "warning")
            return
        try:
            ctrl.import_mask(path)
        except Exception as exc:  # noqa: BLE001 - surface bad files to the user log
            self.signals.log.emit(f"mask import failed: {exc}", "error")
            return
        self.commit_roi_mask()
        self.signals.log.emit(f"ROI mask imported from {path}", "info")

    def roi_save(self) -> None:
        ctrl = self.roi_ctrl
        if ctrl is None or not ctrl.mask.any():
            self.signals.log.emit("no ROI mask to save — draw one first", "warning")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Save Mask"), "roi_mask.png", self.tr("PNG image (*.png)")
        )
        if not path:
            return
        try:
            ctrl.save_mask(path)
        except Exception as exc:  # noqa: BLE001 - surface IO errors to the user log
            self.signals.log.emit(f"mask save failed: {exc}", "error")
            return
        self.signals.log.emit(f"ROI mask saved to {path}", "success")

    def _on_roi_changed(self) -> None:
        """ROI edits change the dense-field support: drop mask-derived caches."""
        self._viz_ctrl.invalidate_masks()
        self._sync_roi()
        if self.controller.state.result is not None:
            self.render()

    def _sync_roi(self) -> None:
        """Draft -> view: bbox rectangle, mask overlay, and the mesh preview."""
        draft = self.controller.state.draft
        self._canvas.set_roi(draft.roi)
        if self._roi_ctrl is not None:
            mask = draft.roi_mask_array
            if mask is None:
                if self._roi_ctrl.mask.any():
                    self._roi_ctrl.clear()
            elif np.asarray(mask).shape == self._roi_ctrl.shape and mask is not self._roi_ctrl.mask:
                self._roi_ctrl.mask = np.asarray(mask) > 0
            self._canvas.update_roi_overlay()
        self._schedule_mesh_preview()

    # ---- refinement brush ---------------------------------------------------------

    def set_refine_brush(self, mode: str, radius: int) -> None:
        """Arm the canvas refinement brush ('paint' or 'erase') at ``radius`` px."""
        self._canvas.set_brush_tool(mode, radius)

    def set_brush_radius(self, radius: int) -> None:
        self._canvas.set_brush_radius(radius)

    def clear_brush(self) -> None:
        self._canvas.clear_brush()

    def _on_brush_changed(self) -> None:
        mask = self._canvas.brush_mask()
        draft = self.controller.state.draft
        draft.refinement_mask_array = None if mask is None or not mask.any() else mask
        self.controller.state.mark_dirty()
        self.signals.params_changed.emit()

    # ---- mesh preview + subset hover ------------------------------------------------

    def _on_grid_toggled(self, checked: bool) -> None:
        self._subset_cb.setEnabled(checked)
        if not checked:
            self._subset_cb.setChecked(False)
            self._mesh_timer.stop()
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
            self._mesh_timer.start()

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

    def _generate_preview_mesh(self) -> None:
        """Build the preview mesh with the REAL pipeline grid code (debounced)."""
        if not self._grid_cb.isChecked() or not self._mesh_preview_applicable():
            self._hide_mesh_overlay()
            return

        draft = self.controller.state.draft
        rect = self._canvas.scene().sceneRect()
        img_h, img_w = int(rect.height()), int(rect.width())
        roi_mask = draft.roi_mask_array
        try:
            from al_dic_3d.runner import build_reference_mesh

            mask_f = None
            if roi_mask is not None:
                mask_f = (np.asarray(roi_mask) > 0).astype(np.float64)
            brush = draft.refinement_mask_array
            brush_f = (np.asarray(brush) > 0).astype(np.float64) if brush is not None else None
            mesh = build_reference_mesh(
                img_h,
                img_w,
                tuple(int(v) for v in draft.roi),
                winsize=int(draft.winsize),
                winstepsize=int(draft.winstepsize),
                winsize_min=int(draft.winsize_min),
                refine_inner=bool(draft.refine_inner),
                refine_outer=bool(draft.refine_outer),
                refinement_level=int(draft.refinement_level),
                refinement_brush=brush_f,
                mask=mask_f,
            )
            coords = np.asarray(mesh.coordinates_fem, dtype=np.float64)
            elements = np.asarray(mesh.elements_fem, dtype=np.int64)
            valid = self._node_valid_mask(coords, roi_mask)
        except Exception:  # noqa: BLE001 - preview is best-effort, never block the GUI
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

    @staticmethod
    def _node_valid_mask(coords: np.ndarray, roi_mask) -> np.ndarray:
        """Per-node boolean: True when the node lies inside the ROI mask."""
        n = coords.shape[0]
        if roi_mask is None:
            return np.ones(n, dtype=bool)
        m = np.asarray(roi_mask) > 0
        h, w = m.shape
        ix = np.clip(np.round(coords[:, 0]).astype(int), 0, w - 1)
        iy = np.clip(np.round(coords[:, 1]).astype(int), 0, h - 1)
        return m[iy, ix]

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
        self._viz_ctrl.clear_all()  # image size may have changed
        self.render()
        self._ensure_roi_ctrl()
        self._schedule_mesh_preview()

    def _on_results(self) -> None:
        result = self.controller.state.result
        if result is not None:
            self._field_range_cache: dict = {}
        self._viz_ctrl.clear_all()
        self.render()

    # ---- rendering ------------------------------------------------------------------

    def render(self) -> None:
        """Redraw the current view (2D frame + overlay, or the 3D surface)."""
        if self._stack.currentIndex() == 1:
            self._render_3d()
            return

        draft = self.controller.state.draft
        cam = self.signals.current_camera
        files = draft.left if cam == "L" else draft.right
        k = self.signals.current_frame

        if not files:
            self._canvas.clear_image()
            self._colorbar.setVisible(False)
            return
        k = min(k, len(files) - 1)
        # Reference-frame plotting (2D idiom): the toggle switches GEOMETRY —
        # background image and node positions — while the field VALUES stay
        # those of frame k. Without results there is no geometry to switch.
        has_result = self.controller.state.result is not None
        bg = k if self.signals.show_deformed or not has_result else 0
        try:
            self._canvas.set_image_file(files[bg])
        except Exception:  # noqa: BLE001 - a bad frame must not crash the canvas
            self._canvas.clear_image()
            return

        self._render_overlay(k)
        self._sync_roi()

    def _render_3d(self) -> None:
        result = self.controller.state.result
        if result is None:
            self._view3d.show_message(
                self.tr("3D view — run an analysis to see the reconstructed surface.")
            )
            return
        k = min(self.signals.current_frame, result.reconstruction.n_frames - 1)
        vals = self._field_values(result, k)
        if vals is None:
            self._view3d.show_message(self.tr("Selected field is not available."))
            return
        if self.signals.color_auto:
            vmin, vmax = self._field_range(result)
        else:
            vmin, vmax = self.signals.color_min, self.signals.color_max
        self._view3d.update_view(
            result.reconstruction.points[k],
            vals,
            field_label=_FIELD_LABELS.get(self.signals.display_field, self.signals.display_field),
            cmap=self.signals.colormap,
            vmin=vmin,
            vmax=vmax,
            rig=self._load_rig(),
            ref_coords=result.ref_coords,
        )

    def _field_values(self, result, k: int) -> np.ndarray | None:
        field = self.signals.display_field
        rec = result.reconstruction
        if field in ("U", "V", "W"):
            return rec.displacement[k][:, ("U", "V", "W").index(field)]
        if field == "mag":
            return np.linalg.norm(rec.displacement[k], axis=1)
        if field in _STRAIN_IDS and result.strain is not None:
            return getattr(result.strain, field)[k]
        return None

    def _field_range(self, result) -> tuple[float, float]:
        """Stable color range over ALL frames (playback doesn't re-scale)."""
        field = self.signals.display_field
        cache = getattr(self, "_field_range_cache", None)
        if cache is None:
            cache = self._field_range_cache = {}
        if field in cache:
            return cache[field]
        lo, hi = np.inf, -np.inf
        for k in range(result.reconstruction.n_frames):
            vals = self._field_values(result, k)
            if vals is None or not np.isfinite(vals).any():
                continue
            lo = min(lo, float(np.nanmin(vals)))
            hi = max(hi, float(np.nanmax(vals)))
        if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
            lo, hi = 0.0, 1.0
        cache[field] = (lo, hi)
        return lo, hi

    def _clear_overlay(self) -> None:
        self._canvas.set_overlay_pixmap(None)
        self._canvas.set_points_pixmap(None)
        self._colorbar.setVisible(False)

    def _render_overlay(self, k: int) -> None:
        result = self.controller.state.result
        if result is None:
            self._clear_overlay()
            return

        cs = result.correspondence
        if k >= cs.n_frames:
            self._clear_overlay()
            return
        cam = self.signals.current_camera
        x_cam = cs.xL if cam == "L" else cs.xR
        # Geometry follows the toggle (frame-k vs frame-1 positions); the
        # field values below always belong to the navigated frame k.
        deformed = bool(self.signals.show_deformed) and k > 0
        pts = x_cam[k] if deformed else x_cam[0]
        ref_pts = x_cam[0]
        vals = self._field_values(result, k)
        if vals is None:
            self._clear_overlay()
            return
        ref_uv = None
        if deformed:
            d = x_cam[k] - x_cam[0]  # 2D ref_uv contract: x_k - x_1 per node
            ref_uv = (d[:, 0], d[:, 1])

        # LEFT camera: the user-drawn reference ROI mask bounds the field.
        # RIGHT camera: no drawn mask exists (ROI tools live on the left
        # view), so the renderer falls back to the valid-node hull support.
        roi_mask = None
        if cam == "L":
            drawn = self.controller.state.draft.roi_mask_array
            if drawn is not None:
                roi_mask = np.asarray(drawn) > 0

        # Auto colorbar range from VISIBLE nodes only (2D visible_values
        # contract): clipped-by-mask nodes must not stretch the range. The
        # range is written back so switching Auto off starts from live values.
        if self.signals.color_auto:
            vis = visible_values(vals, ref_pts, roi_mask)
            finite = vis[np.isfinite(vis)]
            if finite.size:
                vmin, vmax = float(finite.min()), float(finite.max())
            else:
                vmin, vmax = 0.0, 1.0
            self.signals.color_min, self.signals.color_max = vmin, vmax
        else:
            vmin, vmax = self.signals.color_min, self.signals.color_max

        img_rect = self._canvas.scene().sceneRect()
        w, h = int(img_rect.width()), int(img_rect.height())
        if w <= 0 or h <= 0:
            self._clear_overlay()
            return

        try:
            pixmap, xg, yg, out_step = self._viz_ctrl.render_field(
                k,
                f"{cam}:{self.signals.display_field}",
                pts,
                vals,
                img_shape=(h, w),
                mesh_step=int(self.controller.state.draft.winstepsize),
                cmap=self.signals.colormap,
                vmin=vmin,
                vmax=vmax,
                roi_mask=roi_mask,
                deformed=deformed,
                ref_uv=ref_uv,
                ref_pts=ref_pts,
            )
        except Exception as exc:  # noqa: BLE001 - a render bug must not kill the GUI
            self.signals.log.emit(f"overlay render failed: {type(exc).__name__}: {exc}", "error")
            self._clear_overlay()
            return
        if pixmap is None:
            self._clear_overlay()
            return

        self._canvas.set_overlay_pixmap(pixmap)
        self._canvas.set_overlay_geometry(float(out_step), float(xg.min()), float(yg.min()))
        self._canvas.set_overlay_opacity(self.signals.overlay_alpha)

        # Optional node markers on top of the dense field (small fixed dots).
        if self._show_points_cb.isChecked():
            self._canvas.set_points_pixmap(
                scatter_field_pixmap(
                    pts,
                    vals,
                    w,
                    h,
                    cmap_name=self.signals.colormap,
                    vmin=vmin,
                    vmax=vmax,
                    radius=2.0,
                )
            )
        else:
            self._canvas.set_points_pixmap(None)

        self._colorbar.update_params(
            self.signals.colormap, vmin, vmax, _FIELD_LABELS.get(self.signals.display_field, "")
        )
        self._colorbar.setVisible(True)

    # ---- overlay geometry ------------------------------------------------------------

    def eventFilter(self, obj, event) -> bool:  # noqa: N802 (Qt override)
        if obj is self._canvas.viewport() and event.type() == QEvent.Type.Resize:
            self._colorbar.setGeometry(0, 0, obj.width(), obj.height())
            self._mesh_overlay.setGeometry(0, 0, obj.width(), obj.height())
            self._config_overlay.reposition()
        return super().eventFilter(obj, event)
