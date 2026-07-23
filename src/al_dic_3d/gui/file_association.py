"""Register the ``.aldic3d`` file type so double-clicking opens pyALDIC-3D.

Port of the 2D ``al_dic.gui.file_association`` (Q6). Windows-only, per-user
(``HKCU\\Software\\Classes``) so no administrator rights are needed. The launch
command is ``pythonw -m al_dic_3d "%1"``; the CLI folds a bare session path
into the ``gui`` sub-command (:func:`al_dic_3d.cli.normalize_argv`).
"""

from __future__ import annotations

import sys
from pathlib import Path

PROGID = "pyALDIC3D.Session"
EXT = ".aldic3d"


def is_supported() -> bool:
    """True on platforms where association is implemented (Windows)."""
    return sys.platform == "win32"


def _launcher() -> str:
    """Prefer pythonw.exe (no console window) next to the interpreter."""
    exe = Path(sys.executable)
    candidate = exe.with_name("pythonw.exe")
    return str(candidate if candidate.exists() else exe)


def open_command() -> str:
    """The ``shell\\open\\command`` string used for the association."""
    return f'"{_launcher()}" -m al_dic_3d "%1"'


def is_associated() -> bool:
    """True if ``.aldic3d`` currently points at our ProgID for this user."""
    if not is_supported():
        return False
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{EXT}") as key:
            value, _ = winreg.QueryValueEx(key, "")
            return value == PROGID
    except OSError:
        return False


def register_association() -> None:
    """Register ``.aldic3d`` -> pyALDIC-3D for the current user (HKCU).

    Raises ``RuntimeError`` on unsupported platforms and ``OSError`` if the
    registry cannot be written.
    """
    if not is_supported():
        raise RuntimeError("File association is only supported on Windows.")
    import winreg

    cmd = open_command()
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{EXT}") as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, PROGID)
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{PROGID}") as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "pyALDIC-3D Project")
    with winreg.CreateKey(
        winreg.HKEY_CURRENT_USER,
        rf"Software\Classes\{PROGID}\shell\open\command",
    ) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, cmd)

    # Ask Explorer to pick up the change immediately.
    try:  # pragma: no cover - cosmetic shell refresh
        import ctypes

        SHCNE_ASSOCCHANGED = 0x08000000  # noqa: N806 (Win32 constant name)
        ctypes.windll.shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, 0, None, None)
    except Exception:  # noqa: BLE001, S110 - refresh is best-effort only
        pass


def unregister_association() -> None:
    """Remove the ``.aldic3d`` association for the current user (best effort)."""
    if not is_supported():
        return
    import winreg

    for sub in (
        rf"Software\Classes\{PROGID}\shell\open\command",
        rf"Software\Classes\{PROGID}\shell\open",
        rf"Software\Classes\{PROGID}\shell",
        rf"Software\Classes\{PROGID}",
        rf"Software\Classes\{EXT}",
    ):
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, sub)
        except OSError:  # noqa: PERF203 - per-key best effort
            pass
