"""Right-camera resampling keeps the displacement gradient past the last node.

track_both tracks the right camera on its own grid and carries that motion onto
the stereo points with ``resample_to_points``. A stereo point near a free edge
can lie past the right grid's last valid node (up to one node step). The old
fill copied the NEAREST node's motion there, which drops the displacement
gradient: at a strain eps the right position is off by eps x distance (1-4 px
at a notch root under large strain). The left/right mismatch becomes a depth
error and Green-Lagrange eyy gains 0.5 * (dW/dY)^2 >= 0 at every free edge.

``fill_method="affine"`` fills those points with a Gaussian-weighted local
affine least-squares fit of the nearby finite nodes instead. It is exact on a
linear field, keeps the same distance cap, and falls back to the nearest node
where the fit is ill-posed.
"""

from __future__ import annotations

import numpy as np
import pytest

from al_dic_3d.matching.resample import _RESAMPLE_CACHE, resample_to_points

STEP = 8.0


def _grid(n: int = 12, step: float = STEP) -> np.ndarray:
    g = np.arange(n, dtype=np.float64) * step
    xx, yy = np.meshgrid(g, g)
    return np.column_stack([xx.ravel(), yy.ravel()])


def _linear(p: np.ndarray) -> np.ndarray:
    """A strongly strained affine field (30 % / 50 % gradients, like a notch root)."""
    return np.column_stack(
        [1.5 + 0.3 * p[:, 0] - 0.1 * p[:, 1], -2.0 + 0.05 * p[:, 0] + 0.5 * p[:, 1]]
    )


def _outside(ref: np.ndarray, gap: float) -> np.ndarray:
    """Queries `gap` px past the right / bottom edge of the node grid (not a corner:
    a corner has only 4 nodes within reach and takes the nearest node)."""
    right = ref[:, 0].max() + gap
    bottom = ref[:, 1].max() + gap
    return np.array([[right, 20.0], [right, 50.0], [30.0, bottom], [60.0, bottom]])


def test_affine_fill_is_exact_on_a_linear_field_past_the_last_node():
    ref = _grid()
    q = _outside(ref, 6.0)
    out = resample_to_points(
        ref, _linear(ref), q, max_edge=1.5 * STEP, max_fill_dist=STEP, fill_method="affine"
    )
    np.testing.assert_allclose(out, _linear(q), atol=1e-9)


def test_nearest_fill_drops_the_gradient_affine_fill_does_not():
    """Documents the defect: nearest is off by gradient x distance, affine is not."""
    ref = _grid()
    q = _outside(ref, 6.0)
    near = resample_to_points(ref, _linear(ref), q, max_edge=1.5 * STEP, max_fill_dist=STEP)
    aff = resample_to_points(
        ref, _linear(ref), q, max_edge=1.5 * STEP, max_fill_dist=STEP, fill_method="affine"
    )
    assert np.abs(near - _linear(q)).max() > 1.0  # 0.5 x 6 px = 3 px for v
    assert np.abs(aff - _linear(q)).max() < 1e-9


def test_affine_fill_keeps_the_distance_cap():
    ref = _grid()
    q = _outside(ref, 40.0)
    out = resample_to_points(
        ref, _linear(ref), q, max_edge=1.5 * STEP, max_fill_dist=STEP, fill_method="affine"
    )
    assert np.isnan(out).all()


def test_affine_fill_does_not_bridge_a_gated_hole():
    ref = _grid(step=10.0, n=11)
    vals = _linear(ref)
    hole = (np.abs(ref[:, 0] - 50) <= 20) & (np.abs(ref[:, 1] - 50) <= 20)
    vals[hole] = np.nan
    q = np.array([[50.0, 50.0], [45.0, 52.0], [5.0, 5.0], [92.0, 18.0]])
    out = resample_to_points(ref, vals, q, max_edge=15.0, max_fill_dist=10.0, fill_method="affine")
    assert np.isnan(out[:2]).all()  # inside the hole: no bridging
    np.testing.assert_allclose(out[2:], _linear(q[2:]), atol=1e-9)


