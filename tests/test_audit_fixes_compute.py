"""Adversarial-audit regressions for the compute layer (A3-1/2/3, A6-1).

Each test encodes the audit's measured numerical experiment and FAILS on the
pre-fix code, PASSING only once the corresponding fix lands:

- A3-1: ``_znssd`` must drop out-of-bounds warped samples (engine
  ``|tempg|>1e-10`` rule). A perfect boundary match scores ~0, not ~1.04.
- A3-2: ``_znssd`` masks with the CENTER-connected component (engine
  ``_connected_center_mask``), not the raw window patch across a hole.
- A3-3: ``_znssd`` scores partial edge subsets (center in-image) on their
  in-image support instead of NaN-ing them (engine default Numba backend).
- A6-1: ``edge_trim_mask`` treats the node-grid OUTER boundary as trim
  evidence, so a clean rectangular plate trims its biased outer ring at the
  GUI-default alpha=0.7.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates

from al_dic_3d.matching.contracts import TRACKED
from al_dic_3d.matching.primitives import _znssd
from al_dic_3d.reconstruct import Reconstruction3D
from al_dic_3d.strain3d import compute_surface_strain
from al_dic_3d.strain3d.edgetrim import edge_trim_mask


def _speckle(h: int, w: int, sigma: float = 2.0, seed: int = 3) -> np.ndarray:
    rng = np.random.default_rng(seed)
    f = gaussian_filter(rng.standard_normal((h, w)), sigma=sigma, mode="nearest")
    f -= f.min()
    f /= f.max()
    return 20.0 + 215.0 * f


# ---------------------------------------------------------------------------
# A3-1 — out-of-bounds warped samples must be excluded from ZNSSD
# ---------------------------------------------------------------------------


def test_a3_1_perfect_boundary_match_scores_near_zero():
    """A subset fully in the REFERENCE image but half OOB on the DEFORMED side.

    Audit: 60x60 speckle, def = ref shifted +10px, winsize=20 subset whose
    right half warps off the deformed image at U=+10. The in-image half is a
    PERFECT match; the pre-fix wrapper injects ~210 off-image zeros and reports
    ZNSSD ~1.04 (killed by the znssd_max=0.5 / temporal_gate=1.0 gates); the
    engine-faithful objective drops the OOB samples and returns ~0.
    """
    h = w = 60
    ref = _speckle(h, w)
    dfm = np.roll(ref, 10, axis=1)  # dfm(x) = ref(x - 10) -> match warp U=+10

    # Center at col 49: subset cols 39..59 all in the REFERENCE image (passes
    # even the strict whole-subset rule, so the bug is a wrong value, not NaN),
    # but gu = col + 10 = 49..69 pushes cols 50..59 off the deformed image.
    pts = np.array([[49.0, 29.0]])
    u = np.array([[10.0, 0.0]])
    f = np.zeros((1, 4))
    mask = np.ones((h, w), dtype=np.float64)

    z = _znssd(ref, dfm, pts, u, f, 20, np.array([True]), mask)[0]

    assert np.isfinite(z)
    # Post-fix: a perfect boundary correspondence must pass BOTH gates.
    assert z < 0.1, f"perfect boundary match scored ZNSSD={z:.4f} (off-image pollution)"


# ---------------------------------------------------------------------------
# A3-2 — mask must use the center-connected component, not the raw patch
# ---------------------------------------------------------------------------


def test_a3_2_center_connected_component_excludes_far_island():
    """A window split by a masked column into two 4-connected islands.

    The center sits in the LEFT island where def == ref (perfect); the RIGHT
    island is unrelated material. The engine keeps only the center-connected
    component (ZNSSD ~0); the pre-fix wrapper contaminates the statistic with
    the right island (~0.47), flipping the gate decision.
    """
    h = w = 61
    ref = _speckle(h, w, seed=7)
    rng = np.random.default_rng(21)
    dfm = ref.copy()
    dfm[:, 39:] = _speckle(h, w, seed=99)[:, 39:]  # unrelated right island

    mask = np.ones((h, w), dtype=np.float64)
    mask[:, 38] = 0.0  # full-height barrier splitting the window at col 38

    pts = np.array([[30.0, 30.0]])  # center in the LEFT island (cols 15..37)
    u = np.zeros((1, 2))
    f = np.zeros((1, 4))

    z = _znssd(ref, dfm, pts, u, f, 30, np.array([True]), mask)[0]

    assert np.isfinite(z)
    assert z < 0.05, f"center-connected match scored ZNSSD={z:.4f} (right-island leak)"
    del rng


# ---------------------------------------------------------------------------
# A3-3 — partial edge subsets scored on in-image support, not NaN
# ---------------------------------------------------------------------------


def test_a3_3_near_edge_subset_scored_not_nan():
    """A near-edge node the engine's default Numba backend tracks (center
    in-image, right half OOB) must get a finite, small ZNSSD — not NaN — so the
    temporal honesty gate (NaN == failure) does not silently kill it.
    """
    h = w = 220
    ref = _speckle(h, w, seed=5)
    dx, dy = 1.4, 0.9
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    dfm = map_coordinates(ref, [yy - dy, xx - dx], order=5, mode="nearest").reshape(h, w)

    interior = [100.0, 110.0]
    near_edge = [210.0, 110.0]  # center in-image (<=219) but 210+20=230 OOB
    pts = np.array([interior, near_edge])
    u = np.tile([dx, dy], (2, 1))
    f = np.zeros((2, 4))
    mask = np.ones((h, w), dtype=np.float64)

    z = _znssd(ref, dfm, pts, u, f, 40, np.array([True, True]), mask)

    assert np.isfinite(z[0]) and z[0] < 0.05  # interior: near-perfect
    # Post-fix: the near-edge node is scored on its in-image half (well
    # correlated), far below the gate threshold 1.0 — no false kill.
    assert np.isfinite(z[1]), "near-edge subset NaN'd instead of scored on in-image support"
    assert z[1] < 0.05, f"near-edge in-image correlation should be ~0, got {z[1]:.4f}"


# ---------------------------------------------------------------------------
# A6-1 — edge trim must fence the node-grid OUTER boundary too
# ---------------------------------------------------------------------------


def _flat_plate(n: int, step_px: float, step_mm: float, c: float):
    """Clean n x n all-valid plate, flat Z=0, quadratic U = c*X^2 (V=W=0)."""
    ii, jj = np.meshgrid(np.arange(n), np.arange(n))
    ii = ii.ravel().astype(np.float64)
    jj = jj.ravel().astype(np.float64)
    ref_2d = np.column_stack([ii * step_px + 40.0, jj * step_px + 40.0])
    xw = ii * step_mm
    yw = jj * step_mm
    ref_3d = np.column_stack([xw, yw, np.zeros_like(xw)])  # flat -> local == world
    disp = np.column_stack([c * xw**2, np.zeros_like(xw), np.zeros_like(xw)])
    points = np.stack([ref_3d, ref_3d + disp])
    displacement = points - points[0][None]
    reproj = np.zeros(points.shape[:2])
    source = np.full(points.shape[:2], TRACKED, np.uint8)
    return ref_2d, xw, Reconstruction3D(points, displacement, reproj, source)


def test_a6_1_clean_plate_trims_outer_ring_at_default_alpha():
    ref_2d, xw, rec = _flat_plate(n=20, step_px=16.0, step_mm=2.0, c=1e-3)

    strain = compute_surface_strain(
        rec, ref_2d, strain_size=5, winstepsize=16, coordinate="local", edge_trim_alpha=0.7
    )

    assert strain.n_trimmed is not None
    # The A6-1 fix: the biased one-sided outer ring is now trimmed even though
    # the plate has no holes/invalid nodes (pre-fix reported 0).
    assert int(strain.n_trimmed[1]) > 0, "clean outer ring not trimmed (A6-1 not fixed)"

    # Interior nodes (far from every edge) keep their exact Green-Lagrange strain.
    x_min, x_max = ref_2d[:, 0].min(), ref_2d[:, 0].max()
    y_min, y_max = ref_2d[:, 1].min(), ref_2d[:, 1].max()
    band = 0.7 * 32.5 + 16.0  # trim band + one node step
    interior = (
        (ref_2d[:, 0] > x_min + band)
        & (ref_2d[:, 0] < x_max - band)
        & (ref_2d[:, 1] > y_min + band)
        & (ref_2d[:, 1] < y_max - band)
    )
    dudx = 2.0 * 1e-3 * xw  # dU/dX of c*X^2
    expected = dudx + 0.5 * dudx**2  # analytic Green-Lagrange exx
    got = strain.exx[1][interior]
    assert np.isfinite(got).all(), "interior nodes should stay finite (not over-trimmed)"
    assert np.nanmax(np.abs(got - expected[interior])) < 1e-6


def test_a6_1_edge_trim_mask_fences_clean_grid_outer_boundary():
    ref_2d, _, _ = _flat_plate(n=20, step_px=16.0, step_mm=2.0, c=1e-3)
    finite = np.ones(ref_2d.shape[0], dtype=bool)

    trim = edge_trim_mask(ref_2d, finite, vsg_radius=32.5, alpha=0.7)
    assert trim.any(), "outer boundary ring must be trimmed on a clean all-valid grid"

    # alpha = 0 still fully disables.
    assert not edge_trim_mask(ref_2d, finite, vsg_radius=32.5, alpha=0.0).any()

    # A deep-interior node is never trimmed.
    center = ref_2d.mean(axis=0)
    ci = int(np.argmin(np.linalg.norm(ref_2d - center, axis=1)))
    assert not trim[ci]
