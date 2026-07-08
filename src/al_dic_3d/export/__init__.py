"""Export — result serialization (Batch E1).

Field-selective NPZ / MAT / per-frame CSV tables, per-frame PLY point clouds,
a VTU surface-mesh time series for ParaView, and an always-written parameters
JSON. Shared naming utilities (`make_prefix` / `make_timestamp` / `frame_tag`)
follow the 2D platform: every export entry point mints a fresh timestamp so
repeated exports never overwrite. Screenshot / animation rendering lands in a
later batch.

Layer: compute (**Qt-free**; pyvista lazily imported inside the VTU writer
only).  Spec: docs/architecture/01 §B.1.
"""

from al_dic_3d.export.params import export_params
from al_dic_3d.export.ply import export_ply_frames
from al_dic_3d.export.tables import (
    DISPLACEMENT_IDS,
    STRAIN_IDS,
    export_csv_frames,
    export_mat,
    export_npz,
    field_frame,
    selected_arrays,
)
from al_dic_3d.export.utils import ensure_dir, frame_tag, make_prefix, make_timestamp
from al_dic_3d.export.vtu import export_vtu_series

__all__ = [
    "DISPLACEMENT_IDS",
    "STRAIN_IDS",
    "ensure_dir",
    "export_csv_frames",
    "export_mat",
    "export_npz",
    "export_params",
    "export_ply_frames",
    "export_vtu_series",
    "field_frame",
    "frame_tag",
    "make_prefix",
    "make_timestamp",
    "selected_arrays",
]
