"""Tabular result export — NPZ / MAT / per-frame CSV (Qt-free).

Field-selective serialization of a run: the caller picks displacement components
and strain invariants; formats are written side by side into one output folder.
The GUI export dialog drives this; it is equally usable headless.

Progress + cancel (fix batch V, M5): every writer takes an optional
``progress_cb(done, total, label)`` and a ``threading.Event``-like
``stop_event``. NPZ streams each array into the archive in chunks and MAT
appends one variable at a time, both into a temporary file that replaces the
target only when complete — a cancel (``ExportCancelled``) or a failure never
leaves a truncated archive. CSV stops between frames and returns the frames it
finished (an :class:`~al_dic_3d.export.outcome.ExportOutcome` flagged
``cancelled``).
"""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

from al_dic_3d.export.outcome import ExportOutcome, raise_if_stopped, stop_requested, unlink_quietly
from al_dic_3d.export.utils import frame_tag

if TYPE_CHECKING:
    from al_dic_3d.runner import RunResult

ProgressCb = Callable[[int, int, str], None]

# Selectable field ids -> (source, column/attr)
DISPLACEMENT_IDS = ("U", "V", "W", "mag")
STRAIN_IDS = ("exx", "eyy", "exy", "e1", "e2", "max_shear", "von_mises")
#: Per-frame speed |D_k - D_(k-1)| in mm/FRAME (NaN at frame 1). Display-derived
#: (the canvas "Vel" field); media exports scale it to unit/s via ``value_scale``.
VELOCITY_ID = "velocity"

# NPZ member data is written in chunks of about this many bytes (cancel latency).
_NPZ_CHUNK_BYTES = 16 * 2**20


def field_frame(result: RunResult, field: str, k: int) -> np.ndarray | None:
    """One frame of a selectable field id, or ``None`` when unavailable."""
    rec = result.reconstruction
    if field in ("U", "V", "W"):
        return rec.displacement[k][:, ("U", "V", "W").index(field)]
    if field == "mag":
        return np.linalg.norm(rec.displacement[k], axis=1)
    if field == VELOCITY_ID:
        disp = rec.displacement
        if k <= 0:
            return np.full(disp.shape[1], np.nan, dtype=np.float64)
        return np.linalg.norm(disp[k] - disp[k - 1], axis=1)
    if field in STRAIN_IDS and result.strain is not None:
        return getattr(result.strain, field)[k]
    if field == "strain_valid" and result.strain is not None:
        valid = getattr(result.strain, "strain_valid", None)
        return None if valid is None else valid[k]
    return None


def display_field_frame(
    result: RunResult, field: str, k: int, *, deformed: bool = False
) -> np.ndarray | None:
    """One frame of a field with trimmed strain nodes NaN-masked (WYSIWYG helper).

    The strain canvas hides ``~strain_valid`` nodes before both display and
    auto-range, so every render/export path must too (Batch C, C3): dense strain
    VALUES stay finite, ``strain_valid`` is the sole trim signal. This centralizes
    the mask so the canvas, image export, animation, and 3D view agree. The
    reference view (``deformed=False``) applies frame-0 validity, the deformed
    view frame-k validity (the 2D rule). Displacement fields and strain-free
    results pass through :func:`field_frame` unchanged.
    """
    vals = field_frame(result, field, k)
    if vals is None or field not in STRAIN_IDS or result.strain is None:
        return vals
    valid = getattr(result.strain, "strain_valid", None)
    if valid is None:
        return vals
    return np.where(valid[k if deformed else 0], vals, np.nan)


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
    if field == "strain_valid" and result.strain is not None:
        return getattr(result.strain, "strain_valid", None)
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


def _tmp_path(path: Path) -> Path:
    """Sibling temp name for an atomic write (same folder -> ``os.replace`` works)."""
    return path.with_name(f".{path.name}.{os.getpid()}.tmp")