def test_affine_fill_is_exact_inside_a_rejected_long_triangle():
    """A query in a long (rejected) triangle next to a gap is filled from nearby nodes."""
    ref = _grid(step=10.0, n=11)
    vals = _linear(ref)
    gap = (ref[:, 0] >= 40) & (ref[:, 0] <= 60) & (ref[:, 1] >= 40) & (ref[:, 1] <= 60)
    vals[gap] = np.nan
    q = np.array([[33.0, 50.0]])  # 3 px past the last valid column, inside a 30 px wide triangle
    out = resample_to_points(ref, vals, q, max_edge=15.0, max_fill_dist=10.0, fill_method="affine")
    np.testing.assert_allclose(out, _linear(q), atol=1e-9)


def test_affine_fill_falls_back_to_nearest_with_too_few_nodes():
    ref = np.array([[0.0, 0.0], [8.0, 0.0], [0.0, 8.0], [8.0, 8.0]])
    vals = np.array([[3.0, 7.0], [3.0, 7.0], [3.0, 7.0], [4.0, 9.0]])
    q = np.array([[13.0, 8.0]])
    out = resample_to_points(ref, vals, q, max_fill_dist=STEP, fill_method="affine")
    np.testing.assert_allclose(out, [[4.0, 9.0]])  # nearest node, not an extrapolation


def test_affine_fill_falls_back_to_nearest_on_collinear_nodes():
    x = np.arange(20, dtype=np.float64) * 4.0
    ref = np.column_stack([x, np.zeros_like(x)])  # one row: no y information
    vals = _linear(ref)
    q = np.array([[29.0, 5.0]])  # >= 6 neighbours in reach, but all collinear
    out = resample_to_points(ref, vals, q, max_fill_dist=STEP, fill_method="affine")
    near = vals[np.argmin(np.linalg.norm(ref - q, axis=1))]
    np.testing.assert_allclose(out[0], near)


def test_affine_fill_leaves_interior_values_and_nan_queries_alone():
    ref = _grid()
    vals = _linear(ref)
    rng = np.random.default_rng(3)
    inside = rng.uniform(10.0, 80.0, size=(30, 2))
    q = np.vstack([inside, [[np.nan, 1.0]]])
    lin = resample_to_points(ref, vals, q, fill_method="nearest")
    aff = resample_to_points(ref, vals, q, fill_method="affine")
    np.testing.assert_array_equal(aff[:-1], lin[:-1])  # linear pass untouched
    assert np.isnan(aff[-1]).all()


def test_affine_fill_reuses_the_cached_tree():
    ref = _grid()
    q = _outside(ref, 4.0)
    _RESAMPLE_CACHE.clear()
    rng = np.random.default_rng(5)
    for _ in range(4):
        vals = _linear(ref) + rng.normal(0.0, 0.01, size=ref.shape)
        cached = resample_to_points(ref, vals, q, max_fill_dist=STEP, fill_method="affine")
        fresh = resample_to_points(
            ref, vals, q, max_fill_dist=STEP, fill_method="affine", reuse_geometry=False
        )
        np.testing.assert_array_equal(cached, fresh)
    assert _RESAMPLE_CACHE.kdtree_builds == 1


def test_fill_method_is_validated():
    ref = _grid()
    with pytest.raises(ValueError, match="fill_method"):
        resample_to_points(ref, _linear(ref), ref[:3], fill_method="cubic")


def test_track_both_fills_the_right_motion_affinely(monkeypatch, tmp_path):
    """track_both asks for the affine fill on the motion and keeps nearest for ZNSSD."""
    pytest.importorskip("al_dic")
    from al_dic_3d.matching.strategies import track_both as tb
    from al_dic_3d.runner import load_config, run_pipeline
    from tests import synth_stereo

    seen: list[tuple[int, str]] = []
    original = tb.resample_to_points

    def spy(ref, values, query, **kwargs):
        seen.append((np.asarray(values).ndim, kwargs.get("fill_method", "nearest")))
        return original(ref, values, query, **kwargs)

    monkeypatch.setattr(tb, "resample_to_points", spy)
    scene = synth_stereo.build_scene(tmp_path, n_frames=2)
    run_pipeline(load_config(synth_stereo.write_config(tmp_path, scene)))
    assert seen, "track_both did not resample the right camera"
    methods = {m for _, m in seen}
    assert "affine" in methods  # the motion
    assert methods <= {"affine", "nearest"}
