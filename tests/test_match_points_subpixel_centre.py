"""match_points at non-integer points returns the motion of the point itself.

The engine centres each subset on the nearest pixel, so the IC-GN solve gives
the motion of ``round(x)``. A caller that asks about a non-integer point ``x``
(the per-frame stereo strategy matches at tracked, sub-pixel left positions)
must still get the motion of ``x``: under a displacement gradient ``F`` the two
differ by ``F (x - round(x))``, up to ~0.1 px at a stereo disparity gradient of
0.17.

The ground truth is an exact affine pair: both images are rendered from the
same analytic speckle, the right one through ``x' = A x + t``, so the motion of
any point ``x`` is ``(A - I) x + t`` with no interpolation error.
"""

from __future__ import annotations

import numpy as np
import pytest
from al_dic.solver.local_icgn import local_icgn_solve_subset

from al_dic_3d.matching.primitives import make_dicpara, match_points, prepare_reference

SIZE = 240
BLOB_RADIUS = 2.2
G = np.array([[0.17, 0.03], [0.02, 0.05]])  # rows (u, v), columns (d/dx, d/dy)
A = np.eye(2) + G
T = np.array([12.3, -3.7])


def _render(centres: np.ndarray, amps: np.ndarray, a: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Exact image of a Gaussian-blob speckle seen through ``x' = a X + t``."""
    img = np.zeros((SIZE, SIZE))
    a_inv = np.linalg.inv(a)
    reach = int(np.ceil(5 * BLOB_RADIUS * np.abs(a).sum(1).max())) + 1
    for c, amp in zip(centres, amps, strict=True):
        cx, cy = a @ c + t
        x0, x1 = max(0, int(cx) - reach), min(SIZE, int(cx) + reach + 1)
        y0, y1 = max(0, int(cy) - reach), min(SIZE, int(cy) + reach + 1)
        if x0 >= x1 or y0 >= y1:
            continue
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float64)
        dx = a_inv[0, 0] * (xx - t[0]) + a_inv[0, 1] * (yy - t[1]) - c[0]
        dy = a_inv[1, 0] * (xx - t[0]) + a_inv[1, 1] * (yy - t[1]) - c[1]
        img[y0:y1, x0:x1] += amp * np.exp(-(dx * dx + dy * dy) / (2 * BLOB_RADIUS**2))
    return img * 120.0 + 40.0


@pytest.fixture(scope="module")
def affine_pair():
    rng = np.random.default_rng(7)
    centres = rng.uniform(-30, SIZE + 30, size=(3200, 2))
    amps = rng.uniform(0.4, 1.0, size=len(centres))
    ref = _render(centres, amps, np.eye(2), np.zeros(2))
    dfm = _render(centres, amps, A, T)
    para = make_dicpara((SIZE, SIZE), (0, SIZE - 1, 0, SIZE - 1), winsize=32, use_global_step=False)
    return ref, dfm, para


def _grid() -> np.ndarray:
    """100 interior points: every subset stays inside both images, and at 50+
    points the engine takes its production (Numba) precompute path."""
    g = np.arange(50.0, 161.0, 12.0)
    xx, yy = np.meshgrid(g, g)
    return np.column_stack([xx.ravel(), yy.ravel()])


def _true_motion(points: np.ndarray) -> np.ndarray:
    return points @ G.T + T


def test_non_integer_points_get_their_own_motion(affine_pair):
    ref, dfm, para = affine_pair
    base = _grid()
    # Sub-pixel offsets of up to 0.45 px in both directions (all four signs).
    signs = np.array([[1, 1], [1, -1], [-1, 1], [-1, -1]], dtype=np.float64)
    pts = base + 0.45 * signs[np.arange(len(base)) % 4]

    U, _, valid = match_points(ref, dfm, pts, _true_motion(pts), para, tol=1e-4)

    assert valid.all()
    err = U - _true_motion(pts)
    # The motion of round(x) instead of x would be off by G (x - round(x)),
    # about 0.09 px in u here; the solver itself is good to ~0.002 px.
    assert np.abs(err).max() < 0.01, f"max error {np.abs(err).max():.4f} px"


def test_integer_points_are_unchanged(affine_pair):
    ref, dfm, para = affine_pair
    pts = _grid()
    U0 = _true_motion(pts)

    U, _, valid = match_points(ref, dfm, pts, U0, para, tol=1e-4)
    reference = prepare_reference(ref, pts, para)
    u_raw, _, _ = local_icgn_solve_subset(reference.ctx, None, U0, np.ascontiguousarray(dfm), 1e-4)

    assert valid.all()
    np.testing.assert_array_equal(U, u_raw)


def test_invalid_points_stay_nan(affine_pair):
    # A lost track reaches match_points as a NaN point (the per-frame stereo
    # strategy passes every tracked position). The point set is large enough
    # for the engine's production precompute, which flags NaN points invalid.
    ref, dfm, para = affine_pair
    pts = _grid() + 0.3
    pts[[5, 17]] = np.nan

    U, znssd, valid = match_points(ref, dfm, pts, _true_motion(np.nan_to_num(pts)), para)

    assert not valid[[5, 17]].any()
    assert np.isnan(U[[5, 17]]).all() and np.isnan(znssd[[5, 17]]).all()
    assert np.isnan(U[~valid]).all()
    assert np.isfinite(U[valid]).all()
