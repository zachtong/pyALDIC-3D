"""Drive a whole ``Reconstruction3D`` through surface-strain (Qt-free).

Per frame: (optionally smooth the displacement,) fit local tangent-frame
displacement gradients, and reduce to Green-Lagrange strain + invariants. The VSG
is a square pixel window of side ``strain_length = (strain_size-1)*winstepsize+1``
(docs/strain3d_math.md §1). Downstream of ``reconstruct``; consumes only the
``Reconstruction3D`` + the reference 2D node coords.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.strain3d.gradients import MIN_NEIGHBORS, fit_gradients, green_lagrange_strain
from al_dic_3d.strain3d.model import STRAIN_FIELDS, StrainResult3D

if TYPE_CHECKING:
    from al_dic_3d.reconstruct import Reconstruction3D


def smooth_displacement(
    ref_2d: NDArray[np.float64],
    disp: NDArray[np.float64],
    sigma: float,
) -> NDArray[np.float64]:
    """NaN-aware Gaussian smoothing of a scattered displacement field (funSmoothDisp idea).

    Row-normalized Gaussian weights over the ``3*sigma`` pixel neighbourhood (in the
    reference image), applied per component. Invalid (NaN) nodes neither contribute
    nor receive an estimate.
    """
    from scipy.spatial import cKDTree

    ref_2d = np.asarray(ref_2d, dtype=np.float64).reshape(-1, 2)
    disp = np.asarray(disp, dtype=np.float64).reshape(-1, 3)
    out = np.full_like(disp, np.nan)
    finite = np.isfinite(disp).all(axis=1) & np.isfinite(ref_2d).all(axis=1)
    if not finite.any():
        return out

    src_idx = np.where(finite)[0]
    tree = cKDTree(ref_2d[finite])
    for i in src_idx:
        nbr = tree.query_ball_point(ref_2d[i], r=3.0 * sigma, p=2)
        if not nbr:
            out[i] = disp[i]
            continue
        sel = src_idx[nbr]
        d2 = np.sum((ref_2d[sel] - ref_2d[i]) ** 2, axis=1)
        w = np.exp(-d2 / (2.0 * sigma**2))
        out[i] = (w[:, None] * disp[sel]).sum(axis=0) / w.sum()
    return out


def compute_surface_strain(
    reconstruction: Reconstruction3D,
    ref_2d: NDArray[np.float64],
    *,
    strain_size: int = 5,
    winstepsize: int = 16,
    coordinate: str = "local",
    specimen_R: NDArray[np.float64] | None = None,
    min_neighbors: int = MIN_NEIGHBORS,
    smooth_sigma: float = 0.0,
) -> StrainResult3D:
    """Compute Green-Lagrange surface strain for every frame of a reconstruction.

    Args:
        reconstruction: the 3D points/displacement (``points[0]`` = reference surface).
        ref_2d: ``(n_pts, 2)`` reference node coords in the left image (VSG search).
        strain_size: VSG size in grid steps (odd). ``strain_length =
            (strain_size-1)*winstepsize+1`` px; the gauge radius is half of that.
        winstepsize: node grid spacing in pixels.
        coordinate: ``"local"`` (default), ``"camera0"``, or ``"specific"``.
        specimen_R: specimen frame for ``coordinate="specific"``.
        smooth_sigma: if > 0, Gaussian-smooth the displacement first (px).

    Returns:
        A :class:`StrainResult3D`; frame 0 is all-zero strain (zero displacement).
    """
    ref_2d = np.asarray(ref_2d, dtype=np.float64).reshape(-1, 2)
    ref_3d = np.asarray(reconstruction.points[0], dtype=np.float64)
    n_frames, n_pts = reconstruction.n_frames, reconstruction.n_pts

    strain_length = (strain_size - 1) * winstepsize + 1
    vsg_radius = 0.5 * strain_length

    fields = {name: np.full((n_frames, n_pts), np.nan, dtype=np.float64) for name in STRAIN_FIELDS}
    for k in range(n_frames):
        disp = np.asarray(reconstruction.displacement[k], dtype=np.float64)
        if smooth_sigma > 0:
            disp = smooth_displacement(ref_2d, disp, smooth_sigma)
        coef = fit_gradients(
            ref_2d,
            ref_3d,
            disp,
            vsg_radius,
            coordinate=coordinate,
            specimen_R=specimen_R,
            min_neighbors=min_neighbors,
        )
        strain = green_lagrange_strain(coef)
        for name in STRAIN_FIELDS:
            fields[name][k] = strain[name]

    return StrainResult3D(**fields)
