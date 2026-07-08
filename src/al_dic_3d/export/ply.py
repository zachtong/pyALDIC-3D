"""Per-frame PLY point-cloud export (pure numpy, Qt-free, no PLY library).

One ``frame_XXX.ply`` per frame under ``{prefix}_ply_{timestamp}/``: vertices
are the reconstructed world points, and every selected scalar field (the same
ids as :data:`al_dic_3d.export.tables.DISPLACEMENT_IDS` / ``STRAIN_IDS``)
becomes a ``float`` vertex property. Binary little-endian by default (compact,
lossless enough at float32); ASCII on request. ``NaN = invalid`` propagates:
``drop_invalid`` removes NaN-position vertices, otherwise they are kept and
flagged by a ``valid`` uchar property.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from al_dic_3d.export.tables import field_frame
from al_dic_3d.export.utils import ensure_dir, frame_tag

if TYPE_CHECKING:
    from al_dic_3d.runner import RunResult

ProgressCb = Callable[[float, str], None]


def _ply_header(n_vertices: int, fields: list[str], *, binary: bool, keep_valid: bool) -> str:
    fmt = "binary_little_endian" if binary else "ascii"
    lines = [
        "ply",
        f"format {fmt} 1.0",
        "comment pyALDIC-3D export",
        f"element vertex {n_vertices}",
        "property float x",
        "property float y",
        "property float z",
    ]
    lines += [f"property float {name.lower()}" for name in fields]
    if keep_valid:
        lines.append("property uchar valid")
    lines.append("end_header")
    return "\n".join(lines) + "\n"


def _write_frame(
    path: Path,
    points: np.ndarray,
    columns: list[tuple[str, np.ndarray]],
    *,
    binary: bool,
    drop_invalid: bool,
) -> None:
    valid = np.isfinite(points).all(axis=1)
    if drop_invalid:
        points = points[valid]
        columns = [(name, vals[valid]) for name, vals in columns]
    field_names = [name for name, _ in columns]
    header = _ply_header(len(points), field_names, binary=binary, keep_valid=not drop_invalid)

    dtype = [("x", "<f4"), ("y", "<f4"), ("z", "<f4")]
    dtype += [(name.lower(), "<f4") for name in field_names]
    if not drop_invalid:
        dtype.append(("valid", "u1"))
    rows = np.empty(len(points), dtype=dtype)
    rows["x"], rows["y"], rows["z"] = points[:, 0], points[:, 1], points[:, 2]
    for name, vals in columns:
        rows[name.lower()] = vals
    if not drop_invalid:
        rows["valid"] = valid.astype(np.uint8)

    with path.open("wb") as fh:
        fh.write(header.encode("ascii"))
        if binary:
            fh.write(rows.tobytes())
        else:
            widths = len(dtype)
            for row in rows:
                fh.write((" ".join(f"{row[i]:g}" for i in range(widths)) + "\n").encode("ascii"))


def export_ply_frames(
    dest_dir: Path,
    prefix: str,
    timestamp: str,
    result: RunResult,
    fields: list[str],
    *,
    binary: bool = True,
    drop_invalid: bool = True,
    progress_cb: ProgressCb | None = None,
    stop_event=None,
) -> list[Path]:
    """Write ``{prefix}_ply_{timestamp}/frame_XXX.ply`` for every frame.

    Args:
        dest_dir: export root; the timestamped subfolder is created inside it.
        prefix, timestamp: naming per the export convention (fresh timestamp
            per export, so repeats never overwrite).
        result: completed run; vertices come from ``reconstruction.points[k]``.
        fields: selectable field ids (``DISPLACEMENT_IDS`` / ``STRAIN_IDS``);
            unavailable ones are silently skipped.
        binary: little-endian binary PLY (default) or ASCII.
        drop_invalid: drop NaN-position vertices (default); when ``False`` all
            rows are kept and a ``valid`` uchar property flags them.
        progress_cb: optional ``(fraction, message)`` callback per frame.
        stop_event: optional ``threading.Event``-like; when set, stops between
            frames and returns the paths written so far.

    Returns:
        The written frame paths (possibly partial when cancelled).
    """
    rec = result.reconstruction
    n_frames = rec.n_frames
    out_dir = ensure_dir(Path(dest_dir) / f"{prefix}_ply_{timestamp}")
    paths: list[Path] = []
    for k in range(n_frames):
        if stop_event is not None and stop_event.is_set():
            break
        columns = [
            (name, vals) for name in fields if (vals := field_frame(result, name, k)) is not None
        ]
        path = out_dir / f"{frame_tag(k, n_frames)}.ply"
        _write_frame(
            path,
            np.asarray(rec.points[k], dtype=np.float64),
            columns,
            binary=binary,
            drop_invalid=drop_invalid,
        )
        paths.append(path)
        if progress_cb is not None:
            progress_cb((k + 1) / n_frames, f"PLY {path.name}")
    return paths
