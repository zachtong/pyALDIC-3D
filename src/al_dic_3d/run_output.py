"""Writing a run's results: the unified NPZ / MAT archive plus CSV / PLY / VTU.

Split out of :mod:`al_dic_3d.runner` (the 800-line cap); the runner re-exports
everything here, which is where the CLI, the tools and the README import it
from (``from al_dic_3d.runner import write_results``).
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from al_dic_3d.strain3d import STRAIN_FIELDS

if TYPE_CHECKING:
    from al_dic_3d.runner import RunConfig, RunResult


RESULT_FORMATS = ("npz", "mat", "csv", "ply", "vtu")

# Archive layout version recorded in the parameters JSON. Schema 2 (P3.3)
# dropped the doubled ``strain_<name>`` aliases: strain stacks live ONLY under
# their canonical GUI-selection ids (``exx`` ... ``von_mises`` plus ``dwdx`` /
# ``dwdy``). Schema 3 (Batch C item 3) adds an OPTIONAL ``strain_valid``
# ``(n_frames, n_pts)`` bool stack (edge-trim UNION crack-trim) alongside the
# now-DENSE strain values; readers that ignore unknown keys are unaffected.
ARCHIVE_SCHEMA = 3


def _arrays(result: RunResult) -> dict:
    """The unified archive: GUI selection schema + correspondence extras.

    Built on :func:`al_dic_3d.export.tables.selected_arrays` with ALL field ids
    (strategy / ref_coords / points3D / reproj_error / source + one
    ``(n_frames, n_pts)`` stack per field: U, V, W, mag, exx, ...), merged with
    the correspondence extras ``xL`` / ``xR`` / ``quality`` and the LEGACY keys
    ``displacement3D`` / ``n_frames`` / ``n_pts`` that parity tools read.
    Schema 2 (see :data:`ARCHIVE_SCHEMA`): ONE canonical key per strain field —
    ``dwdx`` / ``dwdy`` (not in the GUI picker) are added under their bare
    names and the old ``strain_<name>`` duplicates are gone.
    """
    from al_dic_3d.export import DISPLACEMENT_IDS, STRAIN_IDS, selected_arrays

    cs = result.correspondence
    arrays = selected_arrays(result, [*DISPLACEMENT_IDS, *STRAIN_IDS])
    arrays.update(
        {
            "xL": cs.xL,
            "xR": cs.xR,
            "quality": cs.quality,
            "displacement3D": result.reconstruction.displacement,
            "n_frames": np.int64(cs.n_frames),
            "n_pts": np.int64(cs.n_pts),
        }
    )
    if result.strain is not None:
        for name in STRAIN_FIELDS:
            arrays.setdefault(name, getattr(result.strain, name))
        # Schema 3: DENSE strain values + an optional validity stack (edge-trim
        # UNION crack-trim). Absent when trimming/crack-awareness was off.
        if getattr(result.strain, "strain_valid", None) is not None:
            arrays.setdefault("strain_valid", np.asarray(result.strain.strain_valid))
    return arrays


def write_results(
    result: RunResult,
    cfg: RunConfig,
    formats: Sequence[str] = ("npz", "mat"),
    *,
    errors: list[str] | None = None,
) -> dict[str, Path]:
    """Write the run outputs under ``cfg.output_dir``; return format -> path.

    ``npz`` / ``mat`` carry the unified SUPERSET archive (see :func:`_arrays`)
    at the fixed ``<prefix>.npz`` / ``<prefix>.mat`` paths that the parity
    tooling reads. ``csv`` / ``ply`` / ``vtu`` route through the export package
    into ``<prefix>_{fmt}_{timestamp}`` folders — a fresh timestamp per call,
    so repeated runs never overwrite them. A ``<prefix>_parameters_{ts}.json``
    recording the full RunConfig is ALWAYS written (key ``"params"``).

    ``errors``: when given, a format that fails is recorded there as
    ``"<fmt>: <ExcType>: <message>"`` and the remaining formats are still
    written (fix batch V: a MAT size failure at the end of a long run used to
    lose every other output); when ``None`` the first failure raises.
    """
    from dataclasses import asdict

    from al_dic_3d.export import (
        DISPLACEMENT_IDS,
        STRAIN_IDS,
        export_csv_frames,
        export_params,
        export_ply_frames,
        export_vtu_series,
        make_timestamp,
    )

    unknown = sorted(set(formats) - set(RESULT_FORMATS))
    if unknown:
        raise ValueError(f"unknown output format(s): {', '.join(unknown)}")

    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    prefix = cfg.output_prefix
    ts = make_timestamp()
    fields = list(DISPLACEMENT_IDS) + (list(STRAIN_IDS) if result.strain is not None else [])
    # Schema 3: csv/vtu/ply also carry the DENSE strain's validity column when present.
    if result.strain is not None and getattr(result.strain, "strain_valid", None) is not None:
        fields.append("strain_valid")
    # archive_schema documents the npz/mat key layout (P3.3 alias removal).
    extra = {**asdict(cfg), "archive_schema": ARCHIVE_SCHEMA}
    # The EFFECTIVE ROI (a [roi].mask run carries a placeholder bbox in cfg).
    run_params = (result.meta or {}).get("run_params") or {}
    if run_params.get("roi"):
        extra["roi"] = list(run_params["roi"])
    paths: dict[str, Path] = {
        "params": export_params(cfg.output_dir, prefix, ts, result, extra=extra)
    }

    def attempt(fmt: str, write) -> None:
        try:
            paths[fmt] = write()
        except Exception as exc:
            if errors is None:
                raise
            errors.append(f"{fmt}: {type(exc).__name__}: {exc}")

    if "npz" in formats or "mat" in formats:
        arrays = _arrays(result)
        if "npz" in formats:

            def _npz() -> Path:
                out = cfg.output_dir / f"{prefix}.npz"
                np.savez_compressed(out, **arrays)
                return out

            attempt("npz", _npz)
        if "mat" in formats:
            from al_dic_3d.export.tables import save_mat_checked

            attempt("mat", lambda: save_mat_checked(cfg.output_dir / f"{prefix}.mat", arrays))
    if "csv" in formats:

        def _csv() -> Path:
            csv_dir = cfg.output_dir / f"{prefix}_csv_{ts}"
            export_csv_frames(result, fields, csv_dir, prefix)
            return csv_dir

        attempt("csv", _csv)
    if "ply" in formats:

        def _ply() -> Path:
            export_ply_frames(cfg.output_dir, prefix, ts, result, fields)
            return cfg.output_dir / f"{prefix}_ply_{ts}"

        attempt("ply", _ply)
    if "vtu" in formats:

        def _vtu() -> Path:
            export_vtu_series(cfg.output_dir, prefix, ts, result, fields)
            return cfg.output_dir / f"{prefix}_vtu_{ts}"

        attempt("vtu", _vtu)
    return paths
