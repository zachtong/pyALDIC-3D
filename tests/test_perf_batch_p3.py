"""Performance batch P3 — throughput + export hygiene.

P3.1 animation renderer cache cleared per frame (not per camera/field pass)
P3.2 render3d sequence: one plotter, in-place mesh updates, hoisted field values
P3.3 npz/mat archive hygiene (view-built stacks, schema-2 canonical strain keys)
P3.4 resample_to_points Delaunay/KD-tree reuse across frames
P3.5 strain3d vectorization equivalence + progress/cancel plumbing
P3.6 opt-in parallel L/R temporal tracks (identical results, dual progress)
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import sys
import threading
import time
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from al_dic_3d.matching.contracts import TRACKED, CorrespondenceSet  # noqa: E402
from al_dic_3d.reconstruct import Reconstruction3D  # noqa: E402
from al_dic_3d.runner import RunResult, load_config, run_pipeline  # noqa: E402
from al_dic_3d.strain3d.model import STRAIN_FIELDS, StrainResult3D  # noqa: E402

try:
    import pyvista as pv  # PolyData only (no GL) for the P3.2 stub tests
except Exception:  # pragma: no cover - optional extra
    pv = None

needs_pyvista = pytest.mark.skipif(pv is None, reason="pyvista not installed")

Z0 = 800.0


# ---------------------------------------------------------------------------
# Shared synthetic result (no pipeline run): regular grid -> quad topology.
# ---------------------------------------------------------------------------


def _grid_result(nx: int = 9, n_frames: int = 4, with_strain: bool = True) -> RunResult:
    ii, jj = np.meshgrid(np.arange(nx), np.arange(nx))
    ii, jj = ii.ravel(), jj.ravel()
    ref_2d = np.column_stack([ii * 16.0 + 40.0, jj * 16.0 + 40.0])
    xw = (ii - (nx - 1) / 2.0) * 2.0
    yw = (jj - (nx - 1) / 2.0) * 2.0
    ref_3d = np.column_stack([xw, yw, np.full_like(xw, Z0)])
    n_pts = ref_2d.shape[0]

    points = np.stack([ref_3d + k * np.array([0.05, 0.0, 0.2]) for k in range(n_frames)])
    displacement = points - points[0][None]
    rec = Reconstruction3D(
        points,
        displacement,
        np.zeros((n_frames, n_pts)),
        np.full((n_frames, n_pts), TRACKED, np.uint8),
    )
    x_img = np.stack([ref_2d] * n_frames)
    cs = CorrespondenceSet(
        strategy="track_both",
        xL=x_img.copy(),
        xR=x_img.copy(),
        quality=np.zeros((n_frames, n_pts)),
        source=np.full((n_frames, n_pts), TRACKED, np.uint8),
    )
    strain = None
    if with_strain:
        rng = np.random.default_rng(11)
        fields = {name: rng.normal(0, 1e-3, size=(n_frames, n_pts)) for name in STRAIN_FIELDS}
        strain = StrainResult3D(**fields)
    return RunResult(
        strategy="track_both",
        ref_coords=ref_2d,
        correspondence=cs,
        reconstruction=rec,
        strain=strain,
        meta={},
    )


# ---------------------------------------------------------------------------
# P3.1 — animation renderer cache cleared INSIDE the frame loop
# ---------------------------------------------------------------------------


def test_animation_clears_renderer_caches_per_frame(tmp_path, monkeypatch):
    from al_dic_3d.export import FieldImageConfig
    from al_dic_3d.export import animation as anim_mod

    clears: list[int] = []
    orig = anim_mod.FieldmapRenderer.clear_frame_caches

    def counting(self):
        clears.append(1)
        orig(self)

    monkeypatch.setattr(anim_mod.FieldmapRenderer, "clear_frame_caches", counting)
    img = np.zeros((32, 40, 3), np.uint8)
    monkeypatch.setattr(anim_mod, "render_field_frame", lambda *a, **k: (img, 0.0, 1.0))

    n_frames = 5
    result = SimpleNamespace(reconstruction=SimpleNamespace(n_frames=n_frames))
    paths = anim_mod.export_animation(
        tmp_path,
        "p",
        "20260710000000",
        result,
        {},
        [FieldImageConfig(field_id="U"), FieldImageConfig(field_id="W")],
        cameras=("L",),
        fmt="gif",
        include_colorbar=False,
    )
    assert len(paths) == 2
    # One clear per ENCODED frame (2 fields x 5 frames) — the pre-P3.1 code
    # cleared once per (camera, field) pass (2 total) and let the Tier-1
    # grids/masks of the whole sequence accumulate during the encode.
    assert len(clears) == 2 * n_frames


# ---------------------------------------------------------------------------
# P3.2 — render3d sequence: single plotter + in-place updates + hoisted values
# ---------------------------------------------------------------------------


class _FakePlotter:
    def __init__(self):
        self.camera_position = None
        self.add_mesh_calls = 0
        self.clear_calls = 0
        self.iso_calls = 0
        self.closed = False

    def clear(self):
        self.clear_calls += 1

    def add_mesh(self, mesh, **_kw):
        self.add_mesh_calls += 1
        return SimpleNamespace(mapper=None)

    def view_isometric(self):
        self.iso_calls += 1

    def close(self):
        self.closed = True


@needs_pyvista
def test_export_view3d_frames_single_plotter_in_place(tmp_path, monkeypatch):
    from al_dic_3d.export import render3d

    made: list[_FakePlotter] = []

    def fake_make(window_size, background):
        p = _FakePlotter()
        made.append(p)
        return p

    monkeypatch.setattr(render3d, "_make_plotter", fake_make)
    monkeypatch.setattr(render3d, "_screenshot_bgr", lambda pl: np.zeros((24, 32, 3), np.uint8))
    field_calls: list[int] = []
    orig_ff = render3d.display_field_frame

    def counting_ff(result, field_id, k, **kw):
        field_calls.append(k)
        return orig_ff(result, field_id, k, **kw)

    monkeypatch.setattr(render3d, "display_field_frame", counting_ff)

    result = _grid_result(n_frames=4, with_strain=False)
    # Frame 3 loses a point -> the quad topology changes -> rebuild path.
    result.reconstruction.points[3, 0] = np.nan
    result.reconstruction.displacement[3, 0] = np.nan

    paths = render3d.export_view3d_frames(
        tmp_path,
        "v",
        "20260710000001",
        result,
        "U",
        write_frames=True,
        animation_format=None,
        auto_range=True,
    )
    assert len(paths) == 4  # one PNG per frame
    assert len(made) == 1 and made[0].closed  # ONE plotter for the sequence
    # Frames 0-2 share topology (one add_mesh + in-place updates); frame 3's
    # NaN point changes the faces and takes the rebuild path.
    assert made[0].add_mesh_calls == 2
    assert made[0].iso_calls == 2  # camera re-framed only on rebuilds
    # Hoisted values (P3.2): field_frame ran ONCE per frame — the color-range
    # pass and the render loop share the same arrays (was 2x per frame).
    assert len(field_calls) == 4


# ---------------------------------------------------------------------------
# P3.3 — archive hygiene
# ---------------------------------------------------------------------------


def test_field_stack_matches_per_frame_loop():
    from al_dic_3d.export import field_frame, field_stack

    result = _grid_result()
    n_frames = result.reconstruction.n_frames
    for field in ("U", "V", "W", "mag", "exx", "von_mises"):
        stack = field_stack(result, field)
        assert stack is not None and stack.shape[0] == n_frames
        for k in range(n_frames):
            np.testing.assert_array_equal(stack[k], field_frame(result, field, k))
    assert field_stack(replace(result, strain=None), "exx") is None
    assert field_stack(result, "not_a_field") is None


def test_runner_arrays_schema3_single_canonical_strain_keys():
    from al_dic_3d.runner import ARCHIVE_SCHEMA, _arrays

    assert ARCHIVE_SCHEMA == 3
    result = _grid_result()
    arrays = _arrays(result)
    for name in ("exx", "eyy", "von_mises", "dwdx", "dwdy"):
        np.testing.assert_array_equal(arrays[name], getattr(result.strain, name))
    # No legacy strain_<name> aliases (schema 2); the ONLY strain_-prefixed key
    # allowed is the schema-3 strain_valid validity stack (absent here — no trim).
    assert not any(key.startswith("strain_") and key != "strain_valid" for key in arrays)
    # Legacy tool keys survive.
    for key in ("points3D", "displacement3D", "xL", "xR", "quality", "n_frames", "n_pts"):
        assert key in arrays


def test_export_npz_mat_reuse_prebuilt_arrays(tmp_path):
    import scipy.io

    from al_dic_3d.export import export_mat, export_npz, selected_arrays

    result = _grid_result()
    fields = ["U", "mag", "exx"]
    arrays = selected_arrays(result, fields)
    npz_path = export_npz(result, fields, tmp_path, "pre", arrays=arrays)
    mat_path = export_mat(result, fields, tmp_path, "pre", arrays=arrays)
    npz = np.load(npz_path)
    mat = scipy.io.loadmat(str(mat_path))
    fresh = selected_arrays(result, fields)
    for key in ("U", "mag", "exx", "points3D"):
        np.testing.assert_array_equal(npz[key], fresh[key])
        np.testing.assert_array_equal(np.asarray(mat[key]), fresh[key])


# ---------------------------------------------------------------------------
# P3.4 — resample_to_points geometry reuse
# ---------------------------------------------------------------------------


def _resample_inputs(n: int = 60, seed: int = 0):
    rng = np.random.default_rng(seed)
    ref = rng.uniform(0, 100, size=(n, 2))
    query = np.vstack(
        [
            rng.uniform(10, 90, size=(20, 2)),  # inside the hull
            [[500.0, 500.0], [-50.0, -50.0]],  # outside -> nearest fill
            [[np.nan, 1.0]],  # non-finite query stays NaN
        ]
    )
    return ref, query


def test_resample_cache_identical_results_and_single_delaunay():
    from al_dic_3d.matching.temporal import _RESAMPLE_CACHE, resample_to_points

    ref, query = _resample_inputs()
    rng = np.random.default_rng(1)
    _RESAMPLE_CACHE.clear()

    for _frame in range(5):  # static finite mask, changing values (frame loop)
        values = rng.normal(0, 1, size=ref.shape)
        values[:4] = np.nan  # same invalid rows every frame
        cached = resample_to_points(ref, values, query)
        fresh = resample_to_points(ref, values, query, reuse_geometry=False)
        np.testing.assert_array_equal(cached, fresh)
        assert np.isnan(cached[-1]).all()  # non-finite query contract intact
    assert _RESAMPLE_CACHE.delaunay_builds == 1  # ONE triangulation for 5 frames
    assert _RESAMPLE_CACHE.kdtree_builds == 1  # ONE tree for the nearest fills

    values = rng.normal(0, 1, size=ref.shape)
    values[:6] = np.nan  # finite-node SET changed -> rebuild expected
    resample_to_points(ref, values, query)
    assert _RESAMPLE_CACHE.delaunay_builds == 2


def test_resample_cache_bounded():
    from al_dic_3d.matching.temporal import _RESAMPLE_CACHE, resample_to_points

    ref, query = _resample_inputs()
    _RESAMPLE_CACHE.clear()
    rng = np.random.default_rng(2)
    for k in range(_RESAMPLE_CACHE._capacity + 3):
        values = rng.normal(0, 1, size=ref.shape)
        values[: 3 + k] = np.nan  # a new finite set every call
        resample_to_points(ref, values, query, fill_nearest=False)
    assert len(_RESAMPLE_CACHE._entries) <= _RESAMPLE_CACHE._capacity


# ---------------------------------------------------------------------------
# P3.5 — vectorized strain fits: proven equivalence + progress/cancel
# ---------------------------------------------------------------------------


def _strain_cloud(seed: int = 42, n_side: int = 21):
    rng = np.random.default_rng(seed)
    ii, jj = np.meshgrid(np.arange(n_side), np.arange(n_side))
    ref_2d = np.column_stack([ii.ravel() * 16.0 + 40, jj.ravel() * 16.0 + 40])
    x = (ii.ravel() - n_side / 2) * 2.0
    y = (jj.ravel() - n_side / 2) * 2.0
    ref_3d = np.column_stack([x, y, Z0 + 0.5 * np.sin(x / 10) + rng.normal(0, 0.01, x.size)])
    disp = np.column_stack(
        [
            0.01 * x + rng.normal(0, 1e-4, x.size),
            0.005 * y + rng.normal(0, 1e-4, x.size),
            0.02 * np.cos(y / 8) + rng.normal(0, 1e-4, x.size),
        ]
    )
    disp[rng.random(x.size) < 0.1] = np.nan  # holes -> boundary nodes inside
    # A rank-deficient stripe: identical 3D coordinates collapse the plane and
    # gradient fits to singular systems (exercises the per-node fallback).
    ref_3d[:n_side, :2] = 0.0
    return ref_2d, ref_3d, disp


@pytest.mark.parametrize("coordinate", ["local", "camera0", "specific"])
def test_fit_gradients_matches_reference_loop(coordinate):
    from al_dic_3d.strain3d.gradients import _fit_gradients_loop, fit_gradients

    rng = np.random.default_rng(7)
    specimen = np.linalg.qr(rng.normal(size=(3, 3)))[0] if coordinate == "specific" else None
    ref_2d, ref_3d, disp = _strain_cloud()
    old = _fit_gradients_loop(
        ref_2d, ref_3d, disp, 32.5, coordinate=coordinate, specimen_R=specimen
    )
    new = fit_gradients(ref_2d, ref_3d, disp, 32.5, coordinate=coordinate, specimen_R=specimen)
    assert np.array_equal(np.isnan(old), np.isnan(new))  # identical void pattern
    finite = np.isfinite(old)
    if finite.any():
        assert np.max(np.abs(old[finite] - new[finite])) < 1e-10


def test_fit_gradients_isolated_points_all_nan():
    from al_dic_3d.strain3d.gradients import fit_gradients

    ref_2d = np.array([[0.0, 0.0], [500.0, 0.0], [0.0, 500.0]])
    ref_3d = np.column_stack([ref_2d, np.full(3, Z0)])
    coef = fit_gradients(ref_2d, ref_3d, np.zeros((3, 3)), 32.5)
    assert np.isnan(coef).all()


def test_neighbor_cache_reused_across_frames_and_bounded():
    from al_dic_3d.strain3d.gradients import (
        _NEIGHBOR_CACHE_CAPACITY,
        fit_gradients,
    )

    ref_2d, ref_3d, disp = _strain_cloud()
    cache: dict = {}
    a = fit_gradients(ref_2d, ref_3d, disp, 32.5, neighbor_cache=cache)
    assert len(cache) == 1
    table = next(iter(cache.values()))
    b = fit_gradients(ref_2d, ref_3d, disp * 2.0, 32.5, neighbor_cache=cache)
    assert len(cache) == 1 and next(iter(cache.values())) is table  # reused
    assert np.array_equal(np.isnan(a), np.isnan(b))
    # Distinct validity patterns stay bounded.
    rng = np.random.default_rng(0)
    for _ in range(_NEIGHBOR_CACHE_CAPACITY + 4):
        d = disp.copy()
        d[rng.integers(0, len(d), size=3)] = np.nan
        fit_gradients(ref_2d, ref_3d, d, 32.5, neighbor_cache=cache)
    assert len(cache) <= _NEIGHBOR_CACHE_CAPACITY


def test_smooth_displacement_matches_reference_loop():
    from al_dic_3d.strain3d.compute import _smooth_displacement_loop, smooth_displacement

    rng = np.random.default_rng(3)
    ref_2d = rng.uniform(0, 400, size=(1500, 2))
    disp = rng.normal(0, 1, size=(1500, 3))
    disp[rng.random(1500) < 0.15] = np.nan
    old = _smooth_displacement_loop(ref_2d, disp, 8.0)
    new = smooth_displacement(ref_2d, disp, 8.0)
    assert np.array_equal(np.isnan(old), np.isnan(new))
    assert np.nanmax(np.abs(old - new)) < 1e-12


def test_compute_surface_strain_progress_and_cancel():
    from al_dic_3d.strain3d import compute_surface_strain

    result = _grid_result(n_frames=4, with_strain=False)
    ticks: list[tuple[float, str]] = []
    strain = compute_surface_strain(
        result.reconstruction,
        result.ref_coords,
        strain_size=3,
        winstepsize=16,
        progress_cb=lambda f, m: ticks.append((f, m)),
    )
    assert strain.n_frames == 4
    assert [round(f, 6) for f, _ in ticks] == [0.25, 0.5, 0.75, 1.0]
    assert all("frame" in m for _, m in ticks)

    # threading.Event and plain callables both cancel before the first frame.
    event = threading.Event()
    event.set()
    for stop in (event, lambda: True):
        with pytest.raises(RuntimeError, match="cancelled"):
            compute_surface_strain(
                result.reconstruction, result.ref_coords, strain_size=3, stop_event=stop
            )


# ---------------------------------------------------------------------------
# P3.5 — GUI plumbing: worker cancel + window progress slots
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def qapp():
    pytest.importorskip("PySide6")
    from al_dic_3d.gui.app import create_app

    return create_app([])


def test_strain_worker_relays_progress_and_cancels(qapp):
    from PySide6.QtWidgets import QApplication

    from al_dic_3d.gui.widgets.strain_support import StrainWorker

    started = threading.Event()

    class SlowCtrl:
        def compute(self, override, progress_cb=None, stop_event=None):
            started.set()
            for k in range(2000):
                if stop_event is not None and stop_event.is_set():
                    raise RuntimeError("cancelled")
                if progress_cb is not None:
                    progress_cb((k + 1) / 2000, f"strain frame {k + 1}/2000")
                time.sleep(0.002)
            return "never"

    worker = StrainWorker(SlowCtrl(), {})
    seen = {"cancelled": False, "failed": None, "done": None, "progress": []}
    worker.cancelled.connect(lambda: seen.__setitem__("cancelled", True))
    worker.failed.connect(lambda m: seen.__setitem__("failed", m))
    worker.finished_ok.connect(lambda s: seen.__setitem__("done", s))
    worker.progress.connect(lambda f, m: seen["progress"].append(f))
    worker.start()
    assert started.wait(10)
    worker.request_stop()
    assert worker.wait(10_000)
    QApplication.processEvents()  # deliver queued cross-thread signals
    assert seen["cancelled"] is True
    assert seen["failed"] is None and seen["done"] is None
    assert seen["progress"]  # per-frame ticks arrived before the cancel


def test_strain_window_progress_and_cancel_ui(qapp):
    from al_dic_3d.gui.state import GuiSignals
    from al_dic_3d.gui.strain_window import StrainWindow3D
    from tests.test_strain_window import _synthetic_controller

    win = StrainWindow3D(_synthetic_controller(), GuiSignals())
    try:
        # isVisibleTo(win) ignores that the window itself is never shown.
        assert not win._cancel_btn.isVisibleTo(win)  # hidden until a compute runs
        assert win._progress.maximum() == 100  # determinate (P3.5)
        win._on_worker_progress(0.5, "strain frame 2/4")
        assert win._progress.value() == 50
        assert "50" in win._progress_lbl.text()
        win._on_worker_cancelled()
        assert win._compute_btn.isEnabled()
        assert not win._cancel_btn.isVisibleTo(win)
        assert not win._progress.isVisibleTo(win)
    finally:
        win.close()


# ---------------------------------------------------------------------------
# P3.6 — parallel L/R tracks (opt-in)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def parity_cfg(tmp_path_factory):
    from tests import synth_parity

    d = tmp_path_factory.mktemp("p3_scene")
    scene = synth_parity.build_parity_scene(d, img=200, n_frames=3, seed=7)
    return load_config(synth_parity.write_config(d, scene))


def test_load_config_parses_parallel_cameras(parity_cfg):
    assert parity_cfg.parallel_cameras is False  # default off

    scene_dir = parity_cfg.base_dir
    text = (scene_dir / "config.toml").read_text(encoding="utf-8")
    alt = scene_dir / "parallel.toml"  # same dir: relative specs still resolve
    alt.write_text(
        text.replace("[matching]", "[matching]\nparallel_cameras = true", 1),
        encoding="utf-8",
    )
    assert load_config(alt).parallel_cameras is True


@pytest.mark.skipif(
    sys.platform == "darwin",
    reason="parallel_cameras falls back to sequential on macOS (numba workqueue "
    "threading layer aborts on concurrent JIT entry) — no dual progress there; "
    "the fallback itself is covered platform-independently below",
)
def test_parallel_cameras_identical_results_and_dual_progress(parity_cfg):
    seq_result = run_pipeline(parity_cfg)

    seen: list[tuple[float, str]] = []
    par_result = run_pipeline(
        replace(parity_cfg, parallel_cameras=True),
        progress=lambda f, m: seen.append((f, m)),
    )

    cs_a, cs_b = seq_result.correspondence, par_result.correspondence
    np.testing.assert_array_equal(cs_a.xL, cs_b.xL)
    np.testing.assert_array_equal(cs_a.xR, cs_b.xR)
    np.testing.assert_array_equal(cs_a.quality, cs_b.quality)
    np.testing.assert_array_equal(cs_a.source, cs_b.source)
    np.testing.assert_array_equal(
        seq_result.reconstruction.points, par_result.reconstruction.points
    )
    # Per-camera diagnostics stayed intact (honesty gate accounting, F3.1):
    # identical rows — same cams, same validity counts, same gate kills.
    assert list(cs_a.diagnostics) == list(cs_b.diagnostics)

    fracs = [f for f, _ in seen]
    assert fracs and all(0.0 <= f <= 1.0 for f in fracs)
    assert fracs[-1] == pytest.approx(1.0)
    msgs = " | ".join(m for _, m in seen)
    assert "L: " in msgs and "R: " in msgs  # both cameras reported (serialized)


def test_parallel_cameras_darwin_falls_back_sequential(parity_cfg, monkeypatch):
    """On macOS the parallel path must warn and run sequentially (v1.0.2).

    numba's workqueue threading layer aborts the process when two host threads
    enter JIT-parallel regions concurrently, so track_both serializes on
    darwin. Monkeypatching sys.platform exercises that branch on every OS.
    """
    import al_dic_3d.matching.strategies.track_both as tb

    monkeypatch.setattr(tb.sys, "platform", "darwin")
    with pytest.warns(UserWarning, match="parallel camera tracking is unavailable on macOS"):
        result = run_pipeline(replace(parity_cfg, parallel_cameras=True))
    baseline = run_pipeline(parity_cfg)
    np.testing.assert_array_equal(result.correspondence.xL, baseline.correspondence.xL)
    np.testing.assert_array_equal(result.correspondence.xR, baseline.correspondence.xR)


def test_parallel_cameras_cancel_reaches_both(parity_cfg):
    cfg = replace(parity_cfg, parallel_cameras=True)
    t0 = time.perf_counter()
    with pytest.raises(RuntimeError, match="cancelled"):
        run_pipeline(cfg, stop=lambda: True)
    assert time.perf_counter() - t0 < 120.0  # both tracks aborted cooperatively


def test_parallel_zero_fill_guard_survives_threading(monkeypatch):
    """The all-NaN zero-fill warning must become a hard error even when it is
    emitted from a worker thread (catch_warnings is process-global; the
    parallel path holds ONE thread-safe recorder instead)."""
    import warnings

    from al_dic_3d.matching.strategies import track_both as tb
    from al_dic_3d.matching.temporal import ZERO_FILL_ERROR

    def fake_track(frames, mesh, para, **kwargs):
        assert kwargs.get("capture_warnings") is False  # per-call capture off
        if frames == "right":  # one camera zero-fills, the other is fine
            warnings.warn("All nodes are NaN, cannot interpolate. Returning zeros.", stacklevel=1)
        return f"tf_{frames}"

    monkeypatch.setattr(tb, "temporal_track", fake_track)
    strategy = tb.TrackBothStrategy(parallel_cameras=True)
    kwargs = {"L": {}, "R": {}}
    with pytest.raises(RuntimeError) as exc:
        strategy._track_parallel("left", "right", None, None, None, None, kwargs, None, None)
    assert str(exc.value) == ZERO_FILL_ERROR

    # Without the warning both fields come back and the guard stays silent.
    monkeypatch.setattr(tb, "temporal_track", lambda frames, *a, **k: f"tf_{frames}")
    tf_l, tf_r = strategy._track_parallel(
        "left", "right", None, None, None, None, kwargs, None, None
    )
    assert (tf_l, tf_r) == ("tf_left", "tf_right")


def test_memcheck_parallel_doubles_engine_transient():
    from al_dic_3d import memcheck

    seq = memcheck.estimate_peak_bytes(20, 2048, 2448, 2, lazy=True, n_pts=20000)
    par = memcheck.estimate_peak_bytes(20, 2048, 2448, 2, lazy=True, n_pts=20000, parallel=True)
    transient = int(memcheck.ENGINE_TRANSIENT_BYTES_PER_MPX * (2048 * 2448 / 1e6))
    assert par - seq == transient  # P3.6: both engine working sets live at once
