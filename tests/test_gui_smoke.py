"""Offscreen smoke test of the Qt shell (Phase 4).

Constructs the real MainWindow3D under the offscreen Qt platform and walks the 8
workflow steps + a menu action, asserting no crash and that the view stays in sync
with the controller. No display required; skipped if PySide6 is absent.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")

from al_dic_3d.gui.app import create_app  # noqa: E402
from al_dic_3d.gui.controller import N_STEPS  # noqa: E402
from al_dic_3d.gui.main_window import MainWindow3D  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


def test_mainwindow_constructs_and_walks_steps(qapp):
    win = MainWindow3D()
    assert win._steps.count() == N_STEPS
    assert win._stack.count() == N_STEPS
    assert win.windowTitle()  # translated title, non-empty

    for step in range(N_STEPS):
        win._steps.setCurrentRow(step)
        assert win.controller.state.workflow_step == step
        assert win._stack.currentIndex() == step
    win.close()


def test_menu_new_project_does_not_crash(qapp):
    win = MainWindow3D()
    win._new_project()  # resets state + status bar
    assert win.controller.state.workflow_step == 0
    win.close()


def test_pages_populate_the_draft(qapp):
    win = MainWindow3D()
    draft = win.controller.state.draft

    roi_page = win._pages[3]
    roi_page._xmin.setValue(10)
    roi_page._xmax.setValue(200)
    roi_page._ymin.setValue(20)
    roi_page._ymax.setValue(180)
    assert draft.roi == (10, 200, 20, 180)

    corr_page = win._pages[4]
    corr_page._strategy.setCurrentText("ref_direct")
    corr_page._strain.setChecked(False)
    assert draft.strategy == "ref_direct" and draft.compute_strain is False

    win._new_project()  # a fresh project resets the draft
    assert win.controller.state.draft.roi is None
    win.close()


def test_run_page_button_reflects_readiness(qapp):
    win = MainWindow3D()
    run_page = win._pages[5]
    assert not run_page._run_btn.isEnabled()  # empty draft -> not runnable
    win.close()
