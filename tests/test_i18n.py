"""i18n static scan — the enforceable pseudo-locale gate (Phase 4).

Every user-facing string in the GUI must be wrapped in ``tr()``; a bare literal at
a view sink would render untranslated under any locale. This asserts the GUI
source is clean and that the scanner itself distinguishes wrapped from bare.
"""

from __future__ import annotations

from pathlib import Path

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
