"""Strain-window RIGID MOTION wiring (split out of ``strain_window.py`` for the cap).

The panel edits the project's rigid-motion setting through
:class:`RigidMotionController3D`; every change swaps the run result (refit on the
measured reconstruction) and is announced with ``results_changed``, so the main
window, the 3D view and this window redraw from one corrected result. The fit
region is drawn on this window's canvas with the ROI shape tools, into a private
:class:`ROIController` (the main window's ROI is untouched) shown in amber.

Methods run in the context of ``StrainWindow3D`` and use its attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from al_dic.gui.widgets.collapsible_section import CollapsibleSection
from PySide6.QtCore import Qt

from al_dic_3d.gui.controllers.rigid_motion_controller import (
    STATE_NOT_REMOVED,
    STATE_OFF,
    STATE_REMOVED,
    RigidMotionController3D,
)
from al_dic_3d.gui.controllers.roi_controller import ROIController
from al_dic_3d.gui.rigid_motion_text import mode_name
from al_dic_3d.gui.widgets.rigid_motion_panel import RigidMotionPanel3D

if TYPE_CHECKING:
    from PySide6.QtWidgets import QLabel

    from al_dic_3d.gui.controller import WorkflowController
    from al_dic_3d.gui.state import GuiSignals
    from al_dic_3d.gui.widgets.strain_support import PickCanvas


class StrainRigidMotionMixin:
    """RIGID MOTION section of :class:`StrainWindow3D`."""

    if TYPE_CHECKING:  # attributes owned by StrainWindow3D.__init__
        _canvas: PickCanvas
        _stale_lbl: QLabel
        _frame: int
        controller: WorkflowController
        signals: GuiSignals

    def _init_rigid_motion(self) -> CollapsibleSection:
        self._rbm_ctrl = RigidMotionController3D(self.controller)
        self._rbm_roi: ROIController | None = None
        self._rbm_panel = RigidMotionPanel3D()
        panel = self._rbm_panel
        panel.mode_changed.connect(self._on_rbm_mode)
        panel.draw_requested.connect(self._on_rbm_draw)
        panel.use_all_requested.connect(self._on_rbm_use_all)
        panel.show_region_toggled.connect(lambda _on: self._show_rbm_region())
        self._canvas.roi_mask_edited.connect(self._on_rbm_region_edited)
        section = CollapsibleSection(self.tr("RIGID MOTION"), expanded=True)
        section.add_widget(panel)
        return section

    # ---- public accessors (tests) -------------------------------------------------

    def rigid_motion_panel(self) -> RigidMotionPanel3D:
        return self._rbm_panel

    def rigid_motion_roi(self) -> ROIController | None:
        """The fit-region mask engine the draw tools rasterize into (synced to the draft)."""
        return self._sync_rbm_roi()

    # ---- handlers --------------------------------------------------------------------

    def _on_rbm_mode(self, mode: str) -> None:
        self._apply_rbm(mode, self._rbm_ctrl.region())

    def _on_rbm_use_all(self) -> None:
        self._apply_rbm(self._rbm_ctrl.mode(), None)

    def _on_rbm_draw(self, shape: str, mode: str) -> None:
        if self._sync_rbm_roi() is None:
            self._log(self.tr("Run 3D analysis first — no results to post-process."), "warning")
            return
        # The region lives on the frame-1 reference image: draw there.
        self._cancel_pick()
        self._frame = 0
        self._nav.set_state(self._frame_count(), 0)
        self._deformed_cb.setChecked(False)
        self._show_rbm_region()
        self._canvas.set_tool(shape, mode)

    def _on_rbm_region_edited(self) -> None:
        if self._rbm_roi is None:
            return
        mask = self._rbm_roi.mask
        self._apply_rbm(self._rbm_ctrl.mode(), mask.copy() if mask.any() else None)

    def _apply_rbm(self, mode: str, region) -> None:
        from PySide6.QtWidgets import QApplication

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self._rbm_ctrl.apply(mode, region)
        except ValueError as exc:
            self._log(self.tr("Rigid motion not removed: {0}").format(exc), "warning")
            self._refresh_rigid_motion()  # back to the stored setting
            return
        finally:
            QApplication.restoreOverrideCursor()
        if self.controller.state.result is None:
            self._refresh_rigid_motion()
            return
        self._viz_ctrl.clear_all()
        self.signals.results_changed.emit()  # every view redraws (this one included)

    # ---- display -----------------------------------------------------------------------

    def _sync_rbm_roi(self) -> ROIController | None:
        """The private fit-region controller, holding the draft's region."""
        shape = self._rbm_ctrl.image_shape()
        if shape is None:
            return None
        if self._rbm_roi is None or self._rbm_roi.shape != shape:
            self._rbm_roi = ROIController(shape)
            self._canvas.set_roi_controller(self._rbm_roi)
        region = self._rbm_ctrl.region()
        if region is not None and region.shape == shape:
            self._rbm_roi.mask = region.copy()
        else:
            self._rbm_roi.mask = np.zeros(shape, dtype=bool)
        return self._rbm_roi

    def _show_rbm_region(self) -> None:
        self._sync_rbm_roi()
        self._canvas.set_region_visible(self._rbm_panel.region_shown())
        self._canvas.update_roi_overlay()

    def _refresh_rigid_motion(self) -> None:
        ctrl, panel = self._rbm_ctrl, self._rbm_panel
        busy = self._worker is not None and self._worker.isRunning()
        has_result = self.controller.state.result is not None
        panel.set_mode(ctrl.mode())
        panel.set_controls_enabled(not busy)
        panel.set_tools_enabled(has_result and not busy)
        n_region = ctrl.region_node_count()
        if ctrl.region() is None:
            panel.set_region_text(self.tr("Fit region: all valid points"))
        elif n_region is None:
            panel.set_region_text(self.tr("Fit region: drawn"))
        else:
            panel.set_region_text(self.tr("Fit region: drawn ({0} nodes)").format(n_region))
        st = ctrl.status()
        if st.state == STATE_OFF:
            panel.set_status(self.tr("Rigid motion is not removed."))
        elif st.state == STATE_REMOVED:
            panel.set_status(
                self.tr("Removed ({0}), fitted on {1} points.").format(
                    mode_name(st.mode), st.n_used
                )
            )
        elif st.state == STATE_NOT_REMOVED:
            reason = st.reason or self.tr("the fit region does not cover this run")
            panel.set_status(self.tr("Not removed: {0}").format(reason), warning=True)
        else:
            panel.set_status(self.tr("It will be removed once the analysis has run."))
        panel.set_rows(ctrl.rows(), self.tr("Not fitted on this frame: {0}"))
        panel.set_current_frame(self._frame)
        self._show_rbm_region()
        stale_text = self.tr("⚠ Rigid-motion setting changed -- click Compute Strain")
        if ctrl.strain_is_stale():
            self._stale_lbl.setText(stale_text)
        elif self._stale_lbl.text() == stale_text:
            self._stale_lbl.setText("")
