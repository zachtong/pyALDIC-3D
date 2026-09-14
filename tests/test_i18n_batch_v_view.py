"""tools/i18n_batch_v_view.py covers every string the viewer-performance fix added.

The batch is merged into the catalogs by the i18n tooling; this keeps it in
step with the source (every new ``tr()`` string, all seven target locales, real
translations, placeholders intact).
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

from al_dic_3d.i18n import TARGET_LOCALES

_REPO = Path(__file__).resolve().parents[1]
_BATCH = _REPO / "tools" / "i18n_batch_v_view.py"
_NEW_STRINGS = {"Starting the 3D view…": _REPO / "src/al_dic_3d/gui/widgets/view3d.py"}


def _batch() -> dict[str, dict[str, str]]:
    spec = importlib.util.spec_from_file_location("i18n_batch_v_view", _BATCH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.BATCH


def test_new_strings_are_tr_wrapped_in_the_source():
    for text, path in _NEW_STRINGS.items():
        assert f'self.tr("{text}")' in path.read_text(encoding="utf-8"), text


def test_batch_covers_every_new_string_in_every_locale():
    batch = _batch()
    assert set(batch) == set(TARGET_LOCALES)
    for locale, table in batch.items():
        assert set(table) == set(_NEW_STRINGS), locale


def test_translations_are_real_and_keep_placeholders():
    for locale, table in _batch().items():
        for source, text in table.items():
            assert text and text != source, (locale, source)
            assert re.findall(r"\{\d\}", text) == re.findall(r"\{\d\}", source), (locale, source)
