"""Surface-mesh time-series export for ParaView (.vtu frames + .pvd collection).

Each frame becomes a ``pyvista.UnstructuredGrid``: points are that frame's
reconstructed world coordinates, cells are the regular-grid quads from
:func:`al_dic_3d.viz3d.build_quad_connectivity` (the same builder the 3D view
uses) with cells touching NaN (invalid) points dropped, and point-data carries
the selected displacement/strain fields plus ``reproj_error`` and ``source``.
A ``{prefix}.pvd`` collection references every frame with its timestep so
ParaView loads the whole sequence in one open.

Qt-free; pyvista/VTK is imported lazily INSIDE the entry point (the
``al-dic-3d[viz3d]`` extra) so the compute layer stays installable without it.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from al_dic_3d.export.tables import field_frame
from al_dic_3d.export.utils import ensure_dir, frame_tag
from al_dic_3d.viz3d import as_vtk_faces, build_quad_connectivity, filter_cells_finite

if TYPE_CHECKING:
    from al_dic_3d.runner import RunResult

ProgressCb = Callable[[float, str], None]


def _write_pvd(path: Path, frame_files: list[Path]) -> Path:
    """Write a ParaView collection referencing *frame_files* (same folder)."""
    lines = [
        '<?xml version="1.0"?>',
        '<VTKFile type="Collection" version="0.1" byte_order="LittleEndian">',
        "  <Collection>",
    ]
    lines += [
        f'    <DataSet timestep="{k}" group="" part="0" file="{f.name}"/>'
        for k, f in enumerate(frame_files)
    ]
    lines += ["  </Collection>", "</VTKFile>", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def export_vtu_series(
    dest_dir: Path,
    prefix: str,
    timestamp: str,
    result: RunResult,
    fields: list[str],
    *,
    progress_cb: ProgressCb | None = None,
    stop_event=None,
) -> list[Path]:
    """Write ``{prefix}_vtu_{timestamp}/frame_XXX.vtu`` + ``{prefix}.pvd``.

    Args:
        dest_dir: export root; the timestamped subfolder is created inside it.
        prefix, timestamp: naming per the export convention.
        result: completed run (points, ref grid, QC arrays).
        fields: selectable field ids; unavailable ones are silently skipped.
        progress_cb: optional ``(fraction, message)`` callback per frame.
        stop_event: optional ``threading.Event``-like; when set, stops between
            frames — the ``.pvd`` then references only the frames written.

    Returns:
        The written paths (frame files, ``.pvd`` last). Point count and order
        are identical in every frame (NaN = invalid kept as NaN), so point ids
        are stable across the series.

    Raises:
        ImportError: when pyvista is missing — install the viz3d extra:
            ``pip install al-dic-3d[viz3d]``.
    """
    try:
        import pyvista as pv
    except ImportError as exc:  # pragma: no cover - exercised via sys.modules patch
        raise ImportError(
            "VTU export requires pyvista; install the optional extra with "
            "'pip install al-dic-3d[viz3d]'"
        ) from exc

    rec = result.reconstruction
    n_frames = rec.n_frames
    out_dir = ensure_dir(Path(dest_dir) / f"{prefix}_vtu_{timestamp}")
    connectivity = build_quad_connectivity(result.ref_coords)

    frame_files: list[Path] = []
    for k in range(n_frames):
        if stop_event is not None and stop_event.is_set():
            break
        points = np.asarray(rec.points[k], dtype=np.float64)
        quads = filter_cells_finite(connectivity, points)
        cells = as_vtk_faces(quads)
        celltypes = np.full(len(quads), pv.CellType.QUAD, dtype=np.uint8)
        grid = pv.UnstructuredGrid(cells, celltypes, points)
        for name in fields:
            vals = field_frame(result, name, k)
            if vals is not None:
                grid.point_data[name] = vals
        grid.point_data["reproj_error"] = np.asarray(rec.reproj_error[k], dtype=np.float64)
        grid.point_data["source"] = np.asarray(rec.source[k], dtype=np.uint8)
        path = out_dir / f"{frame_tag(k, n_frames)}.vtu"
        grid.save(str(path))
        frame_files.append(path)
        if progress_cb is not None:
            progress_cb((k + 1) / n_frames, f"VTU {path.name}")

    pvd = _write_pvd(out_dir / f"{prefix}.pvd", frame_files)
    return [*frame_files, pvd]
