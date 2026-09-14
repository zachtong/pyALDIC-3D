"""``.aldic3d`` session save / load (Qt-free), following the 2D envelope design.

A session is a versioned ZIP bundle so a project resumes exactly where it was left,
including a completed run (a long computation is never lost on close):

    session.json         - schema version, the reproducible RunConfig, UI view
                           state, workflow step, and the run metadata
    results.npz          - the correspondence / reconstruction / strain arrays
                           (present only when a run has completed)
    roi_mask.png         - the canvas-drawn arbitrary-shape ROI mask
    refinement_mask.png  - the brush-painted refinement mask

The two mask members are OPTIONAL and additive (absent when nothing was
painted, and absent in every pre-batch-Z bundle), so ``SCHEMA_VERSION`` stays 1
and old sessions keep loading. They are not decoration: the ROI mask is what
bounds correlation, the crack barrier, the strain gauge and the exports, and
the refinement brush is freehand — neither is rebuildable from anything else in
the bundle, so dropping them silently changed what a reopened project computed.

Schema is versioned (:data:`SCHEMA_VERSION`); an unknown version raises
:class:`SessionError` rather than silently loading a newer format. Parsing is
separated from applying (via :class:`Session3DData`) so it is unit-testable without
constructing an :class:`AppState3D`.
"""

from __future__ import annotations

import dataclasses
import io
import json
import os
import time
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
# ProjectDraft mask ARRAY field -> optional PNG member carrying it. ndarrays are
# not JSON-serializable, so these ride beside session.json instead of inside it.
_MASK_MEMBERS = {
    "roi_mask_array": "roi_mask.png",
    "refinement_mask_array": "refinement_mask.png",
}
# Fix batch V (M8): the calibration file travels inside the bundle, so a
# project opened on another machine (or after the file moved) still has it.
_CALIB_PREFIX = "calibration/"
_CALIB_EMBED_MAX_BYTES = 50 * 2**20
_PATH_FIELDS = ("calibration_file", "output_dir", "base_dir")
_OPT_PATH_FIELDS = ("refinement_mask", "roi_mask")  # Path | None on RunConfig


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
    calibration_blob: tuple[str, bytes] | None = None  # (file name, bytes) if embedded


def _new_draft() -> ProjectDraft:
    from al_dic_3d.project.draft import ProjectDraft

    return ProjectDraft()


# --- RunConfig <-> JSON -------------------------------------------------------


def _config_to_json(config: RunConfig) -> dict:
    d = dataclasses.asdict(config)
    for name in _PATH_FIELDS:
        d[name] = str(d[name])
    for name in _OPT_PATH_FIELDS:
        if d.get(name) is not None:
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
    for name in _OPT_PATH_FIELDS:
        if kw.get(name) is not None:
            kw[name] = Path(kw[name])
    if "roi" in kw and kw["roi"] is not None:
        kw["roi"] = tuple(kw["roi"])
    if kw.get("disparity_offset") is not None:
        kw["disparity_offset"] = tuple(kw["disparity_offset"])
    if kw.get("seed_point") is not None:
        kw["seed_point"] = tuple(kw["seed_point"])
    # ``dataclasses.asdict`` always emits ``seed_points`` (an empty tuple ()
    # serializes to []), so guard on presence, NOT truthiness: an empty list is
    # falsy but must still coerce to the tuple () — leaving a mutable list on a
    # frozen RunConfig breaks equality (``[] != ()``) and hashability. When the
    # multi-seed KEY is entirely ABSENT (a pre-Batch-S session) migrate the legacy
    # single ``seed_point`` into the list so old sessions stay self-consistent.
    raw_seed_points = kw.get("seed_points")
    if raw_seed_points is None and kw.get("seed_point") is not None:
        raw_seed_points = [kw["seed_point"]]
    if raw_seed_points is not None:
        kw["seed_points"] = tuple((float(p[0]), float(p[1])) for p in raw_seed_points)
    if kw.get("ref_update_frames") is not None:
        kw["ref_update_frames"] = tuple(int(f) for f in kw["ref_update_frames"])
    return RunConfig(**kw)


_DRAFT_PATH_FIELDS = ("calibration_file", "output_dir")


def _draft_to_json(draft: ProjectDraft) -> dict:
    d = dataclasses.asdict(draft)
    # The canvas-painted masks are ndarrays: not JSON-serializable, so they
    # travel as the bundle's optional PNG members (_MASK_MEMBERS) instead.
    for name in _MASK_MEMBERS:
        d.pop(name, None)
    for name in _DRAFT_PATH_FIELDS:
        d[name] = str(d[name]) if d[name] is not None else None
    return d


