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


def test_run_page_shows_readiness(qapp):
    win = MainWindow3D()
    run_page = win._pages[5]
    run_page.refresh()
    assert "Not ready" in run_page._ready.text()  # empty draft explains what's missing
    win.close()


def test_theme_stylesheet_is_applied(qapp):
    assert len(qapp.styleSheet()) > 100  # the reused pyALDIC dark theme


def test_images_display_and_roi_draws(qapp, tmp_path):
    cv2 = pytest.importorskip("cv2")  # noqa: F841
    from tests import synth_parity

    scene = synth_parity.build_parity_scene(tmp_path, img=200, n_frames=2, seed=7)
    left = sorted(str(p) for p in scene["dir"].glob("L_*.png"))
    right = sorted(str(p) for p in scene["dir"].glob("R_*.png"))

    win = MainWindow3D()
    draft = win.controller.state.draft
    draft.left = left
    draft.right = right

    import_page = win._pages[1]
    import_page.refresh()
    assert import_page._left_view.has_image and import_page._right_view.has_image

    roi_page = win._pages[3]
    roi_page.refresh()
    assert roi_page._view.has_image
    # simulate a drawn ROI -> draft + spinboxes update
    roi_page._view.roi_changed.emit((10, 150, 20, 160))
    assert draft.roi == (10, 150, 20, 160)
    assert roi_page._xmax.value() == 150
    win.close()
