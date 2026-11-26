"""Engine parameters that are provably dead weight for a given mesh (Qt-free).

The 2D engine smooths the IC-GN displacement field with a sparse Gaussian
before the global step and after every ADMM sub-problem 2 solve
(``al_dic.core.pipeline._smooth_disp`` -> ``al_dic.strain.smooth_field
.smooth_field_sparse``). The kernel width is ``sigma_i = h_i * 500 *
disp_smoothness`` per node, where ``h_i`` is the node's mean element edge
(``compute_node_local_spacing``: corner diagonal / sqrt(2), averaged over the
elements touching the node, midside nodes counted at half the edge), and the
neighbourhood is every node within ``3 * sigma_i`` (KD-tree ball query,
inclusive). With the default ``disp_smoothness = 5e-4`` that radius is
``0.75 * h_i``.

When no OTHER node lies inside any node's radius, each row of the row-normalised
weight matrix is the single diagonal weight ``exp(0) / exp(0) = 1.0`` and the
smoothing returns its input bit for bit (NaN nodes are restored as NaN either
way). Computing it is then pure cost: it was 50-61 % of engine time on 3D runs.

That holds for the uniform Q8 grid 3D builds (no midside nodes, every element
edge equals the node spacing ``s``, nearest other node at ``s > 0.75 s``), for
its crack-cut and mask-trimmed variants (they drop elements, never add nodes or
move them, so a node's ``h_i`` is either ``s`` or ``0``), and it fails for a
quadtree-refined mesh, where a node shared by a coarse and a fine element sees
its fine neighbour inside the radius -- there the smoothing really averages and
is kept.

:func:`disp_smoothing_is_noop` proves the condition for EVERY sub-mesh the engine
can derive from the external mesh during a run (any subset of its elements, any
region split), not just for the mesh as given: the radius bound uses the
largest element edge of the whole mesh (a mean over a subset of a node's
elements never exceeds the largest one) and the closest pair of DISTINCT node
indices (regions only shrink neighbourhoods).
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
from al_dic.core.data_structures import DICMesh, DICPara
from scipy.spatial import cKDTree

# The engine's thresholds/constants (al_dic core/pipeline.py ``_smooth_disp``
# and the ``disp_smoothness > 1e-6`` gates; strain/smooth_field.py radius = 3
# sigma). Mirrored here so the proof uses the engine's own numbers.
_ENGINE_SIGMA_FACTOR = 500.0
_ENGINE_RADIUS_SIGMAS = 3.0
_ENGINE_SMOOTH_GATE = 1e-6
# Safety margin on the proof: the closest distinct pair must clear the radius by
# 1 % so a float round-off in the engine's spacing or distance arithmetic can
# never put a neighbour exactly on the (inclusive) ball boundary.
_MARGIN = 1.01


def _max_element_edge(mesh: DICMesh) -> float:
    """Largest per-element edge ``h`` the engine's spacing rule can assign.

    Reproduces ``compute_node_local_spacing``'s element edge (corner 0 to corner
    2 diagonal / sqrt(2)) with the same NumPy indexing, so a ``-1`` corner row
    (an element the engine blanked) is measured exactly as the engine measures
    it.
    """
    coords = np.asarray(mesh.coordinates_fem, dtype=np.float64)
    elements = np.asarray(mesh.elements_fem)
    if elements.size == 0 or coords.shape[0] == 0:
        return 0.0
    c0 = coords[elements[:, 0]]
    c2 = coords[elements[:, 2]]
    h = np.sqrt(np.sum((c0 - c2) ** 2, axis=1)) / np.sqrt(2.0)
    return float(np.max(h)) if h.size else 0.0


def _min_distinct_node_distance(coords: np.ndarray) -> float:
    """Distance between the closest two DISTINCT node indices (0 for duplicates)."""
    if coords.shape[0] < 2:
        return float("inf")
    dist, _ = cKDTree(coords).query(coords, k=2)
    return float(np.min(dist[:, 1]))


def disp_smoothing_is_noop(mesh: DICMesh, para: DICPara) -> bool:
    """True iff the engine's displacement smoothing provably returns its input.

    See the module docstring for the argument. ``True`` also when the smoothing
    is already off (``disp_smoothness <= 1e-6``) or the global step that runs it
    is disabled. Any doubt (non-finite coordinates, coincident nodes, a refined
    mesh) returns ``False`` so the caller keeps the engine's behaviour.
    """
    smoothness = float(para.disp_smoothness)
    if smoothness <= _ENGINE_SMOOTH_GATE or not para.use_global_step:
        return True
    coords = np.asarray(mesh.coordinates_fem, dtype=np.float64)
    if coords.ndim != 2 or coords.shape[0] < 2:
        return True
    if not np.isfinite(coords).all():
        return False
    # The engine falls back to ``winstepsize`` when it is handed no mesh; bound
    # by both so the proof covers either call form.
    h_max = max(_max_element_edge(mesh), float(para.winstepsize))
    radius = _ENGINE_RADIUS_SIGMAS * _ENGINE_SIGMA_FACTOR * smoothness * h_max
    return _min_distinct_node_distance(coords) > _MARGIN * radius


def engine_para(para: DICPara, mesh: DICMesh) -> DICPara:
    """``para`` as handed to ``run_aldic`` for ``mesh``: no-op smoothing dropped.

    Returns ``para`` itself when nothing changes, else a copy with
    ``disp_smoothness = 0`` -- the engine then skips the smoothing calls, whose
    result would have been bit-identical to their input.
    """
    if float(para.disp_smoothness) > 0.0 and disp_smoothing_is_noop(mesh, para):
        return replace(para, disp_smoothness=0.0)
    return para
