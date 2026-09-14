"""A right-camera tracking failure must reach the output (fix batch V, blocker B3).

track_both resamples the right camera's temporal field onto the stereo points.
The resampler used to triangulate whatever right nodes survived the honesty gate
and to nearest-fill everything outside their hull with no distance limit, while
the final validity only looked at the LEFT camera — so a right-camera region the
gate had rejected was silently re-filled from distant nodes and shipped as
TRACKED (the 24 Mpx stress run: 97% of right nodes gated, 37% of output points
still "valid" with 10-20 mm 3D error).
"""

from __future__ import annotations

import cv2
import numpy as np
import pytest

pytest.importorskip("al_dic")

from al_dic_3d.matching.contracts import INVALID  # noqa: E402
from al_dic_3d.matching.temporal import resample_to_points  # noqa: E402
from al_dic_3d.runner import load_config, run_pipeline  # noqa: E402
from tests import synth_stereo  # noqa: E402

# --------------------------------------------------------------------------- #
# resampler caps
# --------------------------------------------------------------------------- #


def _grid(step: float = 10.0, n: int = 11) -> np.ndarray:
    g = np.arange(n, dtype=np.float64) * step
    xx, yy = np.meshgrid(g, g)
    return np.column_stack([xx.ravel(), yy.ravel()])


def _hole_values(ref: np.ndarray) -> np.ndarray:
    vals = np.column_stack([ref[:, 0] * 0.01, ref[:, 1] * 0.02])
    hole = (np.abs(ref[:, 0] - 50) <= 20) & (np.abs(ref[:, 1] - 50) <= 20)
    vals[hole] = np.nan
    return vals


def test_uncapped_resampling_bridges_a_gated_hole():
    """Documents the old behaviour the caps exist to prevent."""
    ref = _grid()
    out = resample_to_points(ref, _hole_values(ref), np.array([[50.0, 50.0]]))
    assert np.isfinite(out).all()


def test_edge_cap_leaves_a_gated_hole_invalid():
    ref = _grid()
    q = np.array([[50.0, 50.0], [45.0, 52.0], [5.0, 5.0], [92.0, 18.0]])
    out = resample_to_points(ref, _hole_values(ref), q, max_edge=15.0, max_fill_dist=10.0)
    assert np.isnan(out[:2]).all()  # inside the hole: no bridging
    assert np.isfinite(out[2:]).all()  # healthy neighbourhoods still interpolate


def test_nearest_fill_respects_the_distance_cap():
    ref = _grid()
    vals = np.column_stack([ref[:, 0] * 0.01, ref[:, 1] * 0.02])
    q = np.array([[105.0, 50.0], [140.0, 50.0]])  # 5 px and 40 px outside the hull
    out = resample_to_points(ref, vals, q, max_edge=15.0, max_fill_dist=10.0)
    assert np.isfinite(out[0]).all()
    assert np.isnan(out[1]).all()


# --------------------------------------------------------------------------- #
# end to end: corrupt a patch of the RIGHT camera after frame 0
# --------------------------------------------------------------------------- #


def test_right_camera_failure_invalidates_the_affected_points(tmp_path):
    from scipy.ndimage import gaussian_filter

    scene = synth_stereo.build_scene(tmp_path, n_frames=3)
    y0, y1, x0, x1 = 80, 180, 80, 180  # right-image patch that decorrelates
    # A DIFFERENT speckle pattern: textured (the engine still converges somewhere)
    # but uncorrelated with frame 0, so only the honesty gate can tell.
    rng = np.random.default_rng(99)
    f = gaussian_filter(rng.standard_normal((y1 - y0, x1 - x0)), sigma=2.2, mode="nearest")
    f = (f - f.min()) / (f.max() - f.min())
    patch = np.clip((20.0 + 215.0 * f) * 256.0, 0, 65535).astype(np.uint16)
    for k in (1, 2):
        p = tmp_path / f"R_{k:03d}.png"
        img = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
        img[y0:y1, x0:x1] = patch
        cv2.imwrite(str(p), img)

    cfg = load_config(synth_stereo.write_config(tmp_path, scene))
    result = run_pipeline(cfg)
    cs = result.correspondence
    xr0 = cs.xR[0]
    inside = (
        np.isfinite(xr0).all(axis=1)
        & (xr0[:, 0] > x0 + 20)
        & (xr0[:, 0] < x1 - 20)
        & (xr0[:, 1] > y0 + 20)
        & (xr0[:, 1] < y1 - 20)
    )
    assert inside.sum() >= 5, "test geometry: expected stereo points inside the patch"
    for k in (1, 2):
        # Before the fix these were interpolated from distant right nodes and
        # shipped as TRACKED with finite (wrong) 3D points.
        assert (cs.source[k][inside] == INVALID).all()
        assert np.isnan(result.reconstruction.points[k][inside]).all()

    # Nothing grossly wrong may be shipped as valid. The corrupted patch degrades
    # the right camera's global (ADMM) solution everywhere — the gate rejects
    # ~97% of its nodes — and the few survivors carry sub-pixel errors no
    # correlation check can see (a 0.5 px misregistration still scores ZNCC
    # ~0.97). Before the fix the same run shipped points 113 mm off.
    gt = synth_stereo.gt_world_points(scene, result.ref_coords)
    rec = result.reconstruction
    for k in (1, 2):
        ok = np.isfinite(rec.points[k]).all(axis=1) & np.isfinite(rec.points[0]).all(axis=1)
        if ok.any():
            err = np.linalg.norm(rec.displacement[k][ok] - (gt[k] - gt[0])[ok], axis=1)
            assert err.max() < 2.0, f"frame {k}: max 3D error {err.max():.3f} mm"
