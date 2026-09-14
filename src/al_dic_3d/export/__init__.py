"""Export — result serialization + rendered media (Batches E1 + E2).

Field-selective NPZ / MAT / per-frame CSV tables, per-frame PLY point clouds,
a VTU surface-mesh time series for ParaView, an always-written parameters
JSON (E1); rendered per-camera field images, streaming GIF/MP4 animations,
and offscreen 3D-view exports (E2). Shared naming utilities (`make_prefix` /
`make_timestamp` / `frame_tag`) follow the 2D platform: every export entry
point mints a fresh timestamp so repeated exports never overwrite.

Multi-file writers return an :class:`ExportOutcome` (a ``list`` of the
written paths plus cancel / skip / discard bookkeeping); single-file writers
raise :class:`ExportCancelled` on cancel and never leave a partial file.

Layer: compute (**Qt-free**; pyvista lazily imported inside the VTU writer
and the 3D-view renderer only).  Spec: docs/architecture/01 §B.1.
"""

from al_dic_3d.export.animation import StreamingAnimWriter, animation_fps, export_animation
from al_dic_3d.export.colorbar import (
    ColorbarStyle,
    add_margin,
    attach_colorbar,
    colorbar_label,
    render_colorbar_strip,
)
from al_dic_3d.export.gifstream import GIF_MAX_FPS, GifStreamWriter
from al_dic_3d.export.outcome import ExportCancelled, ExportOutcome
from al_dic_3d.export.params import export_params, run_mesh_step, run_param
from al_dic_3d.export.ply import export_ply_frames
from al_dic_3d.export.render import (
    RESOLUTION_PRESETS,
    CameraTuple,
    FieldImageConfig,
    VizExportHint,
    camera_roi_masks,
    encode_params_for,
    export_image_frames,
    field_color_range,
    output_shape_for,
    render_field_frame,
)
from al_dic_3d.export.render3d import (
    VIEW3D_RESOLUTIONS,
    export_view3d_frames,
    export_view3d_turntable,
    render_view3d_frame,
    view3d_color_range,
)
from al_dic_3d.export.tables import (
    DISPLACEMENT_IDS,
    STRAIN_IDS,
    VELOCITY_ID,
    display_field_frame,
    export_csv_frames,
    export_mat,
    export_npz,
    field_frame,
    field_stack,
    selected_arrays,
)
from al_dic_3d.export.utils import ensure_dir, frame_tag, make_prefix, make_timestamp
from al_dic_3d.export.vtu import export_vtu_series

__all__ = [
    "DISPLACEMENT_IDS",
    "GIF_MAX_FPS",
    "RESOLUTION_PRESETS",
    "STRAIN_IDS",
    "VELOCITY_ID",
    "VIEW3D_RESOLUTIONS",
    "CameraTuple",
    "ColorbarStyle",
    "ExportCancelled",
    "ExportOutcome",
    "FieldImageConfig",
    "GifStreamWriter",
    "StreamingAnimWriter",
    "VizExportHint",
    "add_margin",
    "animation_fps",
    "attach_colorbar",
    "camera_roi_masks",
    "colorbar_label",
    "display_field_frame",
    "encode_params_for",
    "ensure_dir",
    "export_animation",
    "export_csv_frames",
    "export_image_frames",
    "export_mat",
    "export_npz",
    "export_params",
    "export_ply_frames",
    "export_view3d_frames",
    "export_view3d_turntable",
    "export_vtu_series",
    "field_color_range",
    "field_frame",
    "field_stack",
    "frame_tag",
    "make_prefix",
    "make_timestamp",
    "output_shape_for",
    "render_colorbar_strip",
    "render_field_frame",
    "render_view3d_frame",
    "run_mesh_step",
    "run_param",
    "selected_arrays",
    "view3d_color_range",
]
