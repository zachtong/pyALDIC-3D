"""Setup-phase speed and feedback (fix batch V, stage 4)."""

from __future__ import annotations

import cv2
import numpy as np
import pytest

pytest.importorskip("al_dic")

from al_dic_3d.matching import gate, stereo  # noqa: E402
from al_dic_3d.runner import load_config, run_pipeline  # noqa: E402
from al_dic_3d.sequence.lazy import LazyFrameProvider, LazyMaskList, _LruDecoder  # noqa: E402
from al_dic_3d.sequence.model import StereoSequence  # noqa: E402
from tests import synth_stereo  # noqa: E402


def _speckle(h: int, w: int, seed: int) -> np.ndarray:
    from scipy.ndimage import gaussian_filter

    return gaussian_filter(np.random.default_rng(seed).random((h, w)), 1.5)


def test_threaded_ncc_seed_equals_the_serial_search(monkeypatch):
    left = _speckle(300, 400, 1)
    right = np.roll(left, (2, 7), axis=(0, 1))
    xs, ys = np.meshgrid(np.arange(30, 370, 6), np.arange(30, 270, 6))
    pts = np.column_stack([xs.ravel(), ys.ravel()]).astype(np.float64)
    pts[3] = (np.nan, 50.0)  # a non-finite point is skipped, never raises
    pts[4] = (1.0, 1.0)  # template off the image
    assert len(pts) > 2 * stereo._NCC_SEED_CHUNK  # exercises several pool tasks

    monkeypatch.setattr(gate, "_GATE_MAX_WORKERS", 1)
    serial = stereo._ncc_seed(left, right, pts, (0.0, 0.0), 12, 8)
    monkeypatch.setattr(gate, "_GATE_MAX_WORKERS", 8)
    monkeypatch.setattr(gate.os, "cpu_count", lambda: 16)
    threaded = stereo._ncc_seed(left, right, pts, (0.0, 0.0), 12, 8)

    assert np.array_equal(serial[0], threaded[0]) and np.array_equal(serial[1], threaded[1])
    ok = threaded[1]
    assert not ok[3] and not ok[4]
    assert np.all(threaded[0][ok] == (7.0, 2.0))


def test_gate_worker_cap_leaves_headroom(monkeypatch):
    monkeypatch.setattr(gate.os, "cpu_count", lambda: 24)
    assert gate._gate_workers() == 8
    monkeypatch.setattr(gate.os, "cpu_count", lambda: 4)
    assert gate._gate_workers() == 2
    monkeypatch.setattr(gate.os, "cpu_count", lambda: None)
    assert gate._gate_workers() == 1


def _write_masks(folder, shapes):
    paths = []
    for i, (h, w) in enumerate(shapes):
        m = np.zeros((h, w), np.uint8)
        m[2:-2, 2:-2] = 255
        p = folder / f"mask_{i:03d}.png"
        cv2.imwrite(str(p), m)
        paths.append(p)
    return paths


def test_validation_decodes_only_the_first_and_last_lazy_mask(tmp_path, monkeypatch):
    img = np.zeros((20, 30), np.uint8)
    frames = []
    for i in range(6):
        p = tmp_path / f"f{i}.png"
        cv2.imwrite(str(p), img)
        frames.append(p)
    masks = LazyMaskList(_write_masks(tmp_path, [(20, 30)] * 6))

    decoded: list[int] = []
    real = _LruDecoder._get

    def spy(self, idx):
        if self is masks._decoder:
            decoded.append(idx)
        return real(self, idx)

    monkeypatch.setattr(_LruDecoder, "_get", spy)
    prov = LazyFrameProvider(frames)
    seq = StereoSequence(providers={"L": prov, "R": prov}, masks={"L": masks})
    seq.validate()
    seq.validate()
    assert sorted(set(decoded)) == [0, 5]


def test_a_lazy_mask_of_another_size_fails_when_it_is_decoded(tmp_path):
    masks = LazyMaskList(_write_masks(tmp_path, [(20, 30), (20, 30), (21, 30)]))
    assert masks[0].shape == (20, 30)
    assert set(np.unique(masks[1])) <= {0.0, 1.0}
    with pytest.raises(ValueError, match="mask_002.png is 30x21"):
        masks[2]


def test_setup_steps_report_progress_before_tracking(tmp_path):
    scene = synth_stereo.build_scene(tmp_path, n_frames=2)
    events: list[tuple[float, str]] = []
    run_pipeline(
        load_config(synth_stereo.write_config(tmp_path, scene)),
        progress=lambda f, m: events.append((f, m)),
    )
    msgs = [m for _, m in events]
    first_track = next(i for i, m in enumerate(msgs) if m.startswith(("L:", "R:")))
    setup = msgs[:first_track]
    assert setup[0].startswith("Setup: checking the sequence")
    assert any(m.startswith("Setup: frame-1 stereo match at") for m in setup)
    assert any(m.startswith("Setup: left-camera initial guess") for m in setup)
    assert any(m.startswith("Setup: right-camera mesh") for m in setup)
    assert all(f == 0.0 for f, m in events[:first_track])


