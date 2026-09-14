"""Result rendering for :class:`CanvasArea3D` (split out for the 800-line cap).

Background frames, the dense field overlay, and the 3D surface — V-view:

* frames go through a :class:`FrameShower` (prefetched -> blit, small cold ->
  inline, large cold -> worker decode while the last image stays up);
* the dense overlay goes through an :class:`OverlayPresenter` (Tier-2 hit or
  small -> inline, large -> generation-tagged worker render);
* the node step is the RUN's (``run_params``, else the reference spacing),
  never the live draft (H3);
* strain values hide ``~strain_valid`` nodes like the strain window and every
  export (M2), before the auto range sees them;
* the crack barrier is the drawn bool ROI itself — no per-render full-image
  float copy (H6).

Methods run in the context of ``CanvasArea3D`` and use its attributes.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

import numpy as np

from al_dic_3d.gui.controllers.viz_controller import VizController3D, auto_range, visible_values
from al_dic_3d.gui.display_units import display_field_key, field_display_factor, field_label
from al_dic_3d.gui.widgets.frame_prefetcher import FramePrefetcher
from al_dic_3d.gui.widgets.overlay_presenter import (
    FrameShower,
    LazyValue,
    OverlayPresenter,
    OverlayRequest,
    pump_until,
)
from al_dic_3d.viz3d.raster import overlay_origin
from al_dic_3d.viz3d.runstep import run_node_step

if TYPE_CHECKING:
    from al_dic.gui.widgets.colorbar_overlay import ColorbarOverlay
    from PySide6.QtWidgets import QLabel, QStackedWidget

    from al_dic_3d.gui.controller import WorkflowController
    from al_dic_3d.gui.state import GuiSignals
    from al_dic_3d.gui.widgets.image_view import ImageCanvas3D
    from al_dic_3d.gui.widgets.mesh_overlay import MeshOverlay
    from al_dic_3d.gui.widgets.view3d import View3D


def _warp_to_right(mask_left, xl0, xr0, log) -> np.ndarray | None:
    """The left ROI as the right camera's display support (worker-safe).

    Uses the shared display helper (the image / animation exports call the same
    one, so the right-camera canvas and exports agree); ``None`` -> hull fallback.
    """
    from al_dic_3d.viz3d import maskwarp

    helper = getattr(maskwarp, "right_camera_mask", None)
    try:
        if helper is not None:
            return helper(mask_left, xl0, xr0, mask_left.shape)
        return maskwarp.warp_mask_left_to_right(mask_left, xl0, xr0, mask_left.shape)
    except Exception as exc:  # noqa: BLE001 - warp is display support, never fatal
        from PySide6.QtCore import QCoreApplication

        # translate() is thread-safe; the emit is queued when off-thread.
        text = QCoreApplication.translate(
            "CanvasRenderMixin", "Could not map the ROI into the right camera: {0}"
        )
        log.emit(text.format(exc), "warning")
        return None


class CanvasRenderMixin:
    """Frames + dense overlay + 3D view; host class provides the attributes."""

    if TYPE_CHECKING:  # attributes owned by CanvasArea3D.__init__
        _canvas: ImageCanvas3D
        _stack: QStackedWidget
        _colorbar: ColorbarOverlay
        _empty_notice: QLabel
        _empty_hint: QLabel
        _mesh_overlay: MeshOverlay
        _view3d: View3D
        _result_empty: bool
        _right_mask_lazy: LazyValue | None
        _right_mask_dirty: bool
        controller: WorkflowController
        signals: GuiSignals

    def _init_render_pipeline(self) -> None:
        """Dense renderer, frame prefetcher (P2.2) and the V-view presenters."""
        self._viz_ctrl = VizController3D()
        self._prefetcher = FramePrefetcher(self)
        self._frames = FrameShower(self._canvas, self._prefetcher, self)
        self._frames.shown_async.connect(self._on_frame_landed)
        self._frames.failed_async.connect(self._on_frame_failed)
        self._overlays = OverlayPresenter(self._viz_ctrl, self)
        self._run_step_memo: tuple[object, int] | None = None

    # ---- idle probes (tests / benchmarks) ------------------------------------

    def render_idle(self) -> bool:
        """True when no frame decode or overlay render is outstanding."""
        return self._overlays.is_idle() and self._frames.is_idle()

    def wait_render_idle(self, timeout_ms: int = 30_000) -> bool:
        """Join outstanding decodes / renders and apply them (tests)."""
        ok = self._overlays.wait_idle(timeout_ms)
        return ok and pump_until(self.render_idle, timeout_ms, self._prefetcher.wait_idle)

    def _cancel_render_work(self) -> None:
        """Drop queued overlay renders / wanted frames (data changed)."""
        self._overlays.cancel()
        self._frames.cancel()

    # ---- node step -------------------------------------------------------------

    def _display_label(self) -> str:
        """Colorbar / scalar-bar label: velocity is per frame until a rate is set."""
        s = self.signals
        return field_label(s.display_field, s.display_unit, per_frame=not s.frame_rate_known)

    def _run_step(self, result) -> int:
        """The node step of the run that produced ``result`` (memoised per result)."""
        memo = self._run_step_memo
        if memo is not None and memo[0] is result:
            return memo[1]
        step = run_node_step(result, default=int(self.controller.state.draft.winstepsize))
        self._run_step_memo = (result, step)
        return step

    # ---- rendering ------------------------------------------------------------------

    def render(self) -> None:
        """Redraw the current view (2D frame + overlay, or the 3D surface)."""
        # Q8: mesh-overlay appearance follows the display state (cheap no-op
        # when unchanged; render() is already the display_changed sink).
        self._mesh_overlay.set_appearance(
            self.signals.mesh_line_color, int(self.signals.mesh_line_width)
        )
        show_notice = self._result_empty and self._stack.currentIndex() == 0
        if show_notice:
            vp = self._canvas.viewport()
            self._empty_notice.setGeometry(0, vp.height() // 2 - 40, vp.width(), 80)
        self._empty_notice.setVisible(show_notice)
        if self._stack.currentIndex() == 1:
            self._update_empty_hint()  # never over the 3D page (G3.3)
            self._render_3d()
            return

        draft = self.controller.state.draft
        cam = self.signals.current_camera
        files = draft.left if cam == "L" else draft.right
        k = self.signals.current_frame

        if not files:
            self._cancel_render_work()
            self._canvas.clear_image()
            self._colorbar.setVisible(False)
            self._update_empty_hint()  # G3.3: quick-start hint on the blank canvas
            return
        self._empty_hint.setVisible(False)
        k = min(k, len(files) - 1)
        # Reference-frame plotting (2D idiom): the toggle switches GEOMETRY —
        # background image and node positions — while the field VALUES stay
        # those of frame k. Without results there is no geometry to switch.
        has_result = self.controller.state.result is not None
        bg = k if self.signals.show_deformed or not has_result else 0
        path = files[bg]
        try:
            self._frames.show(path)  # blit / inline decode / worker decode
        except Exception:  # noqa: BLE001 - a bad frame must not crash the canvas
            self._cancel_render_work()
            self._canvas.clear_image()
            return
        # Warm current/next/prev; navigation drops queued decodes of the rest.
        neighbors = [path]
        if bg + 1 < len(files):
            neighbors.append(files[bg + 1])
        if bg - 1 >= 0:
            neighbors.append(files[bg - 1])
        self._prefetcher.request(neighbors)

        self._render_overlay(k)
        self._sync_roi()
        self._sync_seed_marker()

    def _on_frame_landed(self, _path: str, resized: bool) -> None:
        """A deferred background decode is on screen; re-render if its size changed."""
        if resized:
            self.render()

    def _on_frame_failed(self, _path: str, _message: str) -> None:
        """An unreadable deferred frame: clear the canvas like the inline path."""
        self._overlays.cancel()
        self._canvas.clear_image()
        self._colorbar.setVisible(False)

    def _render_3d(self) -> None:
        result = self.controller.state.result
        if result is None:
            self._view3d.show_message(
                self.tr("3D view — run an analysis to see the reconstructed surface.")
            )
            return
        k = min(self.signals.current_frame, result.reconstruction.n_frames - 1)
        # The surface is frame k's geometry: frame-k strain validity (M2).
        vals = self._field_values(result, k, deformed=True)
        if vals is None:
            self._view3d.show_message(self.tr("Selected field is not available."))
            return
        # Q1: display-layer unit conversion (mm-native data untouched).
        factor = field_display_factor(self.signals.display_field, self.signals.display_unit)
        if factor != 1.0:
            vals = vals * factor

        # F3.2: the drawn LEFT reference ROI mask bounds the surface exactly
        # like the 2D dense view (holes stay open), and the auto color range
        # comes from the VISIBLE nodes of THIS frame (2–98 percentile, G2.3)
        # and is written back to the shared signals — 2D and 3D show identical
        # field/colormap/range, and the Min/Max spins seed from live values.
        roi_mask = self._drawn_roi_bool()
        if self.signals.color_auto:
            vmin, vmax = auto_range(visible_values(vals, result.ref_coords, roi_mask))
            self.signals.color_min, self.signals.color_max = vmin, vmax
        else:
            vmin, vmax = self.signals.color_min, self.signals.color_max
        # Item 4: on a crack-aware run the drawn ROI mask doubles as the crack
        # barrier (the bool mask itself — no full-image float copy, H6); the
        # frame-independent filtered cells are cached in viz3d.surface.
        crack = roi_mask is not None and bool(result.meta.get("crack_aware", False))
        self._view3d.update_view(
            result.reconstruction.points[k],
            vals,
            field_label=self._display_label(),
            cmap=self.signals.colormap,
            vmin=vmin,
            vmax=vmax,
            rig=self._load_rig(),
            ref_coords=result.ref_coords,
            roi_mask=roi_mask,
            barrier_mask=roi_mask if crack else None,
        )

    def _clear_overlay(self) -> None:
        self._overlays.cancel()
        self._canvas.set_overlay_pixmap(None)
        self._colorbar.setVisible(False)

    def _right_mask_source(self, result) -> LazyValue | None:
        """The left ROI warped into the RIGHT camera, as a compute-once value.

        The warp costs ~0.6 s at 12 Mpx, so it is NOT run here: heavy renders
        resolve it inside their worker job (once, shared by queued jobs).
        Rebuilt after ROI edits / new results (``_right_mask_dirty``).
        """
        mask = self._drawn_roi_bool()
        if mask is None or result is None:
            return None
        if self._right_mask_dirty or self._right_mask_lazy is None:
            cs = result.correspondence
            self._right_mask_lazy = LazyValue(
                partial(_warp_to_right, mask, cs.xL[0], cs.xR[0], self.signals.log)
            )
            self._right_mask_dirty = False
        return self._right_mask_lazy

    def _right_roi_mask(self, result) -> np.ndarray | None:
        """The warped right-camera ROI now (synchronous; None -> hull fallback)."""
        lazy = self._right_mask_source(result)
        return None if lazy is None else lazy()

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
        # M2: trimmed strain nodes are hidden with the geometry's validity.
        vals = self._field_values(result, k, deformed=deformed)
        if vals is None:
            self._clear_overlay()
            return
        # Q1: display-layer unit conversion (mm-native data untouched).
        factor = field_display_factor(self.signals.display_field, self.signals.display_unit)
        if factor != 1.0:
            vals = vals * factor
        ref_uv = None
        if deformed:
            d = x_cam[k] - x_cam[0]  # 2D ref_uv contract: x_k - x_1 per node
            ref_uv = (d[:, 0], d[:, 1])

        # LEFT camera: the user-drawn reference ROI mask bounds the field.
        # RIGHT camera (F2.3): the left mask warped into right pixel space via
        # the frame-1 correspondence (holes preserved; the display helper the
        # exports share); when unavailable the renderer falls back to the F1.5
        # valid-node support. A warp not computed yet is resolved by the render
        # job (off the GUI thread for heavy renders).
        left_mask = self._drawn_roi_bool()
        roi_mask = left_mask if cam == "L" else None
        mask_factory = None
        if cam == "R":
            lazy = self._right_mask_source(result)
            if lazy is not None and lazy.ready():
                roi_mask = lazy()
            else:
                mask_factory = lazy

        # Item 4 WYSIWYG: on a crack-aware run the drawn LEFT ROI mask doubles as
        # the crack barrier so the overlay blanks crack-bridging cells exactly
        # like the image export. Reference view only (the export does not
        # blank the deformed crack), LEFT camera (the barrier lives in left
        # reference coords). The bool mask is passed as is (no float copy).
        barrier_mask = None
        if (
            cam == "L"
            and not deformed
            and roi_mask is not None
            and bool(result.meta.get("crack_aware", False))
        ):
            barrier_mask = roi_mask

        # Auto colorbar range from VISIBLE nodes only (2D visible_values
        # contract), clipped to the 2–98 percentile (G2.3, 2D parity):
        # clipped-by-mask nodes and outliers must not stretch the range. The
        # range is written back so switching Auto off starts from live values.
        # A node's ROI membership is decided at its LEFT frame-1 position (the
        # drawn mask), so the right camera needs no warp for its range.
        if self.signals.color_auto:
            vmin, vmax = auto_range(visible_values(vals, cs.xL[0], left_mask))
            self.signals.color_min, self.signals.color_max = vmin, vmax
        else:
            vmin, vmax = self.signals.color_min, self.signals.color_max

        img_rect = self._canvas.scene().sceneRect()
        w, h = int(img_rect.width()), int(img_rect.height())
        if w <= 0 or h <= 0:
            self._clear_overlay()
            return

        # Q1/Q2 cache honesty: unit (and frame rate, for velocity) change the
        # rendered VALUES, so they are part of the interp-cache field key.
        field_key = display_field_key(
            self.signals.display_field, self.signals.display_unit, self.signals.frame_rate
        )
        req = OverlayRequest(
            frame_idx=k,
            field_name=f"{cam}:{field_key}",
            nodes=pts,
            values=vals,
            img_shape=(h, w),
            mesh_step=self._run_step(result),
            cmap=self.signals.colormap,
            vmin=vmin,
            vmax=vmax,
            roi_mask=roi_mask,
            deformed=deformed,
            ref_uv=ref_uv,
            ref_pts=ref_pts,
            barrier_mask=barrier_mask,
            roi_mask_factory=mask_factory,
        )
        label = self._display_label()
        self._overlays.request(
            req,
            partial(self._apply_overlay, self.signals.colormap, vmin, vmax, label),
            self._on_overlay_error,
        )

    def _apply_overlay(self, cmap: str, vmin: float, vmax: float, label: str, out) -> None:
        """Show a rendered overlay (inline or delivered by the worker)."""
        pixmap, xg, yg, out_step = out
        if pixmap is None:
            self._canvas.set_overlay_pixmap(None)
            self._colorbar.setVisible(False)
            return
        self._canvas.set_overlay_pixmap(pixmap)
        self._canvas.set_overlay_geometry(float(out_step), *overlay_origin(xg, yg, out_step))
        self._canvas.set_overlay_opacity(self.signals.overlay_alpha)
        self._colorbar.update_params(cmap, vmin, vmax, label)
        self._colorbar.setVisible(True)

    def _on_overlay_error(self, message: str) -> None:
        self.signals.log.emit(self.tr("Could not draw the overlay: {0}").format(message), "error")
        self._canvas.set_overlay_pixmap(None)
        self._colorbar.setVisible(False)
