"""Batch S — multi-seed F-aware propagation initial-guess system (Qt-free).

The 2D engine's ``init_guess_mode='seed_propagation'`` path is SKIPPED under an
external mesh (how the 3D layer always calls ``run_aldic``), so seed propagation
for 3D is orchestrated OURSELVES: build a full per-node ``U0`` displacement field
from sparse user-placed seeds by driving the engine's pure ``propagate_from_seeds``
(F-aware BFS, predictor ``u_j = u_i + F_i·(x_j − x_i)``) and marshalling the result
into the ``U0`` array ``run_aldic`` consumes.

Covered here:
* F-aware prediction is EXACT on a synthetic sheared-affine field (validates the
  whole orchestration incl. the engine predictor's F layout [dudx,dvdx,dudy,dvdy]).
* single-seed NCC bootstrap recovers a known uniform shift at the seed node.
* auto-place rescue fills a region the user left unseeded (existing seed kept).
* per-connected-region readiness readout ("N/M regions ready").
* END-TO-END: a large-motion, two-region scene where a single uniform seed
  DECORRELATES the far region but one-seed-per-region propagation TRACKS both —
  the test that earns the feature its place.
"""

from __future__ import annotations

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from al_dic_3d.matching.primitives import make_dicpara  # noqa: E402
from al_dic_3d.matching.seed import uniform_u0  # noqa: E402
from al_dic_3d.matching.seed_propagation import (  # noqa: E402
    SeedU0Result,
    build_seed_u0,
    seed_region_readiness,
)
from al_dic_3d.matching.temporal import build_grid_mesh, temporal_track  # noqa: E402

# --- synthetic scene helpers --------------------------------------------------


def _speckle(h: int, w: int, seed: int = 4, sigma: float = 2.1) -> np.ndarray:
    from scipy.ndimage import gaussian_filter

    rng = np.random.default_rng(seed)
    f = gaussian_filter(rng.standard_normal((h, w)), sigma=sigma, mode="nearest")
    f -= f.min()
    f /= f.max()
    return (20.0 + 215.0 * f).astype(np.float64)


