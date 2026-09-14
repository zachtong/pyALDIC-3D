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

# Translators installed by the latest install_translators() call, in install
# order; removed again by the next call so a language switch never piles up.
_INSTALLED: list = []


def source_ts(locale: str) -> Path:
    """Path to the ``.ts`` source catalog for a locale (may not exist yet)."""
    return _SOURCE_DIR / f"al_dic_3d_{locale}.ts"


def compiled_qm(locale: str) -> Path:
    """Path to the compiled ``.qm`` catalog for a locale (may not exist yet)."""
    return _COMPILED_DIR / f"al_dic_3d_{locale}.qm"


def _al_dic_compiled_dir() -> Path | None:
    """``al_dic/i18n/compiled`` of the installed 2D engine, or ``None``.

    Located through the import system (``find_spec`` does not execute
    ``al_dic.i18n``), so an editable checkout, a wheel and the frozen bundle
    all resolve to their own copy.
    """
    import importlib.util

    try:
        spec = importlib.util.find_spec("al_dic.i18n")
    except (ImportError, ValueError):
        return None
    if spec is None or not spec.submodule_search_locations:
        return None
    return Path(next(iter(spec.submodule_search_locations))) / "compiled"


def al_dic_compiled_qm(locale: str) -> Path | None:
    """Path to the ``al_dic`` (2D engine) catalog for a locale, ``None`` without al_dic."""
    folder = _al_dic_compiled_dir()
    return None if folder is None else folder / f"al_dic_{locale}.qm"


def installed_translators() -> tuple:
    """The translators the latest :func:`install_translators` call installed, in order."""
    return tuple(_INSTALLED)


def install_translators(app, locale: str | None = None) -> str:
    """Install the ``al_dic`` (reused 2D widgets) and ``al_dic_3d`` translators on ``app``.

    ``locale`` defaults to the system locale; a region variant falls back to its
    language (``de_AT`` -> ``de``). The ``al_dic`` catalog is installed FIRST: Qt
    searches the most recently installed translator first, so where both
    catalogs translate the same source string the 3D wording wins. Translators
    from a previous call are removed first, so switching the language replaces
    the catalogs instead of stacking them. A missing ``.qm`` simply leaves those
    strings in the English source (``tr()`` returns its argument). Returns the
    resolved locale name.
    """
    from PySide6.QtCore import QLocale, QTranslator

    for old in _INSTALLED:
        try:
            app.removeTranslator(old)
        except RuntimeError:  # its application (and the translator) is already gone
            pass
    _INSTALLED.clear()

    name = locale or QLocale.system().name()  # e.g. "zh_CN"
    candidates = (name, name.split("_")[0])
    for catalog in (al_dic_compiled_qm, compiled_qm):  # 2D first, so 3D wins
        for base_locale in candidates:
            qm = catalog(base_locale)
            if qm is None or not qm.exists():
                continue
            tr = QTranslator(app)
            if tr.load(str(qm)):
                app.installTranslator(tr)
                _INSTALLED.append(tr)
            break
    return name


__all__ = [
    "LOCALES",
    "TARGET_LOCALES",
    "Leak",
    "al_dic_compiled_qm",
    "compiled_qm",
    "install_translators",
    "installed_translators",
    "scan_file",
    "scan_tree",
    "source_ts",
]