def _mask_members(draft: ProjectDraft) -> dict[str, bytes]:
    """Encode whichever canvas masks the draft carries as ``member -> PNG bytes``."""
    from al_dic_3d.project.draft import encode_mask_png

    out: dict[str, bytes] = {}
    for name, member in _MASK_MEMBERS.items():
        array = getattr(draft, name, None)
        if array is not None:
            out[member] = encode_mask_png(array)
    return out


def _apply_mask_members(draft: ProjectDraft, zf: zipfile.ZipFile, names: set[str]) -> None:
    """Restore the mask arrays from the bundle's PNG members (absent -> None).

    Absent members are the pre-batch-Z / nothing-painted case and leave the
    field at ``None``; a member that is PRESENT but undecodable is an error —
    silently returning None there is exactly the data loss this member fixes.
    """
    from al_dic_3d.project.draft import decode_mask_png

    for name, member in _MASK_MEMBERS.items():
        if member not in names:
            continue
        try:
            setattr(draft, name, decode_mask_png(zf.read(member)))
        except (OSError, ValueError) as exc:
            raise SessionError(f"corrupt mask member {member}: {exc}") from exc


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
    if kw.get("seed_point") is not None:
        kw["seed_point"] = tuple(kw["seed_point"])
    # ``ProjectDraft.seed_points`` is the surface the GUI trusts (readout +
    # markers); ``build()`` only falls back to the legacy ``seed_point`` via
    # ``_effective_seed_points``. When the multi-seed KEY is entirely ABSENT (a
    # pre-Batch-S session) migrate the legacy single seed into the list so an old
    # session surfaces its seed instead of reading "no points placed". A
    # present-but-empty list is left untouched (a current no-seed draft). Kept a
    # list (mutable) to match the field type + the canvas edit path.
    raw_seed_points = kw.get("seed_points")
    if raw_seed_points is None and kw.get("seed_point") is not None:
        raw_seed_points = [kw["seed_point"]]
    if raw_seed_points is not None:
        kw["seed_points"] = [(float(p[0]), float(p[1])) for p in raw_seed_points]
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
        # Batch C item 3: persist the DENSE strain's validity stack (edge-trim
        # UNION crack-trim) as an OPTIONAL array — absent when trimming was off,
        # and absent in pre-Batch-C archives (loaded back as None; SCHEMA_VERSION
        # stays 1, no migration needed).
        if result.strain.strain_valid is not None:
            arrays["strain_valid"] = np.asarray(result.strain.strain_valid)
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
    if f"{_STRAIN_PREFIX}exx" in arrays:
        from al_dic_3d.strain3d import STRAIN_FIELDS, StrainResult3D
        from al_dic_3d.strain3d.gradients import von_mises_strain

        # strain_valid is optional (absent in pre-Batch-C archives / no-trim runs).
        valid = arrays["strain_valid"] if "strain_valid" in arrays else None
        fields = {n: arrays[f"{_STRAIN_PREFIX}{n}"] for n in STRAIN_FIELDS}
        # von Mises is re-derived from the stored components: sessions saved
        # before fix batch V hold the old formula's values (shear counted
        # twice); for newer ones this reproduces the stored bits exactly.
        fields["von_mises"] = von_mises_strain(fields["exx"], fields["eyy"], fields["exy"])
        strain = StrainResult3D(**fields, strain_valid=valid)
    return RunResult(
        strategy=strategy,
        ref_coords=ref_coords,
        correspondence=cs,
        reconstruction=rec,
        strain=strain,
        meta=meta,
    )


# --- save / load --------------------------------------------------------------


def estimated_result_nbytes(result) -> int:
    """Uncompressed byte size of the arrays a with-results save would write (Q7)."""
    total = 0
    for arr in _result_arrays(result).values():
        total += int(np.asarray(arr).nbytes)
    return total


def save_session(state: AppState3D, path: str | Path, *, include_results: bool = True) -> Path:
    """Write ``state`` to ``path`` as a ``.aldic3d`` bundle; return the path.

    ``include_results=False`` (Q7) writes a small configuration-only session:
    the results member is skipped and ``has_results`` is False, so the file
    loads back with ``result is None`` (shareable, recompute to restore).
    """
    path = Path(path)
    save_results = include_results and state.result is not None
    session = {
        "schema_version": SCHEMA_VERSION,
        "config": _config_to_json(state.config) if state.config is not None else None,
        "draft": _draft_to_json(state.draft),
        "view_state": state.view_state,
        "workflow_step": int(state.workflow_step),
        "strategy": state.result.strategy if save_results else None,
        "meta": state.result.meta if save_results else {},
        "has_results": save_results,
    }
    calib = _calibration_member(state.draft)
    if calib is not None:
        session["calibration_member"] = calib[0]
    path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic save (fix batch V): write a temporary bundle NEXT TO the target and
    # replace it only once complete. Writing straight onto ``path`` meant any
    # failure part-way (disk full, crash, a sync client holding the file)
    # destroyed the previous save along with the new one.
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        _write_bundle(tmp, session, state, save_results)
        with open(tmp, "rb+") as fh:
            os.fsync(fh.fileno())
        _replace_with_retry(tmp, path)
    except BaseException:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return path


