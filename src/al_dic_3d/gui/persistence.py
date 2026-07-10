"""GUI persistence (G3.2) — window geometry, recent projects, last-used dirs.

Thin wrappers over ``QSettings('pyALDIC', 'pyALDIC-3D')`` so every persisted
preference goes through ONE factory (:func:`settings`) — tests monkeypatch it
to an isolated INI file and the app never leaks state between test runs. No
user-facing strings live here (menu labels stay in the view layer).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings

MAX_RECENT = 8
_RECENT_KEY = "recent_projects"


def settings() -> QSettings:
    """The application's QSettings store (the single seam tests replace)."""
    return QSettings("pyALDIC", "pyALDIC-3D")


# ---- window geometry ---------------------------------------------------------


def save_window_state(window, key: str) -> None:
    """Persist a window's geometry (and QMainWindow state) under ``key``."""
    s = settings()
    s.setValue(f"{key}/geometry", window.saveGeometry())
    if hasattr(window, "saveState"):
        s.setValue(f"{key}/state", window.saveState())


def restore_window_state(window, key: str) -> bool:
    """Restore a window's geometry/state; False when nothing was stored."""
    s = settings()
    geometry = s.value(f"{key}/geometry")
    restored = bool(geometry is not None and window.restoreGeometry(geometry))
    state = s.value(f"{key}/state")
    if state is not None and hasattr(window, "restoreState"):
        window.restoreState(state)
    return restored


# ---- recent projects ---------------------------------------------------------


def recent_projects() -> list[str]:
    """Most-recent-first ``.aldic3d`` paths; missing files are pruned in place."""
    s = settings()
    raw = s.value(_RECENT_KEY, [])
    if isinstance(raw, str):  # QSettings collapses a 1-item list to a string
        raw = [raw]
    paths = [str(p) for p in (raw or [])]
    kept = [p for p in paths if Path(p).exists()]
    if kept != paths:
        s.setValue(_RECENT_KEY, kept)
    return kept


def add_recent_project(path) -> None:
    """Move ``path`` to the front of the recent list (bounded, deduplicated)."""
    p = str(Path(path))
    items = [x for x in recent_projects() if x != p]
    items.insert(0, p)
    settings().setValue(_RECENT_KEY, items[:MAX_RECENT])


def remove_recent_project(path) -> None:
    p = str(Path(path))
    settings().setValue(_RECENT_KEY, [x for x in recent_projects() if x != p])


def clear_recent_projects() -> None:
    settings().setValue(_RECENT_KEY, [])


# ---- last-used directories (per dialog kind) -----------------------------------


def last_dir(key: str) -> str:
    """Last directory used for the ``key`` dialog kind ('' when unknown)."""
    value = settings().value(f"last_dir/{key}", "")
    return str(value) if value else ""


def set_last_dir(key: str, path) -> None:
    """Remember the directory of ``path`` (a file's parent, or the dir itself)."""
    p = Path(str(path))
    d = p if p.is_dir() else p.parent
    settings().setValue(f"last_dir/{key}", str(d))
