"""Analytic-field validation of al_dic_3d.strain3d (Phase 3 gate).

Strain is computed directly on synthetic node clouds with a KNOWN answer:
  - rigid rotation -> zero Green-Lagrange strain (rotation invariance);
  - uniaxial stretch on a flat plane -> exx = eps + eps^2/2;
  - uniaxial (axial) stretch on a cylinder -> eyy = eps + eps^2/2 in the tangent
    frame (tests the local plane fit on a curved surface).
Plus unit tests of the strain formula and tangent frame.
"""

from __future__ import annotations

import numpy as np

from al_dic_3d.matching.contracts import TRACKED
from al_dic_3d.reconstruct import Reconstruction3D
from al_dic_3d.strain3d import (
    compute_surface_strain,
    green_lagrange_strain,
    specimen_frame,
    tangent_frame,
)

Z0 = 800.0


def _recon(ref_3d: np.ndarray, disp1: np.ndarray) -> Reconstruction3D:
    """A 2-frame reconstruction: frame 0 = reference, frame 1 = reference + disp1."""
    points = np.stack([ref_3d, ref_3d + disp1])
    displacement = points - points[0][None]
    reproj = np.zeros(points.shape[:2])
    source = np.full(points.shape[:2], TRACKED, np.uint8)
    return Reconstruction3D(points, displacement, reproj, source)


def _grid(nx: int = 17, ny: int = 17, step_px: float = 16.0, step_mm: float = 2.0):
    ii, jj = np.meshgrid(np.arange(nx), np.arange(ny))
    ii = ii.ravel()
    jj = jj.ravel()
    ref_2d = np.column_stack([ii * step_px + 40.0, jj * step_px + 40.0])
    xw = (ii - (nx - 1) / 2.0) * step_mm
    yw = (jj - (ny - 1) / 2.0) * step_mm
    interior = (ii >= 3) & (ii <= nx - 4) & (jj >= 3) & (jj <= ny - 4)
    return ref_2d, xw, yw, interior


def test_green_lagrange_formula_uniaxial():
    # coef row0 = d/dx of [U,V,W]; uniaxial dU/dx = eps -> exx = eps + eps^2/2.
    eps = 0.02
    coef = np.zeros((1, 3, 3))
    coef[0, 0, 0] = eps
    s = green_lagrange_strain(coef)
    assert abs(s["exx"][0] - (eps + 0.5 * eps**2)) < 1e-12
    assert abs(s["eyy"][0]) < 1e-12 and abs(s["exy"][0]) < 1e-12


def test_tangent_frame_flat_is_world_axes():
    r = tangent_frame((0.0, 0.0))  # flat plane -> z_hat = [0,0,-1]
    assert np.allclose(np.abs(r[:, 2]), [0, 0, 1])
    assert np.allclose(r.T @ r, np.eye(3), atol=1e-12)  # orthonormal


def test_rigid_rotation_gives_zero_strain():
    ref_2d, xw, yw, interior = _grid()
    ref_3d = np.column_stack([xw, yw, np.full_like(xw, Z0)])
    th = np.deg2rad(8.0)
    rot = np.array([[np.cos(th), -np.sin(th), 0], [np.sin(th), np.cos(th), 0], [0, 0, 1.0]])
    disp = ref_3d @ rot.T - ref_3d  # rigid rotation about Z

    strain = compute_surface_strain(_recon(ref_3d, disp), ref_2d, strain_size=5, winstepsize=16)
    for comp in ("exx", "eyy", "exy"):
        vals = getattr(strain, comp)[1][interior]
        assert np.nanmax(np.abs(vals)) < 1e-9, f"{comp} not zero under rigid rotation"


def test_uniaxial_stretch_on_plane():
    eps = 0.02
    ref_2d, xw, yw, interior = _grid()
    ref_3d = np.column_stack([xw, yw, np.full_like(xw, Z0)])
    disp = np.column_stack([eps * xw, np.zeros_like(xw), np.zeros_like(xw)])

    strain = compute_surface_strain(_recon(ref_3d, disp), ref_2d, strain_size=5, winstepsize=16)
    exx = strain.exx[1][interior]
    expected = eps + 0.5 * eps**2
    assert np.nanmax(np.abs(exx - expected)) < 1e-6
    assert np.nanmax(np.abs(strain.eyy[1][interior])) < 1e-6
    assert np.nanmax(np.abs(strain.exy[1][interior])) < 1e-6


def test_uniaxial_axial_stretch_on_cylinder():
    # Cylinder about the world Y axis (straight along Y); stretch ALONG the axis.
    eps = 0.02
    r_cyl = 400.0
    ref_2d, xw, yw, interior = _grid()
    theta = xw / r_cyl  # arc angle from the X material coordinate
    ref_3d = np.column_stack([r_cyl * np.sin(theta), yw, Z0 - r_cyl * (1 - np.cos(theta))])
    disp = np.column_stack([np.zeros_like(yw), eps * yw, np.zeros_like(yw)])  # axial stretch

    strain = compute_surface_strain(_recon(ref_3d, disp), ref_2d, strain_size=5, winstepsize=16)
    expected = eps + 0.5 * eps**2
    eyy = strain.eyy[1][interior]
    # Axis is straight -> the plane fit captures the axial stretch accurately.
    assert np.nanmedian(np.abs(eyy - expected)) < 0.02 * expected + 5e-5
    assert np.nanmedian(np.abs(strain.exx[1][interior])) < 1e-3


def test_specimen_frame_from_base_points():
    nx = 17
    ref_2d, xw, yw, _ = _grid(nx=nx, ny=nx)
    ref_3d = np.column_stack([xw, yw, np.full_like(xw, Z0)])
    # O = centre node, +X = node to the right, +Y = node above (world +X / +Y).
    o_i, x_i, y_i = 8 * nx + 8, 8 * nx + 9, 9 * nx + 8
    r, t = specimen_frame(ref_2d, ref_3d, ref_2d[[o_i, x_i, y_i]])
    assert np.allclose(r.T @ r, np.eye(3), atol=1e-9)  # orthonormal frame
    assert np.allclose(r[:, 0], [1.0, 0.0, 0.0], atol=1e-9)  # x_hat along world +X
    assert np.allclose(t, ref_3d[o_i])


def test_specimen_frame_out_of_hull_base_point_does_not_raise():
    # A base point just outside the node hull is nearest-filled (GetRTMatrix.m
    # extrapolates), so a finite orthonormal frame is still returned.
    nx = 17
    ref_2d, xw, yw, _ = _grid(nx=nx, ny=nx)
    ref_3d = np.column_stack([xw, yw, np.full_like(xw, Z0)])
    base = np.array([ref_2d[8 * nx + 8], ref_2d[8 * nx + 9], [10000.0, 10000.0]])
    r, t = specimen_frame(ref_2d, ref_3d, base)
    assert np.isfinite(r).all() and np.isfinite(t).all()
    assert np.allclose(r.T @ r, np.eye(3), atol=1e-9)


def test_void_nodes_are_nan():
    # A handful of isolated points (fewer than 9 neighbours) -> NaN strain.
    ref_2d = np.array([[0.0, 0.0], [500.0, 0.0], [0.0, 500.0]])
    ref_3d = np.column_stack([ref_2d[:, 0], ref_2d[:, 1], np.full(3, Z0)])
    disp = np.zeros((3, 3))
    strain = compute_surface_strain(_recon(ref_3d, disp), ref_2d, strain_size=5, winstepsize=16)
    assert np.isnan(strain.exx[1]).all()
