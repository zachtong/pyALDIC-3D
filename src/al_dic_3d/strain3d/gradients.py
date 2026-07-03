"""Local displacement-gradient fit + Green-Lagrange strain (Qt-free).

Ports the math of ``PlaneFit3_Quadtree.m`` + ``computeStrain3D.m`` (see
docs/strain3d_math.md): a per-node VSG neighbourhood (square pixel window) →
local tangent frame from a plane fit on the reference 3D coords → plain
least-squares displacement gradients in that frame → deformation gradient →
Green-Lagrange strain. Pure numpy/scipy — no ``al_dic`` coupling.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

MIN_NEIGHBORS = 9  # minimum nodes in a VSG for a stable plane + gradient fit


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


def _lstsq(a: NDArray[np.float64], b: NDArray[np.float64]) -> NDArray[np.float64]:
    return np.linalg.lstsq(a, b, rcond=None)[0]


def fit_gradients(
    ref_2d: NDArray[np.float64],
    ref_3d: NDArray[np.float64],
    disp: NDArray[np.float64],
    vsg_radius: float,
    *,
    coordinate: str = "local",
    specimen_R: NDArray[np.float64] | None = None,
    min_neighbors: int = MIN_NEIGHBORS,
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

    Returns:
        ``(n, 3, 3)`` with rows = derivative axis, columns = displacement component;
        ``NaN`` rows for void nodes (fewer than ``min_neighbors`` finite neighbours).
    """
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
        sel = idx_map[local]
        x3 = ref_3d[sel]
        d3 = disp[sel]

        if coordinate == "camera0":
            amat = np.column_stack([x3, np.ones(len(sel))])
            coef[i] = _lstsq(amat, d3)[:3]  # rows [dX,dY,dZ], cols [U,V,W]
            continue

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

    return coef


def green_lagrange_strain(coefficients: NDArray[np.float64]) -> dict[str, NDArray[np.float64]]:
    """Green-Lagrange strain + invariants from gradient matrices (computeStrain3D.m).

    ``coefficients`` is ``(n, 3, 3)`` with rows = derivative axis, columns =
    displacement component. ``F = I + coefficients^T``; ``E = 0.5(F^T F - I)``.
    Returns the nine :data:`STRAIN_FIELDS` arrays, each ``(n,)`` with ``NaN`` where
    the gradient is ``NaN`` (void nodes).
    """
    coef = np.asarray(coefficients, dtype=np.float64).reshape(-1, 3, 3)
    eye = np.eye(3)
    f = eye[None] + np.transpose(coef, (0, 2, 1))  # F = I + coef^T
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
