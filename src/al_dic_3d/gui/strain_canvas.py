"""Strain-window rendering (split out of ``strain_window.py`` for the 800-line cap).

The strain window renders the dense strain overlay on the LEFT-camera image
through a PRIVATE :class:`VizController3D` (namespaced ``strain_window:<field>``)
— V-view gives it the main canvas's treatment:

* background frames go through its own :class:`FramePrefetcher` +
  :class:`FrameShower` (it had no prefetcher: every deformed-mode frame change
  decoded the image on the GUI thread);
* the overlay goes through an :class:`OverlayPresenter` (inline when cheap,
  generation-tagged worker render when heavy — the last overlay stays up);
* the node step is the RUN's (:func:`run_node_step`), never the live draft;
* the drawn ROI is converted to bool once per ROI array (identity cache) and
  doubles as the crack barrier without a full-image float copy.

Methods run in the context of ``StrainWindow3D`` and use its attributes; this
module carries no user-facing strings except the log line it relays.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

import numpy as np

from al_dic_3d.gui.controllers.viz_controller import VizController3D
from al_dic_3d.gui.strain_render import prepare_strain_render, trim_count
from al_dic_3d.gui.widgets.frame_prefetcher import FramePrefetcher
from al_dic_3d.gui.widgets.overlay_presenter import (
    FrameShower,
    OverlayPresenter,
    OverlayRequest,
    pump_until,
)
from al_dic_3d.gui.widgets.strain_field_selector import STRAIN_FIELD_LABELS
from al_dic_3d.viz3d.raster import overlay_origin
from al_dic_3d.viz3d.runstep import run_node_step

if TYPE_CHECKING:
    from al_dic.gui.widgets.colorbar_overlay import ColorbarOverlay

    from al_dic_3d.gui.controller import WorkflowController
    from al_dic_3d.gui.widgets.strain_support import PickCanvas


class StrainRenderMixin:
    """Background + dense strain overlay for :class:`StrainWindow3D`."""

    if TYPE_CHECKING:  # attributes owned by StrainWindow3D.__init__
        _canvas: PickCanvas
        _colorbar: ColorbarOverlay
        _frame: int
        _last_rendered: tuple[float, float]
        controller: WorkflowController

    def _init_strain_render(self) -> None:
        self._viz_ctrl = VizController3D()  # private dense renderer + caches
        self._prefetcher = FramePrefetcher(self)
        self._frames = FrameShower(self._canvas, self._prefetcher, self)
        self._frames.shown_async.connect(self._on_strain_frame_landed)
        self._overlays = OverlayPresenter(self._viz_ctrl, self)
        self._roi_bool: tuple[object, np.ndarray] | None = None
        self._run_step_memo: tuple[object, int] | None = None

    # ---- idle probes (tests / benchmarks) ------------------------------------

    def render_idle(self) -> bool:
        return self._overlays.is_idle() and self._frames.is_idle()

    def wait_render_idle(self, timeout_ms: int = 30_000) -> bool:
        ok = self._overlays.wait_idle(timeout_ms)
        return ok and pump_until(self.render_idle, timeout_ms, self._prefetcher.wait_idle)

    def _cancel_render_work(self) -> None:
        self._overlays.cancel()
        self._frames.cancel()
        self._run_step_memo = None

    # ---- inputs ------------------------------------------------------------------

    def _run_step(self) -> int:
        """The node step of the run behind the current result (never the draft)."""
        result = self.controller.state.result
        draft_step = int(self.controller.state.draft.winstepsize)
        if result is None:
            return draft_step
        memo = self._run_step_memo
        if memo is not None and memo[0] is result:
            return memo[1]
        step = run_node_step(result, default=draft_step)
        self._run_step_memo = (result, step)
        return step

    def _roi_bool_mask(self) -> np.ndarray | None:
        """The drawn LEFT ROI as bool, converted once per draft array."""
        drawn = self.controller.state.draft.roi_mask_array
        if drawn is None:
            return None
        cached = self._roi_bool
        if cached is not None and cached[0] is drawn:
            return cached[1]
        mask = np.asarray(drawn) > 0
        self._roi_bool = (drawn, mask)
        return mask

    # ---- rendering -------------------------------------------------------------

    def _try_load_background(self, img_idx: int) -> None:
        """Best-effort LEFT-camera background (prefetched / inline / worker)."""
        files = self.controller.state.draft.left
        if not files:
            return
        idx = min(img_idx, len(files) - 1)
        path = files[idx]
        try:
            self._frames.show(path)
        except Exception:  # noqa: BLE001 - a bad frame must not crash the canvas
            return
        neighbors = [path]
        if idx + 1 < len(files):
            neighbors.append(files[idx + 1])
        if idx - 1 >= 0:
            neighbors.append(files[idx - 1])
        self._prefetcher.request(neighbors)

    def _on_strain_frame_landed(self, _path: str, resized: bool) -> None:
        if resized:
            self._render()

    def _on_roi_changed(self) -> None:
        """The ROI was edited (main window): the display mask follows it."""
        self._viz_ctrl.invalidate_masks()  # drop grids built on the old mask
        if self.isVisible():
            self._render()

    def _clear_overlay(self) -> None:
        self._overlays.cancel()
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
        # renderer falls back to the valid-node support.
        roi_mask = self._roi_bool_mask()
        # Display mask + geometry + range prep (Qt-free helper, shared with the
        # export paths). The crack barrier is the bool ROI itself (reference
        # view only, like the export).
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
        barrier = rd.barrier_mask
        self._last_rendered = (rd.vmin, rd.vmax)

        rect = self._canvas.scene().sceneRect()
        w, h = int(rect.width()), int(rect.height())
        if w <= 0 or h <= 0:
            self._clear_overlay()
            return
        cmap = self._cmap_combo.currentText()
        req = OverlayRequest(
            frame_idx=k,
            field_name=f"strain_window:{field}",
            nodes=rd.pts,
            values=rd.vals,
            img_shape=(h, w),
            mesh_step=self._run_step(),
            cmap=cmap,
            vmin=rd.vmin,
            vmax=rd.vmax,
            roi_mask=roi_mask,
            deformed=deformed,
            ref_uv=rd.ref_uv,
            ref_pts=rd.ref_pts,
            barrier_mask=barrier,
        )
        label = STRAIN_FIELD_LABELS.get(field, field)
        self._overlays.request(
            req,
            partial(self._apply_strain_overlay, cmap, rd.vmin, rd.vmax, label),
            self._on_strain_render_error,
        )

    def _apply_strain_overlay(self, cmap: str, vmin: float, vmax: float, label, out) -> None:
        pixmap, xg, yg, out_step = out
        if pixmap is None:
            self._canvas.set_overlay_pixmap(None)
            self._colorbar.setVisible(False)
            return
        self._canvas.set_overlay_pixmap(pixmap)
        self._canvas.set_overlay_geometry(float(out_step), *overlay_origin(xg, yg, out_step))
        self._canvas.set_overlay_opacity(self._opacity_slider.value() / 100.0)
        vp = self._canvas.viewport()
        self._colorbar.setGeometry(0, 0, vp.width(), vp.height())
        self._colorbar.update_params(cmap, vmin, vmax, label)
        self._colorbar.setVisible(True)

    def _on_strain_render_error(self, message: str) -> None:
        self._log(self.tr("Could not draw the overlay: {0}").format(message), "error")
        self._canvas.set_overlay_pixmap(None)
        self._colorbar.setVisible(False)
