"""Reconstruct — triangulation and 3D displacement.

DLT triangulation from point correspondences, per-frame reprojection error, and
world/specimen-frame transforms. Mode- and strategy-agnostic:
``Displacement = P^k - P^1``.

Layer: compute (**Qt-free**).  Lands: Phase 1.  Spec: docs/architecture/01 §B.1, §E.
"""

from al_dic_3d.reconstruct.outliers import (
    apply_reproj_gate,
    rebuild_reconstruction,
    remove_3d_outliers,
)
from al_dic_3d.reconstruct.reconstruction import (
    Reconstruction3D,
    reconstruct_correspondence,
)
from al_dic_3d.reconstruct.rigid import (
    RIGID_MOTION_MODES,
    RigidMotionFit,
    RigidMotionState,
    apply_rigid_motion,
    fit_rigid_motion,
    region_to_nodes,
)
from al_dic_3d.reconstruct.triangulate import reprojection_error, triangulate_dlt

__all__ = [
    "RIGID_MOTION_MODES",
    "Reconstruction3D",
    "RigidMotionFit",
    "RigidMotionState",
    "apply_reproj_gate",
    "apply_rigid_motion",
    "fit_rigid_motion",
    "rebuild_reconstruction",
    "reconstruct_correspondence",
    "region_to_nodes",
    "remove_3d_outliers",
    "reprojection_error",
    "triangulate_dlt",
]
