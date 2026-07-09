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
    # Invalid points never enter the mesh (the F1.5 edge cap may drop a few
    # more boundary vertices of this sparse random cloud — that is intended).
    assert 3 <= surf.n_points <= 48
    assert np.isfinite(surf.points).all()
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


def _holed_scene(nx: int = 14, ny: int = 12, step: float = 16.0):
    """A regular ref lattice + a drawn ROI mask with a circular hole.

    The hole nodes still EXIST and carry finite 3D points (the real failure
    mode: the engine launders masked nodes into finite values), so only the
    mask can keep the hole open.
    """
    xs = 100.0 + step * np.arange(nx)
    ys = 60.0 + step * np.arange(ny)
    gx, gy = np.meshgrid(xs, ys)
    ref = np.column_stack([gx.ravel(), gy.ravel()])
    pts = np.column_stack([ref * 0.1, np.full(len(ref), 800.0)])
    vals = pts[:, 0].copy()

    cx, cy = float(xs.mean()), float(ys.mean())
    hole_r = 2.2 * step
    mask = np.zeros((500, 500), dtype=bool)
    mask[40 : int(ys[-1]) + 20, 80 : int(xs[-1]) + 20] = True
    yy, xx = np.mgrid[0:500, 0:500]
    mask[(xx - cx) ** 2 + (yy - cy) ** 2 <= hole_r**2] = False
    return ref, pts, vals, mask, (cx, cy), hole_r


def _face_corners(surf) -> np.ndarray:
    """(n_cells, k, 3) corner coordinates of a PolyData with uniform faces."""
    faces = surf.faces
    k = int(faces[0])
    return np.asarray(surf.points)[faces.reshape(-1, k + 1)[:, 1:]]


def test_holed_roi_mask_keeps_hole_open_in_quads():
    ref, pts, vals, mask, (cx, cy), hole_r = _holed_scene()

    surf = build_surface_mesh(pts, vals, "U", ref, roi_mask=mask)
    assert surf is not None and surf.n_cells > 0
    corners = _face_corners(surf)
    assert corners.shape[1] == 4  # quad path
    # Map 3D corners back to reference pixels (x3d = ref * 0.1) and assert NO
    # cell touches the hole interior — the 3D shape matches the 2D dense view.
    ref_xy = corners[:, :, :2] / 0.1
    d = np.sqrt((ref_xy[:, :, 0] - cx) ** 2 + (ref_xy[:, :, 1] - cy) ** 2)
    assert (d.min(axis=1) > hole_r - 1.0).all()

    # Control: WITHOUT the mask the (finite) hole nodes fill the hole — the
    # exact E1 bug the mask filter fixes.
    surf_nomask = build_surface_mesh(pts, vals, "U", ref)
    corners_nm = _face_corners(surf_nomask)
    ref_nm = corners_nm[:, :, :2] / 0.1
    d_nm = np.sqrt((ref_nm[:, :, 0] - cx) ** 2 + (ref_nm[:, :, 1] - cy) ** 2)
    assert (d_nm.min(axis=1) <= hole_r - 1.0).any()


def test_holed_fallback_never_spans_the_hole():
    # Jitter the lattice so no quad connectivity can be inferred -> the
    # triangulated fallback runs; the F1.5 edge cap + mask filter must keep
    # the hole open instead of bridging it with long Delaunay triangles.
    ref, pts, vals, mask, (cx, cy), hole_r = _holed_scene()
    rng = np.random.default_rng(3)
    ref = ref + rng.uniform(-4.0, 4.0, size=ref.shape)  # off-lattice everywhere
    pts = np.column_stack([ref * 0.1, np.full(len(ref), 800.0)])

    from al_dic_3d.viz3d import build_quad_connectivity

    assert len(build_quad_connectivity(ref)) == 0  # quad path really failed

    surf = build_surface_mesh(pts, vals, "U", ref, roi_mask=mask)
    assert surf is not None and surf.n_cells > 0
    corners = _face_corners(surf)
    assert corners.shape[1] == 3  # triangulated fallback
    centroids = corners.mean(axis=1)[:, :2] / 0.1
    d = np.sqrt((centroids[:, 0] - cx) ** 2 + (centroids[:, 1] - cy) ** 2)
    # No triangle centroid deep inside the hole (mask nodes gone + edge cap).
    assert (d > hole_r * 0.5).all()


def test_mask_helpers_are_pure_and_consistent():
    from al_dic_3d.viz3d import (
        build_quad_connectivity,
        filter_cells_by_mask,
        filter_cells_edge_cap,
        nodes_in_mask,
    )

    ref, _pts, _vals, mask, (cx, cy), _hole_r = _holed_scene()
    inside = nodes_in_mask(ref, mask)
    assert inside.any() and not inside.all()  # hole nodes excluded
    assert not nodes_in_mask(np.array([[np.nan, 5.0], [-3.0, 2.0]]), mask).any()

    quads = build_quad_connectivity(ref)
    kept = filter_cells_by_mask(quads, ref, mask)
    assert 0 < len(kept) < len(quads)
    # Edge cap: a regular grid survives untouched; stretching one node's
    # coordinate far away kills exactly the cells that touch it.
    assert len(filter_cells_edge_cap(quads, ref)) == len(quads)
    stretched = ref.copy()
    stretched[0] += 1000.0
    capped = filter_cells_edge_cap(quads, stretched)
    assert len(capped) < len(quads)


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
