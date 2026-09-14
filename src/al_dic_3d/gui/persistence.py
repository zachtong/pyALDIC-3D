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


def _deleted(path: str) -> bool:
    """True when ``path`` is gone from a folder that is still reachable."""
    p = Path(path)
    return not p.exists() and p.parent.exists()


def recent_projects() -> list[str]:
    """Most-recent-first ``.aldic3d`` paths; deleted files are pruned in place.

    A file is pruned only when its folder is reachable and the file is gone.
    One on an unplugged drive or an offline share stays listed (fix batch V: it
    used to be dropped for good); the menu shows it disabled until it is back.
    """
    s = settings()
    raw = s.value(_RECENT_KEY, [])
    if isinstance(raw, str):  # QSettings collapses a 1-item list to a string
        raw = [raw]
    paths = [str(p) for p in (raw or [])]
    kept = [p for p in paths if not _deleted(p)]
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


def suggested_save_path(name: str, key: str, near=None) -> str:
    """The file a save dialog proposes: in ``near``'s folder, else the last
    folder used for ``key``, else the home folder.

    Never a bare file name: that resolves against the working directory, which
    for an application started from a shortcut is not the user's data (the
    same fix 2D made in 0.8.0).
    """
    candidates = (Path(str(near)).parent if near else None, last_dir(key))
    for folder in candidates:
        if folder and Path(folder).is_dir():
            return str(Path(folder) / name)
    return str(Path.home() / name)
