"""``.aldic3d`` session save / load (Qt-free), following the 2D envelope design.

A session is a versioned ZIP bundle so a project resumes exactly where it was left,
including a completed run (a long computation is never lost on close):

    session.json   - schema version, the reproducible RunConfig, UI view state,
                     workflow step, and the run metadata (human-readable)
    results.npz    - the correspondence / reconstruction / strain arrays
                     (present only when a run has completed)

Schema is versioned (:data:`SCHEMA_VERSION`); an unknown version raises
:class:`SessionError` rather than silently loading a newer format. Parsing is
separated from applying (via :class:`Session3DData`) so it is unit-testable without
constructing an :class:`AppState3D`.
"""

from __future__ import annotations

import dataclasses
import io
import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

from al_dic_3d.project.state import AppState3D

if TYPE_CHECKING:
    from al_dic_3d.project.draft import ProjectDraft
    from al_dic_3d.runner import RunConfig

SCHEMA_VERSION = 1
_CONFIG_NAME = "session.json"
_RESULTS_NAME = "results.npz"
_PATH_FIELDS = ("calibration_file", "output_dir", "base_dir")


class SessionError(Exception):
    """Raised when a ``.aldic3d`` session cannot be parsed or applied cleanly."""


@dataclass
class Session3DData:
    """Parsed contents of a ``.aldic3d`` file (before it is applied to AppState3D)."""

    schema_version: int
    config: RunConfig | None
    draft: ProjectDraft = field(default_factory=lambda: _new_draft())
    view_state: dict = field(default_factory=dict)
    workflow_step: int = 0
    meta: dict = field(default_factory=dict)
    result_arrays: dict[str, Any] | None = None  # raw npz arrays if results were saved


def _new_draft() -> ProjectDraft:
    from al_dic_3d.project.draft import ProjectDraft

    return ProjectDraft()


# --- RunConfig <-> JSON -------------------------------------------------------


def _config_to_json(config: RunConfig) -> dict:
    d = dataclasses.asdict(config)
    for name in _PATH_FIELDS:
        d[name] = str(d[name])
    return d


def _config_from_json(d: dict | None) -> RunConfig | None:
    if d is None:
        return None
    from al_dic_3d.runner import RunConfig

    valid = {f.name for f in dataclasses.fields(RunConfig)}
    kw = {k: v for k, v in d.items() if k in valid}
    for name in _PATH_FIELDS:
        if name in kw:
            kw[name] = Path(kw[name])
    if "roi" in kw and kw["roi"] is not None:
        kw["roi"] = tuple(kw["roi"])
    if kw.get("disparity_offset") is not None:
        kw["disparity_offset"] = tuple(kw["disparity_offset"])
    return RunConfig(**kw)


_DRAFT_PATH_FIELDS = ("calibration_file", "output_dir")


def _draft_to_json(draft: ProjectDraft) -> dict:
    d = dataclasses.asdict(draft)
    # The brush-painted refinement mask is an ndarray — not JSON-serializable
    # and rebuildable from the canvas; it is materialized to a PNG at build().
    d.pop("refinement_mask_array", None)
    for name in _DRAFT_PATH_FIELDS:
        d[name] = str(d[name]) if d[name] is not None else None
    return d


def _draft_from_json(d: dict | None) -> ProjectDraft:
    from al_dic_3d.project.draft import ProjectDraft

    if not d:
        return ProjectDraft()
    valid = {f.name for f in dataclasses.fields(ProjectDraft)}
    kw = {k: v for k, v in d.items() if k in valid}
    for name in _DRAFT_PATH_FIELDS:
        if kw.get(name) is not None:
            kw[name] = Path(kw[name])
    if kw.get("roi") is not None:
        kw["roi"] = tuple(kw["roi"])
    if kw.get("disparity_offset") is not None:
        kw["disparity_offset"] = tuple(kw["disparity_offset"])
    return ProjectDraft(**kw)


# --- results <-> npz ----------------------------------------------------------

_STRAIN_PREFIX = "strain_"


def _result_arrays(result) -> dict:
    cs, rec = result.correspondence, result.reconstruction
    arrays = {
        "strategy": np.asarray(result.strategy),
        "ref_coords": result.ref_coords,
        "xL": cs.xL,
        "xR": cs.xR,
        "quality": cs.quality,
        "cs_source": cs.source,
        "points3D": rec.points,
        "displacement3D": rec.displacement,
        "reproj_error": rec.reproj_error,
        "rec_source": rec.source,
    }
    if result.strain is not None:
        from al_dic_3d.strain3d import STRAIN_FIELDS

        for name in STRAIN_FIELDS:
            arrays[f"{_STRAIN_PREFIX}{name}"] = getattr(result.strain, name)
    return arrays