def _affine_warp(f: np.ndarray, G: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Deformed image with reference displacement field ``u(X) = G·X + t``.

    Enforces the DIC convention ``g(X + u(X)) = f(X)`` exactly: with ``A = I + G``
    the inverse map sends an output pixel ``y`` back to source ``A⁻¹(y − t)``.
    """
    h, w = f.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    ainv = np.linalg.inv(np.eye(2) + G)
    sx = ainv[0, 0] * (xx - t[0]) + ainv[0, 1] * (yy - t[1])
    sy = ainv[1, 0] * (xx - t[0]) + ainv[1, 1] * (yy - t[1])
    return cv2.remap(
        f.astype(np.float32),
        sx.astype(np.float32),
        sy.astype(np.float32),
        cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REFLECT,
    ).astype(np.float64)


def _shift(f: np.ndarray, dx: float, dy: float) -> np.ndarray:
    """Uniform translation by (dx, dy) px (g(X + d) = f(X))."""
    return _affine_warp(f, np.zeros((2, 2)), np.array([dx, dy], dtype=np.float64))


def _two_region_mask(h: int, w: int) -> tuple[np.ndarray, tuple, tuple, tuple, tuple]:
    """Mask with two wide, disconnected rectangular blobs + their bbox/centers."""
    mask = np.zeros((h, w), dtype=np.float64)
    a = (25, 30, int(w * 0.42), h - 30)  # xlo, ylo, xhi, yhi (left blob)
    b = (int(w * 0.58), 30, w - 25, h - 30)  # right blob
    mask[a[1] : a[3], a[0] : a[2]] = 1.0
    mask[b[1] : b[3], b[0] : b[2]] = 1.0
    ca = ((a[0] + a[2]) / 2.0, (a[1] + a[3]) / 2.0)
    cb = ((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0)
    return mask, a, b, ca, cb


def _interior_nodes(coords: np.ndarray, box: tuple, margin: int) -> np.ndarray:
    """Nodes strictly inside ``box`` by ``margin`` px (subset fully on the blob)."""
    return (
        (coords[:, 0] >= box[0] + margin)
        & (coords[:, 0] < box[2] - margin)
        & (coords[:, 1] >= box[1] + margin)
        & (coords[:, 1] < box[3] - margin)
    )


def _para(h: int, w: int, roi, mask=None, *, global_step: bool = False):
    return make_dicpara(
        img_size=(h, w),
        roi=roi,
        winsize=32,
        winstepsize=16,
        winsize_min=8,
        img_ref_mask=mask,
        use_global_step=global_step,
        fft_search=20,
        tol=1e-2,
    )


# --- 1. F-aware predictor exactness on a sheared-affine field -----------------


def test_seed_u0_reproduces_sheared_affine_field():
    h = w = 200
    f = _speckle(h, w, seed=11)
    # Distinct gradients + real shear so a transposed-F predictor bug would show.
    G = np.array([[0.012, 0.004], [0.003, -0.009]], dtype=np.float64)
    t = np.array([2.0, 1.5], dtype=np.float64)
    g = _affine_warp(f, G, t)

    roi = (40, w - 40, 40, h - 40)
    mask = np.ones((h, w), dtype=np.float64)
    para = _para(h, w, roi, mask)
    mesh = build_grid_mesh(para, h, w)
    coords = np.asarray(mesh.coordinates_fem, dtype=np.float64)

    res = build_seed_u0(f, g, mesh, mask, [(w / 2.0, h / 2.0)], para, search_radius=20)
    assert isinstance(res, SeedU0Result)
    assert res.n_solved > 0.9 * res.n_nodes  # a smooth field propagates everywhere

    u0 = res.u0_2d
    solved = np.isfinite(u0).all(axis=1)
    u_true = coords @ G.T + t  # analytic reference displacement per node
    err = np.linalg.norm(u0[solved] - u_true[solved], axis=1)
    # The predictor SEEDS IC-GN; the converged field must match analytics tightly.
    assert np.median(err) < 0.05
    assert np.percentile(err, 95) < 0.20


# --- 2. single-seed NCC bootstrap ---------------------------------------------


def test_seed_node_bootstraps_known_shift():
    h = w = 190
    f = _speckle(h, w, seed=7)
    dx, dy = 9.0, -6.0
    g = _shift(f, dx, dy)
    roi = (40, w - 40, 40, h - 40)
    mask = np.ones((h, w), dtype=np.float64)
    para = _para(h, w, roi, mask)
    mesh = build_grid_mesh(para, h, w)

    res = build_seed_u0(f, g, mesh, mask, [(w / 2.0, h / 2.0)], para, search_radius=20)
    assert res is not None
    u0 = res.u0_2d
    solved = np.isfinite(u0).all(axis=1)
    # Uniform translation: every solved node recovers (dx, dy).
    assert np.allclose(u0[solved, 0], dx, atol=0.3)
    assert np.allclose(u0[solved, 1], dy, atol=0.3)


def test_low_texture_only_seed_returns_none():
    """A seed with no correspondence (independent texture) can't seed -> None."""
    h = w = 190
    f = _speckle(h, w, seed=1)
    g = _speckle(h, w, seed=99)  # unrelated texture: no true match anywhere
    roi = (40, w - 40, 40, h - 40)
    mask = np.ones((h, w), dtype=np.float64)
    para = _para(h, w, roi, mask)
    mesh = build_grid_mesh(para, h, w)
    with pytest.warns(UserWarning):
        res = build_seed_u0(f, g, mesh, mask, [(w / 2.0, h / 2.0)], para, search_radius=20)
    assert res is None  # caller falls back to FFT


# --- 3. auto-place rescue of an unseeded region -------------------------------


def test_auto_place_fills_unseeded_region():
    h = w = 210
    f = _speckle(h, w, seed=5)
    g = _shift(f, 3.0, 2.0)  # small uniform shift both blobs
    mask, a, b, ca, cb = _two_region_mask(h, w)
    roi = (20, w - 20, 20, h - 20)
    para = _para(h, w, roi, mask)
    mesh = build_grid_mesh(para, h, w)
    coords = np.asarray(mesh.coordinates_fem, dtype=np.float64)

    # Seed ONLY the left blob; the right blob must be auto-placed + rescued.
    res = build_seed_u0(f, g, mesh, mask, [ca], para, search_radius=20)
    assert res is not None
    assert res.n_regions == 2
    assert res.auto_placed >= 1  # a seed was auto-placed for the unseeded region

    u0 = res.u0_2d
    solved = np.isfinite(u0).all(axis=1)
    in_b = (
        (coords[:, 0] >= b[0])
        & (coords[:, 0] < b[2])
        & (coords[:, 1] >= b[1])
        & (coords[:, 1] < b[3])
    )
    # The auto-placed region B is actually solved (not left all-NaN).
    assert solved[in_b].mean() > 0.8


# --- 4. per-connected-region readiness ("N/M regions ready") ------------------


def test_seed_region_readiness_counts_seeded_regions():
    h = w = 210
    mask, a, b, ca, cb = _two_region_mask(h, w)

    assert seed_region_readiness(mask, []) == (0, 2)
    assert seed_region_readiness(mask, [ca]) == (1, 2)
    assert seed_region_readiness(mask, [ca, cb]) == (2, 2)
    # A seed in the gap between blobs belongs to no region.
    assert seed_region_readiness(mask, [(w / 2.0, h / 2.0)]) == (0, 2)
    # Two seeds in the SAME region still count as one seeded region.
    ca2 = (ca[0] + 5, ca[1] + 5)
    assert seed_region_readiness(mask, [ca, ca2]) == (1, 2)


def test_seed_region_readiness_mesh_matches_runner_node_regions():
    """S4-1: the mesh-based readiness agrees with the runner's node-region logic
    (area>20 AND >=2 mesh nodes + seed node-snapping), where the mask-only
    heuristic disagrees in BOTH directions."""
    from al_dic_3d.matching.seed_propagation import seed_region_readiness_mesh

    kw = dict(winsize=32, winstepsize=16, winsize_min=8)

    # (1) DENOMINATOR: a tiny blob (area > 20 px but too small to carry 2 mesh
    # nodes at step 16) is COUNTED by the mask-only heuristic yet DROPPED by the
    # runner. The mesh readout matches the runner (1 region, not 2).
    h = w = 200
    two = np.zeros((h, w), dtype=np.float64)
    two[40:160, 40:160] = 1.0  # big blob: many nodes
    two[10:16, 180:186] = 1.0  # 6x6 = 36 px > 20, but < 2 nodes
    assert seed_region_readiness(two, [])[1] == 2  # mask-only over-counts
    assert seed_region_readiness_mesh(two, [], **kw)[1] == 1  # runner drops it

    # (2) ATTRIBUTION: a seed just OUTSIDE a blob is background to the mask-only
    # heuristic but the runner snaps it to the nearest mesh node (inside) and
    # counts the region. Single-blob mask so the grid can't reach above y=40.
    one = np.zeros((h, w), dtype=np.float64)
    one[40:160, 40:160] = 1.0
    outside = (100.0, 36.0)  # 4 px above the blob's top edge
    assert seed_region_readiness(one, [outside]) == (0, 1)  # mask-only: unseeded
    assert seed_region_readiness_mesh(one, [outside], **kw) == (1, 1)  # runner: seeded

    # Empty mask -> (0, 0) either way.
    assert seed_region_readiness_mesh(np.zeros((h, w)), [(1.0, 1.0)], **kw) == (0, 0)


# --- S2-2. coverage gate: a sparse propagation degrades to FFT ----------------


def _seed_result(n_solved: int, n_region_nodes: int) -> SeedU0Result:
    return SeedU0Result(
        u0=np.full(2 * max(n_region_nodes, 1), np.nan),
        n_nodes=n_region_nodes,
        n_solved=n_solved,
        n_region_nodes=n_region_nodes,
        n_regions=1,
        n_seeds=1,
        auto_placed=0,
        rescued=0,
        seed_ncc_min=0.9,
        dropped=(),
    )


def test_low_coverage_seed_u0_rejected_to_fft():
    """A BFS stall solving < MIN_SEED_COVERAGE of the region nodes is rejected
    (with a warning, never silent) so the caller falls back to FFT."""
    from al_dic_3d.matching.strategies._common import MIN_SEED_COVERAGE, _accept_seed_u0

    assert 0.0 < MIN_SEED_COVERAGE < 1.0
    assert _accept_seed_u0(_seed_result(90, 100)) is True  # healthy propagation
    assert _accept_seed_u0(_seed_result(50, 100)) is True  # boundary is inclusive
    assert _accept_seed_u0(None) is False
    assert _accept_seed_u0(_seed_result(0, 100)) is False  # nothing solved
    with pytest.warns(UserWarning, match="falling back to FFT"):
        assert _accept_seed_u0(_seed_result(3, 500)) is False  # sparse stall


def test_temporal_camera_u0_falls_back_on_low_coverage(monkeypatch):
    """Wiring: temporal_camera_u0 must NOT return a sparse field — it takes the
    single-seed / FFT path instead of the mostly-NaN u0."""
    import al_dic_3d.matching.strategies._common as common

    sparse = _seed_result(1, 10)
    monkeypatch.setattr(common, "build_seed_u0", lambda *a, **k: sparse)
    with pytest.warns(UserWarning, match="falling back to FFT"):
        out = common.temporal_camera_u0(
            "seed",
            np.zeros((8, 8)),
            np.zeros((8, 8)),
            mesh=None,
            mask=None,
            seed_points=((1.0, 1.0),),
            single_seed=None,  # temporal_u0 -> None (engine FFT)
            para=None,
            n_nodes=10,
            search_radius=20,
        )
    assert out is None  # the sparse field was rejected, not returned


# --- 5. END-TO-END: multi-seed tracks where a single uniform seed fails --------


def test_multiseed_beats_single_on_large_motion_two_regions():
    """Two blobs move OPPOSITE ways by 14 px; a single uniform seed decorrelates
    the far region, one-seed-per-region propagation tracks both."""
    h = w = 260
    f = _speckle(h, w, seed=3)
    mask, a, b, ca, cb = _two_region_mask(h, w)

    # Region A shifts +14 px in x, region B shifts −14 px in x (28 px disagreement,
    # far beyond a 32 px subset's IC-GN basin under the wrong uniform seed).
    gA = _shift(f, 14.0, 0.0)
    gB = _shift(f, -14.0, 0.0)
    left_sel = np.zeros((h, w), dtype=bool)
    left_sel[a[1] : a[3], a[0] : a[2]] = True
    right_sel = np.zeros((h, w), dtype=bool)
    right_sel[b[1] : b[3], b[0] : b[2]] = True
    g = f.copy()
    g[left_sel] = gA[left_sel]
    g[right_sel] = gB[right_sel]

    roi = (20, w - 20, 20, h - 20)
    para = _para(h, w, roi, mask, global_step=False)
    mesh = build_grid_mesh(para, h, w)
    coords = np.asarray(mesh.coordinates_fem, dtype=np.float64)
    n = coords.shape[0]
    # Interior of blob B (subset fully on the moving blob — edge nodes straddle
    # the static background and legitimately cannot track under either seeding).
    in_b = _interior_nodes(coords, b, margin=24)
    assert in_b.sum() >= 6  # enough interior nodes for a meaningful fraction

    frames = [f, g]
    masks = [mask, mask]

    # (a) single uniform seed = region A's motion (+14, 0): wrong for region B.
    u0_single = uniform_u0(n, (14.0, 0.0))
    tf_single = temporal_track(frames, mesh, para, masks=masks, u0=u0_single, gate_znssd=1.0)
    single_valid_b = tf_single.valid[1][in_b].mean()

    # (b) multi-seed: one per region -> F-aware per-region U0.
    res = build_seed_u0(f, g, mesh, mask, [ca, cb], para, search_radius=20)
    assert res is not None and res.n_regions == 2
    tf_multi = temporal_track(frames, mesh, para, masks=masks, u0=res.u0, gate_znssd=1.0)
    multi_valid_b = tf_multi.valid[1][in_b].mean()

    # The decisive contrast: the far region is lost single-seed, tracked
    # multi-seed. (The near region A tracks in both — the uniform seed matches it.)
    assert single_valid_b < 0.3, f"single-seed region B unexpectedly tracked ({single_valid_b:.2f})"
    assert multi_valid_b > 0.9, f"multi-seed region B failed to track ({multi_valid_b:.2f})"

    # And where multi-seed tracked region B, it recovered the true −14 px shift.
    good_b = in_b & tf_multi.valid[1]
    ux = tf_multi.u_accum[1][good_b, 0]
    assert np.allclose(ux, -14.0, atol=0.5)


# --- 6. runner-level integration: multi-seed 'seed' mode drives a full run ----


def test_runner_multiseed_seed_mode_end_to_end(tmp_path):
    """A full pipeline run in multi-seed 'seed' mode tracks the synthetic scene.

    Exercises the whole wiring: draft/RunConfig seed_points -> CorrespondenceConfig
    -> effective_seed_points -> temporal_camera_u0/stereo_seed_u0 -> build_seed_u0
    -> temporal_track / stereo_match_pair(seed_u0=)."""
    import dataclasses

    from al_dic_3d.runner import load_config, run_pipeline
    from tests.synth_stereo import build_scene, write_config

    scene = build_scene(tmp_path, n_frames=3)
    cfg = load_config(write_config(tmp_path, scene))
    # Two Starting Points inside the ROI (one connected plane region → the second
    # is redundant, but proves multi-seed placement runs cleanly end to end).
    cfg = dataclasses.replace(cfg, init_guess="seed", seed_points=((95.0, 100.0), (150.0, 160.0)))
    import warnings

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = run_pipeline(cfg)
    # It must genuinely run in seed mode, not silently degrade to FFT.
    assert not any("falling back to FFT" in str(w.message) for w in caught)
    cs = result.correspondence
    assert cs.n_frames == 3
    from al_dic_3d.matching.contracts import INVALID

    tracked = (cs.source != INVALID).mean()
    assert tracked > 0.85, f"multi-seed run tracked only {tracked:.0%} of points"
