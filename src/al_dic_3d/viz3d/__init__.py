"""Viz3D — interactive 3D visualization.

pyvista / pyvistaqt scenes: deformed surface with scalar coloring, camera
frustums, and timeline playback.

Heavy dependencies (pyvista, VTK) live behind the ``al-dic-3d[viz3d]`` optional
extra and MUST be imported lazily inside functions, never at module import time,
so the compute layer and headless CLI stay installable without them. The package
itself is Qt-free (architecture test enforced): Qt widgets that render these
scenes live in ``gui/``.

Layer: visualization (GUI).  Lands: Phase 4.  Spec: docs/architecture/01 §B.1, §F.
"""

from al_dic_3d.viz3d.surface import (
    as_vtk_faces,
    build_quad_connectivity,
    build_surface_polydata,
    build_tri_connectivity,
    filter_cells_by_mask,
    filter_cells_cross_barrier,
    filter_cells_edge_cap,
    filter_cells_finite,
    nodes_in_mask,
)

__all__ = [
    "as_vtk_faces",
    "build_quad_connectivity",
    "build_surface_polydata",
    "build_tri_connectivity",
    "filter_cells_by_mask",
    "filter_cells_cross_barrier",
    "filter_cells_edge_cap",
    "filter_cells_finite",
    "nodes_in_mask",
]
