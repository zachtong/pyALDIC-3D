"""Export run parameters as a structured JSON file (Qt-free).

The parameters file is always written regardless of which data formats were
selected, so every export folder records how its numbers were produced (the 2D
platform's ``export_params`` idiom). It merges the run's own bookkeeping
(``result.meta``) with a caller-supplied ``extra`` dict — the CLI passes the
full ``RunConfig``, the GUI passes the draft's matching parameters.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

from al_dic_3d.export.utils import ensure_dir

if TYPE_CHECKING:
    from al_dic_3d.runner import RunResult


def _to_json_value(v: Any) -> Any:
    """Convert an arbitrary parameter value to a JSON-serializable type.

    ``Path`` becomes ``str``; ``ndarray`` becomes ``None`` (large payloads are
    summarised by counts, never inlined); numpy scalars unbox; containers and
    dataclasses recurse; anything else falls back to ``str``.
    """
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, Path):
        return str(v)
    if isinstance(v, np.generic):
        return _to_json_value(v.item())
    if isinstance(v, np.ndarray):
        return None
    if isinstance(v, (list, tuple)):
        return [_to_json_value(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _to_json_value(x) for k, x in v.items()}
    if dataclasses.is_dataclass(v) and not isinstance(v, type):
        return {f.name: _to_json_value(getattr(v, f.name)) for f in dataclasses.fields(v)}
    return str(v)


def export_params(
    dest_dir: Path,
    prefix: str,
    timestamp: str,
    result: RunResult,
    extra: dict[str, Any] | None = None,
) -> Path:
    """Write ``{prefix}_parameters_{timestamp}.json`` describing the run.

    Args:
        dest_dir: directory to write into (created if absent).
        prefix: filename prefix (e.g. derived via :func:`make_prefix`).
        timestamp: 14-digit ``YYYYMMDDHHMMSS`` string (fresh per export).
        result: the completed run whose metadata is recorded.
        extra: caller-supplied parameter dict (RunConfig fields, GUI draft
            fields, ...); values are JSON-sanitised, ndarrays dropped.

    Returns:
        Path to the written JSON file.
    """
    rec = result.reconstruction
    data: dict[str, Any] = {
        "export_timestamp": timestamp,
        "n_frames": rec.n_frames,
        "n_pts": rec.n_pts,
        "strategy": result.strategy,
        "has_strain": result.strain is not None,
    }
    for key, value in (result.meta or {}).items():
        data.setdefault(str(key), _to_json_value(value))
    for key, value in (extra or {}).items():
        data[str(key)] = _to_json_value(value)

    out = ensure_dir(Path(dest_dir)) / f"{prefix}_parameters_{timestamp}.json"
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return out
