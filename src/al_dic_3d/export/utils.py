"""Shared utility functions for all export backends (Qt-free).

Ported from the 2D platform's ``al_dic.export.export_utils`` (consulted
read-only). Every export ENTRY POINT mints a FRESH :func:`make_timestamp` per
invocation and threads it through the writers, so repeated exports into the
same folder never overwrite earlier ones.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


def frame_tag(i: int, n_frames: int) -> str:
    """Return a 1-based, zero-padded frame label.

    Examples:
        frame_tag(0, 10)   -> "frame_01"
        frame_tag(9, 10)   -> "frame_10"
        frame_tag(0, 100)  -> "frame_001"
    """
    width = len(str(n_frames))
    return f"frame_{i + 1:0{width}d}"


def make_prefix(folder: Path | None) -> str:
    """Derive a safe export filename prefix from a folder name.

    Replaces characters forbidden in Windows filenames (and whitespace) with
    underscores so the prefix can be used on all platforms. Falls back to
    ``"dic3d"`` when no folder is available.
    """
    if folder is None:
        return "dic3d"
    stem = folder.name or "dic3d"
    return re.sub(r'[<>:"/\\|?*\s]', "_", stem)


def make_timestamp() -> str:
    """Return the current local time as a ``YYYYMMDDHHMMSS`` string."""
    return datetime.now().strftime("%Y%m%d%H%M%S")


def ensure_dir(path: Path) -> Path:
    """Create *path* (and any parents) if it does not already exist."""
    path.mkdir(parents=True, exist_ok=True)
    return path