def _result_from_arrays(arrays: dict, ref_coords: np.ndarray, strategy: str, meta: dict):
    from al_dic_3d.matching.contracts import CorrespondenceSet
    from al_dic_3d.reconstruct import Reconstruction3D
    from al_dic_3d.runner import RunResult

    cs = CorrespondenceSet(
        strategy=strategy,
        xL=arrays["xL"],
        xR=arrays["xR"],
        quality=arrays["quality"],
        source=arrays["cs_source"],
    )
    rec = Reconstruction3D(
        points=arrays["points3D"],
        displacement=arrays["displacement3D"],
        reproj_error=arrays["reproj_error"],
        source=arrays["rec_source"],
    )
    strain = None
    strain_keys = [k for k in arrays if k.startswith(_STRAIN_PREFIX)]
    if strain_keys:
        from al_dic_3d.strain3d import STRAIN_FIELDS, StrainResult3D

        strain = StrainResult3D(**{n: arrays[f"{_STRAIN_PREFIX}{n}"] for n in STRAIN_FIELDS})
    return RunResult(
        strategy=strategy,
        ref_coords=ref_coords,
        correspondence=cs,
        reconstruction=rec,
        strain=strain,
        meta=meta,
    )


# --- save / load --------------------------------------------------------------


def save_session(state: AppState3D, path: str | Path) -> Path:
    """Write ``state`` to ``path`` as a ``.aldic3d`` bundle; return the path."""
    path = Path(path)
    session = {
        "schema_version": SCHEMA_VERSION,
        "config": _config_to_json(state.config) if state.config is not None else None,
        "draft": _draft_to_json(state.draft),
        "view_state": state.view_state,
        "workflow_step": int(state.workflow_step),
        "strategy": state.result.strategy if state.result is not None else None,
        "meta": state.result.meta if state.result is not None else {},
        "has_results": state.result is not None,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(_CONFIG_NAME, json.dumps(session, indent=2))
        if state.result is not None:
            buf = io.BytesIO()
            np.savez_compressed(buf, **_result_arrays(state.result))
            zf.writestr(_RESULTS_NAME, buf.getvalue())
    return path


def parse_session(path: str | Path) -> Session3DData:
    """Parse a ``.aldic3d`` file into :class:`Session3DData` (no AppState3D needed)."""
    path = Path(path)
    if not zipfile.is_zipfile(path):
        raise SessionError(f"{path} is not a .aldic3d bundle (expected a zip)")
    with zipfile.ZipFile(path, "r") as zf:
        names = set(zf.namelist())
        if _CONFIG_NAME not in names:
            raise SessionError(f"{path} is missing {_CONFIG_NAME}")
        session = json.loads(zf.read(_CONFIG_NAME))
        version = int(session.get("schema_version", -1))
        if version != SCHEMA_VERSION:
            raise SessionError(f"unsupported session schema {version} (expected {SCHEMA_VERSION})")
        result_arrays = None
        if session.get("has_results") and _RESULTS_NAME in names:
            with np.load(io.BytesIO(zf.read(_RESULTS_NAME)), allow_pickle=False) as npz:
                result_arrays = dict(npz.items())
    return Session3DData(
        schema_version=version,
        config=_config_from_json(session.get("config")),
        draft=_draft_from_json(session.get("draft")),
        view_state=session.get("view_state", {}),
        workflow_step=int(session.get("workflow_step", 0)),
        meta={**session.get("meta", {}), "_strategy": session.get("strategy")},
        result_arrays=result_arrays,
    )


def load_session(path: str | Path) -> AppState3D:
    """Load a ``.aldic3d`` file into a fresh :class:`AppState3D`."""
    data = parse_session(path)
    result = None
    if data.result_arrays is not None:
        strategy = data.meta.get("_strategy") or str(data.result_arrays["strategy"])
        meta = {k: v for k, v in data.meta.items() if k != "_strategy"}
        result = _result_from_arrays(
            data.result_arrays, data.result_arrays["ref_coords"], strategy, meta
        )
    return AppState3D(
        draft=data.draft,
        config=data.config,
        result=result,
        view_state=data.view_state,
        workflow_step=data.workflow_step,
        project_path=Path(path),
        dirty=False,
    )
