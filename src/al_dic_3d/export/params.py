"""Export run parameters as a structured JSON file (Qt-free).

The parameters file is always written regardless of which data formats were
selected, so every export folder records how its numbers were produced (the 2D
platform's ``export_params`` idiom). It merges the run's own bookkeeping
(``result.meta``, including ``meta["run_params"]`` — what was actually run) with
a caller-supplied ``extra`` dict — the CLI passes the full ``RunConfig``, the
GUI passes the draft's matching parameters.

Precedence (fix batch V, H6): whatever the RUN recorded wins. The GUI draft is
live — the user may have changed Subset Size or Step after the run — so a
draft value only fills a key the run did not record; it never overrides one.

:func:`run_mesh_step` is the one place the node step of a result is resolved
(the run's ``winstepsize``, else the median node spacing of an older result),
so overlays and support masks never follow a later draft edit (H3).
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


def run_param(result: Any, name: str, default: Any = None) -> Any:
    """One value of ``result.meta["run_params"]`` (what was run), or *default*."""
    run_params = (getattr(result, "meta", None) or {}).get("run_params") or {}
    value = run_params.get(name)
    return default if value is None else value


def run_mesh_step(result: Any, default: int = 16) -> int:
    """The node step (px) the result was computed with.

    ``run_params["winstepsize"]`` when the run recorded it; otherwise (sessions
    saved before fix batch V) the median nearest-neighbour spacing of the
    reference nodes; *default* only for a degenerate node set. Delegates to
    :func:`al_dic_3d.viz3d.runstep.run_node_step` — the ONE rule the canvas,
    the strain window and the exports share, so their overlays agree.
    """
    from al_dic_3d.viz3d.runstep import run_node_step

    return run_node_step(result, default=default)


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
            fields, ...); values are JSON-sanitised, ndarrays dropped. A key
            the run itself recorded (``result.meta`` or its ``run_params``)
            keeps the run's value; ``extra`` only fills the gaps.

    Returns:
        Path to the written JSON file.
    """
    rec = result.reconstruction
    meta = result.meta or {}
    data: dict[str, Any] = {
        "export_timestamp": timestamp,
        "n_frames": rec.n_frames,
        "n_pts": rec.n_pts,
        "strategy": result.strategy,
        "has_strain": result.strain is not None,
    }
    for key, value in meta.items():
        data.setdefault(str(key), _to_json_value(value))
    # What was RUN, flattened to the top level (the historical key layout).
    for key, value in (meta.get("run_params") or {}).items():
        data[str(key)] = _to_json_value(value)
    for key, value in (extra or {}).items():
        data.setdefault(str(key), _to_json_value(value))

    out = ensure_dir(Path(dest_dir)) / f"{prefix}_parameters_{timestamp}.json"
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return out
