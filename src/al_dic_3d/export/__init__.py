"""Export — result serialization (field-selective NPZ / MAT / per-frame CSV).

PLY / VTU meshes and screenshot / animation rendering land in Phase 5; the
tabular exporters here back the GUI export dialog and headless use.

Layer: compute (**Qt-free**).  Lands: Phase 4-5.  Spec: docs/architecture/01 §B.1.
"""

from al_dic_3d.export.tables import (
    DISPLACEMENT_IDS,
    STRAIN_IDS,
    export_csv_frames,
    export_mat,
    export_npz,
    selected_arrays,
)

__all__ = [
    "DISPLACEMENT_IDS",
    "STRAIN_IDS",
    "export_csv_frames",
    "export_mat",
    "export_npz",
    "selected_arrays",
]
