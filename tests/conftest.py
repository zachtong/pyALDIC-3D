"""Shared pytest fixtures for pyALDIC-3D.

Holds the cross-file GUI-safety default below; synthetic-scene helpers live in
``tests/synth_*.py`` (mirroring the 2D repo's ``tests/conftest.py`` layout).
"""

from __future__ import annotations

import gc
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
def _qt_native_teardown(_headless_close_guards):
    """Destroy leaked Qt widget trees NATIVELY after every test (crash fix).

    Widget trees like ``ExportDialog`` hold Python reference cycles
    (``tab._dialog`` <-> ``dialog._tabs``), so they die in the CYCLIC garbage
    collector, not by refcount. On Windows + PySide6 6.11, letting the GC
    destroy a C++ ``QWidget`` tree from a wrapper's ``tp_dealloc`` corrupts
    the native heap (STATUS_HEAP_CORRUPTION inside Qt6Widgets' destructor
    cascade). The corruption then detonates at an ARBITRARY later free — the
    intermittent access violations seen in ``wait_for_export``'s
    ``processEvents`` and at interpreter shutdown. Reproducer: two plain
    ``ExportDialog`` construct -> ``gc.collect()`` rounds; ``gc.disable()``
    or deleteLater-first destruction removes the crash entirely.

    So after each test, on the GUI thread: deliver pending queued signals,
    close leaked top-level widgets (their close guards join workers; the
    prompts are stubbed by ``_headless_close_guards``, which this fixture
    depends on so the stubs are still active here), join stray pool tasks,
    then hand every leaked C++ widget tree to Qt via ``deleteLater`` and
    flush it. The ``gc.collect()`` afterwards only frees INVALIDATED
    wrappers — Python never deletes a live C++ widget tree itself. No
    fixture in this suite holds a widget beyond function scope, so any
    top-level widget still alive here is by definition a leak.
    """
    yield
    if "PySide6" not in sys.modules:  # no Qt imported -> no Qt garbage
        return
    from PySide6.QtCore import QCoreApplication, QEvent, QThreadPool
    from PySide6.QtWidgets import QApplication

    app = QCoreApplication.instance()
    if app is None:
        return
    QCoreApplication.processEvents()  # deliver queued signals to live receivers
    if isinstance(app, QApplication):
        for widget in app.topLevelWidgets():
            widget.close()  # runs the G1/G3 close guards -> joins workers
    QThreadPool.globalInstance().waitForDone(10_000)
    if isinstance(app, QApplication):
        for widget in app.topLevelWidgets():
            widget.deleteLater()  # Qt (not Python) deletes the C++ tree
    QCoreApplication.processEvents()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    gc.collect()  # cycles die now; wrappers are already invalidated
    QCoreApplication.processEvents()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


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
