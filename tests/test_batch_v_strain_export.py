"""The strain window's export dialog follows the current result (fix batch V, H7).

A rerun, a strain recompute or a project switch makes a new result object; an
export dialog left open on the old one must not keep exporting it.
"""

from __future__ import annotations

import dataclasses
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QCoreApplication, QEvent  # noqa: E402
from PySide6.QtWidgets import QDialog  # noqa: E402

import al_dic_3d.gui.dialogs.export_dialog as ed  # noqa: E402
from al_dic_3d.gui.app import create_app  # noqa: E402
from al_dic_3d.gui.controller import WorkflowController  # noqa: E402
from al_dic_3d.gui.state import GuiSignals  # noqa: E402
from al_dic_3d.gui.strain_window import StrainWindow3D  # noqa: E402
from tests.test_strain_window import _synthetic_result  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


class _StubDialog(QDialog):
    created: list = []

    def __init__(self, result, extra_params=None, parent=None, **_kw):
        super().__init__(parent)
        self._result = result
        self.busy = False
        type(self).created.append(self)

    def matches(self, result):
        return result is self._result

    def is_busy(self):
        return self.busy

    def closeEvent(self, event):  # noqa: N802 - a running export refuses to close
        if self.busy:
            event.ignore()
        else:
            super().closeEvent(event)


def _flush_deletes():
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


@pytest.fixture
def window(qapp, monkeypatch):
    _StubDialog.created = []
    monkeypatch.setattr(ed, "ExportDialog", _StubDialog)
    signals = GuiSignals()
    win = StrainWindow3D(WorkflowController(), signals)
    yield win, signals
    for dlg in _StubDialog.created:
        dlg.busy = False
    win.controller.state.result = None
    win.close()
    _flush_deletes()


def test_a_new_result_gets_a_new_dialog(window):
    win, _signals = window
    win.controller.state.result = first = object()
    win._on_export()
    win._on_export()  # a second click reuses the open dialog
    assert len(_StubDialog.created) == 1
    old = win._export_dialog
    assert old.matches(first)

    win.controller.state.result = object()  # a rerun or a strain recompute
    win._on_export()
    assert len(_StubDialog.created) == 2
    new = win._export_dialog
    assert new is not old and new.matches(win.controller.state.result)
    _flush_deletes()  # the replaced dialog's late destroy must not drop the new one
    assert win._export_dialog is new


def test_a_busy_stale_dialog_stays_up(window):
    win, _signals = window
    win.controller.state.result = object()
    win._on_export()
    old = win._export_dialog
    old.busy = True  # an export is still running on the old result
    win.controller.state.result = object()
    win._on_export()
    assert len(_StubDialog.created) == 1 and win._export_dialog is old


def test_new_results_close_an_idle_stale_dialog(window):
    win, signals = window
    win._connect_signals()  # done by showEvent for a shown window
    win.controller.state.draft.winstepsize = 16
    win.controller.state.result = result = _synthetic_result()
    win._on_export()
    old = win._export_dialog
    assert old.isVisible()
    # A strain recompute writes back a NEW result object (dataclasses.replace).
    win.controller.state.result = dataclasses.replace(result)
    signals.results_changed.emit()
    assert not old.isVisible()
    _flush_deletes()
    assert win._export_dialog is None
