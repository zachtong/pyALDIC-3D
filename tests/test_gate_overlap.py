"""The left honesty gate overlaps the right camera's track (fix batch V).

The default track-both path used to run L engine -> L gate -> R engine -> R gate
strictly in sequence. The left gate now runs on a worker thread beside the
right engine; results must not change, failures must still surface, and the
reported progress must stay monotonic.
"""

from __future__ import annotations

import threading
from dataclasses import replace

import numpy as np
import pytest

pytest.importorskip("al_dic")

import al_dic_3d.matching.temporal as tmod  # noqa: E402
from al_dic_3d.runner import load_config, run_pipeline  # noqa: E402
from tests import synth_stereo  # noqa: E402


@pytest.fixture(scope="module")
def cfg(tmp_path_factory):
    d = tmp_path_factory.mktemp("overlap")
    scene = synth_stereo.build_scene(d, n_frames=4)
    return load_config(synth_stereo.write_config(d, scene))


def test_left_gate_runs_on_its_own_thread_and_results_match_parallel(cfg, monkeypatch):
    threads: list[str] = []
    real = tmod._gate_by_znssd

    def spy(*a, **k):
        threads.append(threading.current_thread().name)
        return real(*a, **k)

    monkeypatch.setattr(tmod, "_gate_by_znssd", spy)
    events: list[tuple[float, str]] = []
    overlapped = run_pipeline(cfg, progress=lambda f, m: events.append((f, m)))
    assert len(threads) == 2
    assert threads[0].startswith("gate_L") and not threads[1].startswith("gate_L")

    fracs = [f for f, _ in events]
    assert fracs == sorted(fracs), "progress went backwards while the phases overlapped"
    msgs = " | ".join(m for _, m in events)
    assert "L: verifying frame" in msgs and "R: verifying frame" in msgs

    reference = run_pipeline(replace(cfg, parallel_cameras=True))
    a, b = overlapped.correspondence, reference.correspondence
    assert np.array_equal(a.xL, b.xL, equal_nan=True)
    assert np.array_equal(a.xR, b.xR, equal_nan=True)


def test_a_left_gate_failure_surfaces_and_stops_the_right_track(cfg, monkeypatch):
    real = tmod._gate_by_znssd
    right_stopped = {"early": None}
    real_track = tmod.temporal_track

    def failing(*a, **k):
        if threading.current_thread().name.startswith("gate_L"):
            raise RuntimeError("left gate exploded")
        return real(*a, **k)

    def watch(*a, **k):
        tf = real_track(*a, **k)
        right_stopped["early"] = tf.stopped_early
        return tf

    import al_dic_3d.matching.strategies.track_both as tb

    monkeypatch.setattr(tmod, "_gate_by_znssd", failing)
    monkeypatch.setattr(tb, "temporal_track", watch)
    with pytest.raises(RuntimeError, match="left gate exploded"):
        run_pipeline(cfg)
    # The right engine saw the abort at a frame head (or had already finished).
    assert right_stopped["early"] is not None
