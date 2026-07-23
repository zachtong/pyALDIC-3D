"""Auto-relocation of moved session image sequences (Qt-free).

A ``.aldic3d`` session stores the left/right frames as absolute paths
(:class:`~al_dic_3d.project.draft.ProjectDraft.left` / ``.right``). When the
user moves or renames the image folders, opening the session used to fail
downstream (empty canvas, broken re-runs). This module relocates the sequences
before the state is adopted (2D ``_resolve_image_folder`` idea, adapted to the
3D per-camera path lists):

1. Auto-find: directories derived from the session file's location — the
   original folder name (and up to two parent components) re-rooted under the
   session directory, the session directory itself, and finally a scan of its
   immediate subdirectories. A candidate is accepted only when EVERY stored
   file name resolves inside it, and the subdirectory scan additionally
   requires a UNIQUE match (L and R frames often share basenames across
   sibling folders — ambiguity must never silently pick the wrong camera).
2. Prompt: when auto-find fails, an injected ``locate_dir_cb`` (the GUI's
   directory picker) is consulted; the picked directory is re-validated the
   same way. Cancelling raises :class:`RelocationCancelled` so the caller can
   abort the open with a clear message.

Masks (``left_masks`` / ``right_masks``) ride along best-effort through the
auto-find step only — they are optional inputs and never worth blocking an
open over.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from al_dic_3d.project.draft import ProjectDraft

# How many trailing components of the original folder path are re-rooted under
# the session directory ("left", "data/left", "proj/data/left").
_SUFFIX_DEPTH = 3

# Bound on locate-prompt retries: a scripted callback that keeps returning an
# invalid directory must not loop forever.
_MAX_PROMPT_ATTEMPTS = 5

# ``(camera, old_dir, is_retry) -> picked directory or None`` — the GUI seam.
LocateDirCb = Callable[[str, str, bool], str | None]


class RelocationCancelled(Exception):
    """The user cancelled (or exhausted) the locate-images prompt."""


@dataclass(frozen=True)
class CameraRelocation:
    """One relocated sequence, for the caller's log line."""

    camera: str  # "L" or "R"
    old_dir: str
    new_dir: str
    n_files: int


def sequence_missing(paths: Sequence[str]) -> bool:
    """True when any stored path no longer exists (empty sequences are fine)."""
    return any(not Path(p).exists() for p in paths)


def resolve_in_dir(paths: Sequence[str], directory: Path) -> list[str] | None:
    """Map every stored path to ``directory / name``; None unless ALL resolve."""
    try:
        if not directory.is_dir():
            return None
    except OSError:
        return None
    out: list[str] = []
    for p in paths:
        cand = directory / Path(p).name
        try:
            if not cand.is_file():
                return None
        except OSError:
            return None
        out.append(str(cand))
    return out


def _dir_candidates(old_dir: Path, session_dir: Path) -> Iterator[Path]:
    """Auto-find candidates, most specific first (see module docstring)."""
    parts = old_dir.parts
    # Trailing components of the original folder, re-rooted under the session
    # dir; drive anchors ("C:\\") must never appear inside a suffix.
    names = [p for p in parts if p != old_dir.anchor]
    for depth in range(1, min(_SUFFIX_DEPTH, len(names)) + 1):
        yield session_dir.joinpath(*names[-depth:])
    yield session_dir


def find_relocated_dir(paths: Sequence[str], session_dir: Path) -> Path | None:
    """Best-effort directory holding ALL of ``paths``'s file names, or None."""
    if not paths:
        return None
    old_dir = Path(paths[0]).parent
    tried: set[Path] = set()
    for cand in _dir_candidates(old_dir, session_dir):
        if cand in tried:
            continue
        tried.add(cand)
        if resolve_in_dir(paths, cand) is not None:
            return cand
    # Last resort: immediate subdirectories of the session dir, accepted only
    # on a UNIQUE match (same basenames may exist in both L and R folders).
    try:
        subdirs = sorted(d for d in session_dir.iterdir() if d.is_dir())
    except OSError:
        return None
    hits = [d for d in subdirs if d not in tried and resolve_in_dir(paths, d) is not None]
    return hits[0] if len(hits) == 1 else None


def _relocate_sequence(
    camera: str,
    paths: list[str],
    session_dir: Path,
    locate_dir_cb: LocateDirCb | None,
) -> list[str] | None:
    """New paths for one camera sequence, or None when nothing was missing.

    Raises:
        RelocationCancelled: the sequence is missing, auto-find failed, and the
            prompt was cancelled / unavailable / exhausted.
    """
    if not paths or not sequence_missing(paths):
        return None
    found = find_relocated_dir(paths, session_dir)
    if found is not None:
        return resolve_in_dir(paths, found)
    old_dir = str(Path(paths[0]).parent)
    if locate_dir_cb is not None:
        for attempt in range(_MAX_PROMPT_ATTEMPTS):
            picked = locate_dir_cb(camera, old_dir, attempt > 0)
            if not picked:
                break
            resolved = resolve_in_dir(paths, Path(picked))
            if resolved is not None:
                return resolved
    raise RelocationCancelled(f"images for camera {camera} not located (was {old_dir})")


def relocate_draft_images(
    draft: ProjectDraft,
    session_path: str | Path,
    locate_dir_cb: LocateDirCb | None = None,
) -> list[CameraRelocation]:
    """Relocate ``draft.left`` / ``draft.right`` (in place) if their files moved.

    Args:
        draft: the just-loaded session draft; its path lists are REWRITTEN on a
            successful relocation so the next save persists the fix.
        session_path: the ``.aldic3d`` file — auto-find searches around it.
        locate_dir_cb: optional ``(camera, old_dir, is_retry) -> dir | None``
            prompt supplied by the GUI when auto-find fails.

    Returns:
        One :class:`CameraRelocation` per rewritten sequence (empty when
        every stored path still exists).

    Raises:
        RelocationCancelled: a sequence could not be located; the caller
            should abort the open and log the exception message.
    """
    session_dir = Path(session_path).parent
    moves: list[CameraRelocation] = []
    for camera, attr in (("L", "left"), ("R", "right")):
        paths = list(getattr(draft, attr))
        new_paths = _relocate_sequence(camera, paths, session_dir, locate_dir_cb)
        if new_paths is None:
            continue
        setattr(draft, attr, new_paths)
        moves.append(
            CameraRelocation(
                camera=camera,
                old_dir=str(Path(paths[0]).parent),
                new_dir=str(Path(new_paths[0]).parent),
                n_files=len(new_paths),
            )
        )
    # Masks are optional: auto-find only, never prompt, never block the open.
    for attr in ("left_masks", "right_masks"):
        paths = getattr(draft, attr) or []
        if not paths or not sequence_missing(paths):
            continue
        found = find_relocated_dir(paths, session_dir)
        if found is not None:
            setattr(draft, attr, resolve_in_dir(paths, found))
    return moves
