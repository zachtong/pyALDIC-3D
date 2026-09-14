"""Register the ``.aldic3d`` file type so double-clicking opens pyALDIC-3D.

Port of the 2D ``al_dic.gui.file_association`` (Q6). Windows-only, per-user
(``HKCU\\Software\\Classes``) so no administrator rights are needed. The launch
command is ``pythonw -m al_dic_3d "%1"`` for a source install (the CLI folds a
bare session path into the ``gui`` sub-command, :func:`al_dic_3d.cli.normalize_argv`)
and simply ``pyaldic3d.exe "%1"`` for a frozen build.

Fix batch V mirrored two 2D 0.8.0 fixes: a frozen build registered
``-m al_dic_3d``, which only an interpreter can run (it worked by accident,
because the launcher scans every argument), and an association left pointing
at a deleted or moved copy was reported as current.
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
    """The ``shell\\open\\command`` string used for the association.

    A frozen build's ``sys.executable`` is the application itself, which takes
    the session path as a plain argument; there is no interpreter for ``-m``.
    """
    if getattr(sys, "frozen", False):
        return f'"{Path(sys.executable)}" "%1"'
    return f'"{_launcher()}" -m al_dic_3d "%1"'


def _registered_command() -> str | None:
    """The command currently stored for our ProgID, or None."""
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, rf"Software\Classes\{PROGID}\shell\open\command"
        ) as key:
            value, _ = winreg.QueryValueEx(key, "")
            return value
    except OSError:
        return None


def is_associated() -> bool:
    """True if ``.aldic3d`` currently opens with THIS copy of pyALDIC-3D.

    The stored command is compared as well as the ProgID: after the
    application moved (a reinstall elsewhere, a portable copy deleted), the
    registry still names the old path, and "already associated" would leave a
    dead double-click with nothing in the interface offering to repair it.
    """
    if not is_supported():
        return False
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{EXT}") as key:
            value, _ = winreg.QueryValueEx(key, "")
    except OSError:
        return False
    return value == PROGID and _registered_command() == open_command()


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
