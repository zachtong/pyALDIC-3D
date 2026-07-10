"""UX Batch G2 — focused tests for the high-frequency experience items.

Covers: zoom clamp + readout (G2.4), manual color range (G2.2), percentile
auto-range (G2.3), keyboard shortcuts (G2.5), cancel feedback (G2.6),
stale-params indicator (G2.7), save workflow + window title (G2.8), and the
drop-zone loaded state (G2.9). Offscreen; no pipeline runs needed.
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
from PySide6.QtGui import QKeyEvent, QMouseEvent  # noqa: E402

from al_dic_3d.gui.app import create_app  # noqa: E402
from al_dic_3d.gui.main_window import MainWindow3D  # noqa: E402
from al_dic_3d.gui.widgets.image_view import ZOOM_MAX, ZOOM_MIN, ImageCanvas3D  # noqa: E402
from al_dic_3d.project.draft import ProjectDraft  # noqa: E402
from al_dic_3d.viz3d.fieldmap import auto_range  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


def _key_event(key, kind=QEvent.Type.KeyPress):
    return QKeyEvent(kind, key, Qt.KeyboardModifier.NoModifier)


def _mouse_event(kind, pos, button, buttons):
    # 6-arg (non-deprecated) ctor: localPos, scenePos, button, buttons, mods.
    return QMouseEvent(kind, pos, pos, button, buttons, Qt.KeyboardModifier.NoModifier)


# ---------------------------------------------------------------------------
# G2.4 — zoom clamp, zoom readout, right-drag / Space pan
# ---------------------------------------------------------------------------


def test_zoom_is_clamped(qapp):
    canvas = ImageCanvas3D()
    canvas.set_image_gray(np.random.default_rng(0).random((50, 50)))
    canvas.zoom_to_100()
    for _ in range(40):
        canvas.zoom_in()
    assert canvas.zoom_level == pytest.approx(ZOOM_MAX)
    for _ in range(80):
        canvas.zoom_out()
    assert canvas.zoom_level == pytest.approx(ZOOM_MIN)


def test_zoom_readout_follows_and_resets(qapp):
    win = MainWindow3D()
    canvas = win._canvas_area.canvas
    canvas.set_image_gray(np.zeros((40, 40)))
    canvas.zoom_to_100()
    assert win._canvas_area._zoom_btn.text() == "100%"
    canvas.zoom_in()  # 1.25x
    assert win._canvas_area._zoom_btn.text() == "125%"
    win._canvas_area._zoom_btn.click()  # reset to 100%
    assert canvas.zoom_level == pytest.approx(1.0)
    assert win._canvas_area._zoom_btn.text() == "100%"
    win.close()


def test_right_button_drag_pans(qapp):
    canvas = ImageCanvas3D()
    canvas.set_image_gray(np.zeros((40, 40)))
    press = _mouse_event(
        QEvent.Type.MouseButtonPress,
        QPointF(10, 10),
        Qt.MouseButton.RightButton,
        Qt.MouseButton.RightButton,
    )
    canvas.mousePressEvent(press)
    assert canvas._panning and canvas._pan_button == Qt.MouseButton.RightButton
    release = _mouse_event(
        QEvent.Type.MouseButtonRelease,
        QPointF(20, 15),
        Qt.MouseButton.RightButton,
        Qt.MouseButton.NoButton,
    )
    canvas.mouseReleaseEvent(release)
    assert not canvas._panning


def test_space_switches_to_pan_mode(qapp):
    canvas = ImageCanvas3D()
    canvas.set_image_gray(np.zeros((40, 40)))
    canvas.keyPressEvent(_key_event(Qt.Key.Key_Space))
    assert canvas._space_pan  # hand-drag pan mode armed
    # Left press while Space is held starts a pan, not a tool.
    press = _mouse_event(
        QEvent.Type.MouseButtonPress,
        QPointF(10, 10),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
    )
    canvas.mousePressEvent(press)
    assert canvas._panning and canvas._pan_button == Qt.MouseButton.LeftButton
    release = _mouse_event(
        QEvent.Type.MouseButtonRelease,
        QPointF(12, 12),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.NoButton,
    )
    canvas.mouseReleaseEvent(release)
    canvas.keyReleaseEvent(_key_event(Qt.Key.Key_Space, QEvent.Type.KeyRelease))
    assert not canvas._space_pan and not canvas._panning


# ---------------------------------------------------------------------------
# G2.3 — percentile auto-range helper
# ---------------------------------------------------------------------------


def test_auto_range_clips_outliers():
    vals = np.concatenate([np.linspace(0.0, 1.0, 98), [50.0, -50.0], [np.nan]])
    lo, hi = auto_range(vals)
    exp_lo, exp_hi = np.nanpercentile(vals[np.isfinite(vals)], [2.0, 98.0])
    assert (lo, hi) == (pytest.approx(float(exp_lo)), pytest.approx(float(exp_hi)))
    assert -50.0 < lo and hi < 50.0  # outliers no longer stretch the range


def test_auto_range_empty_is_unit_interval():
    assert auto_range(np.array([np.nan, np.nan])) == (0.0, 1.0)
    assert auto_range(np.array([])) == (0.0, 1.0)


# ---------------------------------------------------------------------------
# G2.2 — manual color range (right sidebar)
# ---------------------------------------------------------------------------


def test_manual_range_seeds_and_writes_signals(qapp):
    win = MainWindow3D()
    right = win._right
    win.signals.color_min, win.signals.color_max = -1.5, 2.5  # live auto range
    assert not right._vmin_spin.isEnabled()  # disabled while Auto is on

    changed = []
    win.signals.display_changed.connect(lambda: changed.append(True))
    right._auto_range_cb.setChecked(False)
    assert not win.signals.color_auto
    # spins enabled + seeded from the live range
    assert right._vmin_spin.isEnabled() and right._vmax_spin.isEnabled()
    assert right._vmin_spin.value() == pytest.approx(-1.5)
    assert right._vmax_spin.value() == pytest.approx(2.5)

    changed.clear()
    right._vmax_spin.setValue(9.0)
    assert win.signals.color_max == pytest.approx(9.0)
    assert changed  # display_changed emitted -> canvas re-renders

    # Re-checking Auto disables the spins again.
    right._auto_range_cb.setChecked(True)
    assert win.signals.color_auto and not right._vmin_spin.isEnabled()
    win.close()


# ---------------------------------------------------------------------------
# G2.5 — keyboard shortcuts
# ---------------------------------------------------------------------------


def test_arrow_keys_change_frame_and_space_toggles_playback(qapp):
    win = MainWindow3D()
    draft = win.controller.state.draft
    draft.left = ["a.png", "b.png", "c.png"]  # names only; no render happens
    draft.right = ["a.png", "b.png", "c.png"]
    win._canvas_area._frame_nav.set_frame_count(3)

    assert win.signals.current_frame == 0
    win.keyPressEvent(_key_event(Qt.Key.Key_Right))
    assert win.signals.current_frame == 1
    win.keyPressEvent(_key_event(Qt.Key.Key_Left))
    assert win.signals.current_frame == 0
    win.keyPressEvent(_key_event(Qt.Key.Key_Left))  # clamped at frame 1
    assert win.signals.current_frame == 0

    nav = win._canvas_area._frame_nav
    assert not nav._playing
    win.keyPressEvent(_key_event(Qt.Key.Key_Space))
    assert nav._playing
    win.keyPressEvent(_key_event(Qt.Key.Key_Space))
    assert not nav._playing
    win.close()


def test_strain_navigator_step_and_toggle(qapp):
    from al_dic_3d.gui.widgets.strain_navigator import StrainNavigator3D

    nav = StrainNavigator3D()
    nav.set_state(5, 2)
    seen = []
    nav.frame_changed.connect(seen.append)
    nav.step(1)
    assert seen[-1] == 3
    nav.step(-1)
    assert seen[-1] == 2
    nav.toggle_playback()
    assert nav._playing
    nav.toggle_playback()
    assert not nav._playing


# ---------------------------------------------------------------------------
# G2.6 — cancel feedback
# ---------------------------------------------------------------------------


def test_cancel_shows_indeterminate_bar_and_label(qapp):
    win = MainWindow3D()
    right = win._right

    class _FakeWorker:
        stopped = False

        def isRunning(self):  # noqa: N802 (Qt API shape)
            return True

        def request_stop(self):
            self.stopped = True

    right._worker = _FakeWorker()
    right._on_cancel()
    assert right._worker.stopped
    assert (right._progress_bar.minimum(), right._progress_bar.maximum()) == (0, 0)
    # Locale-agnostic: an earlier test in the natural-order suite may have
    # installed a translator on the shared QApplication — compare via tr().
    assert right._progress_lbl.text() == right.tr("Cancelling — finishing current frame…")

    right._worker = None
    right._on_cancelled()  # worker acknowledged the stop
    assert right._progress_bar.maximum() == 1000  # determinate again
    win.close()


# ---------------------------------------------------------------------------
# G2.7 — stale-params indicator
# ---------------------------------------------------------------------------


def test_result_signature_tracks_result_fields_only():
    draft = ProjectDraft()
    sig = draft.result_signature()
    draft.output_prefix = "other"  # output naming must NOT flip the signature
    assert draft.result_signature() == sig
    draft.winsize = 64
    assert draft.result_signature() != sig
    sig2 = draft.result_signature()
    draft.roi_mask_array = np.ones((8, 8), dtype=bool)
    assert draft.result_signature() != sig2  # mask CONTENT is hashed


def test_stale_label_flips_on_param_change(qapp):
    win = MainWindow3D()
    win.show()  # offscreen show: isVisible() reflects setVisible states
    right = win._right
    win.controller.state.result = object()  # results present (type irrelevant here)

    right.refresh_readiness()  # adopts the current draft as the baseline
    assert not right._stale_lbl.isVisible()

    win.controller.state.draft.winsize = 64  # a result-affecting edit
    right.refresh_readiness()
    assert right._stale_lbl.isVisible()

    # A new run start re-baselines and clears the hint.
    right._run_hash = win.controller.state.draft.result_signature()
    right.refresh_readiness()
    assert not right._stale_lbl.isVisible()

    # Results gone (new project) -> hidden and baseline dropped.
    win.controller.state.result = None
    right.refresh_readiness()
    assert not right._stale_lbl.isVisible() and right._run_hash is None
    win.close()


# ---------------------------------------------------------------------------
# G2.8 — save workflow + window title
# ---------------------------------------------------------------------------


def test_save_uses_bound_path_without_dialog(qapp, monkeypatch, tmp_path):
    win = MainWindow3D()
    saved = []
    monkeypatch.setattr(win.controller, "save_project", lambda p: saved.append(Path(p)) or Path(p))
    # Any dialog would be a regression: make it explode if called.
    from PySide6.QtWidgets import QFileDialog

    def _boom(*a, **k):
        raise AssertionError("Save must not open a dialog when project_path is set")

    monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(_boom))

    bound = tmp_path / "proj.aldic3d"
    win.controller.state.project_path = bound
    assert win._save_project() is True
    assert saved == [bound]
    win.close()


def test_save_falls_back_to_save_as_when_unbound(qapp, monkeypatch):
    win = MainWindow3D()
    from PySide6.QtWidgets import QFileDialog

    monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: ("", "")))
    assert win.controller.state.project_path is None
    assert win._save_project() is False  # dialog cancelled -> not saved
    win.close()


def test_window_title_shows_project_and_dirty_star(qapp, monkeypatch, tmp_path):
    win = MainWindow3D()
    # Locale-agnostic (a translator may be installed by an earlier test in the
    # natural-order suite): the unsaved title is '<tr(Untitled)>[*] — pyALDIC-3D'.
    assert "[*]" in win.windowTitle()
    assert win.windowTitle() == win.tr("{0}[*] — pyALDIC-3D").format(win.tr("Untitled"))
    assert not win.isWindowModified()

    # mark_dirty sites always emit a change signal right after (G2.8 route).
    win.controller.state.mark_dirty()
    win.signals.params_changed.emit()
    assert win.isWindowModified()

    monkeypatch.setattr(win.controller, "save_project", lambda p: Path(p))
    win.controller.state.project_path = tmp_path / "demo.aldic3d"
    win.controller.state.dirty = False  # the real save_project clears it
    assert win._save_project() is True
    assert "demo.aldic3d" in win.windowTitle()
    assert not win.isWindowModified()
    win.close()


# ---------------------------------------------------------------------------
# G2.9 — drop-zone loaded state
# ---------------------------------------------------------------------------


def test_drop_zone_loaded_state_and_reset(qapp):
    from al_dic_3d.gui.widgets.camera_drop_zone import CameraDropZone

    zone = CameraDropZone("Drop LEFT camera\nfolder or click")
    zone.set_loaded(r"C:\data\left_cam", 12)
    assert "left_cam" in zone._text.text()
    assert "12" in zone._text.text()
    assert zone.toolTip() == r"C:\data\left_cam"

    zone.reset()
    assert zone._text.text() == "Drop LEFT camera\nfolder or click"
    assert "left_cam" not in zone.toolTip()


def test_sidebar_syncs_drop_zones_from_draft(qapp, tmp_path):
    win = MainWindow3D()
    draft = win.controller.state.draft
    folder = tmp_path / "camL"
    folder.mkdir()
    draft.left = [str(folder / f"img_{i}.png") for i in range(4)]
    win._left.refresh_images()
    assert "camL" in win._left._left_drop._text.text()
    assert "4" in win._left._left_drop._text.text()
    # right camera still empty -> caption state
    assert "4" not in win._left._right_drop._text.text()

    draft.left = []
    win._left.refresh_images()
    assert "camL" not in win._left._left_drop._text.text()
    win.close()
