"""i18n static scan — the enforceable pseudo-locale gate (Phase 4).

Every user-facing string in the GUI must be wrapped in ``tr()``; a bare literal at
a view sink would render untranslated under any locale. This asserts the GUI
source is clean and that the scanner itself distinguishes wrapped from bare.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from al_dic_3d.i18n import LOCALES, TARGET_LOCALES, scan_file, scan_tree

_GUI = Path(__file__).resolve().parents[1] / "src" / "al_dic_3d" / "gui"


def test_gui_source_is_translation_clean():
    leaks = scan_tree(_GUI)
    detail = "; ".join(f"{lk.file.name}:{lk.line} {lk.sink}({lk.text!r})" for lk in leaks)
    assert not leaks, f"untranslated user-facing strings: {detail}"


def test_scanner_flags_a_bare_literal(tmp_path):
    f = tmp_path / "bad.py"
    f.write_text("label.setText('Bare untranslated text')\n", encoding="utf-8")
    leaks = scan_file(f)
    assert len(leaks) == 1 and leaks[0].sink == "setText"


def test_scanner_accepts_tr_wrapped(tmp_path):
    f = tmp_path / "ok.py"
    f.write_text("label.setText(self.tr('Wrapped text'))\n", encoding="utf-8")
    assert scan_file(f) == []


def test_eight_locale_contract():
    assert LOCALES == ("en", "zh_CN", "zh_TW", "ja", "ko", "de", "fr", "es")
    assert "en" not in TARGET_LOCALES and len(TARGET_LOCALES) == 7


def test_all_locale_catalogs_are_complete():
    # Every target locale ships a fully-translated .ts (no unfinished entries)
    # and a compiled .qm next to it.
    import re

    from al_dic_3d.i18n import compiled_qm, source_ts

    for locale in TARGET_LOCALES:
        ts = source_ts(locale)
        assert ts.exists(), f"missing catalog {ts}"
        text = ts.read_text(encoding="utf-8")
        assert 'type="unfinished"' not in text, f"{locale} has unfinished entries"
        n = len(re.findall(r"<translation>", text))
        assert n >= 100, f"{locale} suspiciously few translations ({n})"
        assert compiled_qm(locale).exists(), f"missing compiled {locale}.qm"


def test_zh_cn_translation_loads_at_runtime():
    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from al_dic_3d.i18n import install_translators

    app = QApplication.instance() or QApplication([])
    install_translators(app, locale="zh_CN")
    from al_dic_3d.gui.main_window import MainWindow3D

    win = MainWindow3D()
    assert win._right._run_btn.text() == "运行 3D 分析"
    win.close()
