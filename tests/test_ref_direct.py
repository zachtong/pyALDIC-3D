"""RefDirectStrategy (S3) — parity + reference-anchored (zero-drift) semantics.

S3 tracks the left camera temporally (accumulative) and obtains every right-camera
position by a DIRECT L1 -> R_k cross match at the reference nodes (chain-seeded).
On a small-deformation scene the hard M match succeeds everywhere; it must recover
the analytic 3D truth (parity gate) and, being reference-anchored, keep the
reprojection error flat across frames (no drift growth).
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from al_dic_3d.matching import get_strategy
from al_dic_3d.matching.contracts import INVALID
from al_dic_3d.runner import load_config, run_pipeline

cv2 = pytest.importorskip("cv2")

from tests import synth_parity  # noqa: E402  (after importorskip guard)


@pytest.fixture(scope="module")
def s3(tmp_path_factory):
    d = tmp_path_factory.mktemp("s3")
    scene = synth_parity.build_parity_scene(d, img=300, n_frames=5, seed=7)
    cfg = load_config(synth_parity.write_config(d, scene))
    result = run_pipeline(replace(cfg, strategy="ref_direct"))
    gt = synth_parity.gt_tracks(scene, result.ref_coords)
    return result, gt


def test_s3_is_registered():
    assert get_strategy("ref_direct").name == "ref_direct"


def test_s3_passes_parity_gate(s3):
    result, gt = s3
    m = synth_parity.metrics(result, gt)
    failed = [r for r in synth_parity.gate_rows(m) if not r["pass"]]
    detail = "; ".join(f"{r['name']}={r['value']:.4g} !{r['op']} {r['tol']}" for r in failed)
    assert not failed, f"S3 parity-gate failures: {detail}"


def test_s3_high_coverage_on_small_deformation(s3):
    # The hard L1 -> R_k match still succeeds everywhere when deformation is small.
    result, _ = s3
    tracked = result.correspondence.source != INVALID
    assert tracked.mean() > 0.97


def test_s3_reprojection_is_flat_across_frames(s3):
    # Reference-anchored: each x_R^k is an independent direct match -> no drift.
    result, _ = s3
    rec = result.reconstruction
    per_frame_med = [
        np.nanmedian(rec.reproj_error[k])
        for k in range(rec.n_frames)
        if np.isfinite(rec.reproj_error[k]).any()
    ]
    assert max(per_frame_med) < 1e-3
