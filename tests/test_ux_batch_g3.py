"""UX Batch G3 — focused tests for the polish items.

Covers: pair-list removal semantics (G3.1a), the canvas right-click gesture
(G3.1b), the empty-state quick-start hint (G3.3), the next-step hint
transitions (G3.4), the log filter/ring buffer/save (G3.5 + G3.1c),
strain-window auto-open-once (G3.6), calibration pick merging (G3.7b),
issue-text mapping (G3.8), the Help dialogs (G3.9), view-state round-trip
(G3.10), the exclusive language group (G3.11), the non-modal export-dialog
singleton (G3.12), and the G3.2 persistence layer (recents pruning, last
dirs, geometry). Offscreen; no pipeline runs needed.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QEvent, QPointF, Qt  # noqa: E402
from PySide6.QtGui import QMouseEvent  # noqa: E402

from al_dic_3d.gui import persistence  # noqa: E402
from al_dic_3d.gui.app import create_app  # noqa: E402
from al_dic_3d.gui.issue_text import issue_text, issues_text  # noqa: E402
from al_dic_3d.gui.main_window import MainWindow3D  # noqa: E402
from al_dic_3d.gui.widgets.image_view import ImageCanvas3D  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


def _mouse_event(kind, pos, button, buttons):
    return QMouseEvent(kind, pos, pos, button, buttons, Qt.KeyboardModifier.NoModifier)


def _right_click(canvas, pos=None):
    pos = pos if pos is not None else QPointF(10, 10)
    canvas.mousePressEvent(
        _mouse_event(
            QEvent.Type.MouseButtonPress,
            pos,
            Qt.MouseButton.RightButton,
            Qt.MouseButton.RightButton,
        )
    )
    canvas.mouseReleaseEvent(
        _mouse_event(
            QEvent.Type.MouseButtonRelease,
            pos,
            Qt.MouseButton.RightButton,
            Qt.MouseButton.NoButton,
        )
    )


# ---------------------------------------------------------------------------
# G3.1a — pair removal updates the draft and invalidates results
# ---------------------------------------------------------------------------


def test_pair_removal_updates_draft_and_invalidates_results(qapp, monkeypatch):
    win = MainWindow3D()
    draft = win.controller.state.draft
    draft.left = ["a.png", "b.png", "c.png"]
    draft.right = ["x.png", "y.png", "z.png"]
    win.controller.state.result = object()  # results present
    win.controller.state.dirty = False

    asked = []
    monkeypatch.setattr(
        type(win._left), "_confirm_invalidate_results", lambda self, n: asked.append(n) or True
    )
    results_events = []
    win.signals.results_changed.connect(lambda: results_events.append(True))

    win._left._remove_pairs([1])
    assert asked == [1]  # confirm consulted with the pair count
    assert draft.left == ["a.png", "c.png"]
    assert draft.right == ["x.png", "z.png"]
    assert win.controller.state.result is None  # Q6 idiom: results invalidated
    assert win.signals.run_state == "idle"
    assert win.controller.state.dirty
    assert results_events  # views told the results are gone
    win.close()


def test_pair_removal_declined_confirm_changes_nothing(qapp, monkeypatch):
    win = MainWindow3D()
    draft = win.controller.state.draft
    draft.left = ["a.png", "b.png"]
    draft.right = ["x.png", "y.png"]
    win.controller.state.result = object()
    monkeypatch.setattr(type(win._left), "_confirm_invalidate_results", lambda self, n: False)
    win._left._remove_pairs([0])
    assert draft.left == ["a.png", "b.png"]  # untouched
    assert win.controller.state.result is not None
    win.controller.state.result = None
    win.close()


def test_pair_removal_without_results_needs_no_confirm(qapp, monkeypatch):
    win = MainWindow3D()
    draft = win.controller.state.draft
    draft.left = ["a.png", "b.png"]
    draft.right = ["x.png", "y.png"]

    def _boom(self, n):
        raise AssertionError("no confirm expected without results")

    monkeypatch.setattr(type(win._left), "_confirm_invalidate_results", _boom)
    win._left._remove_pairs([0, 1])
    assert draft.left == [] and draft.right == []
    win.close()


def test_pair_list_context_menu_suppressed_when_empty(qapp):
    win = MainWindow3D()
    # Empty list: the handler returns before building a menu (would block).
    win._left._pair_list._show_context_menu(QPointF(5, 5).toPoint())
    win.close()


# ---------------------------------------------------------------------------
# G3.1b — canvas right-click gesture (click = menu request, drag = pan only)
# ---------------------------------------------------------------------------


def test_right_click_without_drag_requests_menu(qapp):
    canvas = ImageCanvas3D()
    canvas.set_image_gray(np.zeros((40, 40)))
    requests = []
    canvas.context_menu_requested.connect(lambda p: requests.append(p))
    _right_click(canvas)
    assert len(requests) == 1


def test_right_drag_pans_without_menu(qapp):
    canvas = ImageCanvas3D()
    canvas.set_image_gray(np.zeros((40, 40)))
    requests = []
    canvas.context_menu_requested.connect(lambda p: requests.append(p))
    canvas.mousePressEvent(
        _mouse_event(
            QEvent.Type.MouseButtonPress,
            QPointF(10, 10),
            Qt.MouseButton.RightButton,
            Qt.MouseButton.RightButton,
        )
    )
    canvas.mouseMoveEvent(
        _mouse_event(
            QEvent.Type.MouseMove,
            QPointF(30, 25),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.RightButton,
        )
    )
    canvas.mouseReleaseEvent(
        _mouse_event(
            QEvent.Type.MouseButtonRelease,
            QPointF(30, 25),
            Qt.MouseButton.RightButton,
            Qt.MouseButton.NoButton,
        )
    )
    assert requests == []  # a drag is a pan, never a menu


def test_right_click_suppressed_while_tool_armed_or_imageless(qapp):
    canvas = ImageCanvas3D()
    requests = []
    canvas.context_menu_requested.connect(lambda p: requests.append(p))
    _right_click(canvas)  # no image yet
    assert requests == []
    canvas.set_image_gray(np.zeros((40, 40)))
    canvas.set_tool("rect")  # draw tool armed
    _right_click(canvas)
    assert requests == []


# ---------------------------------------------------------------------------
# G3.3 — canvas empty-state quick-start hint
# ---------------------------------------------------------------------------


def test_empty_state_hint_shows_then_disappears(qapp):
    win = MainWindow3D()
    win.show()
    area = win._canvas_area
    area.render()  # no images loaded
    assert area._empty_hint.isVisible()
    area.canvas.set_image_gray(np.zeros((40, 40)))
    area._update_empty_hint()
    assert not area._empty_hint.isVisible()
    win.close()


# ---------------------------------------------------------------------------
# G3.4 — next-step hint transitions
# ---------------------------------------------------------------------------


def test_next_step_hint_transitions(qapp):
    win = MainWindow3D()
    win.show()
    hint = win._left._next_hint
    draft = win.controller.state.draft

    assert hint.isVisible()
    assert hint.text() == hint.tr("Load the left and right camera folders")

    draft.left = ["a.png", "b.png"]
    draft.right = ["x.png", "y.png"]
    win.signals.images_changed.emit()
    assert hint.text() == hint.tr("Calibrate from images or import a calibration")

    draft.calibration_file = Path("calib.yml")
    win.signals.calibration_changed.emit()
    assert hint.text() == hint.tr("Draw the ROI on the left camera, frame 1")

    draft.roi = (0, 10, 0, 10)
    win.signals.roi_changed.emit()
    assert not hint.isVisible()  # ready -> hidden

    # Mismatch surfaces the translated issue detail (still the images stage).
    draft.right = ["x.png"]
    win.signals.images_changed.emit()
    assert hint.isVisible()
    assert hint.text() == issue_text("sequence length mismatch: 2 vs 1")
    win.close()


# ---------------------------------------------------------------------------
# G3.5 + G3.1c — log ring buffer, severity filter, save
# ---------------------------------------------------------------------------


def test_log_filter_rerenders_from_ring_buffer(qapp):
    win = MainWindow3D()
    right = win._right
    right._on_clear_log()  # drop the construction-time messages
    right._append_log("plain info", "info")
    right._append_log("a warning", "warning")  # alias normalizes to 'warn'
    right._append_log("an error", "error")
    assert len(right._log_entries) == 3
    text = right._console.toPlainText()
    assert "plain info" in text and "a warning" in text and "an error" in text

    right._log_filter.setCurrentIndex(right._log_filter.findData("error"))
    text = right._console.toPlainText()
    assert "an error" in text and "plain info" not in text and "a warning" not in text

    right._log_filter.setCurrentIndex(right._log_filter.findData("warn"))
    text = right._console.toPlainText()
    assert "an error" in text and "a warning" in text and "plain info" not in text

    right._log_filter.setCurrentIndex(right._log_filter.findData("all"))
    assert "plain info" in right._console.toPlainText()

    # Original timestamps survive the re-render (entries carry their stamp).
    level, stamp, _msg = right._log_entries[0]
    assert stamp in right._console.toPlainText()
    win.close()


def test_log_save_writes_full_buffer(qapp, monkeypatch, tmp_path):
    win = MainWindow3D()
    right = win._right
    right._on_clear_log()
    right._append_log("kept line", "info")
    right._append_log("bad line", "error")
    right._log_filter.setCurrentIndex(right._log_filter.findData("error"))  # filter active

    target = tmp_path / "log.txt"
    from PySide6.QtWidgets import QFileDialog

    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: (str(target), ""))
    )
    right._on_save_log()
    content = target.read_text(encoding="utf-8")
    # The save is the FULL unfiltered buffer, with levels.
    assert "[info] kept line" in content and "[error] bad line" in content
    win.close()


def test_clear_log_also_drops_the_buffer(qapp):
    win = MainWindow3D()
    right = win._right
    right._append_log("soon gone", "info")
    right._on_clear_log()
    assert len(right._log_entries) == 0
    right._log_filter.setCurrentIndex(right._log_filter.findData("all"))
    assert "soon gone" not in right._console.toPlainText()  # no resurrection
    win.close()


# ---------------------------------------------------------------------------
# G3.6 — strain window auto-opens only once per session
# ---------------------------------------------------------------------------


def test_strain_window_auto_open_only_once(qapp, monkeypatch):
    win = MainWindow3D()
    opened = []
    monkeypatch.setattr(win, "_open_strain_window", lambda: opened.append(True))
    logs = []
    win.signals.log.connect(lambda m, lv: logs.append(m))
    win.controller.state.result = object()

    win.signals.set_run_state("done")
    assert opened == [True]

    win.signals.set_run_state("idle")
    logs.clear()
    win.signals.set_run_state("done")
    assert opened == [True]  # NOT opened again
    assert win.tr("Strain window available — open it from the sidebar") in logs
    win.controller.state.result = None
    win.close()


# ---------------------------------------------------------------------------
# G3.7b — calibration pick merging (dedupe + natural sort)
# ---------------------------------------------------------------------------


def test_merge_picks_dedupes_and_natural_sorts(qapp):
    from al_dic_3d.gui.dialogs.calibration_support import merge_picks

    first = [r"C:\d\img10.png", r"C:\d\img2.png"]
    merged = merge_picks(first, [r"C:\d\img1.png", r"C:\d\img2.png"])  # img2 repeated
    assert merged == [r"C:\d\img1.png", r"C:\d\img2.png", r"C:\d\img10.png"]


def test_detection_zoom_dialog_constructs(qapp):
    from PySide6.QtGui import QPixmap

    from al_dic_3d.gui.dialogs.calibration_support import DetectionZoomDialog

    pm = QPixmap(64, 32)
    pm.fill(Qt.GlobalColor.darkGray)
    dlg = DetectionZoomDialog(pm, pair_index=2)
    assert dlg.canvas.has_image
    dlg.close()


# ---------------------------------------------------------------------------
# G3.8 — issue-text mapping
# ---------------------------------------------------------------------------


def test_issue_text_maps_known_and_passes_unknown(qapp):
    assert issue_text("ROI not set")  # known: returns a non-empty string
    assert issue_text("sequence length mismatch: 3 vs 5").count("3") == 1
    assert issue_text("some brand-new issue") == "some brand-new issue"  # fallback
    joined = issues_text(["ROI not set", "need at least 2 frames"])
    assert "; " in joined


# ---------------------------------------------------------------------------
# G3.9 — Help dialogs
# ---------------------------------------------------------------------------


def test_about_and_shortcuts_dialogs_construct(qapp):
    import al_dic_3d
    from al_dic_3d.gui.dialogs.about_dialog import AboutDialog, ShortcutsDialog

    about = AboutDialog()
    assert al_dic_3d.__version__  # version string exists and is shown
    about.close()
    shortcuts = ShortcutsDialog()
    shortcuts.close()


# ---------------------------------------------------------------------------
# G3.10 — view-state save/restore round-trip through the .aldic3d session
# ---------------------------------------------------------------------------


def test_view_state_round_trip(qapp, tmp_path):
    from al_dic_3d.project.session import load_session, save_session

    win = MainWindow3D()
    s = win.signals
    draft = win.controller.state.draft
    draft.left = ["a.png", "b.png", "c.png"]
    draft.right = ["x.png", "y.png", "z.png"]
    s.display_field = "W"
    s.colormap = "viridis"
    s.color_auto = False
    s.color_min, s.color_max = -0.25, 1.75
    s.overlay_alpha = 0.4
    s.show_deformed = False
    s.current_camera = "R"
    s.current_frame = 2

    win.controller.state.view_state = win._capture_view_state()
    path = tmp_path / "roundtrip.aldic3d"
    save_session(win.controller.state, path)

    win2 = MainWindow3D()
    win2.controller.adopt_state(load_session(path))
    win2._resync_all()
    s2 = win2.signals
    assert s2.display_field == "W"
    assert s2.colormap == "viridis"
    assert s2.color_auto is False
    assert (s2.color_min, s2.color_max) == (pytest.approx(-0.25), pytest.approx(1.75))
    assert s2.overlay_alpha == pytest.approx(0.4)
    assert s2.show_deformed is False
    assert s2.current_camera == "R"
    assert s2.current_frame == 2
    # The panel widgets mirror the restored state (not just the signal hub).
    assert win2._right._cmap_combo.currentText() == "viridis"
    assert not win2._right._auto_range_cb.isChecked()
    assert win2._right._cam_right_btn.isChecked()
    win.close()
    win2.close()


# ---------------------------------------------------------------------------
# G3.11 — language menu is an exclusive action group
# ---------------------------------------------------------------------------


def test_language_actions_are_exclusive(qapp):
    win = MainWindow3D()
    group = win._language_group
    actions = group.actions()
    assert len(actions) == 8
    assert sum(a.isChecked() for a in actions) == 1
    actions[3].trigger()  # pick another locale
    assert actions[3].isChecked()
    assert sum(a.isChecked() for a in actions) == 1  # radio semantics
    win.close()


# ---------------------------------------------------------------------------
# G3.12 — non-modal export dialog singleton
# ---------------------------------------------------------------------------


def test_export_dialog_is_nonmodal_singleton(qapp, monkeypatch):
    from PySide6.QtCore import QCoreApplication
    from PySide6.QtWidgets import QDialog

    import al_dic_3d.gui.dialogs.export_dialog as ed

    class _StubDialog(QDialog):
        created = 0

        def __init__(self, result, extra_params=None, parent=None, *, draft=None, hint=None):
            super().__init__(parent)
            type(self).created += 1

    monkeypatch.setattr(ed, "ExportDialog", _StubDialog)
    win = MainWindow3D()
    right = win._right
    win.controller.state.result = object()

    right._on_export()
    assert _StubDialog.created == 1
    dialog = right._export_dialog
    assert dialog is not None
    assert not dialog.isModal()  # show(), not exec(): main window stays usable

    right._on_export()  # second click reuses the open dialog
    assert _StubDialog.created == 1
    assert right._export_dialog is dialog

    dialog.close()  # WA_DeleteOnClose -> deferred delete drops the singleton
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    assert right._export_dialog is None

    right._on_export()  # a fresh dialog can be created afterwards
    assert _StubDialog.created == 2
    right.close_export_dialog()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    win.controller.state.result = None
    win.close()


# ---------------------------------------------------------------------------
# G3.2 — persistence: recents pruning, last dirs, window geometry
# ---------------------------------------------------------------------------


def test_recent_projects_prune_dedupe_and_cap(qapp, tmp_path):
    a = tmp_path / "a.aldic3d"
    b = tmp_path / "b.aldic3d"
    a.write_text("x")
    b.write_text("x")
    persistence.add_recent_project(a)
    persistence.add_recent_project(b)
    assert persistence.recent_projects() == [str(b), str(a)]  # most recent first

    persistence.add_recent_project(a)  # re-add moves to front, no duplicate
    assert persistence.recent_projects() == [str(a), str(b)]

    a.unlink()  # deleted from disk -> pruned on the next read
    assert persistence.recent_projects() == [str(b)]

    for i in range(12):  # the list is capped at 8
        p = tmp_path / f"many_{i}.aldic3d"
        p.write_text("x")
        persistence.add_recent_project(p)
    recents = persistence.recent_projects()
    assert len(recents) == persistence.MAX_RECENT
    assert recents[0].endswith("many_11.aldic3d")

    persistence.clear_recent_projects()
    assert persistence.recent_projects() == []


def test_last_dir_stores_parent_of_files(qapp, tmp_path):
    f = tmp_path / "calib.yml"
    f.write_text("x")
    persistence.set_last_dir("calibration", f)
    assert persistence.last_dir("calibration") == str(tmp_path)
    persistence.set_last_dir("images", tmp_path)  # a directory stays itself
    assert persistence.last_dir("images") == str(tmp_path)
    assert persistence.last_dir("never_used") == ""


def test_window_geometry_round_trip(qapp):
    # Plain QMainWindow: no minimum-size clamp interferes with the restore
    # (the offscreen virtual screen is small; restoreGeometry clamps to it).
    from PySide6.QtWidgets import QMainWindow

    w = QMainWindow()
    w.resize(700, 500)
    persistence.save_window_state(w, "test_win")
    w2 = QMainWindow()
    assert persistence.restore_window_state(w2, "test_win")
    assert (w2.width(), w2.height()) == (700, 500)
    assert not persistence.restore_window_state(QMainWindow(), "never_saved")


def test_main_window_saves_and_restores_geometry_keys(qapp, monkeypatch):
    restored, saved = [], []
    monkeypatch.setattr(
        persistence, "restore_window_state", lambda w, key: restored.append(key) or False
    )
    monkeypatch.setattr(persistence, "save_window_state", lambda w, key: saved.append(key))
    win = MainWindow3D()
    assert restored == ["main_window"]
    win.close()  # closeEvent persists the geometry
    assert saved == ["main_window"]


def test_recent_menu_lists_prunes_and_clears(qapp, tmp_path):
    p = tmp_path / "proj.aldic3d"
    p.write_text("x")
    persistence.add_recent_project(p)
    win = MainWindow3D()
    win._populate_recent_menu()
    texts = [a.text() for a in win._recent_menu.actions() if a.text()]
    assert any(str(p) in t for t in texts)
    p.unlink()
    win._populate_recent_menu()  # pruned now
    texts = [a.text() for a in win._recent_menu.actions()]
    assert not any(str(p) in t for t in texts)
    assert any(t == win.tr("No recent projects") for t in texts)
    win.close()
