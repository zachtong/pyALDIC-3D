"""Reconstruct — triangulation and 3D displacement.

DLT triangulation from point correspondences, per-frame reprojection error, and
world/specimen-frame transforms. Mode- and strategy-agnostic:
``Displacement = P^k - P^1``.

Layer: compute (**Qt-free**).  Lands: Phase 1.  Spec: docs/architecture/01 §B.1, §E.
"""

from al_dic_3d.reconstruct.reconstruction import (
    Reconstruction3D,
    reconstruct_correspondence,
)
from al_dic_3d.reconstruct.triangulate import reprojection_error, triangulate_dlt

__all__ = [
    "Reconstruction3D",
    "reconstruct_correspondence",
    "reprojection_error",
    "triangulate_dlt",
]
