"""Batch P4: the temporal honesty gate must be VISIBLE, CANCELLABLE and FAST.

The 400-frame Tier B stress run spent 66% of its wall time outside the tracking
loop: ``_gate_by_znssd`` re-verifies every tracked frame AFTER ``run_aldic``
returns, cost ~3x the tracking it verifies, and reported no progress at all —
the bar froze at 100% for ~16 min per camera (the "looks hung" failure).

The contract locked in here:

* **Visible** — the gate owns its own progress band; the fraction a caller sees
  from one ``temporal_track`` never goes backwards and always reaches 1.0.
* **Cancellable** — a stop during the gate aborts after AT MOST one more frame,
  and every frame still shipped as tracked was actually verified.
* **Fast, bit-identically** — the optimization (hoisted cubic spline prefilter +
  threaded point chunks) must not move one bit of the ZNSSD field, so not one
  gate verdict can change. Proven against a frozen copy of the pre-P4 kernel.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.ndimage import gaussian_filter, map_coordinates

import al_dic_3d.matching.primitives as primitives
from al_dic_3d.matching.primitives import _znssd, _znssd_block, make_dicpara
from al_dic_3d.matching.temporal import (
    _ENGINE_PROGRESS_SHARE,
    _gate_by_znssd,
    build_grid_mesh,
    temporal_track,
)


def _speckle(h: int, w: int, seed: int = 3) -> np.ndarray:
    rng = np.random.default_rng(seed)
    img = gaussian_filter(rng.random((h, w)), 1.6)
    lo, hi = img.min(), img.max()
    return ((img - lo) / (hi - lo) * 200.0 + 20.0).astype(np.float64)


# --- the frozen pre-P4 kernel (the "reference gate") -------------------------


def _znssd_legacy(ref, dfm, points, u_2d, f_2d, winsize, valid, mask, chunk=2048):
    """Verbatim copy of the pre-batch-P4 ``_znssd`` driver.

    Differs from the shipped one ONLY in what batch P4 changed: it re-runs
    scipy's cubic spline prefilter inside every chunk (``prefilter=True``) and
    never threads. Kept frozen here so "the optimization changed nothing" is
    checked against the actual previous behaviour, not a paraphrase of it.
    """
    h, w = ref.shape
    n = points.shape[0]
    half = winsize // 2
    offs = np.arange(-half, half + 1)
    xx, yy = np.meshgrid(offs.astype(np.float64), offs.astype(np.float64))
    z = np.full(n, np.nan, dtype=np.float64)

    x0 = np.round(points[:, 0])
    y0 = np.round(points[:, 1])
    in_bounds = valid & (x0 >= 0) & (x0 <= w - 1) & (y0 >= 0) & (y0 <= h - 1)
    idx = np.where(in_bounds)[0]
    if idx.size == 0:
        return z
    mask_has_holes = bool((np.asarray(mask) <= 0.5).any())

    chunk = max(1, int(chunk))
    for start in range(0, idx.size, chunk):
        sel = idx[start : start + chunk]
        z[sel] = _legacy_block(
            ref, dfm, sel, x0, y0, u_2d, f_2d, offs, xx, yy, mask, mask_has_holes
        )
    return z


def _legacy_block(ref, dfm, idx, x0, y0, u_2d, f_2d, offs, xx, yy, mask, holes):
    h, w = ref.shape
    s = xx.shape[0]
    rx = x0[idx].astype(np.int64)
    ry = y0[idx].astype(np.int64)
    rows = ry[:, None, None] + offs[None, :, None]
    cols = rx[:, None, None] + offs[None, None, :]
    ref_in = (rows >= 0) & (rows <= h - 1) & (cols >= 0) & (cols <= w - 1)
    rows_c = np.clip(rows, 0, h - 1)
    cols_c = np.clip(cols, 0, w - 1)
    f = ref[rows_c, cols_c]
    msub = (mask[rows_c, cols_c] > 0.5) & ref_in
    if holes:
        msub = primitives._center_connected_stack(msub)

    f11, f21, f12, f22 = f_2d[idx, 0], f_2d[idx, 1], f_2d[idx, 2], f_2d[idx, 3]
    uu, vv = u_2d[idx, 0], u_2d[idx, 1]
    gu = (
        (1 + f11[:, None, None]) * xx
        + f12[:, None, None] * yy
        + rx[:, None, None]
        + uu[:, None, None]
    )
    gv = (
        f21[:, None, None] * xx
        + (1 + f22[:, None, None]) * yy
        + ry[:, None, None]
        + vv[:, None, None]
    )
    # The pre-P4 sampling call: prefilter=True re-filters the WHOLE image here.
    g = map_coordinates(dfm, [gv.ravel(), gu.ravel()], order=3, mode="constant", cval=0.0)
    g = g.reshape(idx.size, s, s)

    comb = msub & (np.abs(g) > 1e-10)
    cnt = comb.sum((1, 2))
    cnt_safe = np.maximum(cnt, 1)
    fm = f * comb
    meanf = fm.sum((1, 2)) / cnt_safe
    varf = ((fm - meanf[:, None, None] * comb) ** 2).sum((1, 2)) / cnt_safe
    bottomf = np.sqrt(np.maximum((cnt - 1) * varf, 1e-30))
    gm = g * comb
    meang = gm.sum((1, 2)) / cnt_safe
    varg = ((gm - meang[:, None, None] * comb) ** 2).sum((1, 2)) / cnt_safe
    bottomg = np.sqrt(np.maximum((cnt - 1) * varg, 1e-30))
    res = (fm - meanf[:, None, None]) / bottomf[:, None, None] - (
        gm - meang[:, None, None]
    ) / bottomg[:, None, None]
    zi = (res * res * comb).sum((1, 2))
    zi[cnt < 4] = np.nan
    return zi


def _gate_case(seed: int, n: int = 1200, hw: int = 220, winsize: int = 24):
    """A gate-shaped ZNSSD case: F == 0 (translation warp) and REAL failures.

    Half the points are given the true displacement (they pass the gate), half a
    garbage one (they fail it), plus border points with no support — so the
    verdict vector genuinely mixes pass / fail / NaN.
    """
    rng = np.random.default_rng(seed)
    ref = _speckle(hw, hw, seed=seed)
    shift = 2.7
    ys, xs = np.mgrid[0:hw, 0:hw].astype(np.float64)
    dfm = map_coordinates(ref, [ys - shift, xs - shift], order=3, mode="constant", cval=0.0)

    pts = rng.uniform(0, hw - 1, size=(n, 2))  # includes border points
    u = np.full((n, 2), shift, dtype=np.float64)
    garbage = rng.uniform(size=n) < 0.5
    u[garbage] += rng.uniform(6.0, 20.0, size=(int(garbage.sum()), 2))  # decorrelated
    f = np.zeros((n, 4), dtype=np.float64)  # the GATE call site: pure translation
    valid = rng.uniform(size=n) > 0.05
    mask = np.ones((hw, hw), dtype=np.float64)
    mask[70:96, 30:60] = 0.0  # a hole exercises the center-connected path
    return ref, dfm, pts, u, f, winsize, valid, mask


# --- (c) optimized gate == reference gate, verdicts element-wise identical ----


def test_optimized_znssd_is_bit_identical_to_pre_p4_kernel():
    for seed in (0, 1, 2):
        args = _gate_case(seed)
        legacy = _znssd_legacy(*args)
        for workers in (1, 2, 4):
            fast = _znssd(*args, workers=workers)
            assert np.array_equal(fast, legacy, equal_nan=True), (
                f"seed={seed} workers={workers}: ZNSSD diverged from the pre-P4 kernel"
            )


def test_gate_verdicts_unchanged_including_genuine_failures():
    """The set of GATED nodes must be identical — with real failures present."""
    args = _gate_case(5)
    legacy = _znssd_legacy(*args)
    for threshold in (0.2, 1.0, 2.0):
        pre = args[6]  # `valid`
        ref_bad = pre & ~(legacy <= threshold)
        assert ref_bad.any(), f"threshold {threshold}: no node fails — test has no power"
        assert (pre & ~ref_bad).any(), f"threshold {threshold}: every node fails — no power"
        for workers in (1, 4):
            fast = _znssd(*args, workers=workers)
            bad = pre & ~(fast <= threshold)
            np.testing.assert_array_equal(bad, ref_bad)


def test_prefilter_hoist_is_the_same_computation():
    """Sampling pre-filtered coefficients with ``prefilter=False`` is exactly
    what scipy does internally for ``mode='constant'`` (npad == 0)."""
    from scipy.ndimage import spline_filter

    rng = np.random.default_rng(11)
    img = rng.uniform(0, 255, size=(64, 71))
    coords = [rng.uniform(-3, 70, size=500), rng.uniform(-3, 74, size=500)]
    direct = map_coordinates(img, coords, order=3, mode="constant", cval=0.0)
    hoisted = map_coordinates(
        spline_filter(img, 3, output=np.float64, mode="constant"),
        coords,
        order=3,
        mode="constant",
        cval=0.0,
        prefilter=False,
    )
    assert np.array_equal(direct, hoisted)


# --- (d) the threading path is deterministic ---------------------------------


def test_znssd_workers_are_deterministic_and_chunk_invariant():
    args = _gate_case(7, n=2600)
    base = _znssd(*args, workers=1)
    for workers in (1, 2, 3, 4, 8):
        for _ in range(2):  # repeated runs: no scheduling-dependent output
            assert np.array_equal(_znssd(*args, workers=workers), base, equal_nan=True)
    for chunk in (1, 37, 512, 10**9):
        assert np.array_equal(_znssd(*args, chunk=chunk, workers=4), base, equal_nan=True)


def test_znssd_block_rejects_unfiltered_input_silently_is_not_possible():
    """``_znssd_block`` samples SPLINE COEFFICIENTS, not raw intensities.

    Guards the refactor: handing it the raw deformed image must NOT accidentally
    reproduce the coefficient-sampled answer (it would mean the prefilter was
    silently dropped and the gate metric changed).
    """
    from scipy.ndimage import spline_filter

    args = _gate_case(3, n=64, hw=120)
    ref, dfm, pts, u, f, winsize, valid, mask = args
    half = winsize // 2
    offs = np.arange(-half, half + 1)
    xx, yy = np.meshgrid(offs.astype(np.float64), offs.astype(np.float64))
    x0, y0 = np.round(pts[:, 0]), np.round(pts[:, 1])
    idx = np.where(valid & (x0 >= 0) & (x0 <= 119) & (y0 >= 0) & (y0 <= 119))[0]
    kw = dict(mask=mask, mask_has_holes=True)
    coeffs = spline_filter(dfm, 3, output=np.float64, mode="constant")
    good = _znssd_block(ref, coeffs, idx, x0, y0, u, f, offs, xx, yy, **kw)
    raw = _znssd_block(ref, dfm, idx, x0, y0, u, f, offs, xx, yy, **kw)
    assert np.isfinite(good).any()
    assert not np.allclose(good, raw, equal_nan=True)


# --- (a) the gate reports progress, monotonically -----------------------------


def _two_frame_scene(h: int = 260, n_frames: int = 3):
    f0 = _speckle(h, h, seed=4)
    frames = [f0]
    for k in range(1, n_frames):
        ys, xs = np.mgrid[0:h, 0:h].astype(np.float64)
        frames.append(
            map_coordinates(f0, [ys - 1.3 * k, xs - 0.9 * k], order=3, mode="constant", cval=0.0)
        )
    para = make_dicpara(img_size=(h, h), roi=(50, h - 50, 50, h - 50), winsize=24)
    return frames, build_grid_mesh(para, h, h), para


def test_temporal_track_progress_covers_the_gate_and_is_monotonic():
    frames, mesh, para = _two_frame_scene(n_frames=3)
    seen: list[tuple[float, str]] = []
    temporal_track(frames, mesh, para, progress=lambda f, m: seen.append((f, m)), gate_znssd=1.0)

    fracs = [f for f, _ in seen]
    assert fracs, "temporal_track reported no progress at all"
    assert all(0.0 <= f <= 1.0 for f in fracs)
    assert fracs == sorted(fracs), "progress went BACKWARDS"
    assert fracs[-1] == pytest.approx(1.0)

    gate_msgs = [(f, m) for f, m in seen if "verifying frame" in m]
    assert gate_msgs, "the gate reported nothing — the bar would freeze at 100%"
    assert len(gate_msgs) == len(frames) - 1  # one tick per verified frame
    # The engine owns [0, share]; the gate owns (share, 1].
    assert all(f > _ENGINE_PROGRESS_SHARE - 1e-9 for f, _ in gate_msgs)
    assert any(f <= _ENGINE_PROGRESS_SHARE + 1e-9 for f, _ in seen)  # engine band used
    assert gate_msgs[-1][0] == pytest.approx(1.0)


def test_progress_reaches_one_even_with_the_gate_disabled():
    frames, mesh, para = _two_frame_scene(n_frames=2)
    seen: list[float] = []
    temporal_track(frames, mesh, para, progress=lambda f, m: seen.append(f), gate_znssd=0.0)
    assert seen == sorted(seen)
    assert seen[-1] == pytest.approx(1.0)


def test_track_both_sequential_reports_the_gate_for_both_cameras(tmp_path):
    """The DEFAULT (sequential) path must show both cameras' tracks + gates.

    Before P4 the sequential branch forwarded no progress at all, so the whole
    two-camera track was invisible and the bar only moved during assembly.
    """
    from al_dic_3d.runner import load_config, run_pipeline
    from tests import synth_parity

    scene = synth_parity.build_parity_scene(tmp_path, img=200, n_frames=3, seed=7)
    cfg = load_config(synth_parity.write_config(tmp_path, scene))

    seen: list[tuple[float, str]] = []
    run_pipeline(cfg, progress=lambda f, m: seen.append((f, m)))

    corr = [(f, m) for f, m in seen if "track_both" in m or "verifying" in m or ": Frame" in m]
    fracs = [f for f, _ in corr]
    assert fracs == sorted(fracs), "correspondence progress went BACKWARDS"
    assert fracs[-1] == pytest.approx(1.0)
    msgs = " | ".join(m for _, m in corr)
    assert "L: verifying frame" in msgs and "R: verifying frame" in msgs


# --- (b) a stop during the gate aborts promptly --------------------------------


def _fake_gate_inputs(n_frames: int, n: int = 40):
    ref_coords = np.stack([np.linspace(10, 90, n), np.full(n, 50.0)], axis=1)
    u_accum = np.zeros((n_frames, n, 2), dtype=np.float64)
    valid = np.ones((n_frames, n), dtype=bool)
    frames = [np.zeros((120, 120), dtype=np.float64) for _ in range(n_frames)]
    return frames, ref_coords, u_accum, valid


def test_stop_during_the_gate_aborts_after_at_most_one_more_frame(monkeypatch):
    n_frames = 40
    frames, ref_coords, u_accum, valid = _fake_gate_inputs(n_frames)
    para = make_dicpara(img_size=(120, 120), roi=(10, 110, 10, 110), winsize=16)
    calls = {"n": 0}

    def spy(*args, **kwargs):
        calls["n"] += 1
        return np.zeros(ref_coords.shape[0], dtype=np.float64)  # everything passes

    monkeypatch.setattr(primitives, "_znssd", spy)

    n_gated, stopped_at = _gate_by_znssd(
        frames,
        np.ones((120, 120)),
        ref_coords,
        u_accum,
        valid,
        para,
        1.0,
        stop=lambda: calls["n"] >= 3,  # the user cancels while frame 3 is verified
    )
    # Prompt: the gate did NOT grind through all 39 frames.
    assert calls["n"] == 3, f"gate ran {calls['n']} frames after the cancel"
    assert stopped_at == 4  # frames 1..3 verified and kept; 4.. never verified


def test_stop_during_the_gate_truncates_to_the_verified_prefix(monkeypatch):
    """Honesty: a frame that skipped verification is never shipped as tracked."""
    n_frames = 6
    frames, ref_coords, u_accum, valid = _fake_gate_inputs(n_frames)
    para = make_dicpara(img_size=(120, 120), roi=(10, 110, 10, 110), winsize=16)
    calls = {"n": 0}

    def spy(*args, **kwargs):
        calls["n"] += 1
        return np.zeros(ref_coords.shape[0], dtype=np.float64)

    monkeypatch.setattr(primitives, "_znssd", spy)
    _, stopped_at = _gate_by_znssd(
        frames,
        np.ones((120, 120)),
        ref_coords,
        u_accum,
        valid,
        para,
        1.0,
        stop=lambda: calls["n"] >= 2,
    )
    assert stopped_at == 3


def test_gate_without_stop_verifies_every_frame(monkeypatch):
    n_frames = 8
    frames, ref_coords, u_accum, valid = _fake_gate_inputs(n_frames)
    para = make_dicpara(img_size=(120, 120), roi=(10, 110, 10, 110), winsize=16)
    calls = {"n": 0}

    def spy(*args, **kwargs):
        calls["n"] += 1
        return np.zeros(ref_coords.shape[0], dtype=np.float64)

    monkeypatch.setattr(primitives, "_znssd", spy)
    n_gated, stopped_at = _gate_by_znssd(
        frames, np.ones((120, 120)), ref_coords, u_accum, valid, para, 1.0
    )
    assert calls["n"] == n_frames - 1
    assert stopped_at is None
    assert n_gated.shape == (n_frames,) and not n_gated.any()


def test_temporal_track_stop_in_the_gate_surfaces_as_a_partial_run(monkeypatch):
    """End to end: a cancel that first trips inside the gate returns a partial
    field (verified prefix kept, later frames NaN) rather than silently shipping
    unverified frames."""
    frames, mesh, para = _two_frame_scene(n_frames=4)
    real = primitives._znssd
    calls = {"n": 0}

    def spy(*args, **kwargs):
        calls["n"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(primitives, "_znssd", spy)
    # The engine finishes (its own stop polls run first and see False); the stop
    # only trips once the gate has verified two frames.
    tf = temporal_track(frames, mesh, para, gate_znssd=1.0, stop=lambda: calls["n"] >= 2)

    assert tf.stopped_early
    assert tf.stopped_at_frame == 3  # frames 0..2 verified, frame 3 dropped
    assert tf.valid[1].any() and tf.valid[2].any()
    assert not tf.valid[3].any()
    assert np.isnan(tf.u_accum[3]).all()
    assert tf.stop_reason
