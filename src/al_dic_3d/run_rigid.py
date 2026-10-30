"""Rigid-motion removal on a whole run result (Qt-free glue).

While rigid motion is removed, ``result.reconstruction`` IS the corrected
reconstruction — every display, strain and export path reads that one field, so
they cannot disagree — and ``result.rigid_motion`` keeps the measured one
(:class:`~al_dic_3d.reconstruct.rigid.RigidMotionState`). Every change of mode or
region refits on that raw reconstruction; mode ``"off"`` restores it. Used by the
pipeline (``[rigid_motion]`` in the config), the GUI and session loading.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.reconstruct.rigid import (
    FIT_OK,
    RIGID_MOTION_MODES,
    RigidMotionState,
    apply_rigid_motion,
    fit_rigid_motion,
    region_to_nodes,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from al_dic_3d.reconstruct import Reconstruction3D
    from al_dic_3d.runner import RunConfig, RunResult

_MIN_NODES = {"translation": 1, "rigid": 3}


def parse_config_section(table: dict, resolve: Callable[[str], Path]) -> tuple[str, Path | None]:
    """``[rigid_motion]`` of a run config -> ``(mode, region_mask path or None)``."""
    section = table.get("rigid_motion", {})
    mode = str(section.get("mode", "off"))
    if mode not in RIGID_MOTION_MODES:
        raise ValueError(f"[rigid_motion].mode must be one of {RIGID_MOTION_MODES}, got {mode!r}")
    region = resolve(str(section["region_mask"])) if "region_mask" in section else None
    return mode, region


def load_fit_region(path: Path, img_shape: tuple[int, int]) -> NDArray[np.bool_]:
    """Read a fit-region mask image (``> 0`` = inside); check its size and content."""
    from al_dic_3d.sequence import load_gray

    try:
        mask = load_gray(path) > 0
    except (OSError, ValueError) as exc:
        raise ValueError(f"cannot read the rigid-motion region mask {path}: {exc}") from exc
    if mask.shape != tuple(img_shape):
        raise ValueError(
            f"rigid-motion region mask is {mask.shape[1]}x{mask.shape[0]} but the images are "
            f"{img_shape[1]}x{img_shape[0]}: {path}"
        )
    if not mask.any():
        raise ValueError(f"rigid-motion region mask is empty: {path}")
    return mask


def config_fit_region(
    cfg: RunConfig, base: Path, img_shape: tuple[int, int]
) -> NDArray[np.bool_] | None:
    """The run's fit region (relative paths resolve against ``base``); ``None`` = all."""
    if cfg.rigid_motion_mode == "off" or cfg.rigid_motion_region is None:
        return None
    path = Path(cfg.rigid_motion_region)
    return load_fit_region(path if path.is_absolute() else base / path, img_shape)


def region_nodes(
    ref_coords: NDArray[np.float64], region: NDArray[np.bool_] | None, mode: str
) -> NDArray[np.bool_] | None:
    """The mesh nodes inside ``region`` (``None`` = all); raise if too few for ``mode``."""
    if region is None:
        return None
    nodes = region_to_nodes(ref_coords, region)
    need = _MIN_NODES[mode]
    if int(nodes.sum()) < need:
        raise ValueError(
            f"the rigid-motion region covers {int(nodes.sum())} mesh node(s); "
            f"{mode} mode needs at least {need}"
        )
    return nodes


def remove_from_reconstruction(
    rec: Reconstruction3D,
    ref_coords: NDArray[np.float64],
    mode: str,
    region: NDArray[np.bool_] | None,
) -> tuple[Reconstruction3D, RigidMotionState | None]:
    """``(corrected, state)``; ``mode == "off"`` returns ``(rec, None)`` unchanged."""
    if mode not in RIGID_MOTION_MODES:
        raise ValueError(f"rigid-motion mode must be one of {RIGID_MOTION_MODES}, got {mode!r}")
    if mode == "off":
        return rec, None
    fit = fit_rigid_motion(rec, mode, node_mask=region_nodes(ref_coords, region, mode))
    return apply_rigid_motion(rec, fit), RigidMotionState(raw=rec, fit=fit, region=region)


def rigid_motion_meta(state: RigidMotionState) -> dict:
    """The JSON summary stored as ``result.meta["rigid_motion"]``."""
    meta = state.fit.to_meta()
    meta["region"] = "all" if state.region is None else "drawn"
    return meta


def rigid_motion_signature(result: RunResult) -> str:
    """Names the rigid-motion setting a result carries (``"off"`` when none).

    Recorded with a computed strain so the Strain window can tell, even after a
    reload, that the strain was computed under a different setting.
    """
    state = getattr(result, "rigid_motion", None)
    if state is None:
        return "off"
    if state.region is None:
        return f"{state.fit.mode}:all"
    bits = np.packbits(np.asarray(state.region, dtype=bool)).tobytes()
    return f"{state.fit.mode}:{hashlib.sha1(bits).hexdigest()[:16]}"


def raw_reconstruction(result: RunResult) -> Reconstruction3D:
    """The measured reconstruction, whether or not rigid motion is removed."""
    state = getattr(result, "rigid_motion", None)
    return state.raw if state is not None else result.reconstruction


def with_rigid_motion(result: RunResult, mode: str, region: NDArray[np.bool_] | None) -> RunResult:
    """``result`` with rigid motion removed per ``mode`` / ``region`` (refit on raw).

    Returns ``result`` itself when nothing changes (Off on a raw result), so a
    no-op never looks like new data to the views.
    """
    if mode == "off" and result.rigid_motion is None and "rigid_motion" not in result.meta:
        return result
    raw = raw_reconstruction(result)
    rec, state = remove_from_reconstruction(raw, result.ref_coords, mode, region)
    meta = {k: v for k, v in result.meta.items() if k != "rigid_motion"}
    if state is not None:
        meta["rigid_motion"] = rigid_motion_meta(state)
    return replace(result, reconstruction=rec, rigid_motion=state, meta=meta)


def with_draft_rigid_motion(result: RunResult, draft) -> tuple[RunResult, str | None]:
    """Apply a project draft's settings; an unusable region gives ``(raw, reason)``.

    Used after a GUI run and when a session opens: the draft is the source of
    truth for the setting, and a region that no longer fits the mesh must not
    cost the user the measured result.
    """
    region = getattr(draft, "rigid_motion_region_array", None)
    region = None if region is None else np.asarray(region) > 0
    try:
        return with_rigid_motion(result, draft.rigid_motion_mode, region), None
    except ValueError as exc:
        return with_rigid_motion(result, "off", None), str(exc)


def summary_lines(state: RigidMotionState) -> list[str]:
    """One plain-text line per frame for the CLI log."""
    fit = state.fit
    angle = fit.angle_rad() * 1e3
    where = "all valid points" if state.region is None else "the drawn region"
    lines = [f"rigid motion removed ({fit.mode}, fitted on {where}):"]
    for k in range(1, fit.n_frames):
        if fit.status[k] != FIT_OK:
            lines.append(f"  frame {k + 1}: not removed ({fit.status[k]}, {fit.n_used[k]} points)")
            continue
        sx, sy, sz = fit.centroid_shift[k] * 1e3
        lines.append(
            f"  frame {k + 1}: shift ({sx:.2f}, {sy:.2f}, {sz:.2f}) um, "
            f"rotation {angle[k]:.4f} mrad, rms {fit.rms[k] * 1e3:.3f} um, "
            f"{fit.n_used[k]} points"
        )
    return lines
