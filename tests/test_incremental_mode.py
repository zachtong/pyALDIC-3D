"""Incremental-mode track_both: parity + acc-vs-inc self-consistency (Phase 2 item 1).

The 2D engine composes per-frame increments into a cumulative frame-1 field
(``_compute_cumulative_displacements_tree``, increments evaluated at deformed
positions per 01 §D.3), so ``temporal_track`` reads ``U_accum`` unchanged in both
modes. These tests confirm (a) incremental mode still recovers the analytic 3D
truth (passes the parity gate) and (b) accumulative and incremental agree well
below the tracking noise floor on a small-deformation dataset.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from al_dic_3d.matching.contracts import INVALID
from al_dic_3d.runner import load_config, run_pipeline

cv2 = pytest.importorskip("cv2")

from tests import synth_parity  # noqa: E402  (after importorskip guard)


@pytest.fixture(scope="module")
def acc_inc(tmp_path_factory):
    d = tmp_path_factory.mktemp("incmode")
    scene = synth_parity.build_parity_scene(d, img=300, n_frames=5, seed=7)
    cfg = load_config(synth_parity.write_config(d, scene))
    acc = run_pipeline(replace(cfg, reference_mode="accumulative"))
    inc = run_pipeline(replace(cfg, reference_mode="incremental"))
    gt = synth_parity.gt_tracks(scene, acc.ref_coords)
    return acc, inc, gt


def test_incremental_passes_parity_gate(acc_inc):
    _, inc, gt = acc_inc
    m = synth_parity.metrics(inc, gt)
    failed = [r for r in synth_parity.gate_rows(m) if not r["pass"]]
    detail = "; ".join(f"{r['name']}={r['value']:.4g} !{r['op']} {r['tol']}" for r in failed)
    assert not failed, f"incremental parity-gate failures: {detail}"


def test_acc_and_inc_use_the_same_reference_mesh(acc_inc):
    acc, inc, _ = acc_inc
    assert np.array_equal(acc.ref_coords, inc.ref_coords)


def test_acc_inc_self_consistent_below_noise_floor(acc_inc):
    acc, inc, gt = acc_inc
    ta = acc.correspondence.source != INVALID
    ti = inc.correspondence.source != INVALID
    diffs = []
    for k in range(acc.reconstruction.n_frames):
        common = ta[k] & ti[k] & ta[0] & ti[0]
        d = np.linalg.norm(
            acc.reconstruction.displacement[k][common] - inc.reconstruction.displacement[k][common],
            axis=1,
        )
        diffs.append(d[np.isfinite(d)])
    diffs = np.concatenate(diffs)

    # The noise floor is the accumulative tracking error vs analytic truth.
    noise_floor = np.median(synth_parity.metrics(acc, gt)["disp"])
    acc_inc_diff = np.median(diffs)
    assert acc_inc_diff < noise_floor, (
        f"acc-inc median diff {acc_inc_diff * 1000:.1f} um is not below the "
        f"noise floor {noise_floor * 1000:.1f} um"
    )
    # Absolute guard: on this small-deformation scene they agree to ~10 um.
    assert acc_inc_diff * 1000 < 20.0
