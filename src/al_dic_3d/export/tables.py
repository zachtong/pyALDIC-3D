"""Tabular result export — NPZ / MAT / per-frame CSV (Qt-free).

Field-selective serialization of a run: the caller picks displacement components
and strain invariants; formats are written side by side into one output folder.
The GUI export dialog drives this; it is equally usable headless.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from al_dic_3d.runner import RunResult

# Selectable field ids -> (source, column/attr)
DISPLACEMENT_IDS = ("U", "V", "W", "mag")
STRAIN_IDS = ("exx", "eyy", "exy", "e1", "e2", "max_shear", "von_mises")


def field_frame(result: RunResult, field: str, k: int) -> np.ndarray | None:
    """One frame of a selectable field id, or ``None`` when unavailable."""
    rec = result.reconstruction
    if field in ("U", "V", "W"):
        return rec.displacement[k][:, ("U", "V", "W").index(field)]
    if field == "mag":
        return np.linalg.norm(rec.displacement[k], axis=1)
    if field in STRAIN_IDS and result.strain is not None:
        return getattr(result.strain, field)[k]
    return None


def field_stack(result: RunResult, field: str) -> np.ndarray | None:
    """All frames of a selectable field id as ``(n_frames, n_pts)``, or ``None``.

    P3.3: built from whole-array views/reductions instead of a per-frame Python
    copy loop — displacement components are slices of ``rec.displacement`` and
    strain stacks already live as full arrays on ``result.strain``.
    """
    rec = result.reconstruction
    if field in ("U", "V", "W"):
        return rec.displacement[:, :, ("U", "V", "W").index(field)]
    if field == "mag":
        return np.linalg.norm(rec.displacement, axis=2)
    if field in STRAIN_IDS and result.strain is not None:
        return getattr(result.strain, field)
    return None


def selected_arrays(result: RunResult, fields: list[str]) -> dict[str, np.ndarray]:
    """Core arrays + the selected per-frame fields, ready for npz/mat."""
    rec = result.reconstruction
    arrays: dict[str, np.ndarray] = {
        "strategy": np.asarray(result.strategy),
        "ref_coords": result.ref_coords,
        "points3D": rec.points,
        "reproj_error": rec.reproj_error,
        "source": rec.source,
    }
    for field in fields:
        stack = field_stack(result, field)
        if stack is not None:
            arrays[field] = stack
    return arrays


def export_npz(
    result: RunResult,
    fields: list[str],
    out_dir: Path,
    prefix: str,
    *,
    arrays: dict[str, np.ndarray] | None = None,
) -> Path:
    """Write ``{prefix}.npz``; ``arrays`` reuses a prebuilt payload (P3.3)."""
    if arrays is None:
        arrays = selected_arrays(result, fields)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{prefix}.npz"
    np.savez_compressed(path, **arrays)
    return path


def export_mat(
    result: RunResult,
    fields: list[str],
    out_dir: Path,
    prefix: str,
    *,
    arrays: dict[str, np.ndarray] | None = None,
) -> Path:
    """Write ``{prefix}.mat``; ``arrays`` reuses a prebuilt payload (P3.3)."""
    import scipy.io

    if arrays is None:
        arrays = selected_arrays(result, fields)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{prefix}.mat"
    scipy.io.savemat(str(path), arrays, do_compression=True)
    return path


def export_csv_frames(
    result: RunResult, fields: list[str], out_dir: Path, prefix: str
) -> list[Path]:
    """One CSV per frame: ref pixel coords, world XYZ, then the selected fields."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rec = result.reconstruction
    paths: list[Path] = []
    for k in range(rec.n_frames):
        columns: list[tuple[str, np.ndarray]] = [
            ("x_px", result.ref_coords[:, 0]),
            ("y_px", result.ref_coords[:, 1]),
            ("X_mm", rec.points[k][:, 0]),
            ("Y_mm", rec.points[k][:, 1]),
            ("Z_mm", rec.points[k][:, 2]),
        ]
        for field in fields:
            vals = field_frame(result, field, k)
            if vals is not None:
                columns.append((field, vals))
        header = ",".join(name for name, _ in columns)
        data = np.column_stack([vals for _, vals in columns])
        path = out_dir / f"{prefix}_frame{k:03d}.csv"
        np.savetxt(path, data, delimiter=",", header=header, comments="")
        paths.append(path)
    return paths
