"""Cut the EXTERNAL reference mesh at thin crack barriers (Batch C, item 1).

The 2D engine cuts its INTERNAL FFT-built mesh at thin barriers
(``al_dic.mesh.mark_bridging``): an element whose bounding box holds >= 2 material
components split by a continuous masked band is dropped so FEM / global-step
elements never bridge a crack. Our external frame-1 mesh
(:func:`al_dic_3d.matching.temporal.build_grid_mesh` /
``runner._build_reference_mesh``) is NOT built by the engine, so we must apply the
same thin-barrier cut ourselves before handing the mesh to ``run_aldic``.

Reuses ``al_dic.mesh.mark_bridging.mark_bridging`` verbatim (see
docs/DEPENDS_ON_2D.md). Gated: with no thin barrier the mesh is returned
UNCHANGED (same object), so a hole-free / crack-free ROI is byte-identical.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
from al_dic.core.data_structures import DICMesh
from numpy.typing import NDArray


def bridging_elements(mesh: DICMesh, mask: NDArray[np.float64] | None) -> NDArray[np.bool_]:
    """Per-element bool: True where a continuous masked barrier locally cuts it.

    Empty (all-False) when ``mask`` is None or the mesh has no elements.
    """
    elements = np.asarray(mesh.elements_fem)
    if mask is None or elements.shape[0] == 0:
        return np.zeros(elements.shape[0], dtype=bool)
    from al_dic.mesh.mark_bridging import mark_bridging  # DEPENDS_ON_2D.md

    coords = np.asarray(mesh.coordinates_fem, dtype=np.float64)
    mask_f = np.ascontiguousarray(mask, dtype=np.float64)
    return mark_bridging(coords, elements, mask_f)


def mask_cuts_mesh(mesh: DICMesh, mask: NDArray[np.float64] | None) -> bool:
    """True iff ``mask`` carries a thin barrier that cuts at least one element."""
    return bool(bridging_elements(mesh, mask).any())


def cut_mesh_at_barriers(mesh: DICMesh, mask: NDArray[np.float64] | None) -> DICMesh:
    """Drop the elements a thin masked barrier bridges; keep all nodes.

    Returns the SAME mesh object when nothing is cut (no barrier / no mask), so
    crack-free runs stay byte-identical. Coordinates are untouched — orphaned
    nodes are harmless (the engine keeps its full node set too), so no
    re-indexing is needed.
    """
    bridging = bridging_elements(mesh, mask)
    if not bridging.any():
        return mesh
    kept = np.asarray(mesh.elements_fem)[~bridging]
    return replace(mesh, elements_fem=kept)
