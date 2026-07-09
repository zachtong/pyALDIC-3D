"""Quad surface connectivity from the regular reference grid (numpy-only).

The frame-1 reference mesh nodes (``RunResult.ref_coords``) lie on a regular
``winstepsize`` lattice, so the reconstructed surface has a natural quad
topology that is far cleaner than a Delaunay triangulation of the scattered 3D
points. This module infers that lattice and builds the shared ``(n_cells, 4)``
connectivity that BOTH the interactive ``View3D`` widget and the VTU exporter
consume — tolerant of missing nodes (masked ROI holes, gated points) and of
off-lattice nodes (quadtree-refined meshes contribute no quads but break
nothing).

:func:`build_surface_polydata` (F3.2) is the ONE surface builder shared by the
interactive ``View3D`` widget and the offscreen 3D exporter, so what the user
sees and what gets exported are the same geometry. It honors the drawn ROI
mask (cells outside it are dropped, exactly like the 2D dense view's knockout)
and its Delaunay fallback is edge-capped so it can never span ROI holes.

Qt-free (architecture test enforced); pyvista appears only as a lazy
in-function import behind the ``[viz3d]`` extra.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

# Cells with an edge longer than this multiple of the node step are dropped by
# :func:`filter_cells_edge_cap`: Delaunay spans node-free ROI holes with long
# triangles, and without the cap those holes get filled instead of staying
# transparent (F1.5). 2.5x leaves regular grids (longest edge = sqrt(2) x step)
# and moderately distorted disparity-warped clouds untouched.
MAX_EDGE_FACTOR = 2.5


def median_nn_spacing(pts: NDArray[np.float64]) -> float:
    """Median nearest-neighbor distance — the de-facto node step of a cloud."""
    if pts.shape[0] < 2:
        return 0.0
    from scipy.spatial import cKDTree

    dist, _ = cKDTree(pts).query(pts, k=2)
    return float(np.median(dist[:, 1]))


def _lattice_indices(coords: NDArray[np.float64], tol: float) -> NDArray[np.int64] | None:
    """Snap one coordinate axis onto its inferred regular lattice.

    Returns per-node integer lattice indices with ``-1`` for off-lattice nodes
    (e.g. quadtree-refined half-step nodes), or ``None`` when no lattice exists
    (fewer than 2 distinct values / zero step).
    """
    values = np.unique(coords)
    if values.size < 2:
        return None
    steps = np.diff(values)
    steps = steps[steps > 0]
    if steps.size == 0:
        return None
    # Modal spacing (ties -> the larger one): robust when a minority of nodes
    # sits at refined half-steps, which would drag a median/min estimate down
    # and de-lattice the regular majority.
    uniq, counts = np.unique(np.round(steps, 6), return_counts=True)
    step = float(uniq[counts == counts.max()].max())
    if step <= 0:
        return None
    idx_f = (coords - values[0]) / step
    idx = np.rint(idx_f).astype(np.int64)
    off_lattice = np.abs(idx_f - idx) > tol
    idx[off_lattice] = -1
    return idx


def build_quad_connectivity(
    ref_coords: NDArray[np.float64], *, tol: float = 0.25
) -> NDArray[np.int64]:
    """Quad cells over a regular 2D node grid, tolerant of missing nodes.

    Args:
        ref_coords: ``(n_pts, 2)`` reference pixel coordinates of the mesh
            nodes (a regular ``winstepsize`` grid, possibly with holes).
        tol: lattice-snap tolerance as a fraction of the inferred step; nodes
            further off the lattice (refined half-step nodes) join no quad.

    Returns:
        ``(n_cells, 4)`` int64 node indices, corners ordered counter-clockwise
        ``(i, j) -> (i+1, j) -> (i+1, j+1) -> (i, j+1)``. Empty ``(0, 4)`` when
        no lattice can be inferred or no complete quad exists.
    """
    coords = np.asarray(ref_coords, dtype=np.float64).reshape(-1, 2)
    empty = np.empty((0, 4), dtype=np.int64)
    if coords.shape[0] < 4:
        return empty
    ix = _lattice_indices(coords[:, 0], tol)
    iy = _lattice_indices(coords[:, 1], tol)
    if ix is None or iy is None:
        return empty

    on_lattice = (ix >= 0) & (iy >= 0)
    lattice: dict[tuple[int, int], int] = {}
    for node in np.flatnonzero(on_lattice):
        lattice.setdefault((int(ix[node]), int(iy[node])), int(node))

    quads: list[tuple[int, int, int, int]] = []
    for (i, j), n00 in lattice.items():
        n10 = lattice.get((i + 1, j))
        n11 = lattice.get((i + 1, j + 1))
        n01 = lattice.get((i, j + 1))
        if n10 is not None and n11 is not None and n01 is not None:
            quads.append((n00, n10, n11, n01))
    if not quads:
        return empty
    return np.asarray(sorted(quads), dtype=np.int64)


def filter_cells_finite(cells: NDArray[np.int64], points: NDArray[np.float64]) -> NDArray[np.int64]:
    """Drop cells touching any non-finite (NaN = invalid) point.

    Args:
        cells: ``(n_cells, k)`` node indices.
        points: ``(n_pts, d)`` coordinates; a row with any NaN invalidates
            every cell referencing it.
    """
    cells = np.asarray(cells, dtype=np.int64)
    if cells.size == 0:
        return cells.reshape(0, cells.shape[1] if cells.ndim == 2 else 4)
    finite = np.isfinite(np.asarray(points, dtype=np.float64)).all(axis=1)
    return cells[finite[cells].all(axis=1)]


def nodes_in_mask(coords: NDArray[np.float64], mask: NDArray[np.bool_]) -> NDArray[np.bool_]:
    """Per-node boolean: node's nearest pixel lies inside the boolean mask.

    Non-finite or out-of-image nodes are False (outside). ``coords`` are
    ``(n, 2)`` reference pixel ``[x, y]``.
    """
    m = np.asarray(mask) > 0
    h, w = m.shape
    xy = np.nan_to_num(np.asarray(coords, dtype=np.float64).reshape(-1, 2), nan=-1.0)
    ix = np.round(xy[:, 0]).astype(int)
    iy = np.round(xy[:, 1]).astype(int)
    in_bounds = (ix >= 0) & (ix < w) & (iy >= 0) & (iy < h)
    out = np.zeros(xy.shape[0], dtype=bool)
    out[in_bounds] = m[iy[in_bounds], ix[in_bounds]]
    return out


def filter_cells_by_mask(
    cells: NDArray[np.int64],
    ref_coords: NDArray[np.float64],
    mask: NDArray[np.bool_],
) -> NDArray[np.int64]:
    """Drop cells with any corner — or the centroid — outside the ROI mask.

    The 3D-view equivalent of the 2D dense render's mask knockout: a drawn ROI
    hole removes every cell touching it, so the surface outline matches the 2D
    field instead of the rectangular node lattice. The centroid check also
    kills cells straddling holes narrower than one cell.
    """
    cells = np.asarray(cells, dtype=np.int64)
    if cells.size == 0:
        return cells
    inside = nodes_in_mask(ref_coords, mask)
    keep = inside[cells].all(axis=1)
    if keep.any():
        centroids = np.asarray(ref_coords, dtype=np.float64)[cells].mean(axis=1)
        keep &= nodes_in_mask(centroids, mask)
    return cells[keep]


def filter_cells_edge_cap(
    cells: NDArray[np.int64],
    coords: NDArray[np.float64],
    *,
    step: float | None = None,
    max_factor: float = MAX_EDGE_FACTOR,
) -> NDArray[np.int64]:
    """Drop cells whose longest edge exceeds ``max_factor x`` the node step.

    The F1.5 hole-spanning guard for triangulated fallbacks: Delaunay bridges
    node-free ROI holes with long triangles; capping the edge length keeps
    holes open. ``coords`` may be 2D (reference plane) or 3D; ``step`` defaults
    to the median nearest-neighbor spacing of the referenced nodes.
    """
    cells = np.asarray(cells, dtype=np.int64)
    if cells.size == 0:
        return cells
    pts = np.asarray(coords, dtype=np.float64)[cells]  # (n_cells, k, d)
    edges = pts - np.roll(pts, 1, axis=1)
    longest = np.sqrt((edges**2).sum(axis=2)).max(axis=1)
    if step is None:
        used = np.unique(cells)
        step = median_nn_spacing(np.asarray(coords, dtype=np.float64)[used])
    if step <= 0.0:
        return cells
    return cells[longest <= max_factor * float(step)]


def build_tri_connectivity(
    coords: NDArray[np.float64], usable: NDArray[np.bool_] | None = None
) -> NDArray[np.int64]:
    """Delaunay triangles over the usable rows; indices refer to ALL rows.

    Returns ``(n_tri, 3)`` int64, empty on degenerate (collinear / too few)
    input — the caller decides how to degrade.
    """
    coords = np.asarray(coords, dtype=np.float64)
    if usable is None:
        usable = np.isfinite(coords).all(axis=1)
    idx = np.flatnonzero(usable)
    empty = np.empty((0, 3), dtype=np.int64)
    if idx.size < 3:
        return empty
    from scipy.spatial import Delaunay, QhullError

    try:
        tri = Delaunay(coords[idx])
    except QhullError:
        return empty
    return idx[tri.simplices].astype(np.int64)


def build_surface_polydata(
    points_3d: NDArray[np.float64],
    values: NDArray[np.float64],
    name: str,
    ref_coords: NDArray[np.float64] | None = None,
    roi_mask: NDArray[np.bool_] | None = None,
):
    """The shared 3D surface (``pv.PolyData``) — View3D and the exporter use THIS.

    Construction (holed-ROI faithful, F3.2):

    1. **Quad path** — regular-grid quads from ``ref_coords``; cells touching a
       NaN point / NaN scalar / a node outside ``roi_mask`` are dropped, so ROI
       holes stay open exactly like the 2D dense view.
    2. **Capped triangulated fallback** — when no quad lattice exists (refined
       or degenerate meshes), Delaunay in the reference plane (or the XY of the
       finite points when ``ref_coords`` is absent) with the F1.5 edge-length
       cap and the same mask filter — it can never span a hole.
    3. **Point cloud** — when no cell survives; ``None`` when fewer than 3
       usable points exist (nothing to render).
    """
    import pyvista as pv

    pts = np.asarray(points_3d, dtype=np.float64).reshape(-1, 3)
    vals = np.asarray(values, dtype=np.float64).reshape(-1)
    usable = np.isfinite(pts).all(axis=1) & np.isfinite(vals)
    ref = None
    if ref_coords is not None:
        ref = np.asarray(ref_coords, dtype=np.float64).reshape(-1, 2)
        if roi_mask is not None:
            usable &= nodes_in_mask(ref, roi_mask)
    if usable.sum() < 3:
        return None

    cells = np.empty((0, 4), dtype=np.int64)
    if ref is not None:
        cells = build_quad_connectivity(ref)
        if roi_mask is not None:
            cells = filter_cells_by_mask(cells, ref, roi_mask)
        if len(cells):
            cells = cells[usable[cells].all(axis=1)]

    if len(cells) == 0:
        # Fallback: triangulate in the reference plane first (holes live
        # there); a degenerate ref lattice degrades to the finite points' XY.
        for plane in ([ref] if ref is not None else []) + [pts[:, :2]]:
            tris = build_tri_connectivity(plane, usable)
            tris = filter_cells_edge_cap(tris, plane)
            if roi_mask is not None and ref is not None:
                tris = filter_cells_by_mask(tris, ref, roi_mask)
            if len(tris):
                cells = tris
                break
        if len(cells) == 0:
            cloud = pv.PolyData(pts[usable])
            cloud[name] = vals[usable]
            return cloud

    used = np.unique(cells)
    remap = np.zeros(len(pts), dtype=np.int64)
    remap[used] = np.arange(len(used))
    surf = pv.PolyData(pts[used], faces=as_vtk_faces(remap[cells]))
    surf[name] = vals[used]
    return surf


def as_vtk_faces(cells: NDArray[np.int64]) -> NDArray[np.int64]:
    """Flatten ``(n_cells, k)`` connectivity to VTK's ``[k, i0..ik-1, ...]`` form.

    The same layout serves ``pyvista.PolyData.faces`` and the legacy-style
    ``pyvista.UnstructuredGrid`` cell array.
    """
    cells = np.asarray(cells, dtype=np.int64)
    if cells.size == 0:
        return np.empty(0, dtype=np.int64)
    sizes = np.full((cells.shape[0], 1), cells.shape[1], dtype=np.int64)
    return np.hstack([sizes, cells]).ravel()
