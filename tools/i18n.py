"""i18n tooling — extract tr() strings and compile the 8-locale catalogs.

Wraps the Qt Linguist workflow for pyALDIC-3D's own strings:

    python tools/i18n.py extract   # pyside6-lupdate: gui/*.py -> i18n/source/*.ts
    python tools/i18n.py compile   # pyside6-lrelease: i18n/source/*.ts -> compiled/*.qm
    python tools/i18n.py scan      # static pseudo-locale-clean check on gui/

``extract`` creates/updates one ``.ts`` per target locale (en is the source, so it
has no ``.ts``); fill the new entries (AI-translate every locale to 100% per the
i18n contract), then ``compile``. Deferred until the GUI strings stabilize during
visual iteration so provisional skeleton strings are not translated twice.

Requires ``pyside6-lupdate`` / ``pyside6-lrelease`` (the ``[gui]`` extra).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GUI_DIR = REPO / "src" / "al_dic_3d" / "gui"
SRC_DIR = REPO / "src" / "al_dic_3d" / "i18n" / "source"
QM_DIR = REPO / "src" / "al_dic_3d" / "i18n" / "compiled"
TARGET_LOCALES = ("zh_CN", "zh_TW", "ja", "ko", "de", "fr", "es")


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise SystemExit(f"{name} not found — install the [gui] extra (PySide6)")
    return path


def _gui_sources() -> list[str]:
    return [str(p) for p in sorted(GUI_DIR.rglob("*.py"))]


def extract() -> int:
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    lupdate = _tool("pyside6-lupdate")
    ts_files: list[str] = []
    for loc in TARGET_LOCALES:
        ts_files += ["-ts", str(SRC_DIR / f"al_dic_3d_{loc}.ts")]
    subprocess.run([lupdate, *_gui_sources(), *ts_files], check=True)
    print(f"extracted {len(TARGET_LOCALES)} locale catalogs into {SRC_DIR}")
    return 0


def compile_qm() -> int:
    QM_DIR.mkdir(parents=True, exist_ok=True)
    lrelease = _tool("pyside6-lrelease")
    n = 0
    for ts in sorted(SRC_DIR.glob("al_dic_3d_*.ts")):
        subprocess.run([lrelease, str(ts), "-qm", str(QM_DIR / f"{ts.stem}.qm")], check=True)
        n += 1
    print(f"compiled {n} catalogs into {QM_DIR}")
    return 0


def scan() -> int:
    sys.path.insert(0, str(REPO / "src"))
    from al_dic_3d.i18n import scan_tree

    leaks = scan_tree(GUI_DIR)
    for lk in leaks:
        print(f"{lk.file.relative_to(REPO)}:{lk.line}: {lk.sink}({lk.text!r}) not wrapped in tr()")
    if leaks:
        print(f"{len(leaks)} untranslated user-facing string(s)", file=sys.stderr)
        return 1
    print("i18n scan clean")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    cmd = argv[0] if argv else "scan"
    if cmd == "extract":
        return extract()
    if cmd == "compile":
        return compile_qm()
    if cmd == "scan":
        return scan()
    print(f"usage: python tools/i18n.py [extract|compile|scan]; got {cmd!r}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
