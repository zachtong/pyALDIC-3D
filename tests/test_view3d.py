"""3D-view data pipeline (pyvista mesh builders) — headless, no GL required.

The QtInteractor render itself needs a real OpenGL context (verified on the
user's display); these tests cover the pure data path: point cloud -> surface
mesh with scalars, NaN filtering, and the camera-frustum wireframe geometry.
"""

from __future__ import annotations

import numpy as np
import pytest

pv = pytest.importorskip("pyvista")

from al_dic_3d.gui.widgets.view3d import build_surface_mesh, camera_frustum_lines  # noqa: E402


def _bump_cloud(n: int = 300, seed: int = 0):
    rng = np.random.default_rng(seed)
    xy = rng.uniform(-50, 50, size=(n, 2))
    z = 800.0 + 20.0 * np.exp(-(xy**2).sum(1) / 800.0)
    return np.column_stack([xy, z])


def test_surface_mesh_triangulates_with_scalars():
    pts = _bump_cloud()
    vals = pts[:, 0] * 0.01
    surf = build_surface_mesh(pts, vals, "U (mm)")
    assert surf is not None
    assert surf.n_cells > 0  # delaunay produced triangles
    assert "U (mm)" in surf.array_names
    assert surf.n_points <= len(pts)


def test_surface_mesh_filters_nan_points():
    pts = _bump_cloud(50)
    vals = np.linspace(0, 1, 50)
    pts[10] = np.nan  # invalid 3D point
    vals[20] = np.nan  # invalid scalar
    surf = build_surface_mesh(pts, vals, "f")
    assert surf is not None
    assert surf.n_points == 48
    assert np.isfinite(surf["f"]).all()


def test_surface_mesh_degenerate_returns_none():
    pts = np.full((5, 3), np.nan)
    assert build_surface_mesh(pts, np.zeros(5), "f") is None


def _regular_grid_cloud(nx: int = 5, ny: int = 4, step: float = 16.0):
    xs = 100.0 + step * np.arange(nx)
    ys = 50.0 + step * np.arange(ny)
    gx, gy = np.meshgrid(xs, ys)
    ref = np.column_stack([gx.ravel(), gy.ravel()])
    pts = np.column_stack([ref * 0.1, np.full(len(ref), 800.0)])
    return ref, pts


def test_surface_mesh_uses_regular_grid_quads():
    ref, pts = _regular_grid_cloud()
    vals = pts[:, 0] * 0.01
    surf = build_surface_mesh(pts, vals, "U", ref)
    assert surf.n_cells == (5 - 1) * (4 - 1)  # quad topology, not delaunay triangles
    assert (surf.faces.reshape(-1, 5)[:, 0] == 4).all()  # every cell is a quad
    assert np.isfinite(surf["U"]).all()


def test_surface_mesh_quads_drop_nan_and_fall_back():
    ref, pts = _regular_grid_cloud()
    vals = pts[:, 0] * 0.01
    pts[1 * 5 + 2] = np.nan  # interior node invalid -> its 4 quads dropped
    surf = build_surface_mesh(pts, vals, "U", ref)
    assert surf.n_cells == 12 - 4
    assert np.isfinite(surf.points).all()  # NaN vertices are not carried into the mesh
    # Without a usable lattice (collinear ref nodes) the builder yields nothing
    # and build_surface_mesh falls back to the delaunay triangulation.
    degenerate_ref = np.column_stack([np.arange(60.0), np.zeros(60)])
    pts2 = _bump_cloud(60, seed=2)
    surf2 = build_surface_mesh(pts2, pts2[:, 2], "f", degenerate_ref)
    assert surf2 is not None and surf2.n_cells > 0


def test_camera_frustum_geometry():
    th = np.deg2rad(18.0)
    R = np.array([[np.cos(th), 0, np.sin(th)], [0, 1, 0], [-np.sin(th), 0, np.cos(th)]])
    T = np.array([-250.0, 0.0, 30.0])
    frustum = camera_frustum_lines(R, T)
    assert frustum.n_points == 5  # apex + 4 corners
    apex = frustum.points[0]
    assert np.allclose(apex, -R.T @ T)  # apex at the camera center
    # all corners lie in front of the camera (positive z in camera frame)
    corners_cam = (np.asarray(frustum.points[1:]) - apex) @ R.T
    assert (corners_cam[:, 2] > 0).all()
