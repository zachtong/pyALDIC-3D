"""Local displacement-gradient fit + Green-Lagrange strain (Qt-free).

Ports the math of ``PlaneFit3_Quadtree.m`` + ``computeStrain3D.m`` (see
docs/strain3d_math.md): a per-node VSG neighbourhood (square pixel window) →
local tangent frame from a plane fit on the reference 3D coords → plain
least-squares displacement gradients in that frame → deformation gradient →
Green-Lagrange strain. Pure numpy/scipy — no ``al_dic`` coupling.

Performance (P3.5): the historical implementation looped Python-side over
every node (``query_ball_point`` + 1–2 ``lstsq`` per node per frame — 4M+
iterations at 200 frames × 20k points). :func:`fit_gradients` now

* computes the neighbour table ONCE per validity pattern (reusable across
  frames via ``neighbor_cache``), and
* solves all per-node least-squares problems in a single batched SVD over a
  mask-padded ``(n, k_max, ·)`` neighbour tensor — zero-padded rows contribute
  nothing to a least-squares residual, so the padded problems have exactly the
  same solutions as the per-node ones.

Nodes whose fit is rank-deficient or near the numerical cutoff (where SVD
implementations may legitimately disagree) are re-fit with the original
per-node ``np.linalg.lstsq`` path, so results match the historical loop to
machine precision everywhere (equivalence enforced by tests).

R3 stacks a Numba engine on top (:mod:`al_dic_3d.strain3d.kernels`): a
``prange`` closed-form normal-equations kernel over the same neighbour table.
``engine="auto"`` (default) uses it when numba imports and silently falls back
to the batched-SVD path otherwise; both engines share the neighbour cache, the
``min_neighbors -> NaN`` contract, and the exact per-node lstsq fallback for
degenerate nodes (equivalence < 1e-9 enforced by tests).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.strain3d import kernels as _kernels

MIN_NEIGHBORS = 9  # minimum nodes in a VSG for a stable plane + gradient fit

# Nodes whose smallest singular value falls below this fraction of the largest
# take the exact per-node lstsq fallback: near-singular systems amplify the
# (tiny) differences between SVD implementations, and truly rank-deficient
# ones must reproduce lstsq's min-norm answer bit-for-bit.
_DEGENERATE_RCOND = 1e-7

# Neighbour tables cached per validity pattern; consecutive frames almost
# always share one, so a handful of entries covers a whole run while bounding
# the cache for pathological per-frame validity churn.
_NEIGHBOR_CACHE_CAPACITY = 8


def tangent_frame(normal_ab: tuple[float, float]) -> NDArray[np.float64]:
    """Orthonormal tangent frame ``R = [x_hat, y_hat, z_hat]`` from a plane ``Z=aX+bY+c``.

    ``z_hat`` is the surface normal ``[a, b, -1]``; ``x_hat`` is world +X projected
    onto the plane; ``y_hat = z_hat x x_hat`` (PlaneFit3_Quadtree.m:99-102).
    """
    a, b = normal_ab
    z = np.array([a, b, -1.0], dtype=np.float64)
    z /= np.linalg.norm(z)
    x = np.array([1.0, 0.0, 0.0]) - np.dot([1.0, 0.0, 0.0], z) * z
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return np.column_stack([x, y, z])


def tangent_frames(ab: NDArray[np.float64]) -> NDArray[np.float64]:
    """Vectorized :func:`tangent_frame`: ``(m, 2)`` plane slopes -> ``(m, 3, 3)``."""
    ab = np.asarray(ab, dtype=np.float64).reshape(-1, 2)
    z = np.column_stack([ab[:, 0], ab[:, 1], -np.ones(ab.shape[0])])
    z /= np.linalg.norm(z, axis=1, keepdims=True)
    x = np.zeros_like(z)
    x[:, 0] = 1.0
    x -= z * z[:, :1]  # e1 - (e1 . z) z, with e1 . z == z[:, 0]
    x /= np.linalg.norm(x, axis=1, keepdims=True)
    y = np.cross(z, x)
    return np.stack([x, y, z], axis=2)


def _lstsq(a: NDArray[np.float64], b: NDArray[np.float64]) -> NDArray[np.float64]:
    return np.linalg.lstsq(a, b, rcond=None)[0]


def _fit_node_into(
    coef: NDArray[np.float64],
    i: int,
    sel: NDArray[np.int64],
    ref_3d: NDArray[np.float64],
    disp: NDArray[np.float64],
    coordinate: str,
    specimen_R: NDArray[np.float64] | None,
) -> None:
    """Write node ``i``'s gradient rows into ``coef`` — the original per-node math."""
    x3 = ref_3d[sel]
    d3 = disp[sel]

    if coordinate == "camera0":
        amat = np.column_stack([x3, np.ones(len(sel))])
        coef[i] = _lstsq(amat, d3)[:3]  # rows [dX,dY,dZ], cols [U,V,W]
        return

    if coordinate == "specific" and specimen_R is not None:
        frame = np.asarray(specimen_R, dtype=np.float64)
    else:
        plane = _lstsq(np.column_stack([x3[:, :2], np.ones(len(sel))]), x3[:, 2])
        frame = tangent_frame((float(plane[0]), float(plane[1])))

    x_loc = x3 @ frame
    d_loc = d3 @ frame
    amat = np.column_stack([x_loc[:, 0], x_loc[:, 1], np.ones(len(sel))])
    grad = _lstsq(amat, d_loc)  # rows [d/dxloc, d/dyloc, const], cols [U,V,W]
    coef[i, 0] = grad[0]
    coef[i, 1] = grad[1]
    coef[i, 2] = 0.0  # surface gauge: out-of-plane derivative dropped


