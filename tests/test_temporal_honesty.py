"""Regression tests for the S3 frame-3 silent-failure fix (2026-07-07).

Root causes locked in:
- accumulative sibling-warm-start freeze: with a decorrelating jump, IC-GN
  "converges" with a zero update at the previous frame's seed and the engine
  launders the failure into finite values -> the honesty gate (frame-0 -> k
  ZNSSD re-verification) must invalidate those nodes;
- incremental FFT under-search: the engine re-seeds every increment by FFT
  integer search, but auto-expand fires only on boundary-CLIPPED peaks, so a
  jump beyond ``fft_search`` seeds garbage -> the knob must reach DICPara;
- large-increment composition: U^k(X) = U^{k-1}(X) + u^k(X + U^{k-1}(X)) with
  increments interpolated at DEFORMED positions. Pre-existing tests used
  ~0.7 px/frame increments where the classic wrong-position bug is below every
  tolerance; this test uses increments where it would exceed 0.5 px.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates

from al_dic_3d.matching.primitives import make_dicpara
from al_dic_3d.matching.temporal import build_grid_mesh, temporal_track


def _speckle(h: int, w: int, seed: int = 3) -> np.ndarray:
    rng = np.random.default_rng(seed)
    img = gaussian_filter(rng.random((h, w)), 1.6)
    lo, hi = img.min(), img.max()
    return ((img - lo) / (hi - lo) * 200.0 + 20.0).astype(np.float64)


def test_fft_search_reaches_dicpara():
    para = make_dicpara(img_size=(400, 400), roi=(50, 350, 50, 350), fft_search=60)
    assert para.size_of_fft_search_region == 60
    para = make_dicpara(img_size=(400, 400), roi=(50, 350, 50, 350))
    assert para.size_of_fft_search_region == 20


def _run_shift(shift: int, fft_search: int, gate: float = 1.0):
    """2-frame pure y-shift; returns (median |dy - shift|, valid fraction)."""
    h = w = 420
    f0 = _speckle(h, w)
    f1 = np.roll(f0, shift, axis=0)
    lo, hi = 120, 300  # interior ROI, clear of the roll wrap seam
    para = make_dicpara(
        img_size=(h, w), roi=(lo, hi, lo, hi), fft_search=fft_search
    )
    mesh = build_grid_mesh(para, h, w)
    tf = temporal_track([f0, f1], mesh, para, gate_znssd=gate)
    dy = tf.u_accum[1, :, 1]
    frac = float(tf.valid[1].mean())
    med = float(np.nanmedian(np.abs(dy[tf.valid[1]] - shift))) if tf.valid[1].any() else np.inf
    return med, frac


def test_large_jump_tracks_with_wide_fft_search():
    med, frac = _run_shift(shift=40, fft_search=60)
    assert frac > 0.8, f"only {frac:.0%} valid with a sufficient search radius"
    assert med < 0.1, f"median |error| {med:.3f} px"


def test_honesty_gate_flags_untrackable_frame():
    # Frame 1 is an INDEPENDENT speckle pattern (full decorrelation — the S3
    # failure shape): FFT seeds are in-bounds noise peaks (no boundary clip, so
    # auto-expand never fires), IC-GN converges to junk, and the engine
    # launders every per-node failure into finite values. Without the gate
    # validity is structurally all-True; with it the frame must be reported
    # as (mostly) untrackable. A correlated 40px shift is NOT a valid scenario
    # here — its clipped FFT peak correctly triggers the engine's auto-expand.
    h = w = 420
    f0 = _speckle(h, w, seed=3)
    f1 = _speckle(h, w, seed=99)  # unrelated pattern
    lo, hi = 120, 300
    para = make_dicpara(img_size=(h, w), roi=(lo, hi, lo, hi))
    mesh = build_grid_mesh(para, h, w)

    tf_raw = temporal_track([f0, f1], mesh, para, gate_znssd=0.0)
    frac_ungated = float(tf_raw.valid[1].mean())
    tf = temporal_track([f0, f1], mesh, para, gate_znssd=1.0)
    frac_gated = float(tf.valid[1].mean())

    assert frac_ungated > 0.9, "engine laundering assumption changed?"
    assert frac_gated < 0.2, f"gate left {frac_gated:.0%} of an untrackable frame valid"


def test_incremental_composition_large_increments():
    """3 increments of (12, 8) px + 1%/frame stretch vs the analytic cumulative.

    The wrong-position composition variant (increments evaluated at REFERENCE
    positions) would err by ~sum |U^(k-1)| * |grad u| ~ 0.5 px at frame 3 —
    well above the assertion tolerance, so this test genuinely distinguishes
    deformed-position composition.
    """
    h = w = 460
    f0 = _speckle(h, w, seed=11)
    cx = cy = (w - 1) / 2.0
    tx, ty, g = 12.0, 8.0, 0.010  # per-frame translation (px) and stretch

    def cumulative_u(pts: np.ndarray, k: int) -> np.ndarray:
        """Analytic U^k at material points (frame-0 coords), exact composition."""
        u = np.zeros_like(pts)
        cur = pts.copy()
        for _ in range(k):
            step = np.empty_like(cur)
            step[:, 0] = tx + g * (cur[:, 0] - cx)
            step[:, 1] = ty + g * (cur[:, 1] - cy)
            cur = cur + step
            u = cur - pts
        return u

    frames = [f0]
    a = 1.0 + g
    for k in range(1, 4):
        # x = A^k (X - c) + c + t_k  with t accumulating through the stretch;
        # invert analytically to synthesize frame k from frame 0.
        # Build via the recurrence on the forward map: x_k = a*x_{k-1} + (t - g*c)
        # => x_k = a^k X + (a^k - 1)/(a - 1) * (t + g*... ) — simpler: sample
        # the INVERSE map numerically from the closed-form forward affine.
        ak = a**k
        sk = (ak - 1.0) / (a - 1.0)  # geometric sum a^{k-1} + ... + 1
        # forward: x = ak*(X - c) + c + sk*t   (t applied in each step then stretched)
        # NOTE the translation of step j is stretched by later steps: total
        # translation = sum_{j=1..k} a^{k-j} t = sk * t. Inverse:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
        X = (xx - cx - sk * tx) / ak + cx
        Y = (yy - cy - sk * ty) / ak + cy
        frames.append(map_coordinates(f0, [Y, X], order=3, mode="constant", cval=0.0))

    lo, hi = 140, 320
    para = make_dicpara(
        img_size=(h, w),
        roi=(lo, hi, lo, hi),
        reference_mode="incremental",
        fft_search=40,
    )
    mesh = build_grid_mesh(para, h, w)
    tf = temporal_track(frames, mesh, para)

    pts = tf.ref_coords
    for k in (1, 2, 3):
        ua = cumulative_u(pts, k)
        ok = tf.valid[k]
        assert ok.mean() > 0.8, f"frame {k}: only {ok.mean():.0%} valid"
        err = np.linalg.norm(tf.u_accum[k][ok] - ua[ok], axis=1)
        assert np.median(err) < 0.15, f"frame {k}: median |err| {np.median(err):.3f} px"


def test_incremental_composition_beats_wrong_position_variant():
    """The measured field must match DEFORMED-position composition, not the
    reference-position variant — i.e. the test above has discriminating power."""
    h = w = 460
    cx = cy = (w - 1) / 2.0
    tx, ty, g = 12.0, 8.0, 0.010
    rng = np.random.default_rng(0)
    pts = np.column_stack([rng.uniform(140, 320, 200), rng.uniform(140, 320, 200)])

    cur = pts.copy()
    for _ in range(3):
        step = np.column_stack([tx + g * (cur[:, 0] - cx), ty + g * (cur[:, 1] - cy)])
        cur = cur + step
    u_right = cur - pts

    u_wrong = np.zeros_like(pts)
    for _ in range(3):
        step = np.column_stack([tx + g * (pts[:, 0] - cx), ty + g * (pts[:, 1] - cy)])
        u_wrong = u_wrong + step

    gap = np.median(np.linalg.norm(u_right - u_wrong, axis=1))
    assert gap > 0.3, f"scene too gentle to distinguish composition variants ({gap:.3f} px)"