def _npy_member_chunks(arr: np.ndarray):
    """Yield the ``.npy`` bytes of *arr* (header, then C-order data in chunks).

    Equivalent to ``numpy.lib.format.write_array`` for the plain (non-object)
    arrays an export holds, but chunked so a cancel is noticed within
    ~``_NPZ_CHUNK_BYTES`` and a strided view is never copied whole.
    """
    import io

    from numpy.lib import format as npformat

    header = {
        "descr": npformat.dtype_to_descr(arr.dtype),
        "fortran_order": False,
        "shape": arr.shape,
    }
    buf = io.BytesIO()
    try:
        npformat.write_array_header_1_0(buf, header)
    except ValueError:  # header too long for format 1.0
        buf = io.BytesIO()
        npformat.write_array_header_2_0(buf, header)
    yield buf.getvalue()
    if arr.ndim == 0 or arr.size == 0:
        if arr.size:
            yield np.ascontiguousarray(arr).tobytes()
        return
    row_bytes = max(1, arr.nbytes // max(1, arr.shape[0]))
    rows = max(1, _NPZ_CHUNK_BYTES // row_bytes)
    for i in range(0, arr.shape[0], rows):
        yield memoryview(np.ascontiguousarray(arr[i : i + rows])).cast("B")


def write_npz_streaming(
    path: Path,
    arrays: dict[str, Any],
    *,
    compress: bool = True,
    progress_cb: ProgressCb | None = None,
    stop_event=None,
) -> Path:
    """``np.savez_compressed`` equivalent with progress, cancel and an atomic write.

    ``progress_cb(bytes_done, bytes_total, label)``; a set ``stop_event``
    raises :class:`ExportCancelled` and removes the temporary file. Arrays
    ``np.load`` reads back identically to ``np.savez_compressed``.
    """
    import zipfile

    from numpy.lib import format as npformat

    path = Path(path)
    items = [(str(k), np.asanyarray(v)) for k, v in arrays.items()]
    total = int(sum(a.nbytes for _, a in items)) or 1
    done = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = _tmp_path(path)
    method = zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED
    try:
        with zipfile.ZipFile(tmp, "w", compression=method, allowZip64=True) as zf:
            for name, arr in items:
                raise_if_stopped(stop_event)
                with zf.open(f"{name}.npy", "w", force_zip64=True) as fh:
                    if arr.dtype.hasobject:  # never in an export; keep numpy's path
                        npformat.write_array(fh, arr, allow_pickle=True)
                        done += arr.nbytes
                    else:
                        header = True
                        for chunk in _npy_member_chunks(arr):
                            raise_if_stopped(stop_event)
                            fh.write(chunk)
                            if not header:
                                done += memoryview(chunk).nbytes
                                if progress_cb is not None:
                                    progress_cb(min(done, total), total, name)
                            header = False
                if progress_cb is not None:
                    progress_cb(min(done, total), total, name)
        os.replace(tmp, path)
    except BaseException:
        unlink_quietly(tmp)
        raise
    if progress_cb is not None:
        progress_cb(total, total, "")
    return path


def export_npz(
    result: RunResult,
    fields: list[str],
    out_dir: Path,
    prefix: str,
    *,
    arrays: dict[str, np.ndarray] | None = None,
    progress_cb: ProgressCb | None = None,
    stop_event=None,
) -> Path:
    """Write ``{prefix}.npz``; ``arrays`` reuses a prebuilt payload (P3.3).

    ``progress_cb(bytes_done, bytes_total, array_name)``; a set ``stop_event``
    raises :class:`~al_dic_3d.export.outcome.ExportCancelled` and leaves no file.
    """
    if arrays is None:
        arrays = selected_arrays(result, fields)
    out_dir.mkdir(parents=True, exist_ok=True)
    return write_npz_streaming(
        out_dir / f"{prefix}.npz", arrays, progress_cb=progress_cb, stop_event=stop_event
    )


# MATLAB's v5 MAT format stores each variable's size in a 32-bit field:
# scipy writes variables of 2-4 GiB that MATLAB cannot read, and raises on
# >= 4 GiB AFTER creating a partial file. Checked up front instead (fix batch V).
MAT_V5_MAX_VAR_BYTES = 2**31 - 2**20


def save_mat_checked(
    path: Path,
    arrays: dict[str, np.ndarray],
    *,
    progress_cb: ProgressCb | None = None,
    stop_event=None,
) -> Path:
    """``scipy.io.savemat`` with an up-front size check and an atomic write.

    Raises ``ValueError`` naming the offending variable(s) before anything is
    written when a variable exceeds MATLAB v5's per-variable limit; otherwise
    writes to a temporary file in the same folder and replaces ``path``, so a
    failure never leaves a truncated ``.mat`` behind.

    Variables are appended one at a time (``savemat`` on an open stream writes
    the file header only at position 0), so ``progress_cb(bytes_done,
    bytes_total, name)`` advances per variable and a set ``stop_event`` raises
    :class:`~al_dic_3d.export.outcome.ExportCancelled` between variables.
    """
    import scipy.io

    path = Path(path)
    too_big = {
        k: int(np.asarray(v).nbytes)
        for k, v in arrays.items()
        if int(np.asarray(v).nbytes) > MAT_V5_MAX_VAR_BYTES
    }
    if too_big:
        detail = ", ".join(f"{k} ({n / 2**30:.2f} GiB)" for k, n in sorted(too_big.items()))
        raise ValueError(
            f"MAT v5 cannot hold variable(s) {detail}: MATLAB limits a variable to 2 GiB. "
            "Export .npz or fewer frames instead."
        )
    total = int(sum(np.asarray(v).nbytes for v in arrays.values())) or 1
    done = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = _tmp_path(path)
    try:
        with open(tmp, "wb") as fh:
            for name, value in arrays.items():
                raise_if_stopped(stop_event)
                scipy.io.savemat(fh, {name: value}, do_compression=True)
                done += int(np.asarray(value).nbytes)
                if progress_cb is not None:
                    progress_cb(min(done, total), total, str(name))
        raise_if_stopped(stop_event)
        os.replace(tmp, path)
    except BaseException:
        unlink_quietly(tmp)
        raise
    if progress_cb is not None:
        progress_cb(total, total, "")
    return path


def export_mat(
    result: RunResult,
    fields: list[str],
    out_dir: Path,
    prefix: str,
    *,
    arrays: dict[str, np.ndarray] | None = None,
    progress_cb: ProgressCb | None = None,
    stop_event=None,
) -> Path:
    """Write ``{prefix}.mat``; ``arrays`` reuses a prebuilt payload (P3.3)."""
    if arrays is None:
        arrays = selected_arrays(result, fields)
    out_dir.mkdir(parents=True, exist_ok=True)
    return save_mat_checked(
        out_dir / f"{prefix}.mat", arrays, progress_cb=progress_cb, stop_event=stop_event
    )


def export_csv_frames(
    result: RunResult,
    fields: list[str],
    out_dir: Path,
    prefix: str,
    *,
    progress_cb: ProgressCb | None = None,
    stop_event=None,
) -> ExportOutcome:
    """One CSV per frame: ref pixel coords, world XYZ, then the selected fields.

    ``progress_cb(frames_done, n_frames, frame_label)``; a set ``stop_event``
    stops BETWEEN frames — the finished frames are returned (complete files)
    with ``cancelled`` set.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    rec = result.reconstruction
    paths = ExportOutcome()
    for k in range(rec.n_frames):
        if stop_requested(stop_event):
            paths.cancelled = True
            break
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
        # 1-based, zero-padded like every other per-frame export (was frame000).
        tag = frame_tag(k, rec.n_frames)
        path = out_dir / f"{prefix}_{tag}.csv"
        np.savetxt(path, data, delimiter=",", header=header, comments="")
        paths.append(path)
        if progress_cb is not None:
            progress_cb(k + 1, rec.n_frames, tag)
    return paths
