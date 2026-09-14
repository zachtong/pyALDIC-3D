"""Viewer performance batch V-view — GUI behaviour (offscreen).

* heavy overlay renders and cold frame decodes leave the GUI thread
  (generation-tagged: stale results are dropped, the last good image stays up);
* navigation cancels queued prefetch decodes;
* slider drags are coalesced; buttons / keys / playback stay immediate;
* the canvas and strain window use the RUN's node step, not the live draft;
* the main canvas hides ``~strain_valid`` nodes (and they do not stretch the
  auto range);
* the crack barrier reaches the 3D view as the bool ROI itself (no float copy).
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import threading
import time
from dataclasses import replace

import numpy as np
import pytest

pytest.importorskip("PySide6")
cv2 = pytest.importorskip("cv2")

from al_dic_3d.matching.contracts import CorrespondenceSet  # noqa: E402
from al_dic_3d.reconstruct import Reconstruction3D  # noqa: E402
from al_dic_3d.runner import RunResult  # noqa: E402

H, W = 260, 300
STEP = 16


@pytest.fixture(scope="module")
def qapp():
    from al_dic_3d.gui.app import create_app

    return create_app([])


@pytest.fixture(scope="module")
def frames(tmp_path_factory):
    d = tmp_path_factory.mktemp("vview_frames")
    rng = np.random.default_rng(3)
    paths = []
    for k in range(6):
        img = rng.integers(0, 255, size=(H, W), dtype=np.uint8)
        img[0, 0] = k
        p = d / f"L_{k:03d}.png"
        cv2.imwrite(str(p), img)
        paths.append(str(p))
    return paths


def _result(n_frames=6, run_step=STEP, strain=False):
    xs, ys = np.meshgrid(40.0 + STEP * np.arange(14), 40.0 + STEP * np.arange(11))
    ref = np.column_stack([xs.ravel(), ys.ravel()])
    n = len(ref)
    shift = np.array([1.5, -1.0])
    x = np.stack([ref + k * shift for k in range(n_frames)])
    pts3 = np.stack([np.column_stack([ref * 0.1, np.full(n, 800.0 + k)]) for k in range(n_frames)])
    cs = CorrespondenceSet(
        strategy="track_both",
        xL=x,
        xR=x + np.array([-20.0, 0.0]),
        quality=np.zeros((n_frames, n)),
        source=np.ones((n_frames, n), dtype=np.uint8),
    )
    rec = Reconstruction3D(
        points=pts3,
        displacement=pts3 - pts3[0],
        reproj_error=np.zeros((n_frames, n)),
        source=np.ones((n_frames, n), dtype=np.uint8),
    )
    meta = {"run_params": {"winstepsize": run_step}, "image_size": (H, W)}
    result = RunResult(
        strategy="track_both", ref_coords=ref, correspondence=cs, reconstruction=rec, meta=meta
    )
    if strain:
        from al_dic_3d.strain3d.model import StrainResult3D

        exx = np.tile(ref[:, 0] * 1e-4, (n_frames, 1))
        valid = np.ones((n_frames, n), dtype=bool)
        exx[:, 5] = 50.0  # a wild trimmed node
        valid[:, 5] = False
        zeros = np.zeros_like(exx)
        fields = dict(exx=exx, eyy=zeros, exy=zeros, e1=exx, e2=zeros, max_shear=zeros)
        result = replace(
            result,
            strain=StrainResult3D(
                **fields, von_mises=zeros, dwdx=zeros, dwdy=zeros, strain_valid=valid
            ),
        )
    return result


def _area(qapp, frames, result=None):
    from al_dic_3d.gui.controller import WorkflowController
    from al_dic_3d.gui.panels.canvas_area import CanvasArea3D
    from al_dic_3d.gui.state import GuiSignals

    controller = WorkflowController()
    signals = GuiSignals()
    area = CanvasArea3D(controller, signals)
    area.show()
    controller.state.draft.left = list(frames)
    controller.state.draft.right = list(frames)
    signals.images_changed.emit()
    if result is not None:
        controller.state.result = result
        signals.results_changed.emit()
    return area, signals


def _pump(seconds=0.3):
    from PySide6.QtWidgets import QApplication

    end = time.monotonic() + seconds
    while time.monotonic() < end:
        QApplication.processEvents()
        time.sleep(0.01)


# ---------------------------------------------------------------------------
# async overlay / frames
# ---------------------------------------------------------------------------


def test_heavy_overlay_renders_off_the_gui_thread_and_drops_stale(qapp, frames):
    area, signals = _area(qapp, frames, _result())
    area.wait_render_idle()
    area._overlays.async_min_grid_points = 0  # force the worker path
    applied: list = []
    real_apply = area._apply_overlay

    def spy(cmap, vmin, vmax, label, out):
        applied.append(signals.current_frame)
        real_apply(cmap, vmin, vmax, label, out)

    area._apply_overlay = spy
    shown_before = area.canvas._overlay_item.pixmap().cacheKey()
    gui = threading.get_ident()
    threads: list[int] = []
    real_rgba = area._viz_ctrl.render_field_rgba

    def rgba_spy(*a, **k):
        threads.append(threading.get_ident())
        return real_rgba(*a, **k)

    area._viz_ctrl.render_field_rgba = rgba_spy
    for k in (1, 2, 3):  # rapid navigation: 1 and 2 become stale
        signals.set_current_frame(k, 6)
    assert not area.render_idle()
    assert area.canvas._overlay_item.pixmap().cacheKey() == shown_before  # last good stays
    assert area.wait_render_idle()
    assert applied == [3]  # only the newest request landed
    assert threads and gui not in threads  # computed on the worker
    assert area.canvas._overlay_item.pixmap().cacheKey() != shown_before


def test_cold_large_frame_decodes_on_worker_and_keeps_last_image(qapp, frames):
    area, signals = _area(qapp, frames, _result())
    area.wait_render_idle()
    area._frames.async_min_pixels = 0  # every cold frame is "large"
    area._prefetcher.invalidate()  # make frame 4 cold
    before = area.canvas.shown_path()
    signals.set_current_frame(4, 6)
    assert area.canvas.shown_path() == before  # not decoded on the GUI thread
    assert area.wait_render_idle()
    assert area.canvas.shown_path() == frames[4]


def test_navigation_drops_queued_prefetch_decodes(qapp, frames, monkeypatch):
    from al_dic_3d.gui.widgets import frame_prefetcher as fp

    gate = threading.Event()
    decoded: list[str] = []
    real = fp.decode_gray_qimage

    def slow(path):
        decoded.append(path)
        gate.wait(10)
        return real(path)

    monkeypatch.setattr(fp, "decode_gray_qimage", slow)
    pf = fp.FramePrefetcher()
    pf.request(frames[:2])  # both workers block on these
    deadline = time.monotonic() + 5
    while len(decoded) < 2 and time.monotonic() < deadline:
        time.sleep(0.01)
    pf.request(frames[:5])  # frames 2..4 queue behind the blocked workers
    pf.request([frames[5]])  # the user moved on: 2..4 are no longer wanted
    gate.set()
    assert pf.wait_idle(10_000)
    _pump(0.2)
    assert pf.wait_idle(10_000)
    _pump(0.2)
    assert set(decoded) == {frames[0], frames[1], frames[5]}
    assert pf.has(frames[5]) and not pf.has(frames[3])


def test_prefetcher_stores_compact_grayscale_and_is_byte_bounded(qapp, frames):
    from PySide6.QtGui import QImage

    from al_dic_3d.gui.widgets.frame_prefetcher import FramePrefetcher

    one = H * W  # bytes per 8-bit frame
    pf = FramePrefetcher(max_bytes=int(2.5 * one))
    pf.request(frames[:4])
    assert pf.wait_idle(10_000)
    _pump(0.2)
    assert len(pf) == 2  # the byte budget binds before the entry cap
    image = next(iter(pf._cache.values()))
    assert image.format() == QImage.Format.Format_Grayscale8


# ---------------------------------------------------------------------------
# slider coalescing
# ---------------------------------------------------------------------------


def test_slider_drag_is_coalesced_but_steps_are_immediate(qapp):
    from al_dic_3d.gui.state import GuiSignals
    from al_dic_3d.gui.widgets.frame_navigator import FrameNavigator3D

    signals = GuiSignals()
    nav = FrameNavigator3D(signals)
    nav.set_frame_count(50)
    seen: list[int] = []
    signals.frame_changed.connect(seen.append)
    nav._slider.setSliderDown(True)
    for v in range(1, 21):
        nav._slider.setValue(v)
    assert seen == [1]  # leading edge only while the window is open
    assert nav._label.text().endswith("21/50")  # the label follows the handle
    _pump(0.25)
    assert seen[-1] == 20  # the window flushed the newest value
    nav._slider.setValue(30)
    nav._slider.setSliderDown(False)  # release applies the final value
    _pump(0.15)
    assert seen[-1] == 30
    count = len(seen)
    nav._step(1)  # buttons / keys stay immediate
    assert seen[-1] == 31 and len(seen) == count + 1


def test_strain_slider_drag_is_coalesced(qapp):
    from al_dic_3d.gui.widgets.strain_navigator import StrainNavigator3D

    nav = StrainNavigator3D()
    nav.set_state(40, 0)
    seen: list[int] = []
    nav.frame_changed.connect(seen.append)
    nav._slider.setSliderDown(True)
    for v in range(1, 16):
        nav._slider.setValue(v)
    assert seen == [1]
    nav._slider.setSliderDown(False)
    _pump(0.15)
    assert seen[-1] == 15
    nav.step(1)
    assert seen[-1] == 16


# ---------------------------------------------------------------------------
# run step, strain validity, crack barrier
# ---------------------------------------------------------------------------


def test_canvas_uses_the_runs_node_step_not_the_draft(qapp, frames):
    area, signals = _area(qapp, frames, _result(run_step=STEP))
    area.controller.state.draft.winstepsize = 8  # edited after the run
    steps: list[int] = []
    real = area._viz_ctrl.render_field

    def spy(*a, **k):
        steps.append(k["mesh_step"])
        return real(*a, **k)

    area._viz_ctrl.render_field = spy
    signals.set_camera("R")  # the no-ROI support fallback (was 0 % coverage)
    signals.set_current_frame(2, 6)
    area.wait_render_idle()
    assert steps and set(steps) == {STEP}
    assert not area.canvas._overlay_item.pixmap().isNull()


def test_canvas_hides_trimmed_strain_nodes_and_their_range(qapp, frames):
    result = _result(strain=True)
    area, signals = _area(qapp, frames, result)
    signals.display_field = "exx"
    for deformed in (False, True):
        vals = area._field_values(result, 2, deformed=deformed)
        assert np.isnan(vals[5]) and np.isfinite(np.delete(vals, 5)).all()
    area.render()
    assert signals.color_max < 1.0  # the 50.0 outlier no longer stretches the range


def test_view3d_receives_bool_roi_as_crack_barrier(qapp, frames):
    result = _result()
    result.meta["crack_aware"] = True
    area, signals = _area(qapp, frames, result)
    roi = np.zeros((H, W), dtype=np.uint8)
    roi[20:240, 20:280] = 1
    roi[:, 150:152] = 0
    area.controller.state.draft.roi_mask_array = roi
    calls: dict = {}
    area._view3d.update_view = lambda points, vals, **kw: calls.update(kw)
    area._view3d_cb.setChecked(True)
    assert calls["barrier_mask"] is calls["roi_mask"]  # same bool array, no copy
    assert calls["barrier_mask"].dtype == np.bool_
    area._view3d_cb.setChecked(False)


def test_strain_window_uses_run_step_and_async_path(qapp, frames):
    from al_dic_3d.gui.controller import WorkflowController
    from al_dic_3d.gui.state import GuiSignals
    from al_dic_3d.gui.strain_window import StrainWindow3D

    ctrl = WorkflowController()
    ctrl.state.draft.left = list(frames)
    ctrl.state.draft.winstepsize = 8  # edited after the run
    ctrl.state.result = _result(strain=True)
    sw = StrainWindow3D(ctrl, GuiSignals())
    try:
        assert sw.param_panel()._winstepsize == STEP
        sw._overlays.async_min_grid_points = 0
        sw._frames.async_min_pixels = 0
        steps: list[int] = []
        real = sw._viz_ctrl.render_field_rgba

        def spy(*a, **k):
            steps.append(k["mesh_step"])
            return real(*a, **k)

        sw._viz_ctrl.render_field_rgba = spy
        sw.set_strain_frame(2)
        sw.set_strain_frame(3)
        assert sw.wait_render_idle()
        assert steps and set(steps) == {STEP}
        assert not sw._canvas._overlay_item.pixmap().isNull()
    finally:
        sw.close()


def test_strain_compute_uses_the_runs_node_step(monkeypatch):
    from al_dic_3d.gui.controller import WorkflowController
    from al_dic_3d.gui.controllers import strain_controller as sc

    seen: dict = {}

    def fake_compute(recon, ref_coords, **kw):
        seen.update(kw)
        return "strain"

    monkeypatch.setattr(sc, "compute_surface_strain", fake_compute)
    ctrl = WorkflowController()
    ctrl.state.draft.winstepsize = 8  # edited after the run
    ctrl.state.result = _result(run_step=STEP)
    assert sc.StrainController3D(ctrl).compute({}) == "strain"
    assert seen["winstepsize"] == STEP


def test_right_camera_roi_warp_runs_once_off_the_gui_thread(qapp, frames, monkeypatch):
    from al_dic_3d.gui.panels import canvas_render

    area, signals = _area(qapp, frames, _result())
    roi = np.zeros((H, W), dtype=np.uint8)
    roi[30:230, 30:270] = 1
    area.controller.state.draft.roi_mask_array = roi
    signals.roi_changed.emit()
    area.wait_render_idle()
    area._overlays.async_min_grid_points = 0
    calls: list[int] = []
    real = canvas_render._warp_to_right

    def spy(*a, **k):
        calls.append(threading.get_ident())
        return real(*a, **k)

    monkeypatch.setattr(canvas_render, "_warp_to_right", spy)
    area._right_mask_dirty = True
    signals.set_camera("R")
    signals.set_current_frame(2, 6)  # a second queued job shares the same warp
    assert area.wait_render_idle()
    assert len(calls) == 1 and calls[0] != threading.get_ident()
    assert not area.canvas._overlay_item.pixmap().isNull()
    warped = area._right_roi_mask(area.controller.state.result)  # now cached
    assert warped is not None and warped.dtype == np.bool_ and len(calls) == 1


def test_roi_fill_overlay_is_pixel_identical_to_the_rgba_fill(qapp):
    from PySide6.QtGui import QImage, QPixmap

    from al_dic_3d.gui.controllers.roi_controller import ROIController
    from al_dic_3d.gui.widgets.image_view import _ROI_OVERLAY_RGBA, ImageCanvas3D

    canvas = ImageCanvas3D()
    canvas.set_image_gray(np.zeros((70, 90)))
    ctrl = ROIController((70, 90))
    ctrl.add_rectangle(5, 5, 60, 50, "add")
    ctrl.add_circle(30, 30, 8, "cut")
    canvas.set_roi_controller(ctrl)
    canvas.update_roi_overlay()
    got = canvas._roi_mask_item.pixmap().toImage()
    ref = np.zeros((70, 90, 4), dtype=np.uint8)
    ref[ctrl.mask] = _ROI_OVERLAY_RGBA  # the original per-pixel fill
    want = QPixmap.fromImage(
        QImage(ref.data, 90, 70, 360, QImage.Format.Format_RGBA8888).copy()
    ).toImage()
    assert got == want


def test_skipped_decode_of_a_frame_cached_inline_does_not_stay_pending(qapp, frames, monkeypatch):
    """A queued decode skipped as unwanted must release its pending entry even
    when the same frame was meanwhile decoded inline and cached."""
    from al_dic_3d.gui.widgets import frame_prefetcher as fp

    gate = threading.Event()
    real = fp.decode_gray_qimage

    def slow(path):
        gate.wait(10)
        return real(path)

    monkeypatch.setattr(fp, "decode_gray_qimage", slow)
    pf = fp.FramePrefetcher()
    pf.request(frames[:2])  # both workers busy (gated)
    time.sleep(0.1)
    pf.request([frames[3]])  # queued behind them
    pf.request([frames[4]])  # navigation moved on: frame 3 is unwanted now
    pf.store_image(frames[3], real(frames[3]))  # ... and was decoded inline
    gate.set()
    deadline = time.monotonic() + 10
    while pf._pending and time.monotonic() < deadline:
        pf.wait_idle(50)
        _pump(0.02)
    assert not pf._pending
    assert pf.has(frames[3]) and pf.has(frames[4])


def test_overlay_presenter_retains_tasks_until_delivery(qapp, frames):
    area, signals = _area(qapp, frames, _result())
    area.wait_render_idle()
    area._overlays.async_min_grid_points = 0
    signals.set_current_frame(3, 6)
    assert area._overlays._tasks  # held while in flight
    assert area.wait_render_idle()
    assert not area._overlays._tasks


def _holed_roi(cx):
    roi = np.zeros((H, W), dtype=np.uint8)
    roi[30:230, 30:270] = 1
    roi[100:160, cx - 25 : cx + 25] = 0
    return roi


def test_tier2_pixmaps_follow_roi_content_not_presence(qapp):
    from al_dic_3d.gui.controllers.viz_controller import VizController3D

    result = _result()
    ctrl = VizController3D()
    pts = result.correspondence.xL[0]
    a = _holed_roi(100) > 0
    b = _holed_roi(200) > 0
    kw = dict(img_shape=(H, W), mesh_step=STEP, vmin=0.0, vmax=1.0)
    pa, *_ = ctrl.render_field(0, "t:U", pts, pts[:, 0] / 300, roi_mask=a, **kw)
    pb, *_ = ctrl.render_field(0, "t:U", pts, pts[:, 0] / 300, roi_mask=b, **kw)
    assert pb is not pa  # an edited ROI (no invalidate call) never reuses the old pixmap
    assert pb.toImage() != pa.toImage()
    again, *_ = ctrl.render_field(0, "t:U", pts, pts[:, 0] / 300, roi_mask=a.copy(), **kw)
    assert again is pa  # same CONTENT, new object: still a Tier-2 hit


def test_strain_window_refreshes_on_main_window_roi_edit(qapp, frames):
    from al_dic_3d.gui.controller import WorkflowController
    from al_dic_3d.gui.state import GuiSignals
    from al_dic_3d.gui.strain_window import StrainWindow3D

    ctrl = WorkflowController()
    ctrl.state.draft.left = list(frames)
    ctrl.state.result = _result(strain=True)
    ctrl.state.draft.roi_mask_array = _holed_roi(100)
    signals = GuiSignals()
    sw = StrainWindow3D(ctrl, signals)
    try:
        sw.show()
        sw.set_strain_frame(2)
        sw.wait_render_idle()
        before = sw._canvas._overlay_item.pixmap().toImage()
        ctrl.state.draft.roi_mask_array = _holed_roi(200)  # edited in the main window
        signals.roi_changed.emit()
        sw.wait_render_idle()
        assert sw._canvas._overlay_item.pixmap().toImage() != before
    finally:
        sw.close()
