"""Validate the non-planar Lagrangian-warp ground-truth generator (Phase 2 item 5).

Checks (a) the ray-vs-curved-surface back-projection and the forward projection
are consistent inverses (so the analytic ground truth is self-consistent) and
(b) the fully rendered non-planar scene drives the real pipeline to recover the
known 3D displacement — proving the generator is projectively consistent and the
tracker works on genuinely curved, distorted stereo imagery.
"""

from __future__ import annotations

import numpy as np
import pytest

from al_dic_3d.calibration import project_points
from al_dic_3d.matching.contracts import INVALID
from al_dic_3d.runner import load_config, run_pipeline

cv2 = pytest.importorskip("cv2")

from tests import synth_surface as ss  # noqa: E402  (after importorskip guard)


def test_backprojection_and_projection_are_inverses():
    intr_L, _, _, _, _ = ss._cameras(300)
    xs, ys = np.meshgrid(np.arange(60, 240, 20.0), np.arange(60, 240, 20.0))
    pts = np.column_stack([xs.ravel(), ys.ravel()])
    material = ss._back_project(pts, intr_L, np.eye(3), np.zeros(3))
    reproj = project_points(ss._X_ref(material), intr_L, np.eye(3), np.zeros(3))
    # pi_L(X_ref(R_L(p))) == p to well below a pixel on the curved surface.
    assert np.max(np.linalg.norm(reproj - pts, axis=1)) < 0.01


def test_surface_scene_recovers_known_3d_displacement(tmp_path):
    scene = ss.build_surface_scene(tmp_path, img=200, n_frames=3, deform=0.5, seed=7)
    cfg = load_config(ss.write_config(tmp_path, scene))
    result = run_pipeline(cfg)
    gt = ss.gt_tracks(scene, result.ref_coords)

    # Ground-truth self-consistency: the frame-0 left projection of each node's
    # material returns the node pixel (independent of the renderer/tracker).
    assert np.max(np.linalg.norm(gt["xL"][0] - result.ref_coords, axis=1)) < 0.02

    rec = result.reconstruction
    tracked = result.correspondence.source != INVALID
    disp_err = []
    for k in range(1, rec.n_frames):
        common = tracked[k] & tracked[0]
        d = np.linalg.norm(rec.displacement[k][common] - gt["displacement"][k][common], axis=1)
        disp_err.append(d[np.isfinite(d)])
    disp_err = np.concatenate(disp_err)

    assert tracked.mean() > 0.9
    # Curved surface + real distortion + Lagrangian warp -> still tens of microns.
    assert np.median(disp_err) < 0.12, f"3D disp median {np.median(disp_err) * 1000:.0f} um"
