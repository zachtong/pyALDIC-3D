"""Seed-point (F2) + refinement-brush tool relays for the central canvas.

Split out of :class:`al_dic_3d.gui.panels.canvas_area.CanvasArea3D` (which
mixes this in) purely to keep that file under the 800-line cap — the methods
are thin state relays between the sidebar tool buttons, the canvas tool state
machine, and the project draft. They run in the context of ``CanvasArea3D``
and use its attributes: ``_canvas``, ``_stack``, ``controller``, ``signals``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QStackedWidget

    from al_dic_3d.gui.controller import WorkflowController
    from al_dic_3d.gui.state import GuiSignals
    from al_dic_3d.gui.widgets.image_view import ImageCanvas3D


class CanvasToolsMixin:
    """Seed + brush relays; host class provides the attributes below."""

    if TYPE_CHECKING:  # attributes owned by CanvasArea3D.__init__
        _canvas: ImageCanvas3D
        _stack: QStackedWidget
        controller: WorkflowController
        signals: GuiSignals

    # ---- seed point (F2) -----------------------------------------------------

    def start_seed_tool(self) -> None:
        """Arm the one-shot seed click tool on the canvas (Esc cancels)."""
        self._canvas.set_seed_tool(True)

    def cancel_seed_tool(self) -> None:
        self._canvas.set_seed_tool(False)

    def clear_seed(self) -> None:
        """Drop the Starting Point from the draft and the canvas."""
        draft = self.controller.state.draft
        if draft.seed_point is None:
            return
        draft.seed_point = None
        self._canvas.set_seed_marker(None)
        self.controller.state.mark_dirty()
        self.signals.log.emit("starting point cleared", "info")
        self.signals.params_changed.emit()

    def _on_seed_clicked(self, x: float, y: float) -> None:
        """Persist the placed seed (replaces any previous point)."""
        draft = self.controller.state.draft
        draft.seed_point = (float(x), float(y))
        self.controller.state.mark_dirty()
        self.signals.log.emit(f"starting point placed at ({x:.1f}, {y:.1f})", "info")
        self._sync_seed_marker()
        self.signals.params_changed.emit()

    def _sync_seed_marker(self) -> None:
        """Marker shows on the LEFT camera's frame 1 only (the seed's home view)."""
        draft = self.controller.state.draft
        show = (
            self._stack.currentIndex() == 0
            and self.signals.current_camera == "L"
            and self.signals.current_frame == 0
            and self._canvas.has_image
            and draft.seed_point is not None
        )
        self._canvas.set_seed_marker(draft.seed_point if show else None)

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
