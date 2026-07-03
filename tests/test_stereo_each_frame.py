"""StereoEachFrameStrategy (S2) — parity + per-frame-stereo semantics (Phase 2 item 2).

S2 keeps ONE temporal chain (left) and re-establishes the stereo correspondence
at every frame via scattered local IC-GN (no resampling), warm-started from the
previous disparity. It must recover the analytic 3D truth (parity gate), tag every
position ``STEREO_REFRESH``, and keep the reprojection error at match-noise level
on every frame (the QC signal S2 exists to provide).
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from al_dic_3d.matching import get_strategy
from al_dic_3d.matching.contracts import INVALID, STEREO_REFRESH, TRACKED
from al_dic_3d.runner import load_config, run_pipeline

cv2 = pytest.importorskip("cv2")

from tests import synth_parity  # noqa: E402  (after importorskip guard)


@pytest.fixture(scope="module")
def s2(tmp_path_factory):
    d = tmp_path_factory.mktemp("s2")
    scene = synth_parity.build_parity_scene(d, img=300, n_frames=5, seed=7)
    cfg = load_config(synth_parity.write_config(d, scene))
    result = run_pipeline(replace(cfg, strategy="stereo_each_frame"))
    gt = synth_parity.gt_tracks(scene, result.ref_coords)
    return result, gt


def test_s2_is_registered():
    cls = get_strategy("stereo_each_frame")
    assert cls.name == "stereo_each_frame"


def test_s2_passes_parity_gate(s2):
    result, gt = s2
    m = synth_parity.metrics(result, gt)
    failed = [r for r in synth_parity.gate_rows(m) if not r["pass"]]
    detail = "; ".join(f"{r['name']}={r['value']:.4g} !{r['op']} {r['tol']}" for r in failed)
    assert not failed, f"S2 parity-gate failures: {detail}"


def test_s2_marks_every_position_stereo_refresh(s2):
    result, _ = s2
    src = result.correspondence.source
    tracked = src != INVALID
    assert (src[tracked] == STEREO_REFRESH).all()
    assert not (src == TRACKED).any()  # S2 has no plain temporal-only positions


def test_s2_reprojection_is_flat_across_frames(s2):
    # Each frame satisfies the epipolar constraint independently, so reproj error
    # stays at match-noise level for every frame (no drift growth) -> a real QC signal.
    result, _ = s2
    rec = result.reconstruction
    per_frame_med = [
        np.nanmedian(rec.reproj_error[k])
        for k in range(rec.n_frames)
        if np.isfinite(rec.reproj_error[k]).any()
    ]
    assert max(per_frame_med) < 1e-3
