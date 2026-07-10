"""Shared pytest fixtures for pyALDIC-3D.

Holds the cross-file GUI-safety default below; synthetic-scene helpers live in
``tests/synth_*.py`` (mirroring the 2D repo's ``tests/conftest.py`` layout).
"""

from __future__ import annotations

import sys

import pytest


@pytest.fixture(autouse=True)
def _headless_close_guards(monkeypatch):
    """Default the Batch-G1 close prompts to 'proceed' for offscreen tests.

    ``MainWindow3D.closeEvent`` may now open a modal QMessageBox (unsaved
    changes / running worker); under the offscreen platform that would block a
    test forever. Stub the prompt seams to their permissive answers; the G1
    guard tests override these per-test with their own monkeypatch (function-
    scoped ``monkeypatch`` is shared, so the test's setattr wins).
    """
    mw = sys.modules.get("al_dic_3d.gui.main_window")
    if mw is not None:
        monkeypatch.setattr(mw.MainWindow3D, "_prompt_unsaved", lambda self: "discard")
        monkeypatch.setattr(mw.MainWindow3D, "_confirm_cancel_run", lambda self: True)
    sw = sys.modules.get("al_dic_3d.gui.strain_window")
    if sw is not None:
        monkeypatch.setattr(sw.StrainWindow3D, "_confirm_close_during_compute", lambda self: True)
    ed = sys.modules.get("al_dic_3d.gui.dialogs.export_dialog")
    if ed is not None:  # G3.12 running-export close guard
        monkeypatch.setattr(ed.ExportDialog, "_confirm_close_during_export", lambda self: True)
    ls = sys.modules.get("al_dic_3d.gui.panels.left_sidebar")
    if ls is not None:  # G3.1a pair-removal results-invalidation confirm
        monkeypatch.setattr(
            ls.LeftSidebar3D, "_confirm_invalidate_results", lambda self, n_pairs: True
        )


@pytest.fixture(autouse=True)
def _isolated_qsettings(monkeypatch, tmp_path):
    """Point the G3.2 persistence layer at a per-test INI file.

    Window-geometry saves, recent-project lists and last-used directories must
    never leak into (or read from) the developer's real registry hive while
    the suite runs.
    """
    try:
        from PySide6.QtCore import QSettings

        from al_dic_3d.gui import persistence as per
    except ImportError:  # PySide6-less environment: nothing to isolate
        return
    ini = str(tmp_path / "test_settings.ini")
    monkeypatch.setattr(per, "settings", lambda: QSettings(ini, QSettings.Format.IniFormat))