def _fit_gradients_loop(
    ref_2d: NDArray[np.float64],
    ref_3d: NDArray[np.float64],
    disp: NDArray[np.float64],
    vsg_radius: float,
    *,
    coordinate: str = "local",
    specimen_R: NDArray[np.float64] | None = None,
    min_neighbors: int = MIN_NEIGHBORS,
) -> NDArray[np.float64]:
    """Reference per-node implementation (pre-P3.5) — fallback + parity tests."""
    from scipy.spatial import cKDTree

    ref_2d = np.asarray(ref_2d, dtype=np.float64).reshape(-1, 2)
    ref_3d = np.asarray(ref_3d, dtype=np.float64).reshape(-1, 3)
    disp = np.asarray(disp, dtype=np.float64).reshape(-1, 3)
    n = ref_2d.shape[0]

    finite = np.isfinite(ref_2d).all(1) & np.isfinite(ref_3d).all(1) & np.isfinite(disp).all(1)
    coef = np.full((n, 3, 3), np.nan, dtype=np.float64)
    if finite.sum() < min_neighbors:
        return coef

    idx_map = np.where(finite)[0]
    tree = cKDTree(ref_2d[finite])
    for i in idx_map:
        local = tree.query_ball_point(ref_2d[i], r=vsg_radius, p=np.inf)
        if len(local) < min_neighbors:
            continue
        _fit_node_into(coef, i, idx_map[local], ref_3d, disp, coordinate, specimen_R)
    return coef


def _neighbor_table(
    ref_2d: NDArray[np.float64],
    finite: NDArray[np.bool_],
    vsg_radius: float,
    cache: dict | None,
) -> tuple[NDArray[np.int64], NDArray[np.int64], NDArray[np.int64]]:
    """VSG neighbour table over the finite nodes, cached per validity pattern.

    Returns ``(idx_map, nbr, counts)``: original indices of the finite nodes,
    a ``(n_finite, k_max)`` padded matrix of LOCAL neighbour indices (``-1`` =
    padding), and the true neighbour count per node. Cached by the finite-mask
    bytes — within one run ``ref_2d`` and ``vsg_radius`` are fixed, so the mask
    fully determines the table (the cache dict must not outlive them).
    """
    key = finite.tobytes() if cache is not None else None
    if cache is not None and key in cache:
        return cache[key]

    from scipy.spatial import cKDTree

    idx_map = np.where(finite)[0]
    pts = ref_2d[finite]
    lists = cKDTree(pts).query_ball_point(pts, r=vsg_radius, p=np.inf)
    counts = np.fromiter((len(x) for x in lists), dtype=np.int64, count=len(lists))
    k_max = int(counts.max()) if counts.size else 0
    nbr = np.full((len(lists), k_max), -1, dtype=np.int64)
    for row, lst in enumerate(lists):
        nbr[row, : len(lst)] = lst

    out = (idx_map, nbr, counts)
    if cache is not None:
        cache[key] = out
        while len(cache) > _NEIGHBOR_CACHE_CAPACITY:
            cache.pop(next(iter(cache)))
    return out


