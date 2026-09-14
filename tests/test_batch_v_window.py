"""Main-window behaviour changed by fix batch V (initial guess, menus, close order)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import numpy as np
import pytest

pytest.importorskip("PySide6")

from al_dic_3d.gui import persistence  # noqa: E402
from al_dic_3d.gui.app import create_app  # noqa: E402
from al_dic_3d.gui.main_menu import effective_language  # noqa: E402
from al_dic_3d.gui.main_window import MIN_WINDOW_SIZE, MainWindow3D  # noqa: E402
from al_dic_3d.matching.seed import central_seed_point  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


def test_central_seed_point_is_deep_inside_the_roi():
    assert central_seed_point(None) is None
    assert central_seed_point((10, 30, 20, 60)) == (20.0, 40.0)
    mask = np.zeros((300, 400), bool)
    mask[50:250, 100:300] = True
    mask[140:160, 190:210] = False  # a hole at the centre pushes the point away
    x, y = central_seed_point((100, 299, 50, 249), mask)
    assert mask[int(y), int(x)]
    assert min(x - 100, 299 - x, y - 50, 249 - y) > 30  # far from the outer edge
    assert np.hypot(x - 200, y - 150) > 10  # and off the hole
    assert central_seed_point((0, 1, 0, 1), np.zeros((5, 5))) is None


def test_auto_place_puts_one_point_inside_the_roi(qapp):
    win = MainWindow3D()
    draft = win.controller.state.draft
    win._on_auto_place_seed()  # no ROI yet: nothing placed
    assert draft.seed_points == []
    draft.roi = (40, 160, 20, 120)
    win._left.init_guess_widget._btn_auto.click()
    assert draft.seed_points == [(100.0, 70.0)] and draft.seed_point == (100.0, 70.0)
    win._on_auto_place_seed()  # already placed: left alone
    assert len(draft.seed_points) == 1
    win.close()


def test_the_window_fits_small_laptop_screens(qapp):
    win = MainWindow3D()
    assert (win.minimumWidth(), win.minimumHeight()) == MIN_WINDOW_SIZE
    assert MIN_WINDOW_SIZE[1] <= 672  # 1920x1080 at 150 % leaves 672 px
    win.close()


def test_language_menu_checks_the_language_actually_shown():
    locales = ("en", "zh_CN", "zh_TW", "ja", "ko", "de", "fr", "es")
    assert effective_language("fr", "zh_CN", locales) == "fr"
    assert effective_language(None, "zh_CN", locales) == "zh_CN"
    assert effective_language(None, "de_DE", locales) == "de"
    assert effective_language(None, "pt_BR", locales) == "en"


def test_language_change_is_announced(qapp, monkeypatch):
    win = MainWindow3D()
    notes: list[str] = []
    monkeypatch.setattr(MainWindow3D, "_notify_language_change", lambda self, m: notes.append(m))
    win._on_language("de")
    assert notes and "Deutsch" in notes[0] and "restart" in notes[0]
    assert persistence.settings().value("language") == "de"
    win.close()


def test_recent_projects_keep_unreachable_entries(qapp, tmp_path):
    kept = tmp_path / "gone_drive" / "p.aldic3d"  # folder unreachable
    deleted = tmp_path / "d.aldic3d"
    deleted.write_text("x")
    persistence.add_recent_project(deleted)
    persistence.settings().setValue("recent_projects", [str(kept), str(deleted)])
    deleted.unlink()
    assert persistence.recent_projects() == [str(kept)]


def test_cancelling_the_unsaved_prompt_keeps_the_run_alive(qapp, monkeypatch):
    class FakeWorker:
        stopped = False

        def request_stop(self):
            self.stopped = True

        def wait(self, _ms):
            return True

    win = MainWindow3D()
    worker = FakeWorker()
    monkeypatch.setattr(win._right, "active_worker", lambda: worker)
    monkeypatch.setattr(MainWindow3D, "_confirm_unsaved", lambda self: False)
    assert not win.close()
    assert not worker.stopped  # the user cancelled: the run keeps going
    monkeypatch.setattr(MainWindow3D, "_confirm_unsaved", lambda self: True)
    assert win.close()
    assert worker.stopped


def _ready_window(tmp_path, *, with_seed: bool):
    from tests import synth_stereo

    scene = synth_stereo.build_scene(tmp_path, n_frames=2)
    win = MainWindow3D()
    draft = win.controller.state.draft
    draft.left = sorted(str(p) for p in tmp_path.glob("L_*.png"))
    draft.right = sorted(str(p) for p in tmp_path.glob("R_*.png"))
    draft.calibration_file = scene["dir"] / scene["calib"]
    draft.roi = (40, 160, 40, 160)
    if with_seed:
        draft.seed_points = [(32.0, 32.0)]
    win._right.refresh_readiness()
    return win


def test_run_is_disabled_until_the_project_is_ready(qapp, tmp_path):
    win = MainWindow3D()
    win._right.refresh_readiness()
    assert not win._right._run_btn.isEnabled()
    assert "Not ready" in win._right._run_btn.toolTip()
    win.close()
    win = _ready_window(tmp_path, with_seed=True)
    assert win._right._run_btn.isEnabled()
    assert win._right._ready_lbl.text() == "Ready to run."
    win.close()


def test_ready_without_a_starting_point_says_what_the_run_will_do(qapp, tmp_path):
    win = _ready_window(tmp_path, with_seed=False)
    text = win._right._ready_lbl.text()
    assert text.startswith("Ready to run.") and "found automatically" in text
    win.close()


def test_a_failed_run_keeps_the_stale_hint_for_the_old_results(qapp, tmp_path):
    win = _ready_window(tmp_path, with_seed=True)
    right = win._right
    state = win.controller.state
    right._run_hash = "hash-of-the-results-on-screen"
    right._pending_hash = state.draft.result_signature()  # what _on_run records
    monkey_has_results = type(state).has_results
    try:
        type(state).has_results = property(lambda self: True)
        right._refresh_stale()
        assert right._stale_lbl.isVisibleTo(right)  # draft != shown results
        right._on_fail("boom")
        assert right._run_hash == "hash-of-the-results-on-screen"  # not adopted
        right._on_done()
        assert right._run_hash == right._pending_hash  # adopted on success only
    finally:
        type(state).has_results = monkey_has_results
    win.close()


def test_readiness_checks_that_the_inputs_are_usable(qapp, tmp_path):
    from al_dic_3d.gui.issue_text import issues_text

    win = _ready_window(tmp_path, with_seed=True)
    draft = win.controller.state.draft
    assert draft.readiness_issues() == []
    good = draft.calibration_file

    bad = tmp_path / "broken.yml"
    bad.write_text("not a calibration", encoding="utf-8")
    draft.calibration_file = bad
    win._right.refresh_readiness()
    assert not win._right._run_btn.isEnabled()
    assert "calibration file cannot be read" in win._right._ready_lbl.text()

    draft.calibration_file = good
    draft.right = list(draft.left)  # the same folder dropped on both cameras
    assert "left and right sequences use the same image files" in draft.readiness_issues()
    draft.right = sorted(str(p) for p in tmp_path.glob("R_*.png"))

    draft.roi_mask_array = np.ones((10, 10), bool)  # drawn for other images
    issue = next(i for i in draft.readiness_issues() if i.startswith("ROI mask"))
    assert "10x10" in issues_text([issue])
    win.close()



def test_progress_messages_are_shown_in_plain_words(qapp):
    from al_dic_3d.gui.progress_text import progress_text

    assert progress_text("L: Frame 3/40: S4 done (local ICGN, 2.1s)") == (
        "Left camera: tracking frame 3 of 40"
    )
    assert progress_text("R: verifying frame 2/9") == "Right camera: verifying frame 2 of 9"
    assert progress_text("track_both frame 5/40") == "assembling frame 5 of 40"
    assert progress_text("Setup: frame-1 stereo match at 27170 nodes").startswith("Preparing")
    assert progress_text("something new") == "something new"  # never hidden


def test_velocity_is_per_frame_until_a_frame_rate_is_given(qapp):
    from al_dic_3d.gui.display_units import field_label

    win = MainWindow3D()
    units = win._right._units
    assert not win.signals.frame_rate_known
    assert units._fps_spin.text() == "not set (per frame)"
    assert field_label("velocity", "mm", per_frame=True) == "|V| (mm/frame)"
    units._fps_spin.setValue(25.0)
    assert win.signals.frame_rate_known and win.signals.frame_rate == 25.0
    units._fps_spin.setValue(0.0)
    assert not win.signals.frame_rate_known and win.signals.frame_rate == 1.0
    units.apply_view_state({"frame_rate": 1.0})  # a pre-fix session: 1.0 = not given
    assert not win.signals.frame_rate_known
    win.close()