def _replace_with_retry(src: Path, dst: Path, attempts: int = 5) -> None:
    """``os.replace`` that rides out a transient Windows sharing violation.

    Antivirus scanners and sync clients (OneDrive) briefly open freshly written
    files; ``os.replace`` then raises ``PermissionError`` for a moment.
    """
    for i in range(attempts):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if i == attempts - 1:
                raise
            time.sleep(0.1 * (i + 1))


def _calibration_member(draft: ProjectDraft) -> tuple[str, bytes] | None:
    """``(member, bytes)`` of the draft's calibration file, if it can travel."""
    path = draft.calibration_file
    if path is None:
        return None
    try:
        p = Path(path)
        if not p.is_file() or p.stat().st_size > _CALIB_EMBED_MAX_BYTES:
            return None
        return (_CALIB_PREFIX + p.name, p.read_bytes())
    except OSError:
        return None


def _write_bundle(path: Path, session: dict, state: AppState3D, save_results: bool) -> None:
    """Write the ``.aldic3d`` zip members to ``path``."""
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(_CONFIG_NAME, json.dumps(session, indent=2))
        calib = _calibration_member(state.draft)
        if calib is not None:
            zf.writestr(calib[0], calib[1])
        # The canvas-painted masks (binary, image-sized): DEFLATEd PNGs, tiny.
        for member, blob in _mask_members(state.draft).items():
            zf.writestr(member, blob)
        if save_results:
            # P2.5: stream the results member instead of materializing it in a
            # BytesIO + getvalue() copy (2x peak memory), and STORE it — the
            # npz payload is already DEFLATE-compressed per array, so wrapping
            # it in a second DEFLATE only burned CPU for ~0 size gain.
            info = zipfile.ZipInfo(_RESULTS_NAME, date_time=time.localtime(time.time())[:6])
            info.compress_type = zipfile.ZIP_STORED
            with zf.open(info, "w", force_zip64=True) as member:
                np.savez_compressed(member, **_result_arrays(state.result))


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
        draft = _draft_from_json(session.get("draft"))
        _apply_mask_members(draft, zf, names)
        calibration_blob = None
        member = session.get("calibration_member")
        if member and member in names and member.startswith(_CALIB_PREFIX):
            calibration_blob = (Path(member).name, zf.read(member))
        result_arrays = None
        if session.get("has_results") and _RESULTS_NAME in names:
            with np.load(io.BytesIO(zf.read(_RESULTS_NAME)), allow_pickle=False) as npz:
                result_arrays = dict(npz.items())
    return Session3DData(
        schema_version=version,
        config=_config_from_json(session.get("config")),
        draft=draft,
        view_state=session.get("view_state", {}),
        workflow_step=int(session.get("workflow_step", 0)),
        meta={**session.get("meta", {}), "_strategy": session.get("strategy")},
        result_arrays=result_arrays,
        calibration_blob=calibration_blob,
    )


def embedded_calibration_dir() -> Path:
    """Per-user folder where embedded calibrations are restored."""
    base = os.environ.get("LOCALAPPDATA") or str(Path.home())
    return Path(base) / "pyALDIC-3D" / "embedded_calibrations"


def _restore_calibration(draft: ProjectDraft, blob: tuple[str, bytes]) -> Path | None:
    """Write the embedded calibration to the per-user folder; its path, or None.

    The folder is keyed by the file's content, so reopening a project reuses
    the same copy instead of piling up new ones.
    """
    import hashlib

    name, data = blob
    target = embedded_calibration_dir() / hashlib.sha256(data).hexdigest()[:16] / name
    try:
        if not (target.is_file() and target.read_bytes() == data):
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    except OSError:
        return None
    draft.calibration_file = target
    return target


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
    notes: list[str] = []
    calib = data.draft.calibration_file
    missing = calib is None or not Path(calib).is_file()
    if data.calibration_blob is not None and missing:
        restored = _restore_calibration(data.draft, data.calibration_blob)
        if restored is not None:
            notes.append(f"calibration restored from the project file: {restored}")
    return AppState3D(
        draft=data.draft,
        config=data.config,
        result=result,
        view_state=data.view_state,
        workflow_step=data.workflow_step,
        project_path=Path(path),
        dirty=False,
        open_notes=notes,
    )
