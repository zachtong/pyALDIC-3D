"""Quad surface connectivity from the regular reference grid (numpy-only).

The frame-1 reference mesh nodes (``RunResult.ref_coords``) lie on a regular
``winstepsize`` lattice, so the reconstructed surface has a natural quad
topology that is far cleaner than a Delaunay triangulation of the scattered 3D
points. This module infers that lattice and builds the shared ``(n_cells, 4)``
connectivity that BOTH the interactive ``View3D`` widget and the VTU exporter
consume — tolerant of missing nodes (masked ROI holes, gated points) and of
off-lattice nodes (quadtree-refined meshes contribute no quads but break
nothing).

Qt-free and pyvista-free by design (architecture test enforced): callers wrap
the connectivity into their own pyvista/VTK structures.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


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
