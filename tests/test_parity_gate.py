"""Phase-1 parity GATE against a synthetic dataset with analytic ground truth.

Stands in for the (deferred) MATLAB-baseline parity until a real dataset is
available. A distorted, tilted-plane stereo scene under a known affine
deformation is rendered to disk, driven through the real ``run_pipeline`` (the
same path as ``al-dic-3d run``), and every recovered quantity — 2D correspondence,
3D points, 3D displacement, reprojection error — is checked against analytic
ground truth. Because the images are rendered WITH lens distortion, this
exercises the full undistortion + triangulation chain, not just the tracker.
"""

from __future__ import annotations

import numpy as np
import pytest

from al_dic_3d.runner import load_config, run_pipeline

cv2 = pytest.importorskip("cv2")

from tests import synth_parity  # noqa: E402  (after importorskip guard)


@pytest.fixture(scope="module")
def parity(tmp_path_factory):
    d = tmp_path_factory.mktemp("parity")
    scene = synth_parity.build_parity_scene(d, img=300, n_frames=4, seed=7)
    cfg = load_config(synth_parity.write_config(d, scene))
    result = run_pipeline(cfg)
    gt = synth_parity.gt_tracks(scene, result.ref_coords)
    return scene, result, gt


def test_reference_render_is_exact():
    # The left camera at frame 0 must reproduce the reference speckle exactly
    # (identity remap) — proving the renderer/GT are self-consistent and the
    # ground truth is independent of the tracker under test.
    l0 = synth_parity._speckle(240, seed=3)
    intr_L, _, _, _, _ = synth_parity.cameras(240)
    rendered = synth_parity._render(l0, intr_L, np.eye(3), np.zeros(3), intr_L, 0)
    assert np.abs(rendered - l0).max() < 1e-3


def test_parity_gate(parity):
    _, result, gt = parity
    m = synth_parity.metrics(result, gt)
    rows = synth_parity.gate_rows(m)
    failed = [r for r in rows if not r["pass"]]
    detail = "; ".join(f"{r['name']}={r['value']:.4g} !{r['op']} {r['tol']}" for r in failed)
    assert not failed, f"parity-gate failures: {detail}"


def test_reprojection_is_near_zero(parity):
    # Undistort + DLT triangulation are mutually consistent to ~1e-5 px on the
    # exact synthetic correspondence (a sanity floor independent of tracking).
    _, result, _ = parity
    assert np.nanmedian(result.reconstruction.reproj_error) < 1e-4
