"""Performance batch P2 — GUI responsiveness.

P2.1 bounded LRU viz caches (eviction never changes results)
P2.2 background frame-decode prefetcher (content parity + bounded)
P2.3 background mesh preview (async apply, coalescing, grid-off drop)
P2.4 3D view incremental update + camera preservation (stub plotter)
P2.5 streaming session save (STORED npz member) + modal worker runner
P2.6 GUI-thread allocation caches (mag per frame, ROI bool, RGBA buffer)
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import time
import zipfile
from types import SimpleNamespace

import numpy as np
import pytest

pytest.importorskip("PySide6")
cv2 = pytest.importorskip("cv2")

from al_dic_3d.viz3d.fieldmap import (  # noqa: E402
    INTERP_CACHE_SIZE,
    SUPPORT_CACHE_SIZE,
    FieldmapRenderer,
)
from al_dic_3d.viz3d.lru import LRUCache  # noqa: E402

IMG_SHAPE = (60, 70)
STEP = 10


@pytest.fixture(scope="module")
def qapp():
    from al_dic_3d.gui.app import create_app

    return create_app([])


@pytest.fixture(scope="module")
def frame_files(tmp_path_factory):
    """10 small distinct grayscale frames on disk."""
    d = tmp_path_factory.mktemp("p2_frames")
    rng = np.random.default_rng(0)
    paths = []
    for k in range(10):
        img = rng.integers(0, 255, size=(48, 64), dtype=np.uint8)
        img[0, 0] = k  # guarantee distinct content per frame
        p = d / f"L_{k:03d}.png"
        cv2.imwrite(str(p), img)
        paths.append(str(p))
    return paths


def _grid_nodes(nx: int = 5, ny: int = 4, step: float = STEP, origin: float = 10.0):
    xs, ys = np.meshgrid(origin + step * np.arange(nx), origin + step * np.arange(ny))
    return np.column_stack([xs.ravel(), ys.ravel()]).astype(np.float64)


def _rgba_at(rgba, xg, yg, out_step, x, y):
    col = int(round((x - float(xg.min())) / out_step))
    row = int(round((y - float(yg.min())) / out_step))
    return rgba[row, col]


# ---------------------------------------------------------------------------
# P2.1 — bounded LRU caches
# ---------------------------------------------------------------------------


def test_lru_evicts_least_recently_used():
    c = LRUCache(3)
    c["a"], c["b"], c["c"] = 1, 2, 3
    assert c["a"] == 1  # refresh "a"
    c["d"] = 4  # evicts "b" (oldest untouched)
    assert list(c) == ["c", "a", "d"]
    assert c.get("b") is None and len(c) == 3


def test_lru_rejects_invalid_maxsize():
    with pytest.raises(ValueError, match="maxsize"):
        LRUCache(0)


def test_interp_cache_bounded_and_eviction_preserves_results():
    nodes = _grid_nodes()
    renderer = FieldmapRenderer()
    frames = INTERP_CACHE_SIZE + 8
    first_pass = {}
    for k in range(frames):
        vals = nodes[:, 0] * (1.0 + 0.01 * k)
        rgba, *_ = renderer.render_field_rgba(
            k, "t:U", nodes, vals, IMG_SHAPE, STEP, vmin=10.0, vmax=60.0
        )
        first_pass[k] = rgba
    assert len(renderer._interp_cache) <= INTERP_CACHE_SIZE
    assert len(renderer._support_cache) <= SUPPORT_CACHE_SIZE
    # Frames 0/1 were evicted; re-rendering them must match a fresh renderer
    # AND the original first-pass pixels (recompute-on-miss contract).
    fresh = FieldmapRenderer()
    for k in (0, 1, frames - 1):
        vals = nodes[:, 0] * (1.0 + 0.01 * k)
        again, *_ = renderer.render_field_rgba(
            k, "t:U", nodes, vals, IMG_SHAPE, STEP, vmin=10.0, vmax=60.0
        )
        clean, *_ = fresh.render_field_rgba(
            k, "t:U", nodes, vals, IMG_SHAPE, STEP, vmin=10.0, vmax=60.0
        )
        np.testing.assert_array_equal(again, first_pass[k])
        np.testing.assert_array_equal(again, clean)


def test_warp_mask_recomputed_after_eviction():
    """Deformed-mode rendering must survive a warp-cache eviction while the
    Tier-1 entry is still alive (the mask is recomputed, never wrongly looked
    up in reference coordinates)."""
    ref = _grid_nodes()
    shift = 6.0
    deformed_nodes = ref + np.array([shift, 0.0])
    values = np.ones(len(ref))
    u, v = np.full(len(ref), shift), np.zeros(len(ref))
    mask = np.zeros(IMG_SHAPE, dtype=bool)
    mask[5:45, 5:55] = True
    mask[26:34, 26:34] = False  # reference-frame hole

    renderer = FieldmapRenderer()
    kwargs = dict(roi_mask=mask, deformed=True, ref_uv=(u, v), ref_pts=ref)
    rgba1, xg, yg, out_step = renderer.render_field_rgba(
        1, "t:U", deformed_nodes, values, IMG_SHAPE, STEP, **kwargs
    )
    renderer._warp_cache.clear()  # simulate LRU eviction of the warp tier only
    assert (1, "t:U", True) in renderer._interp_cache
    rgba2, *_ = renderer.render_field_rgba(
        1, "t:U", deformed_nodes, values, IMG_SHAPE, STEP, **kwargs
    )
    np.testing.assert_array_equal(rgba2, rgba1)
    # The hole still travels WITH the material (warped mask semantics).
    assert _rgba_at(rgba2, xg, yg, out_step, 30 + shift, 30)[3] == 0
    assert _rgba_at(rgba2, xg, yg, out_step, 20 + shift, 20)[3] == 255


def test_pixmap_cache_bounded(qapp):
    from al_dic_3d.gui.controllers.viz_controller import PIXMAP_CACHE_SIZE, VizController3D

    nodes = _grid_nodes()
    vals = nodes[:, 0]
    ctrl = VizController3D()
    for k in range(PIXMAP_CACHE_SIZE + 10):
        pm, *_ = ctrl.render_field(k, "L:U", nodes, vals, IMG_SHAPE, STEP, vmin=10, vmax=50)
        assert pm is not None and not pm.isNull()
    assert len(ctrl._pixmap_cache) <= PIXMAP_CACHE_SIZE
    assert len(ctrl._interp_cache) <= INTERP_CACHE_SIZE


# ---------------------------------------------------------------------------
# P2.2 — frame-decode prefetcher
# ---------------------------------------------------------------------------


def _pump_prefetcher(prefetcher, timeout_s: float = 15.0) -> bool:
    """Join decode jobs and deliver their queued GUI-thread signals."""
    from PySide6.QtWidgets import QApplication

    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        prefetcher.wait_idle(50)
        QApplication.processEvents()
        if not prefetcher._pending:
            return True
    return False


def test_prefetcher_content_parity_and_bounded(qapp, frame_files):
    from al_dic_3d.gui.widgets.frame_prefetcher import PREFETCH_CACHE_SIZE, FramePrefetcher
    from al_dic_3d.gui.widgets.image_view import gray_to_qpixmap, load_gray_image

    pf = FramePrefetcher()
    pf.request(frame_files)  # 10 requested > capacity 8
    assert _pump_prefetcher(pf)
    assert len(pf) == PREFETCH_CACHE_SIZE  # bounded: LRU kept the last 8
    hot = 0
    for p in frame_files:
        pm = pf.get(p)
        if pm is None:
            continue
        hot += 1
        direct = gray_to_qpixmap(load_gray_image(p))
        assert pm.toImage() == direct.toImage()  # pixel-identical to sync decode
    assert hot == PREFETCH_CACHE_SIZE


def test_prefetcher_invalidate_drops_inflight(qapp, frame_files):
    from al_dic_3d.gui.widgets.frame_prefetcher import FramePrefetcher

    pf = FramePrefetcher()
    pf.request(frame_files[:4])
    pf.invalidate()  # images changed while decodes are in flight
    assert _pump_prefetcher(pf)
    assert len(pf) == 0  # stale generations never land


def _canvas_area(qapp, frame_files):
    from al_dic_3d.gui.controller import WorkflowController
    from al_dic_3d.gui.panels.canvas_area import CanvasArea3D
    from al_dic_3d.gui.state import GuiSignals

    controller = WorkflowController()
    signals = GuiSignals()
    area = CanvasArea3D(controller, signals)
    area.show()  # offscreen show: child isVisible() needs a visible ancestor
    controller.state.draft.left = list(frame_files)
    signals.images_changed.emit()
    return area, signals


def test_scrub_shows_identical_pixels_hot_or_cold(qapp, frame_files):
    from al_dic_3d.gui.widgets.frame_prefetcher import PREFETCH_CACHE_SIZE
    from al_dic_3d.gui.widgets.image_view import gray_to_qpixmap, load_gray_image

    area, signals = _canvas_area(qapp, frame_files)
    n = len(frame_files)
    for k in range(n):  # forward scrub: cold path fills the cache as it goes
        signals.set_current_frame(k, n)
    assert _pump_prefetcher(area._prefetcher)
    for k in reversed(range(n)):  # backward scrub: mostly hot now
        signals.set_current_frame(k, n)
        shown = area.canvas.background_pixmap().toImage()
        direct = gray_to_qpixmap(load_gray_image(frame_files[k])).toImage()
        assert shown == direct  # blitted pixmap == synchronous decode
    assert len(area._prefetcher) <= PREFETCH_CACHE_SIZE


# ---------------------------------------------------------------------------
# P2.3 — background mesh preview
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def mesh_files(tmp_path_factory):
    """3 frames large enough for the default winsize-32 / step-16 grid."""
    d = tmp_path_factory.mktemp("p2_mesh_frames")
    rng = np.random.default_rng(3)
    paths = []
    for k in range(3):
        img = rng.integers(0, 255, size=(200, 200), dtype=np.uint8)
        p = d / f"L_{k:03d}.png"
        cv2.imwrite(str(p), img)
        paths.append(str(p))
    return paths


_MESH_ROI = (35, 165, 35, 165)


def test_mesh_preview_applies_async(qapp, mesh_files):
    area, _signals = _canvas_area(qapp, mesh_files)
    area.controller.state.draft.roi = _MESH_ROI
    area._generate_preview_mesh()
    assert not area._mesh_overlay.isVisible()  # nothing applied synchronously
    assert area.wait_mesh_preview()
    assert area._mesh_overlay.isVisible()
    assert area._hover_coords is not None and len(area._hover_coords) >= 4


def test_mesh_preview_coalesces_to_freshest_params(qapp, mesh_files):
    from al_dic_3d.gui.panels.mesh_preview import build_preview_mesh

    area, _signals = _canvas_area(qapp, mesh_files)
    draft = area.controller.state.draft
    draft.roi = _MESH_ROI
    draft.winstepsize = 16
    area._generate_preview_mesh()  # build 1 (step 16) in flight
    draft.winstepsize = 8
    area._generate_preview_mesh()  # params changed: build 1 is now stale
    assert area.wait_mesh_preview()
    expected, _, _ = build_preview_mesh(area._mesh_snapshot())
    assert len(area._hover_coords) == len(expected)  # the FRESH build won
    draft.winstepsize = 16
    coarse, _, _ = build_preview_mesh(area._mesh_snapshot())
    assert len(expected) > len(coarse)  # and it differs from the stale one


def test_mesh_preview_grid_off_drops_inflight_result(qapp, mesh_files):
    area, _signals = _canvas_area(qapp, mesh_files)
    area.controller.state.draft.roi = _MESH_ROI
    area._generate_preview_mesh()  # build in flight
    area._grid_cb.setChecked(False)  # user disables the preview mid-build
    assert area.wait_mesh_preview()
    assert not area._mesh_overlay.isVisible()  # the landing result never shows


# ---------------------------------------------------------------------------
# P2.4 — 3D view incremental update + camera preservation
# ---------------------------------------------------------------------------

pv = None
try:  # stub-plotter tests need pyvista only for PolyData (no GL)
    import pyvista as pv  # noqa: F401
except Exception:  # pragma: no cover - optional extra
    pv = None

needs_pyvista = pytest.mark.skipif(pv is None, reason="pyvista not installed")


class _FakeMapper:
    def __init__(self):
        self.scalar_range = (0.0, 1.0)
        self.lookup_table = SimpleNamespace(scalar_range=(0.0, 1.0))


class _FakeActor:
    def __init__(self):
        self.mapper = _FakeMapper()


class _FakePlotter:
    def __init__(self):
        self.camera_position = ("initial", "camera", "pose")
        self.calls: list[str] = []

    def clear(self):
        self.calls.append("clear")

    def add_mesh(self, mesh, **_kw):
        self.calls.append("add_mesh")
        return _FakeActor()

    def reset_camera(self):
        self.calls.append("reset_camera")

    def render(self):
        self.calls.append("render")


def _grid_frame(dz: float = 0.0, scale: float = 1.0):
    xs = 100.0 + 16.0 * np.arange(5)
    ys = 50.0 + 16.0 * np.arange(4)
    gx, gy = np.meshgrid(xs, ys)
    ref = np.column_stack([gx.ravel(), gy.ravel()])
    pts = np.column_stack([ref * 0.1, np.full(len(ref), 800.0 + dz)])
    vals = pts[:, 0] * scale
    return pts, vals, ref


def _fake_view(qapp):
    from al_dic_3d.gui.widgets.view3d import View3D

    view = View3D()
    view._plotter = _FakePlotter()  # bypass GL: exercise the update logic only
    return view


@needs_pyvista
def test_view3d_scrub_updates_in_place_and_keeps_camera(qapp):
    view = _fake_view(qapp)
    fp = view._plotter
    pts1, vals1, ref = _grid_frame()
    view.update_view(pts1, vals1, field_label="U", cmap="turbo", vmin=0, vmax=1, ref_coords=ref)
    assert fp.calls.count("add_mesh") == 1
    assert fp.calls.count("reset_camera") == 1  # first render after results

    fp.camera_position = ("user", "moved", "camera")
    pts2, vals2, _ = _grid_frame(dz=5.0, scale=2.0)
    view.update_view(pts2, vals2, field_label="U", cmap="turbo", vmin=0, vmax=2, ref_coords=ref)
    assert fp.calls.count("add_mesh") == 1  # in-place: ONE actor kept
    assert fp.calls.count("reset_camera") == 1  # camera NOT re-framed
    assert fp.calls.count("render") == 1
    assert fp.camera_position == ("user", "moved", "camera")
    # scalars and points really updated in place
    np.testing.assert_allclose(np.asarray(view._surf["U"]).max(), vals2.max())
    np.testing.assert_allclose(np.asarray(view._surf.points)[:, 2].max(), 805.0)
    assert view._actor.mapper.scalar_range == (0.0, 2.0)


@needs_pyvista
def test_view3d_field_change_rebuilds_but_preserves_camera(qapp):
    view = _fake_view(qapp)
    fp = view._plotter
    pts1, vals1, ref = _grid_frame()
    view.update_view(pts1, vals1, field_label="U", cmap="turbo", vmin=0, vmax=1, ref_coords=ref)
    fp.camera_position = ("user", "moved", "camera")
    view.update_view(pts1, vals1, field_label="W", cmap="turbo", vmin=0, vmax=1, ref_coords=ref)
    assert fp.calls.count("add_mesh") == 2  # scalar-bar title changed: rebuild
    assert fp.calls.count("reset_camera") == 1  # ... but the camera survives
    assert fp.camera_position == ("user", "moved", "camera")


@needs_pyvista
def test_view3d_results_change_reframes_camera(qapp):
    view = _fake_view(qapp)
    fp = view._plotter
    pts1, vals1, ref = _grid_frame()
    view.update_view(pts1, vals1, field_label="U", cmap="turbo", vmin=0, vmax=1, ref_coords=ref)
    fp.camera_position = ("user", "moved", "camera")
    view.request_camera_reset()  # new results landed
    view.update_view(pts1, vals1, field_label="U", cmap="turbo", vmin=0, vmax=1, ref_coords=ref)
    assert fp.calls.count("reset_camera") == 2  # re-framed exactly once more


# ---------------------------------------------------------------------------
# P2.5 — session save: streaming + STORED member; modal worker runner
# ---------------------------------------------------------------------------


def _synthetic_result(n_frames: int = 4, n_pts: int = 4000):
    from al_dic_3d.matching.contracts import CorrespondenceSet
    from al_dic_3d.reconstruct import Reconstruction3D
    from al_dic_3d.runner import RunResult

    rng = np.random.default_rng(1)
    ref = rng.uniform(0, 500, size=(n_pts, 2))
    x = rng.uniform(0, 500, size=(n_frames, n_pts, 2))
    pts = rng.normal(0, 10, size=(n_frames, n_pts, 3))
    cs = CorrespondenceSet(
        strategy="track_both",
        xL=x,
        xR=x + 1.0,
        quality=rng.uniform(0, 1, size=(n_frames, n_pts)),
        source=np.ones((n_frames, n_pts), dtype=np.uint8),
    )
    rec = Reconstruction3D(
        points=pts,
        displacement=pts - pts[0],
        reproj_error=rng.uniform(0, 1, size=(n_frames, n_pts)),
        source=np.ones((n_frames, n_pts), dtype=np.uint8),
    )
    return RunResult(strategy="track_both", ref_coords=ref, correspondence=cs, reconstruction=rec)


def test_save_streams_results_member_stored(tmp_path):
    from al_dic_3d.project import AppState3D, load_session, save_session

    state = AppState3D(result=_synthetic_result())
    path = save_session(state, tmp_path / "streamed.aldic3d")
    with zipfile.ZipFile(path) as zf:
        info = zf.getinfo("results.npz")
        # The npz payload is already DEFLATEd per array — the member is STORED
        # (no double compression) and was streamed (no BytesIO duplication).
        assert info.compress_type == zipfile.ZIP_STORED
        assert zf.getinfo("session.json").compress_type == zipfile.ZIP_DEFLATED
    loaded = load_session(path)
    np.testing.assert_array_equal(
        loaded.result.reconstruction.points, state.result.reconstruction.points
    )
    np.testing.assert_array_equal(loaded.result.ref_coords, state.result.ref_coords)


def test_save_large_result_size_sane(tmp_path):
    from al_dic_3d.project import AppState3D, save_session

    result = _synthetic_result(n_frames=6, n_pts=20_000)
    raw_bytes = sum(
        a.nbytes
        for a in (
            result.correspondence.xL,
            result.correspondence.xR,
            result.correspondence.quality,
            result.correspondence.source,
            result.reconstruction.points,
            result.reconstruction.displacement,
            result.reconstruction.reproj_error,
            result.reconstruction.source,
            result.ref_coords,
        )
    )
    t0 = time.perf_counter()
    path = save_session(AppState3D(result=result), tmp_path / "large.aldic3d")
    elapsed = time.perf_counter() - t0
    size = path.stat().st_size
    # Random float64 barely compresses; the point is the file is in the same
    # ballpark as the payload (npz-DEFLATE still applied) and the save is not
    # pathologically slow (double DEFLATE + BytesIO copy removed).
    assert 0 < size < raw_bytes * 1.1
    assert elapsed < 30.0


def test_run_with_progress_returns_synchronously(qapp):
    from al_dic_3d.gui.workers import run_with_progress

    ok, out = run_with_progress(None, "Testing…", lambda: 41 + 1, delay_ms=0)
    assert ok is True and out == 42
    ok, msg = run_with_progress(None, "Testing…", lambda: 1 / 0, delay_ms=0)
    assert ok is False and "ZeroDivisionError" in msg


def test_export_worker_alias_still_importable():
    from al_dic_3d.gui.dialogs.export_tabs.common import ExportWorker
    from al_dic_3d.gui.workers import JobWorker

    assert ExportWorker is JobWorker


# ---------------------------------------------------------------------------
# P2.6 — GUI-thread allocation caches
# ---------------------------------------------------------------------------


def test_mag_values_cached_per_frame(qapp, frame_files):
    area, signals = _canvas_area(qapp, frame_files)
    signals.display_field = "mag"
    disp = np.arange(2 * 6 * 3, dtype=np.float64).reshape(2, 6, 3)
    fake = SimpleNamespace(reconstruction=SimpleNamespace(displacement=disp))
    first = area._field_values(fake, 1)
    np.testing.assert_allclose(first, np.linalg.norm(disp[1], axis=1))
    assert area._field_values(fake, 1) is first  # cache hit: same object
    area._mag_cache.clear()
    assert area._field_values(fake, 1) is not first  # results-scoped clear


def test_drawn_roi_bool_cached_by_identity(qapp, frame_files):
    area, _signals = _canvas_area(qapp, frame_files)
    draft = area.controller.state.draft
    mask = np.zeros((48, 64), dtype=np.uint8)
    mask[10:30, 10:40] = 1
    draft.roi_mask_array = mask
    b1 = area._drawn_roi_bool()
    assert b1.dtype == np.bool_ and b1.any()
    assert area._drawn_roi_bool() is b1  # same draft array -> cached bool
    draft.roi_mask_array = mask.copy()  # every edit stores a FRESH array
    assert area._drawn_roi_bool() is not b1
    draft.roi_mask_array = None
    assert area._drawn_roi_bool() is None


def test_roi_overlay_reuses_rgba_buffer(qapp):
    from al_dic_3d.gui.controllers.roi_controller import ROIController
    from al_dic_3d.gui.widgets.image_view import ImageCanvas3D

    canvas = ImageCanvas3D()
    canvas.set_image_gray(np.zeros((40, 50)))
    ctrl = ROIController((40, 50))
    ctrl.add_rectangle(5, 5, 30, 30, "add")
    canvas.set_roi_controller(ctrl)
    canvas.update_roi_overlay()
    buf1 = canvas._roi_rgba_buf
    assert buf1 is not None and buf1.shape == (40, 50, 4)
    ctrl.add_rectangle(10, 10, 35, 35, "add")
    canvas.update_roi_overlay()
    assert canvas._roi_rgba_buf is buf1  # same-shape mask: buffer reused
    assert not canvas._roi_mask_item.pixmap().isNull()