def test_shared_spline_coefficients_give_the_same_znssd():
    from al_dic_3d.matching.primitives import _znssd, spline_coefficients

    rng = np.random.default_rng(3)
    ref = _speckle(120, 140, 4) * 255
    dfm = np.roll(ref, 1, axis=1)
    pts = np.column_stack([rng.uniform(20, 120, 300), rng.uniform(20, 100, 300)])
    u = np.column_stack([np.ones(300), np.zeros(300)])
    f = rng.normal(0, 0.01, (300, 4))
    args = (ref, dfm, pts, u, f, 16, np.ones(300, bool), np.ones_like(ref))
    base = _znssd(*args)
    shared = _znssd(*args, coeffs=spline_coefficients(dfm))
    assert np.array_equal(base, shared, equal_nan=True)
    with pytest.raises(ValueError, match="do not match"):
        _znssd(*args, coeffs=np.zeros((5, 5)))


def test_the_gate_filters_each_deformed_frame_once(monkeypatch):
    from al_dic_3d.matching import primitives
    from al_dic_3d.matching.gate import gate_by_znssd

    calls = {"n": 0}
    real = primitives.spline_coefficients

    def spy(img):
        calls["n"] += 1
        return real(img)

    monkeypatch.setattr(primitives, "spline_coefficients", spy)
    ref = _speckle(120, 120, 5) * 255
    frames = [ref, np.roll(ref, 1, axis=1), np.roll(ref, 2, axis=1)]
    xs, ys = np.meshgrid(np.arange(20, 101, 8.0), np.arange(20, 101, 8.0))
    coords = np.column_stack([xs.ravel(), ys.ravel()])
    n = len(coords)
    u = np.zeros((3, n, 2))
    u[1, :, 0], u[2, :, 0] = 1.0, 2.0
    u[1, :5] += 9.0  # a few wrong tracks force the translation retry
    valid = np.ones((3, n), bool)
    gate_by_znssd(frames, np.ones_like(ref), coords, u, valid, 16, 1.0, workers=1)
    assert calls["n"] == 2  # one filter per deformed frame, retry included


def test_lazy_masks_are_cached_as_uint8_and_served_as_float64(tmp_path):
    masks = LazyMaskList(_write_masks(tmp_path, [(20, 30)] * 2))
    m = masks[0]
    assert m.dtype == np.float64 and m.flags["C_CONTIGUOUS"]
    assert set(np.unique(m)) == {0.0, 1.0}
    cached = masks._decoder._get(0)
    assert cached.dtype == np.uint8 and cached.nbytes == 20 * 30
    m[:] = 7.0  # a caller scribbling on its copy never reaches the cache
    assert set(np.unique(masks[0])) == {0.0, 1.0}


def test_memory_projection_includes_the_setup_and_gate_arrays():
    from al_dic_3d import memcheck

    h, w = 3000, 4000
    base = memcheck.estimate_peak_bytes(6, h, w, 2, lazy=True, n_pts=27170)
    gib = 1024**3
    # Fix batch V calibration point: 6 frames at 12 Mpx (8-bit TIFF, 27,170
    # nodes, left gate overlapping the right engine) peaked at 4.72 GiB above
    # the process baseline; the projection must cover it.
    assert base / gib >= 4.72
    assert memcheck.SETUP_AND_GATE_FRAMES * h * w * 8 <= base


def test_frames_are_cached_in_their_native_dtype(tmp_path):
    img = (np.arange(20 * 30).reshape(20, 30) % 251).astype(np.uint8)
    p = tmp_path / "f.png"
    cv2.imwrite(str(p), img)
    prov = LazyFrameProvider([p])
    out = prov.get_normalized(0)
    assert out.dtype == np.float64 and np.array_equal(out, img.astype(np.float64))
    assert prov._get(0).dtype == np.uint8  # the LRU holds 1 byte per pixel
    out[:] = -1.0  # the caller's copy is private
    assert np.array_equal(prov.get_normalized(0), img.astype(np.float64))
    img16 = (np.arange(20 * 30).reshape(20, 30) * 97).astype(np.uint16)
    p16 = tmp_path / "f16.png"
    cv2.imwrite(str(p16), img16)
    assert np.array_equal(LazyFrameProvider([p16]).get_normalized(0), img16.astype(np.float64))


def test_a_prepared_reference_gives_the_same_match():
    from al_dic_3d.matching.primitives import make_dicpara, match_points, prepare_reference

    ref = _speckle(160, 160, 8) * 255
    dfm = np.roll(ref, (1, 2), axis=(0, 1))
    xs, ys = np.meshgrid(np.arange(40, 121, 10.0), np.arange(40, 121, 10.0))
    pts = np.column_stack([xs.ravel(), ys.ravel()])
    para = make_dicpara(img_size=(160, 160), roi=(20, 140, 20, 140), winsize=20)
    u0 = np.tile([2.0, 1.0], (len(pts), 1))
    fresh = match_points(ref, dfm, pts, u0, para)
    prepared = prepare_reference(ref, pts, para)
    for _ in range(2):  # the precompute is reusable across solves
        again = match_points(ref, dfm, pts, u0, para, reference=prepared)
        for a, b in zip(fresh, again, strict=True):
            assert np.array_equal(a, b, equal_nan=True)
    assert np.allclose(fresh[0][fresh[2]], (2.0, 1.0), atol=1e-3)