def _batched_lstsq(
    a: NDArray[np.float64],
    b: NDArray[np.float64],
    rows: NDArray[np.int64],
) -> tuple[NDArray[np.float64], NDArray[np.bool_]]:
    """Per-node min-norm least squares, replicating ``lstsq(..., rcond=None)``.

    ``a``: ``(n, k_max, c)`` and ``b``: ``(n, k_max, r)`` with all-zero rows
    beyond each node's true row count — a zero row adds ``||0 - 0||^2`` to the
    residual, so the padded problem has exactly the per-node solution. ``rows``
    holds the true counts, feeding lstsq's default cutoff
    ``eps * max(M, N) * s_max`` per node.

    Returns ``(x, degenerate)``: solutions ``(n, c, r)`` plus a flag for nodes
    that are rank-deficient / near the cutoff and should take the exact
    per-node fallback.
    """
    u, s, vt = np.linalg.svd(a, full_matrices=False)
    eps = np.finfo(np.float64).eps
    m = np.maximum(rows, a.shape[2]).astype(np.float64)
    cutoff = (m * eps)[:, None] * s[:, :1]
    keep = s > cutoff
    s_inv = np.where(keep, 1.0 / np.where(s == 0.0, 1.0, s), 0.0)
    utb = np.einsum("nkd,nkr->ndr", u, b)
    x = np.einsum("ndc,nd,ndr->ncr", vt, s_inv, utb)
    degenerate = (~keep.all(axis=1)) | (s[:, -1] <= s[:, 0] * _DEGENERATE_RCOND)
    return x, degenerate


def _fit_batched(
    coef: NDArray[np.float64],
    idx_map: NDArray[np.int64],
    nbr: NDArray[np.int64],
    counts: NDArray[np.int64],
    ok: NDArray[np.bool_],
    finite: NDArray[np.bool_],
    ref_3d: NDArray[np.float64],
    disp: NDArray[np.float64],
    coordinate: str,
    specimen_R: NDArray[np.float64] | None,
) -> list[tuple[int, NDArray[np.int64]]]:
    """Batched min-norm SVD engine (P3.5): fills ``coef`` for the ``ok`` nodes.

    Returns the degenerate nodes as ``(original_index, neighbour_selection)``
    pairs for the caller's exact per-node lstsq fallback.
    """
    nodes = idx_map[ok]  # original indices of the fitted nodes
    rows = counts[ok]
    nbr_ok = nbr[ok]
    pad = nbr_ok < 0
    safe = np.where(pad, 0, nbr_ok)
    valid = (~pad)[..., None].astype(np.float64)  # (m, k_max, 1) row mask
    x3 = ref_3d[finite][safe] * valid  # zero-padded neighbour tensors
    d3 = disp[finite][safe] * valid
    ones = valid[..., 0]

    if coordinate == "camera0":
        amat = np.concatenate([x3, ones[..., None]], axis=2)  # (m, k_max, 4)
        sol, degenerate = _batched_lstsq(amat, d3, rows)
        coef[nodes] = sol[:, :3, :]  # rows [dX,dY,dZ], cols [U,V,W]
    else:
        if coordinate == "specific" and specimen_R is not None:
            frames = np.broadcast_to(np.asarray(specimen_R, dtype=np.float64), (len(nodes), 3, 3))
            degenerate = np.zeros(len(nodes), dtype=bool)
        else:
            amat_p = np.stack([x3[:, :, 0], x3[:, :, 1], ones], axis=2)
            plane, degenerate = _batched_lstsq(amat_p, x3[:, :, 2:3], rows)
            frames = tangent_frames(plane[:, :2, 0])
        x_loc = np.matmul(x3, frames)  # padded rows stay zero
        d_loc = np.matmul(d3, frames)
        amat_g = np.stack([x_loc[:, :, 0], x_loc[:, :, 1], ones], axis=2)
        grad, degen_g = _batched_lstsq(amat_g, d_loc, rows)
        degenerate = degenerate | degen_g
        coef[nodes, 0] = grad[:, 0]
        coef[nodes, 1] = grad[:, 1]
        coef[nodes, 2] = 0.0  # surface gauge: out-of-plane derivative dropped

    return [
        (int(nodes[pos]), idx_map[nbr_ok[pos][~pad[pos]]]) for pos in np.flatnonzero(degenerate)
    ]


