"""tools/i18n_batch_audit.py covers the new-user audit strings, and they load at runtime.

Keeps the batch in step with the extracted sources (no stale rows, all seven
target locales, real translations, placeholders intact) and checks that each
translation context the strings live in resolves under a translator.
"""

from __future__ import annotations

import importlib.util
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from al_dic_3d.i18n import TARGET_LOCALES

_REPO = Path(__file__).resolve().parents[1]
_BATCH = _REPO / "tools" / "i18n_batch_audit.py"
_TS = _REPO / "src" / "al_dic_3d" / "i18n" / "source" / "al_dic_3d_zh_CN.ts"


def _batch() -> dict[str, dict[str, str]]:
    spec = importlib.util.spec_from_file_location("i18n_batch_audit", _BATCH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.BATCH


def _contexts() -> dict[str, str]:
    """English source -> the translation context lupdate filed it under."""
    out: dict[str, str] = {}
    for ctx in ET.parse(_TS).getroot().iter("context"):
        name = ctx.findtext("name")
        for m in ctx.iter("message"):
            out.setdefault(m.findtext("source"), name)
    return out


def test_batch_covers_all_seven_locales_with_one_key_set():
    batch = _batch()
    assert set(batch) == set(TARGET_LOCALES)
    assert len({frozenset(table) for table in batch.values()}) == 1


def test_every_batch_source_is_a_live_catalog_string():
    stale = set(next(iter(_batch().values()))) - set(_contexts())
    assert not stale, f"batch rows no source string uses any more: {sorted(stale)}"


def test_translations_are_real_and_keep_placeholders():
    for locale, table in _batch().items():
        for source, text in table.items():
            assert text and text != source, (locale, source)
            placeholders = sorted(re.findall(r"\{\d\}", text))
            assert placeholders == sorted(re.findall(r"\{\d\}", source)), (locale, source)


def test_every_string_translates_at_runtime():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QCoreApplication
    from PySide6.QtWidgets import QApplication

    from al_dic_3d.i18n import install_translators

    app = QApplication.instance() or QApplication([])
    contexts = _contexts()
    table = _batch()["ja"]
    install_translators(app, locale="ja")
    try:
        for source, want in table.items():
            assert QCoreApplication.translate(contexts[source], source) == want, source
    finally:
        install_translators(app, locale="en")
