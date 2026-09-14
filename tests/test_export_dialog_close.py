"""The real ExportDialog must close, and must not trap the app (fix batch V, B1).

``ExportDialog.reject()`` called ``self.close()`` and ``closeEvent`` then called
``QDialog.closeEvent``, which calls ``reject()`` again: the nested close was a
no-op, the dialog stayed visible and Qt ignored the event. Close, Esc and the
window X all did nothing, and ``MainWindow3D.close()`` refused too because the
export dialog "declined". The only test used a stub ``QDialog``.
"""

from __future__ import annotations

import os
import threading
import time

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")
pytest.importorskip("al_dic")

from PySide6.QtCore import QCoreApplication, QEvent  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from al_dic_3d.gui.main_window import MainWindow3D  # noqa: E402
from al_dic_3d.runner import load_config, run_pipeline  # noqa: E402
from tests import synth_stereo  # noqa: E402


@pytest.fixture(scope="module")
def small_result(tmp_path_factory):
    d = tmp_path_factory.mktemp("export_close")
    scene = synth_stereo.build_scene(d, n_frames=2)
    return run_pipeline(load_config(synth_stereo.write_config(d, scene)))


@pytest.fixture()
def qapp():
    return QApplication.instance() or QApplication([])


def _flush() -> None:
    QCoreApplication.processEvents()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def _open_export(win: MainWindow3D, result):
    win.controller.state.result = result
    win._right._on_export()
    _flush()
    dlg = win._right._export_dialog
    assert dlg is not None and dlg.isVisible()
    return dlg


def test_close_button_closes_the_real_dialog(qapp, small_result):
    win = MainWindow3D()
    win.show()
    dlg = _open_export(win, small_result)
    assert dlg.close() is True
    _flush()
    assert win._right._export_dialog is None  # DeleteOnClose dropped the singleton
    win.close()


def test_escape_closes_the_real_dialog(qapp, small_result):
    win = MainWindow3D()
    win.show()
    dlg = _open_export(win, small_result)
    dlg.reject()  # what Esc does
    _flush()
    assert win._right._export_dialog is None
    win.close()


def test_main_window_closes_after_export_was_opened(qapp, small_result):
    win = MainWindow3D()
    win.show()
    _open_export(win, small_result)
    assert win.close() is True
    _flush()
    assert not win.isVisible()


def test_running_export_close_guard_still_asks(qapp, small_result, monkeypatch):
    import al_dic_3d.gui.dialogs.export_dialog as ed

    win = MainWindow3D()
    win.show()
    dlg = _open_export(win, small_result)
    release = threading.Event()
    tab = dlg._data_tab
    tab.start_job(lambda progress, stop: release.wait(5) or [])
    assert tab.is_busy()

    monkeypatch.setattr(ed.ExportDialog, "_confirm_close_during_export", lambda self: False)
    assert dlg.close() is False  # user chose to keep the export running
    assert dlg.isVisible()

    monkeypatch.setattr(ed.ExportDialog, "_confirm_close_during_export", lambda self: True)
    release.set()
    assert dlg.close() is True
    _flush()
    win.close()


def test_a_worker_outliving_the_join_is_detached_not_destroyed(qapp, small_result):
    """Deleting a still-running QThread aborts the process (2D 0.7.2 crash)."""
    from al_dic_3d.gui.dialogs.export_tabs import common

    win = MainWindow3D()
    win.show()
    dlg = _open_export(win, small_result)
    tab = dlg._images_tab
    done = threading.Event()

    def stubborn(progress, stop):  # ignores the stop request for a while
        time.sleep(0.6)
        done.set()
        return []

    tab.start_job(stubborn)
    worker = tab._worker
    tab.shutdown(timeout_ms=20)
    assert worker in common._ORPHANED_WORKERS
    assert worker.parent() is None
    assert dlg.close() is True
    _flush()
    assert done.wait(5)
    worker.wait(5000)
    common._prune_orphans()
    assert worker not in common._ORPHANED_WORKERS
    win.close()