def _fit_numba(
    coef: NDArray[np.float64],
    idx_map: NDArray[np.int64],
    nbr: NDArray[np.int64],
    counts: NDArray[np.int64],
    finite: NDArray[np.bool_],
    ref_3d: NDArray[np.float64],
    disp: NDArray[np.float64],
    coordinate: str,
    specimen_R: NDArray[np.float64] | None,
    min_neighbors: int,
) -> list[tuple[int, NDArray[np.int64]]]:
    """Numba closed-form engine (R3): fills ``coef`` for all fit-worthy nodes.

    Same return contract as :func:`_fit_batched`; nodes the kernel flags as
    (near-)degenerate are left for the exact per-node lstsq fallback.
    """
    if coordinate == "camera0":
        mode = _kernels.MODE_CAMERA0
    elif coordinate == "specific" and specimen_R is not None:
        mode = _kernels.MODE_SPECIFIC
    else:
        mode = _kernels.MODE_LOCAL
    rmat = specimen_R if mode == _kernels.MODE_SPECIFIC else np.eye(3)
    coef_f, degen = _kernels.fit_kernel(
        ref_3d[finite], disp[finite], nbr, counts, min_neighbors, mode, rmat
    )
    coef[idx_map] = coef_f
    return [(int(idx_map[pos]), idx_map[nbr[pos, : counts[pos]]]) for pos in np.flatnonzero(degen)]


def fit_gradients(
    ref_2d: NDArray[np.float64],
    ref_3d: NDArray[np.float64],
    disp: NDArray[np.float64],
    vsg_radius: float,
    *,
    coordinate: str = "local",
    specimen_R: NDArray[np.float64] | None = None,
    min_neighbors: int = MIN_NEIGHBORS,
    neighbor_cache: dict | None = None,
    engine: str = "auto",
) -> NDArray[np.float64]:
    """Per-node displacement-gradient matrices ``(n, 3, 3)`` = ``d(disp_j)/d(axis_i)``.

    Args:
        ref_2d: ``(n, 2)`` reference node coords in the left image (VSG search space).
        ref_3d: ``(n, 3)`` reference 3D world coords (Lagrangian fit).
        disp: ``(n, 3)`` cumulative displacement.
        vsg_radius: Chebyshev (square-window) radius in pixels = ``0.5*strain_length``.
        coordinate: ``"local"`` (per-node tangent frame, default), ``"camera0"`` (world
            frame, keeps the z-derivative row), or ``"specific"`` (fixed ``specimen_R``).
        specimen_R: ``(3, 3)`` specimen frame for ``coordinate="specific"``.
        neighbor_cache: optional dict reused across frames of one run so the
            neighbour table is built once per validity pattern (P3.5); the
            caller must key its lifetime to fixed ``ref_2d``/``vsg_radius``.
        engine: ``"auto"`` (Numba kernel when numba imports, else the batched
            SVD path — the default), ``"numba"`` (require the kernel), or
            ``"batched"`` (force the P3.5 batched-SVD path).

    Returns:
        ``(n, 3, 3)`` with rows = derivative axis, columns = displacement component;
        ``NaN`` rows for void nodes (fewer than ``min_neighbors`` finite neighbours).
    """
    if engine not in ("auto", "numba", "batched"):
        raise ValueError(f"unknown engine {engine!r}; expected 'auto', 'numba' or 'batched'")
    if engine == "auto":
        engine = "numba" if _kernels.HAS_NUMBA else "batched"
    elif engine == "numba" and not _kernels.HAS_NUMBA:
        raise RuntimeError("engine='numba' requested but numba is not importable")

    ref_2d = np.asarray(ref_2d, dtype=np.float64).reshape(-1, 2)
    ref_3d = np.asarray(ref_3d, dtype=np.float64).reshape(-1, 3)
    disp = np.asarray(disp, dtype=np.float64).reshape(-1, 3)
    n = ref_2d.shape[0]

    finite = np.isfinite(ref_2d).all(1) & np.isfinite(ref_3d).all(1) & np.isfinite(disp).all(1)
    coef = np.full((n, 3, 3), np.nan, dtype=np.float64)
    if finite.sum() < min_neighbors:
        return coef

    idx_map, nbr, counts = _neighbor_table(ref_2d, finite, vsg_radius, neighbor_cache)
    ok = counts >= min_neighbors
    if not ok.any():
        return coef

    if engine == "numba":
        fallback = _fit_numba(
            coef, idx_map, nbr, counts, finite, ref_3d, disp, coordinate, specimen_R, min_neighbors
        )
    else:
        fallback = _fit_batched(
            coef, idx_map, nbr, counts, ok, finite, ref_3d, disp, coordinate, specimen_R
        )

    # Exact-parity fallback: rank-deficient / near-cutoff systems rerun the
    # original per-node lstsq path (same neighbour sets).
    for node, sel in fallback:
        _fit_node_into(coef, node, sel, ref_3d, disp, coordinate, specimen_R)

    return coef


