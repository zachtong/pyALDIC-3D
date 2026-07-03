"""QualityGate enforcement + 3D outlier removal (Phase 2 item 4).

Unit tests for the pure filters (ZNSSD gate on the correspondence; reprojection
gate + universal-outlier test on the reconstruction) plus a runner integration
check that enabling the gates keeps the clean synthetic dataset intact.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from al_dic_3d.matching import apply_znssd_gate
from al_dic_3d.matching.contracts import INVALID, TRACKED, CorrespondenceSet
from al_dic_3d.reconstruct import (
    Reconstruction3D,
    apply_reproj_gate,
    remove_3d_outliers,
)


def _valid_set(quality: np.ndarray) -> CorrespondenceSet:
    nf, n = quality.shape
    xL = np.zeros((nf, n, 2), dtype=np.float64)
    xR = np.ones((nf, n, 2), dtype=np.float64)
    source = np.full((nf, n), TRACKED, dtype=np.uint8)
    return CorrespondenceSet("s", xL, xR, quality.astype(np.float64), source)


def test_znssd_gate_demotes_only_over_threshold():
    q = np.array([[0.1, 0.2, 0.9, 0.3], [0.1, 0.6, 0.1, 0.1]])
    cs = _valid_set(q)
    out = apply_znssd_gate(cs, 0.5)
    # (0,2)=0.9 and (1,1)=0.6 exceed 0.5 -> INVALID/NaN; the rest survive.
    assert out.source[0, 2] == INVALID and np.isnan(out.xL[0, 2]).all()
    assert out.source[1, 1] == INVALID and np.isnan(out.xR[1, 1]).all()
    assert out.source[0, 0] == TRACKED and out.source[1, 3] == TRACKED
    assert int((out.source == INVALID).sum()) == 2


def test_znssd_gate_noop_when_all_good_returns_same_object():
    cs = _valid_set(np.full((2, 3), 0.1))
    assert apply_znssd_gate(cs, 0.5) is cs


def _recon(points: np.ndarray, reproj: np.ndarray) -> Reconstruction3D:
    source = np.full(points.shape[:2], TRACKED, dtype=np.uint8)
    return Reconstruction3D(points, points - points[0][None], reproj, source)


def test_reproj_gate_demotes_and_recomputes_displacement():
    n = 5
    P = np.tile(np.column_stack([np.arange(n), np.zeros(n), np.full(n, 100.0)]), (2, 1, 1)).astype(
        float
    )
    P[1, :, 0] += 0.5  # a uniform shift on frame 1
    reproj = np.zeros((2, n))
    reproj[1, 2] = 3e-3  # one bad point
    rec = _recon(P.copy(), reproj)
    out = apply_reproj_gate(rec, 1e-3)
    assert out.source[1, 2] == INVALID
    assert np.isnan(out.points[1, 2]).all() and np.isnan(out.displacement[1, 2]).all()
    assert np.isfinite(out.displacement[1, 0]).all()  # good points keep D


def test_remove_3d_outliers_flags_spike_keeps_inliers():
    xs, ys = np.meshgrid(np.arange(6), np.arange(6))
    ref = np.column_stack([xs.ravel(), ys.ravel()]).astype(np.float64) * 10.0
    n = ref.shape[0]
    P1 = np.column_stack([ref, np.full(n, 100.0)])
    smooth = np.column_stack([0.01 * ref[:, 0], np.zeros(n), np.full(n, 0.5)])  # gentle field
    points = np.stack([P1, P1 + smooth])
    points[1, 20] += np.array([5.0, 5.0, 5.0])  # inject a 5 mm spike at an interior node
    rec = _recon(points, np.zeros((2, n)))

    cleaned = remove_3d_outliers(rec, ref, threshold=3.0, eps=0.02)
    assert cleaned.source[1, 20] == INVALID and np.isnan(cleaned.points[1, 20]).all()
    # frame 0 (zero displacement) and the spike's neighbours are untouched.
    assert (cleaned.source[0] == TRACKED).all()
    assert cleaned.source[1, 19] == TRACKED and cleaned.source[1, 21] == TRACKED
    assert int((cleaned.source[1] == INVALID).sum()) == 1


def test_quality_gate_preserves_clean_dataset(tmp_path):
    cv2 = pytest.importorskip("cv2")  # noqa: F841
    from al_dic_3d.runner import load_config, run_pipeline
    from tests import synth_parity

    scene = synth_parity.build_parity_scene(tmp_path, img=300, n_frames=4, seed=7)
    cfg = load_config(synth_parity.write_config(tmp_path, scene))
    gated = run_pipeline(replace(cfg, quality_gate=True))

    assert gated.meta["quality_gate"] is True
    gt = synth_parity.gt_tracks(scene, gated.ref_coords)
    m = synth_parity.metrics(gated, gt)
    # The clean dataset trips no gate: coverage stays high and the parity gate holds.
    assert m["coverage_min"] > 0.95
    assert synth_parity.gate_passed(m)
