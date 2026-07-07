"""Central canvas — toolbar, layered image canvas, overlays, playback bar.

The 2D ``CanvasArea`` idiom: a 36 px toolbar (Fit / 100% / zoom, view toggles on
the right), the zoomable canvas with a top-left config card and a right-edge
colorbar (both reused/mirrored from 2D), and the 36 px frame navigator at the
bottom. 3D content: the background is the CURRENT CAMERA's frame; results render
as a colormapped scatter of the tracked correspondence points (the 3D pipeline's
native representation), colored by the selected world-frame field.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from al_dic.gui.icons import icon_maximize, icon_zoom_in, icon_zoom_out
from al_dic.gui.theme import COLORS
from al_dic.gui.widgets.colorbar_overlay import ColorbarOverlay
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.gui.state import GuiSignals
from al_dic_3d.gui.widgets.config_overlay import ConfigOverlay3D
from al_dic_3d.gui.widgets.frame_navigator import FrameNavigator3D
from al_dic_3d.gui.widgets.image_view import ImageCanvas3D

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

        self._show_points_cb = QCheckBox(self.tr("Show Points"))
        self._show_points_cb.setChecked(True)
        self._show_points_cb.toggled.connect(lambda _c: self.render())
        tb.addWidget(self._show_points_cb)
        layout.addWidget(toolbar)

        # ---- canvas + overlays ----
        self._canvas = ImageCanvas3D()
        layout.addWidget(self._canvas, stretch=1)

        self._colorbar = ColorbarOverlay(self._canvas.viewport())
        self._config_overlay = ConfigOverlay3D(controller, self._canvas.viewport())
        self._canvas.viewport().installEventFilter(self)

        # ---- frame navigator ----
        self._frame_nav = FrameNavigator3D(signals)
        layout.addWidget(self._frame_nav)

        # ---- wiring ----
        btn_fit.clicked.connect(self._canvas.fit_to_view)
        btn_100.clicked.connect(self._canvas.zoom_to_100)
        btn_in.clicked.connect(self._canvas.zoom_in)
        btn_out.clicked.connect(self._canvas.zoom_out)

        self._canvas.roi_changed.connect(self._on_canvas_roi)
        signals.frame_changed.connect(lambda _i: self.render())
        signals.camera_changed.connect(lambda _c: self.render())
        signals.display_changed.connect(self.render)
        signals.results_changed.connect(self._on_results)
        signals.images_changed.connect(self._on_images)
        signals.roi_changed.connect(self._sync_roi)
        signals.params_changed.connect(self._config_overlay.refresh)

    @property
    def canvas(self) -> ImageCanvas3D:
        return self._canvas

    # ---- ROI edit mode ----------------------------------------------------------

    def set_roi_edit_mode(self, active: bool) -> None:
        self._canvas.set_roi_editable(active)

    def _on_canvas_roi(self, roi: tuple) -> None:
        self.controller.state.draft.roi = tuple(int(v) for v in roi)
        self.controller.state.mark_dirty()
        self.signals.roi_changed.emit()

    def _sync_roi(self) -> None:
        self._canvas.set_roi(self.controller.state.draft.roi)

    # ---- data-driven refresh ------------------------------------------------------

    def _on_images(self) -> None:
        draft = self.controller.state.draft
        n = max(len(draft.left), len(draft.right))
        self._frame_nav.set_frame_count(n)
        self._config_overlay.refresh()
        self.render()

    def _on_results(self) -> None:
        result = self.controller.state.result
        if result is not None:
            self._field_range_cache: dict = {}
        self.render()

    # ---- rendering ------------------------------------------------------------------

    def render(self) -> None:
        """Redraw the background frame and the result overlay for the current view."""
        draft = self.controller.state.draft
        cam = self.signals.current_camera
        files = draft.left if cam == "L" else draft.right
        k = self.signals.current_frame

        if not files:
            self._canvas.clear_image()
            self._colorbar.setVisible(False)
            return
        k = min(k, len(files) - 1)
        try:
            self._canvas.set_image_file(files[k])
        except Exception:  # noqa: BLE001 - a bad frame must not crash the canvas
            self._canvas.clear_image()
            return

        self._render_overlay(k)
        self._sync_roi()

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

    def _render_overlay(self, k: int) -> None:
        from matplotlib import colormaps

        result = self.controller.state.result
        show = self._show_points_cb.isChecked()
        if result is None or not show:
            self._canvas.set_overlay_pixmap(None)
            self._colorbar.setVisible(False)
            return

        cs = result.correspondence
        if k >= cs.n_frames:
            self._canvas.set_overlay_pixmap(None)
            self._colorbar.setVisible(False)
            return
        cam = self.signals.current_camera
        pts = cs.xL[k] if cam == "L" else cs.xR[k]
        vals = self._field_values(result, k)
        if vals is None:
            self._canvas.set_overlay_pixmap(None)
            self._colorbar.setVisible(False)
            return

        if self.signals.color_auto:
            vmin, vmax = self._field_range(result)
        else:
            vmin, vmax = self.signals.color_min, self.signals.color_max
        span = (vmax - vmin) or 1.0

        img_rect = self._canvas.scene().sceneRect()
        w, h = int(img_rect.width()), int(img_rect.height())
        if w == 0 or h == 0:
            return

        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        cmap = colormaps[self.signals.colormap]
        finite = np.isfinite(pts).all(axis=1) & np.isfinite(vals)
        radius = max(2.0, self.controller.state.draft.winstepsize * 0.30)
        norm = np.clip((vals[finite] - vmin) / span, 0.0, 1.0)
        rgba = (cmap(norm) * 255).astype(np.uint8)
        for (x, y), (r, g, b, _a) in zip(pts[finite], rgba, strict=True):
            painter.setBrush(QColor(int(r), int(g), int(b)))
            painter.drawEllipse(
                int(round(x - radius)),
                int(round(y - radius)),
                int(round(2 * radius)),
                int(round(2 * radius)),
            )
        painter.end()

        self._canvas.set_overlay_pixmap(pixmap)
        self._canvas.set_overlay_opacity(self.signals.overlay_alpha)
        self._colorbar.update_params(
            self.signals.colormap, vmin, vmax, _FIELD_LABELS.get(self.signals.display_field, "")
        )
        self._colorbar.setVisible(True)

    # ---- overlay geometry ------------------------------------------------------------

    def eventFilter(self, obj, event) -> bool:  # noqa: N802 (Qt override)
        if obj is self._canvas.viewport() and event.type() == QEvent.Type.Resize:
            self._colorbar.setGeometry(0, 0, obj.width(), obj.height())
            self._config_overlay.reposition()
        return super().eventFilter(obj, event)
