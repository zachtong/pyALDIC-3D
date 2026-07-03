"""i18n — translation catalogs and runtime loading.

pyALDIC-3D's own ``.ts`` / ``.qm`` catalogs (``i18n/source`` / ``i18n/compiled``)
for the 8-locale contract (en source + zh_CN, zh_TW, ja, ko, de, fr, es). At
runtime :func:`install_translators` installs BOTH the ``al_dic`` (reused 2D
widgets) and ``al_dic_3d`` catalogs so every string is translated from its own
source. Compute code never calls ``tr()`` — it raises English keys and the view
translates (see :mod:`al_dic_3d.i18n.scan`, the enforceable gate).

Layer: presentation (GUI).  Lands: Phase 4.  Spec: docs/architecture/01 §B.1.
"""

from __future__ import annotations

from pathlib import Path

from al_dic_3d.i18n.scan import LOCALES, TARGET_LOCALES, Leak, scan_file, scan_tree

_COMPILED_DIR = Path(__file__).parent / "compiled"
_SOURCE_DIR = Path(__file__).parent / "source"


def source_ts(locale: str) -> Path:
    """Path to the ``.ts`` source catalog for a locale (may not exist yet)."""
    return _SOURCE_DIR / f"al_dic_3d_{locale}.ts"


def compiled_qm(locale: str) -> Path:
    """Path to the compiled ``.qm`` catalog for a locale (may not exist yet)."""
    return _COMPILED_DIR / f"al_dic_3d_{locale}.qm"


def install_translators(app, locale: str | None = None) -> str:
    """Install the ``al_dic_3d`` (and, if present, ``al_dic``) translators on ``app``.

    ``locale`` defaults to the system locale. Missing ``.qm`` files simply leave the
    UI in the English source (``tr()`` returns its argument). Returns the resolved
    locale name.
    """
    from PySide6.QtCore import QLocale, QTranslator

    name = locale or QLocale.system().name()  # e.g. "zh_CN"
    for base_locale in (name, name.split("_")[0]):
        qm = compiled_qm(base_locale)
        if qm.exists():
            tr = QTranslator(app)
            if tr.load(str(qm)):
                app.installTranslator(tr)
            break
    return name


__all__ = [
    "LOCALES",
    "TARGET_LOCALES",
    "Leak",
    "compiled_qm",
    "install_translators",
    "scan_file",
    "scan_tree",
    "source_ts",
]
