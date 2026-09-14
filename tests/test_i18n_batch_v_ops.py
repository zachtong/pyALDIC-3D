"""tools/i18n_batch_v_ops.py covers every string the H2 operations fix added.

The batch is merged into the catalogs by the i18n tooling; this keeps it in
step with ``gui/app.py`` (every ``Application`` string, all seven target
locales, real translations, placeholders intact).
"""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path

from al_dic_3d.i18n import TARGET_LOCALES

_REPO = Path(__file__).resolve().parents[1]
_APP = _REPO / "src" / "al_dic_3d" / "gui" / "app.py"
_BATCH = _REPO / "tools" / "i18n_batch_v_ops.py"


def _application_strings() -> set[str]:
    found = set()
    for node in ast.walk(ast.parse(_APP.read_text(encoding="utf-8"))):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "translate"
            and len(node.args) == 2
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "Application"
        ):
            found.add(node.args[1].value)
    return found


def _batch() -> dict[str, dict[str, str]]:
    spec = importlib.util.spec_from_file_location("i18n_batch_v_ops", _BATCH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.BATCH


def test_batch_covers_every_new_string_in_every_locale():
    sources = _application_strings()
    assert len(sources) == 5
    batch = _batch()
    assert set(batch) == set(TARGET_LOCALES)
    for locale, table in batch.items():
        assert set(table) == sources, locale


def test_translations_are_real_and_keep_placeholders():
    for locale, table in _batch().items():
        for source, text in table.items():
            assert text and text != source, (locale, source)
            assert re.findall(r"\{\d\}", text) == re.findall(r"\{\d\}", source), (locale, source)
