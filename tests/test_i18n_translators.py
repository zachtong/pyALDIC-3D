"""``install_translators`` installs the reused 2D widgets' catalog too (task 6).

The docstring always promised BOTH catalogs; only ``al_dic_3d``'s was loaded,
so every string of a reused ``al_dic`` widget stayed English. The ``al_dic``
catalog is installed first, so the 3D catalog (installed last, searched first)
wins where both translate the same source.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QCoreApplication  # noqa: E402

import al_dic_3d.i18n as i18n  # noqa: E402

# One source string per catalog, each present in only that catalog.
PROBE_2D = ("RightSidebar", "Run DIC Analysis")
PROBE_3D = ("RightSidebar3D", "Run 3D Analysis")


@pytest.fixture
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app
    i18n.install_translators(app, locale="en")  # leave the process in English


def _tr(probe: tuple[str, str]) -> str:
    return QCoreApplication.translate(*probe)


def test_al_dic_catalog_location_is_resolved():
    qm = i18n.al_dic_compiled_qm("zh_CN")
    assert qm is not None and qm.name == "al_dic_zh_CN.qm"
    assert qm.parent.name == "compiled" and qm.parent.parent.name == "i18n"


def test_both_catalogs_translate(qapp):
    assert i18n.install_translators(qapp, locale="zh_CN") == "zh_CN"
    assert _tr(PROBE_2D) == "运行 DIC 分析"  # from al_dic's catalog
    assert _tr(PROBE_3D) == "运行 3D 分析"  # from al_dic_3d's catalog


def test_al_dic_catalog_is_installed_before_the_3d_one(qapp):
    # The 27 (context, source) pairs both catalogs share translate identically,
    # so the order is checked on the installed translators themselves.
    i18n.install_translators(qapp, locale="de")
    order = [Path(t.filePath()).name for t in i18n.installed_translators()]
    assert order == ["al_dic_de.qm", "al_dic_3d_de.qm"]


def test_switching_locale_replaces_the_previous_catalogs(qapp):
    i18n.install_translators(qapp, locale="zh_CN")
    i18n.install_translators(qapp, locale="zh_CN")  # repeated: no pile-up
    assert len(i18n.installed_translators()) == 2
    i18n.install_translators(qapp, locale="de")
    assert _tr(PROBE_3D) == "3D-Analyse starten"
    assert _tr(PROBE_2D) not in ("Run DIC Analysis", "运行 DIC 分析")
    i18n.install_translators(qapp, locale="en")
    assert _tr(PROBE_2D) == "Run DIC Analysis" and _tr(PROBE_3D) == "Run 3D Analysis"
    assert i18n.installed_translators() == ()


def test_region_variant_falls_back_to_the_language(qapp):
    assert i18n.install_translators(qapp, locale="de_AT") == "de_AT"
    assert _tr(PROBE_3D) == "3D-Analyse starten"
    assert _tr(PROBE_2D) != "Run DIC Analysis"


def test_a_missing_al_dic_catalog_is_tolerated(qapp, monkeypatch, tmp_path):
    monkeypatch.setattr(i18n, "_al_dic_compiled_dir", lambda: tmp_path / "missing")
    i18n.install_translators(qapp, locale="zh_CN")
    assert _tr(PROBE_3D) == "运行 3D 分析"
    assert _tr(PROBE_2D) == "Run DIC Analysis"


def test_an_unimportable_al_dic_is_tolerated(qapp, monkeypatch):
    monkeypatch.setattr(i18n, "_al_dic_compiled_dir", lambda: None)
    assert i18n.al_dic_compiled_qm("zh_CN") is None
    i18n.install_translators(qapp, locale="zh_CN")
    assert _tr(PROBE_3D) == "运行 3D 分析"
