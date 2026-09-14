"""A cancelled run keeps every frame it tracked (fix batch V).

The honesty gate polls the stop after each verified frame. When the stop had
already ended the ENGINE, the gate saw it after its first frame and dropped all
later tracked frames, so "partial results kept" meant one frame at most.
"""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("al_dic")

from al_dic_3d.matching import primitives  # noqa: E402
from al_dic_3d.matching.primitives import make_local_dicpara  # noqa: E402
from al_dic_3d.matching.temporal import build_grid_mesh, temporal_track  # noqa: E402
from tests.test_temporal_track import _affine_k, _speckle, _warp  # noqa: E402


def _scene(n_frames: int = 5):
    h = w = 220
    f0 = _speckle(h, w)
    frames = [f0] + [_warp(f0, _affine_k(k)) for k in range(1, n_frames)]
    para = make_local_dicpara(img_size=(h, w), roi=(40, w - 40, 40, h - 40), winsize=32)
    return frames, build_grid_mesh(para, h, w), para


def _stop_after_engine_heads(n_heads: int):
    polls = {"n": 0}

    def stop() -> bool:
        polls["n"] += 1
        return polls["n"] > n_heads

    return stop


def test_every_frame_the_engine_finished_is_verified_and_kept(monkeypatch):
    frames, mesh, para = _scene(5)
    calls = {"n": 0}
    real = primitives._znssd

    def spy(*a, **k):
        calls["n"] += 1
        return real(*a, **k)

    monkeypatch.setattr(primitives, "_znssd", spy)
    # Engine heads 1..3 pass, head 4 trips: frames 1..3 tracked, frame 4 not.
    tf = temporal_track(frames, mesh, para, stop=_stop_after_engine_heads(3), gate_znssd=1.0)

    assert tf.stopped_early
    assert tf.stopped_at_frame == 4  # frames 0..3 kept (used to be 2)
    assert all(tf.valid[k].mean() > 0.9 for k in (1, 2, 3))
    assert not tf.valid[4].any()
    assert calls["n"] >= 3  # all three tracked frames went through the gate
    assert np.isfinite(tf.znssd[1:4]).any(axis=1).all()


def test_a_track_the_caller_discards_is_not_verified(monkeypatch):
    frames, mesh, para = _scene(4)
    calls = {"n": 0}
    real = primitives._znssd

    def spy(*a, **k):
        calls["n"] += 1
        return real(*a, **k)

    monkeypatch.setattr(primitives, "_znssd", spy)
    tf = temporal_track(
        frames, mesh, para, stop=_stop_after_engine_heads(2), gate_znssd=1.0, verify_partial=False
    )
    assert tf.stopped_early and tf.stopped_at_frame == 1
    assert calls["n"] == 0
    assert not tf.valid[1:].any() and np.isnan(tf.u_accum[1:]).all()


def test_a_stop_during_verification_of_a_complete_track_still_cuts_it_short(monkeypatch):
    frames, mesh, para = _scene(4)
    calls = {"n": 0}
    real = primitives._znssd

    def spy(*a, **k):
        calls["n"] += 1
        return real(*a, **k)

    monkeypatch.setattr(primitives, "_znssd", spy)
    tf = temporal_track(frames, mesh, para, gate_znssd=1.0, stop=lambda: calls["n"] >= 1)
    assert tf.stopped_early
    assert tf.stopped_at_frame == 2  # frame 1 verified, frames 2..3 dropped unverified
    assert tf.valid[1].any() and not tf.valid[2:].any()
