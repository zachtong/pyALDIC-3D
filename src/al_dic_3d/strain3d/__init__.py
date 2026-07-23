"""Strain3D — Green-Lagrange surface strain on the reconstructed point cloud.

Local-neighbourhood plane fit -> tangent-frame displacement gradients ->
Green-Lagrange strain + invariants (see docs/strain3d_math.md). Consumes only a
``Reconstruction3D`` + the reference 2D node coords; pure numpy/scipy (no ``al_dic``
coupling). Optional displacement smoothing and specimen-frame transform.

Layer: compute (**Qt-free**).  Lands: Phase 3.  Spec: docs/architecture/01 §B.1, §E.
"""

from al_dic_3d.strain3d.compute import compute_surface_strain, smooth_displacement
from al_dic_3d.strain3d.edgetrim import edge_trim_mask
from al_dic_3d.strain3d.gradients import (
    STRAIN_TYPES,
    fit_gradients,
    green_lagrange_strain,
    strain_tensor,
    tangent_frame,
)
from al_dic_3d.strain3d.model import STRAIN_FIELDS, StrainResult3D
from al_dic_3d.strain3d.specimen import specimen_frame

__all__ = [
    "STRAIN_FIELDS",
    "STRAIN_TYPES",
    "StrainResult3D",
    "compute_surface_strain",
    "edge_trim_mask",
    "fit_gradients",
    "green_lagrange_strain",
    "smooth_displacement",
    "specimen_frame",
    "strain_tensor",
    "tangent_frame",
]