# Strain measures supported by :func:`strain_tensor` (Q3, 2D apply_strain_type
# parity): all derived from the SAME displacement-gradient fit, in the SAME
# tangent frame — only the finite-strain measure changes.
STRAIN_TYPES = ("green_lagrange", "infinitesimal", "almansi")


def strain_tensor(
    coefficients: NDArray[np.float64], strain_type: str = "green_lagrange"
) -> dict[str, NDArray[np.float64]]:
    """Strain + invariants from gradient matrices, for a selectable measure.

    ``coefficients`` is ``(n, 3, 3)`` with rows = derivative axis, columns =
    displacement component, so the displacement-gradient tensor is
    ``G = coefficients^T`` and ``F = I + G``. Measures (2D
    ``apply_strain_type.m`` port, evaluated on the full 3x3 tangent-frame
    tensor):

    * ``green_lagrange`` (default): ``E = 0.5 (F^T F - I)``.
    * ``infinitesimal``: ``e = 0.5 (G + G^T)``.
    * ``almansi`` (Eulerian-Almansi): ``e = 0.5 (I - F^{-T} F^{-1})``;
      nodes with a singular ``F`` come out ``NaN``.

    Returns the nine :data:`STRAIN_FIELDS` arrays, each ``(n,)`` with ``NaN``
    where the gradient is ``NaN`` (void nodes).
    """
    if strain_type not in STRAIN_TYPES:
        raise ValueError(f"unknown strain_type {strain_type!r}; expected one of {STRAIN_TYPES}")
    coef = np.asarray(coefficients, dtype=np.float64).reshape(-1, 3, 3)
    eye = np.eye(3)
    grad = np.transpose(coef, (0, 2, 1))  # G[i, j] = d(disp_i)/d(axis_j)
    if strain_type == "infinitesimal":
        e = 0.5 * (grad + np.transpose(grad, (0, 2, 1)))
    elif strain_type == "almansi":
        f = eye[None] + grad
        e = np.full_like(f, np.nan)
        finite = np.isfinite(f).all(axis=(1, 2))
        ok = finite.copy()
        ok[finite] &= np.abs(np.linalg.det(f[finite])) > np.finfo(np.float64).tiny
        if ok.any():
            f_inv = np.linalg.inv(f[ok])
            e[ok] = 0.5 * (eye - np.transpose(f_inv, (0, 2, 1)) @ f_inv)
    else:  # green_lagrange
        f = eye[None] + grad
        e = 0.5 * (np.transpose(f, (0, 2, 1)) @ f - eye)

    exx = e[:, 0, 0]
    eyy = e[:, 1, 1]
    exy = e[:, 0, 1]
    dwdx = coef[:, 0, 2]  # w_x
    dwdy = coef[:, 1, 2]  # w_y
    max_shear = np.sqrt((0.5 * (exx - eyy)) ** 2 + exy**2)
    mean = 0.5 * (exx + eyy)
    e1 = mean + max_shear
    e2 = mean - max_shear
    von_mises = np.sqrt(e1**2 + e2**2 - e1 * e2 + 3 * max_shear**2)
    return {
        "exx": exx,
        "eyy": eyy,
        "exy": exy,
        "e1": e1,
        "e2": e2,
        "max_shear": max_shear,
        "von_mises": von_mises,
        "dwdx": dwdx,
        "dwdy": dwdy,
    }


def green_lagrange_strain(coefficients: NDArray[np.float64]) -> dict[str, NDArray[np.float64]]:
    """Green-Lagrange strain + invariants (historical name; see :func:`strain_tensor`)."""
    return strain_tensor(coefficients, "green_lagrange")
