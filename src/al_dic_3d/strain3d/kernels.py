"""Numba plane-fit gradient kernel for strain3d (R3, Qt-free).

Closed-form per-node least squares behind
:func:`al_dic_3d.strain3d.gradients.fit_gradients`: for every node with enough
VSG neighbours the kernel accumulates the NORMAL EQUATIONS of the very fits the
batched-SVD path solves (plane fit -> tangent frame -> in-plane displacement
gradient; or the single world-frame fit for ``coordinate="camera0"``) and
solves the small (<= 4x4) symmetric system directly — no per-node LAPACK call,
no ``(n, k_max, ...)`` padded tensors, and ``prange`` parallelism over nodes.
The Python-level frame loop (progress callbacks + cooperative cancel) stays
outside; the kernel sees one frame at a time through the shared neighbour
table of :func:`al_dic_3d.strain3d.gradients._neighbor_table`.

Numerical contract (equivalence < 1e-9 vs the batched-SVD engine, enforced by
tests):

* Every fit is CENTRED at the query node (design columns AND right-hand sides).
  The displacement-gradient rows of a full-rank least-squares problem are
  invariant to those translations, so the centred closed-form solution equals
  the batched min-norm-SVD solution up to roundoff, while centring + diagonal
  scaling keeps the normal equations well conditioned for realistic
  coordinate magnitudes (windows are small relative to coordinate offsets).
* The scaled normal matrix ``C`` has unit diagonal; ``|det(C)| >= _DEGENERATE_DET``
  bounds ``cond(C) <= d / (det / d^(d-1)) ~ 2.6e6`` (d = 4), keeping the
  forward error of the solve ~ ``cond * eps`` well below 1e-9.  Nodes below
  the bound (or with a zero diagonal) are flagged and re-fit by the caller
  with the exact per-node ``np.linalg.lstsq`` fallback — the same escape hatch
  the batched path uses — so rank-deficient nodes reproduce lstsq's min-norm
  answer bit-for-bit and the ``min_neighbors -> NaN`` contract is untouched.

The module imports fine without numba (``HAS_NUMBA = False``); the dispatcher
in ``gradients.py`` then silently keeps the batched-SVD path.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

try:  # numba ships transitively with al-dic, but stay import-safe without it
    from numba import njit, prange

    HAS_NUMBA = True
except ImportError:  # pragma: no cover - exercised via monkeypatched dispatch
    HAS_NUMBA = False

MODE_LOCAL = 0  # per-node tangent frame from a local plane fit
MODE_CAMERA0 = 1  # world frame, keeps the z-derivative row
MODE_SPECIFIC = 2  # fixed specimen frame (rmat)

# Degeneracy gate on |det| of the diagonally-scaled normal matrix (unit
# diagonal, PSD -> det in [0, 1]).  1e-4 keeps the worst accepted cond(C)
# ~ 2.6e6 (see module docstring); healthy VSG windows sit at det >= 1e-2.
_DEGENERATE_DET = 1e-4

if HAS_NUMBA:

    @njit(cache=True)
    def _solve_scaled(m, b, d):  # pragma: no cover - compiled
        """Solve ``m x = b`` (``d x d`` normal matrix, ``d <= 4``, 3 RHS).

        Diagonal (Jacobi) scaling to unit diagonal, then Gaussian elimination
        with partial pivoting.  Returns ``(x, det_scaled, ok)`` where
        ``det_scaled = |det|`` of the scaled matrix (conditioning proxy) and
        ``ok = False`` flags a zero diagonal / exactly singular system.
        """
        x = np.zeros((4, 3))
        s = np.empty(4)
        for i in range(d):
            mii = m[i, i]
            if mii <= 0.0:
                return x, 0.0, False
            s[i] = np.sqrt(mii)
        c = np.empty((4, 4))
        g = np.empty((4, 3))
        for i in range(d):
            for j in range(d):
                c[i, j] = m[i, j] / (s[i] * s[j])
            for r in range(3):
                g[i, r] = b[i, r] / s[i]

        det = 1.0
        for col in range(d):
            piv = col
            big = abs(c[col, col])
            for i in range(col + 1, d):
                mag = abs(c[i, col])
                if mag > big:
                    big = mag
                    piv = i
            if big == 0.0:
                return x, 0.0, False
            if piv != col:
                for j in range(d):
                    tmp = c[col, j]
                    c[col, j] = c[piv, j]
                    c[piv, j] = tmp
                for r in range(3):
                    tmp = g[col, r]
                    g[col, r] = g[piv, r]
                    g[piv, r] = tmp
            det *= big
            inv = 1.0 / c[col, col]
            for i in range(col + 1, d):
                f = c[i, col] * inv
                if f != 0.0:
                    for j in range(col, d):
                        c[i, j] -= f * c[col, j]
                    for r in range(3):
                        g[i, r] -= f * g[col, r]

        for r in range(3):
            for i in range(d - 1, -1, -1):
                acc = g[i, r]
                for j in range(i + 1, d):
                    acc -= c[i, j] * x[j, r]
                x[i, r] = acc / c[i, i]
        for i in range(d):
            si = s[i]
            x[i, 0] /= si
            x[i, 1] /= si
            x[i, 2] /= si
        return x, det, True

    @njit(parallel=True, cache=True)
    def _fit_kernel(pts, dsp, nbr, counts, min_nbr, mode, rmat, degen_tol):  # pragma: no cover
        """Per-node displacement-gradient fit over the padded neighbour table.

        Args:
            pts:     (nf, 3) finite reference 3D coords.
            dsp:     (nf, 3) finite displacement.
            nbr:     (nf, k_max) LOCAL neighbour indices, -1-padded past counts.
            counts:  (nf,) true neighbour count per node.
            min_nbr: nodes below this stay NaN (void contract).
            mode:    MODE_LOCAL / MODE_CAMERA0 / MODE_SPECIFIC.
            rmat:    (3, 3) fixed frame for MODE_SPECIFIC (columns x/y/z hat).
            degen_tol: scaled-determinant gate -> caller's lstsq fallback.

        Returns:
            ``(coef, degen)``: (nf, 3, 3) gradients (NaN for skipped nodes) and
            an (nf,) bool mask of nodes needing the exact per-node fallback.
        """
        nf = pts.shape[0]
        coef = np.full((nf, 3, 3), np.nan)
        degen = np.zeros(nf, np.bool_)

        for i in prange(nf):
            cnt = counts[i]
            if cnt < min_nbr:
                continue
            px = pts[i, 0]
            py = pts[i, 1]
            pz = pts[i, 2]
            d0x = dsp[i, 0]
            d0y = dsp[i, 1]
            d0z = dsp[i, 2]
            m = np.zeros((4, 4))
            b = np.zeros((4, 3))

            if mode == 1:  # camera0: [dX, dY, dZ, 1] -> centred [U, V, W]
                for j in range(cnt):
                    k = nbr[i, j]
                    a0 = pts[k, 0] - px
                    a1 = pts[k, 1] - py
                    a2 = pts[k, 2] - pz
                    r0 = dsp[k, 0] - d0x
                    r1 = dsp[k, 1] - d0y
                    r2 = dsp[k, 2] - d0z
                    m[0, 0] += a0 * a0
                    m[0, 1] += a0 * a1
                    m[0, 2] += a0 * a2
                    m[0, 3] += a0
                    m[1, 1] += a1 * a1
                    m[1, 2] += a1 * a2
                    m[1, 3] += a1
                    m[2, 2] += a2 * a2
                    m[2, 3] += a2
                    b[0, 0] += a0 * r0
                    b[0, 1] += a0 * r1
                    b[0, 2] += a0 * r2
                    b[1, 0] += a1 * r0
                    b[1, 1] += a1 * r1
                    b[1, 2] += a1 * r2
                    b[2, 0] += a2 * r0
                    b[2, 1] += a2 * r1
                    b[2, 2] += a2 * r2
                    b[3, 0] += r0
                    b[3, 1] += r1
                    b[3, 2] += r2
                m[3, 3] = cnt
                for row in range(1, 4):
                    for col in range(row):
                        m[row, col] = m[col, row]
                sol, det, ok = _solve_scaled(m, b, 4)
                if not ok or det < degen_tol:
                    degen[i] = True
                    continue
                for row in range(3):  # rows [dX, dY, dZ], cols [U, V, W]
                    for col in range(3):
                        coef[i, row, col] = sol[row, col]
                continue

            if mode == 2:  # fixed specimen frame
                xhx = rmat[0, 0]
                xhy = rmat[1, 0]
                xhz = rmat[2, 0]
                yhx = rmat[0, 1]
                yhy = rmat[1, 1]
                yhz = rmat[2, 1]
                zhx = rmat[0, 2]
                zhy = rmat[1, 2]
                zhz = rmat[2, 2]
            else:  # local: plane fit [dx, dy, 1] -> dz, then tangent frame
                for j in range(cnt):
                    k = nbr[i, j]
                    a0 = pts[k, 0] - px
                    a1 = pts[k, 1] - py
                    a2 = pts[k, 2] - pz
                    m[0, 0] += a0 * a0
                    m[0, 1] += a0 * a1
                    m[0, 2] += a0
                    m[1, 1] += a1 * a1
                    m[1, 2] += a1
                    b[0, 0] += a0 * a2
                    b[1, 0] += a1 * a2
                    b[2, 0] += a2
                m[2, 2] = cnt
                m[1, 0] = m[0, 1]
                m[2, 0] = m[0, 2]
                m[2, 1] = m[1, 2]
                sol, det, ok = _solve_scaled(m, b, 3)
                if not ok or det < degen_tol:
                    degen[i] = True
                    continue
                pa = sol[0, 0]
                pb = sol[1, 0]
                # tangent_frame((a, b)): z = norm([a, b, -1]); x = norm(e1 - z0*z)
                zn = np.sqrt(pa * pa + pb * pb + 1.0)
                zhx = pa / zn
                zhy = pb / zn
                zhz = -1.0 / zn
                xhx = 1.0 - zhx * zhx
                xhy = -zhx * zhy
                xhz = -zhx * zhz
                xn = np.sqrt(xhx * xhx + xhy * xhy + xhz * xhz)
                xhx /= xn
                xhy /= xn
                xhz /= xn
                yhx = zhy * xhz - zhz * xhy  # y = z x x
                yhy = zhz * xhx - zhx * xhz
                yhz = zhx * xhy - zhy * xhx
                m[:] = 0.0
                b[:] = 0.0

            # gradient fit in the frame: [e_x, e_y, 1] -> centred local disp
            for j in range(cnt):
                k = nbr[i, j]
                wx = pts[k, 0] - px
                wy = pts[k, 1] - py
                wz = pts[k, 2] - pz
                ex = wx * xhx + wy * xhy + wz * xhz
                ey = wx * yhx + wy * yhy + wz * yhz
                gx = dsp[k, 0] - d0x
                gy = dsp[k, 1] - d0y
                gz = dsp[k, 2] - d0z
                r0 = gx * xhx + gy * xhy + gz * xhz  # local U
                r1 = gx * yhx + gy * yhy + gz * yhz  # local V
                r2 = gx * zhx + gy * zhy + gz * zhz  # local W
                m[0, 0] += ex * ex
                m[0, 1] += ex * ey
                m[0, 2] += ex
                m[1, 1] += ey * ey
                m[1, 2] += ey
                b[0, 0] += ex * r0
                b[0, 1] += ex * r1
                b[0, 2] += ex * r2
                b[1, 0] += ey * r0
                b[1, 1] += ey * r1
                b[1, 2] += ey * r2
                b[2, 0] += r0
                b[2, 1] += r1
                b[2, 2] += r2
            m[2, 2] = cnt
            m[1, 0] = m[0, 1]
            m[2, 0] = m[0, 2]
            m[2, 1] = m[1, 2]
            sol, det, ok = _solve_scaled(m, b, 3)
            if not ok or det < degen_tol:
                degen[i] = True
                continue
            for col in range(3):  # rows [d/dx_loc, d/dy_loc, 0], cols [U, V, W]
                coef[i, 0, col] = sol[0, col]
                coef[i, 1, col] = sol[1, col]
                coef[i, 2, col] = 0.0

        return coef, degen


def fit_kernel(
    pts: NDArray[np.float64],
    dsp: NDArray[np.float64],
    nbr: NDArray[np.int64],
    counts: NDArray[np.int64],
    min_neighbors: int,
    mode: int,
    rmat: NDArray[np.float64],
) -> tuple[NDArray[np.float64], NDArray[np.bool_]]:
    """Typed wrapper around the compiled kernel (see :func:`_fit_kernel`)."""
    if not HAS_NUMBA:  # pragma: no cover - dispatcher never routes here
        raise RuntimeError("numba is not importable; use the batched engine")
    return _fit_kernel(
        np.ascontiguousarray(pts, dtype=np.float64),
        np.ascontiguousarray(dsp, dtype=np.float64),
        np.ascontiguousarray(nbr, dtype=np.int64),
        np.ascontiguousarray(counts, dtype=np.int64),
        np.int64(min_neighbors),
        np.int64(mode),
        np.ascontiguousarray(rmat, dtype=np.float64),
        _DEGENERATE_DET,
    )


def warmup() -> None:
    """Compile (or load the on-disk cache of) the kernel before timing runs.

    One tiny call compiles every branch for the production signature (numba
    compiles whole functions, not taken paths) — the JIT-before-timing lesson
    from the 2D engine.  No-op without numba.
    """
    if not HAS_NUMBA:
        return
    n = 9
    rng = np.random.default_rng(0)
    pts = np.column_stack(
        [np.tile(np.arange(3.0), 3), np.repeat(np.arange(3.0), 3), rng.normal(0, 0.01, n)]
    )
    dsp = rng.normal(0, 0.01, (n, 3))
    nbr = np.tile(np.arange(n, dtype=np.int64), (n, 1))
    counts = np.full(n, n, dtype=np.int64)
    fit_kernel(pts, dsp, nbr, counts, n, MODE_LOCAL, np.eye(3))
