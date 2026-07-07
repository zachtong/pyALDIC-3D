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
