"""tools/i18n_batch_rbm.py covers the rigid-motion strings, and they load at runtime.

The batch is merged into the catalogs by the i18n tooling; this keeps it in step
with the extracted sources (no stale or missing rows, all seven target locales,
real translations, placeholders intact) and checks that the mixin and
``QCoreApplication.translate`` strings resolve under a translator.
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
_BATCH = _REPO / "tools" / "i18n_batch_rbm.py"
_TS = _REPO / "src" / "al_dic_3d" / "i18n" / "source" / "al_dic_3d_zh_CN.ts"
# Sources whose correct translation is spelled like the English in some locale.
_SAME_SPELLING = {
    "translation",
    "translation + rotation",
    "Translation + rotation",
    "+ Rectangle",
    "− Rectangle",
    "+ Polygon",
    "− Polygon",
}


def _batch() -> dict[str, dict[str, str]]:
    spec = importlib.util.spec_from_file_location("i18n_batch_rbm", _BATCH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.BATCH


def test_batch_covers_all_seven_locales_with_one_key_set():
    batch = _batch()
    assert set(batch) == set(TARGET_LOCALES)
    keys = {frozenset(table) for table in batch.values()}
    assert len(keys) == 1


def test_every_batch_source_is_a_live_catalog_string():
    sources = {m.findtext("source") for m in ET.parse(_TS).getroot().iter("message")}
    stale = set(next(iter(_batch().values()))) - sources
    assert not stale, f"batch rows no source string uses any more: {sorted(stale)}"


def test_translations_are_real_and_keep_placeholders():
    for locale, table in _batch().items():
        for source, text in table.items():
            assert text, (locale, source)
            if source not in _SAME_SPELLING:
                assert text != source, (locale, source)
            assert re.findall(r"\{\d\}", text) == re.findall(r"\{\d\}", source), (locale, source)
            assert text.count("\n") == source.count("\n") or "\n" in source, (locale, source)


def test_mixin_and_shared_strings_translate_at_runtime():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from al_dic_3d.i18n import install_translators

    app = QApplication.instance() or QApplication([])
    install_translators(app, locale="zh_CN")
    try:
        from al_dic_3d.gui.controller import WorkflowController
        from al_dic_3d.gui.rigid_motion_text import mode_name
        from al_dic_3d.gui.state import GuiSignals
        from al_dic_3d.gui.strain_window import StrainWindow3D

        assert mode_name("rigid") == "平移 + 转动"  # QCoreApplication.translate context
        win = StrainWindow3D(WorkflowController(), GuiSignals())
        assert win.rigid_motion_panel().status_text() == "未去除刚体运动。"  # mixin context
        win.close()
    finally:
        install_translators(app, locale="en")
