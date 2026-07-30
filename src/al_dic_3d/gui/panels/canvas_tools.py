"""Seed-point (F2) + brush relays, context menu, hints, field-value lookup.

Split out of :class:`al_dic_3d.gui.panels.canvas_area.CanvasArea3D` (which
mixes this in) purely to keep that file under the 800-line cap — the methods
are thin state relays between the sidebar tool buttons, the canvas tool state
machine, and the project draft, plus the G3.1b right-click menu and the G3.3
first-launch quick-start hint. They run in the context of ``CanvasArea3D``
and use its attributes: ``_canvas``, ``_stack``, ``controller``, ``signals``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from al_dic_3d.gui.display_units import STRAIN_LABELS, velocity_magnitude

if TYPE_CHECKING:
    from PySide6.QtWidgets import QLabel, QStackedWidget

    from al_dic_3d.gui.controller import WorkflowController
    from al_dic_3d.gui.state import GuiSignals
    from al_dic_3d.gui.widgets.image_view import ImageCanvas3D


class CanvasToolsMixin:
    """Seed + brush relays; host class provides the attributes below."""

    if TYPE_CHECKING:  # attributes owned by CanvasArea3D.__init__
        _canvas: ImageCanvas3D
        _stack: QStackedWidget
        _empty_hint: QLabel
        controller: WorkflowController
        signals: GuiSignals

    # ---- seed point (F2) -----------------------------------------------------

    def start_seed_tool(self) -> None:
        """Arm the one-shot seed click tool on the canvas (Esc cancels)."""
        self._canvas.set_seed_tool(True)

    def cancel_seed_tool(self) -> None:
        self._canvas.set_seed_tool(False)

    def clear_seed(self) -> None:
        """Drop ALL Starting Points from the draft and the canvas (Batch S)."""
        draft = self.controller.state.draft
        if not draft.seed_points and draft.seed_point is None:
            return
        draft.seed_points = []
        draft.seed_point = None
        self._canvas.set_seed_markers([])
        self.controller.state.mark_dirty()
        self.signals.log.emit("starting points cleared", "info")
        self.signals.params_changed.emit()

    def _is_left_reference_view(self) -> bool:
        """True only on the LEFT camera, frame 1, 2D canvas — the seeds' home view."""
        return (
            self._stack.currentIndex() == 0
            and self.signals.current_camera == "L"
            and self.signals.current_frame == 0
            and self._canvas.has_image
        )

    def _on_seed_clicked(self, x: float, y: float) -> None:
        """Append a placed Starting Point to the list (Batch S multi-seed).

        The multi-seed tool deliberately stays armed across clicks, so — unlike
        the one-shot ROI tools — a click can land after the user navigated to
        another camera or frame. A Starting Point is a LEFT-camera frame-1
        coordinate, so a click off that view would record a bogus pixel that is
        counted but never shown (its marker only paints on L/frame 1). Refuse it
        at click time so a click can NEVER record a non-L/frame-1 coordinate.
        """
        draft = self.controller.state.draft
        if not self._is_left_reference_view():
            self.signals.log.emit(
                self.tr(
                    "Starting points are placed on the LEFT camera, frame 1 — "
                    "switch there to add a point"
                ),
                "warning",
            )
            return
        draft.seed_points = [*draft.seed_points, (float(x), float(y))]
        draft.seed_point = draft.seed_points[0]  # primary stays seed_points[0]
        self.controller.state.mark_dirty()
        n = len(draft.seed_points)
        self.signals.log.emit(f"starting point {n} placed at ({x:.1f}, {y:.1f})", "info")
        self._sync_seed_marker()
        self.signals.params_changed.emit()

    def _on_seed_remove(self, x: float, y: float) -> None:
        """Remove the Starting Point nearest to ``(x, y)`` (right-click, Batch S)."""
        import numpy as np

        draft = self.controller.state.draft
        if not draft.seed_points:
            return
        pts = np.asarray(draft.seed_points, dtype=float)
        idx = int(np.argmin(np.sum((pts - np.array([x, y])) ** 2, axis=1)))
        removed = draft.seed_points[idx]
        draft.seed_points = [p for i, p in enumerate(draft.seed_points) if i != idx]
        draft.seed_point = draft.seed_points[0] if draft.seed_points else None
        self.controller.state.mark_dirty()
        self.signals.log.emit(
            f"starting point removed at ({removed[0]:.1f}, {removed[1]:.1f})", "info"
        )
        self._sync_seed_marker()
        self.signals.params_changed.emit()

    def _sync_seed_marker(self) -> None:
        """Markers show on the LEFT camera's frame 1 only (the seeds' home view)."""
        draft = self.controller.state.draft
        show = self._is_left_reference_view() and bool(draft.seed_points)
        self._canvas.set_seed_markers(draft.seed_points if show else [])

    # ---- refinement brush ------------------------------------------------------

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

    def _sync_brush_from_draft(self) -> None:
        """Draft -> canvas: mirror restored refinement zones into the paint buffer.

        A reopened session carries its painted zones on the draft (Z1); the
        canvas keeps its own stroke buffer, so without this the zones would be
        invisible and the next stroke would overwrite them.
        """
        mask = self.controller.state.draft.refinement_mask_array
        current = self._canvas.brush_mask()
        if mask is None:
            if current is not None:
                self._canvas.set_brush_mask(None)
            return
        if current is None or not np.array_equal(current > 0, np.asarray(mask) > 0):
            self._canvas.set_brush_mask(np.asarray(mask))

    # ---- canvas context menu (G3.1b) ---------------------------------------------

    def _on_canvas_menu(self, global_pos) -> None:
        """Right-CLICK (no drag, no tool armed) menu on the 2D canvas."""
        from PySide6.QtWidgets import QMenu

        draft = self.controller.state.draft
        menu = QMenu(self)
        fit = menu.addAction(self.tr("Fit"))
        fit.triggered.connect(self._canvas.fit_to_view)
        full = menu.addAction(self.tr("Zoom to 100%"))
        full.triggered.connect(self._canvas.zoom_to_100)
        menu.addSeparator()
        copy = menu.addAction(self.tr("Copy image to clipboard"))
        copy.triggered.connect(self._copy_canvas_to_clipboard)
        menu.addSeparator()
        clear_roi = menu.addAction(self.tr("Clear ROI"))
        clear_roi.setEnabled(draft.roi_mask_array is not None)
        clear_roi.triggered.connect(self.roi_clear)
        clear_seed = menu.addAction(self.tr("Clear seed points"))
        clear_seed.setEnabled(bool(draft.seed_points))
        clear_seed.triggered.connect(self.clear_seed)
        menu.exec(global_pos)

    def _copy_canvas_to_clipboard(self) -> None:
        """WYSIWYG copy: grab the viewport (image + overlays) as shown."""
        from PySide6.QtGui import QGuiApplication

        QGuiApplication.clipboard().setPixmap(self._canvas.viewport().grab())
        self.signals.log.emit("canvas image copied to clipboard", "info")

    # ---- empty-state quick-start hint (G3.3) ---------------------------------------

    def _init_empty_hint(self) -> None:
        """Centered quick-start text shown until the first image loads."""
        from al_dic.gui.theme import COLORS
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QLabel

        hint = QLabel(self._canvas.viewport())
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setWordWrap(True)
        hint.setText(
            self.tr(
                "1. Drop the left/right camera folders in the sidebar\n"
                "2. Calibrate or import calibration\n"
                "3. Draw the ROI and Run"
            )
        )
        hint.setStyleSheet(
            f"color: {COLORS.TEXT_MUTED}; background: transparent; "
            f"font-size: 13px; line-height: 150%;"
        )
        hint.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._empty_hint = hint
        self._update_empty_hint()

    def _update_empty_hint(self) -> None:
        """Show only on the 2D page while no image is loaded; keep centered."""
        show = self._stack.currentIndex() == 0 and not self._canvas.has_image
        if show:
            vp = self._canvas.viewport()
            self._empty_hint.setGeometry(0, vp.height() // 2 - 50, vp.width(), 100)
        self._empty_hint.setVisible(show)

    # ---- per-frame field values (moved here for the 800-line cap) -------------

    def _field_values(self, result, k: int) -> np.ndarray | None:
        field = self.signals.display_field
        rec = result.reconstruction
        if field in ("U", "V", "W"):
            return rec.displacement[k][:, ("U", "V", "W").index(field)]
        if field == "mag":
            # P2.6: |D| is derived per frame — cache it (results-scoped LRU)
            # so scrubbing back and forth never recomputes the norm.
            mag = self._mag_cache.get(k)
            if mag is None:
                mag = np.linalg.norm(rec.displacement[k], axis=1)
                self._mag_cache[k] = mag
            return mag
        if field == "velocity":
            # Q2: |D_k − D_{k−1}| × frame rate; frame 0 has no predecessor
            # (all-NaN). Cached in mm/frame (P2 pattern), scaled on read.
            vel = self._vel_cache.get(k)
            if vel is None:
                prev = rec.displacement[k - 1] if k > 0 else None
                vel = velocity_magnitude(rec.displacement[k], prev)
                self._vel_cache[k] = vel
            return vel * float(self.signals.frame_rate)
        if field in STRAIN_LABELS and result.strain is not None:
            return getattr(result.strain, field)[k]
        return None

    def _drawn_roi_bool(self) -> np.ndarray | None:
        """The drawn ROI mask as bool, cached by array identity (P2.6).

        Every ROI edit stores a FRESH array on the draft (``commit_roi_mask``
        copies), so identity is a valid cache key — the old per-render
        ``np.asarray(mask) > 0`` allocated a full-image bool each frame change.
        """
        drawn = self.controller.state.draft.roi_mask_array
        if drawn is None:
            return None
        cached = self._roi_bool_cache
        if cached is not None and cached[0] is drawn:
            return cached[1]
        mask = np.asarray(drawn) > 0
        self._roi_bool_cache = (drawn, mask)
        return mask
