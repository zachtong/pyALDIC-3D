"""The honesty gate checks each tracked step against the frame it was tracked from.

An incremental track composes small steps; each step carries a tiny error that
adds up (~0.01 px per step on a notched specimen pulled to failure, ~1.7 px
after 135 steps). Checking every point against its FRAME-1 subset then dropped
the drifted but genuinely tracked points (21 % kept at the end, while the
engine tracked 99 %). The gate now checks each step: frame k against the
reference frame it was correlated from, at the position the track had there.
A garbage step still fails, and since every later step composes it, the track
stays invalid from there on. Accumulative runs (every step from frame 1) are
checked exactly as before.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.ndimage import gaussian_filter

from al_dic_3d.matching.gate import gate_by_znssd, gate_stepwise

H, W = 160, 240
N = 9  # frames
STEP_PX = 2.0  # true rigid translation per frame (+x)
DRIFT_PX = 0.5  # tracking error added at every step (4 px by the last frame)
WIN = 24


def _frames() -> list[np.ndarray]:
    pad = int(STEP_PX * N) + 4
    rng = np.random.default_rng(5)
    base = gaussian_filter(rng.standard_normal((H, W + pad)), sigma=2.0)
    base = 20.0 + 215.0 * (base - base.min()) / (base.max() - base.min())
    # frame k shows the material moved STEP_PX * k to the right
    return [
        np.ascontiguousarray(base[:, pad - int(STEP_PX * k) : pad - int(STEP_PX * k) + W])
        for k in range(N)
    ]


def _nodes() -> np.ndarray:
    xs, ys = np.meshgrid(np.arange(40.0, 160.0, 12.0), np.arange(30.0, 131.0, 12.0))
    return np.column_stack([xs.ravel(), ys.ravel()])


def _drifting_track(n: int) -> np.ndarray:
    u = np.zeros((N, n, 2))
    for k in range(N):
        u[k, :, 0] = (STEP_PX + DRIFT_PX) * k  # true motion + accumulated drift
    return u


def _run(gate, parents=None, u=None, valid=None):
    frames, ref = _frames(), _nodes()
    u = _drifting_track(len(ref)) if u is None else u
    valid = np.ones((N, len(ref)), dtype=bool) if valid is None else valid
    masks = [np.ones((H, W))] * N
    z = np.full(valid.shape, np.nan)
    if gate is gate_stepwise:
        n_gated, stopped = gate_stepwise(
            frames, masks, ref, u, valid, WIN, 1.0, parents, znssd_out=z
        )
    else:
        n_gated, stopped = gate_by_znssd(frames, masks[0], ref, u, valid, WIN, 1.0, znssd_out=z)
    assert stopped is None
    return valid, n_gated, z


INCREMENTAL = [0, *range(N - 1)]  # every frame tracked from the previous one


def test_a_drifting_but_tracked_chain_is_kept():
    valid, n_gated, _ = _run(gate_stepwise, INCREMENTAL)
    assert valid[-1].mean() > 0.95
    assert int(n_gated.sum()) == int((~valid[1:]).sum())
    # The check against frame 1 drops it once the drift reaches a few px.
    old, _, _ = _run(gate_by_znssd)
    assert old[-1].mean() < 0.3


def test_a_garbage_step_breaks_the_track_for_good():
    ref = _nodes()
    u = _drifting_track(len(ref))
    bad = np.zeros(len(ref), dtype=bool)
    bad[::3] = True
    u[4:, bad, 0] += 7.0  # step 3 -> 4 jumps 7 px: a false lock composed onwards
    valid, _, _ = _run(gate_stepwise, INCREMENTAL, u=u)
    assert valid[3, bad].mean() > 0.95  # fine before the jump
    assert not valid[4:, bad].any()  # gone from the jump on, though steps 5.. are fine
    assert valid[-1, ~bad].mean() > 0.95


def test_with_every_n_frames_only_a_failed_reference_breaks_its_children():
    parents = [0, 0, 0, 0, 3, 3, 3, 6, 6]  # references 0, 3, 6
    ref = _nodes()
    u = _drifting_track(len(ref))
    in_frame_2, at_ref_3 = np.zeros(len(ref), bool), np.zeros(len(ref), bool)
    in_frame_2[::4] = True
    at_ref_3[1::4] = True
    u[2, in_frame_2, 0] += 7.0  # a non-reference frame only
    u[3:, at_ref_3, 0] += 7.0  # reference frame 3 (and what composes it)
    valid, _, _ = _run(gate_stepwise, parents, u=u)
    assert not valid[2, in_frame_2].any() and valid[3:, in_frame_2].mean() > 0.95
    assert not valid[3:, at_ref_3].any()


def test_an_accumulative_run_is_checked_exactly_as_before():
    ref = _nodes()
    u = _drifting_track(len(ref))
    u[:, :, 0] -= DRIFT_PX * np.arange(N)[:, None]  # accumulative tracks do not drift
    u[5, ::5, 0] += 6.0  # one frame wrong for some nodes
    new = _run(gate_stepwise, [0] * N, u=u.copy())
    old = _run(gate_by_znssd, u=u.copy())
    np.testing.assert_array_equal(new[0], old[0])
    np.testing.assert_array_equal(new[1], old[1])
    np.testing.assert_array_equal(new[2], old[2])


def test_parents_must_point_backwards():
    with pytest.raises(ValueError):
        _run(gate_stepwise, [0, 2, 1, 2, 3, 4, 5, 6, 7])
