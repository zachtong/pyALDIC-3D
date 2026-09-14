"""Saving a project must never destroy the previous save (fix batch V, H6).

``save_session`` opened ``ZipFile(path, "w")`` on the real file, so a failure
part-way through (disk full, crash, sync lock) left a truncated bundle and the
previous save was gone — a 7.5 MB session became 697 unreadable bytes. It now
writes a temporary file in the same folder and atomically replaces the target.
Save / open / run failures are also surfaced in a dialog, not only in the log.
"""

from __future__ import annotations

import os

import numpy as np
import pytest

from al_dic_3d.project import AppState3D, ProjectDraft, load_session, save_session
from al_dic_3d.project import session as session_mod


def _state() -> AppState3D:
    s = AppState3D()
    s.draft.left = ["L_0.png", "L_1.png"]
    s.draft.right = ["R_0.png", "R_1.png"]
    s.draft.winsize = 40
    return s


def test_failed_save_leaves_the_previous_file_intact(tmp_path, monkeypatch):
    path = tmp_path / "project.aldic3d"
    save_session(_state(), path)
    before = path.read_bytes()

    def boom(*a, **k):
        raise OSError("No space left on device")

    monkeypatch.setattr(session_mod.json, "dumps", boom)
    with pytest.raises(OSError, match="space"):
        save_session(_state(), path)
    assert path.read_bytes() == before  # untouched
    assert load_session(path).draft.winsize == 40
    leftovers = [p for p in tmp_path.iterdir() if p.name != "project.aldic3d"]
    assert not leftovers, leftovers  # no temp file left behind


def test_successful_save_replaces_the_file(tmp_path):
    path = tmp_path / "project.aldic3d"
    save_session(_state(), path)
    s2 = _state()
    s2.draft.winsize = 24
    save_session(s2, path)
    assert load_session(path).draft.winsize == 24
    assert sorted(p.name for p in tmp_path.iterdir()) == ["project.aldic3d"]


def test_replace_retries_a_transient_sharing_violation(tmp_path, monkeypatch):
    """OneDrive / antivirus can hold the target for a moment on Windows."""
    path = tmp_path / "project.aldic3d"
    save_session(_state(), path)
    real_replace = os.replace
    calls = {"n": 0}

    def flaky(src, dst):
        calls["n"] += 1
        if calls["n"] < 3:
            raise PermissionError(13, "The process cannot access the file")
        return real_replace(src, dst)

    monkeypatch.setattr(session_mod.os, "replace", flaky)
    monkeypatch.setattr(session_mod.time, "sleep", lambda s: None)
    save_session(_state(), path)
    assert calls["n"] == 3
    assert np.isfinite(load_session(path).draft.winsize)


# --------------------------------------------------------------------------- #
# failures are shown, not only logged
# --------------------------------------------------------------------------- #


@pytest.fixture()
def gui(monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    import al_dic_3d.gui.main_window as mw
    from al_dic_3d.gui.panels import right_sidebar as rs

    QApplication.instance() or QApplication([])
    shown: list[tuple[str, str]] = []
    monkeypatch.setattr(mw.MainWindow3D, "_show_error", lambda self, t, m: shown.append((t, m)))
    monkeypatch.setattr(rs.RightSidebar3D, "_show_error", lambda self, t, m: shown.append((t, m)))
    win = mw.MainWindow3D()
    yield win, shown
    win.close()


def test_failed_save_shows_an_error_dialog(gui, monkeypatch, tmp_path):
    win, shown = gui

    def boom(path, include_results=True):
        raise OSError("disk full")

    monkeypatch.setattr(win.controller, "save_project", boom)
    assert win._write_project(str(tmp_path / "x.aldic3d")) is False
    assert shown and "disk full" in shown[-1][1]


def test_failed_open_shows_an_error_dialog(gui, tmp_path):
    win, shown = gui
    bad = tmp_path / "broken.aldic3d"
    bad.write_bytes(b"not a zip")
    win._open_project_path(str(bad))
    assert shown and shown[-1][1]


def test_failed_run_shows_an_error_dialog(gui):
    win, shown = gui
    win._right._on_fail("RuntimeError: frame-1 stereo match found no valid correspondences")
    assert shown and "stereo match" in shown[-1][1]


def test_the_calibration_travels_inside_the_project(tmp_path, monkeypatch):
    # Fix batch V (M8): only the calibration PATH was saved, so a project sent
    # to someone else (or opened after the file moved) had no calibration.
    from al_dic_3d.project import session as session_mod

    calib = tmp_path / "rig" / "calib.yml"
    calib.parent.mkdir()
    calib.write_text("%YAML:1.0\nfake: 1\n", encoding="utf-8")
    state = AppState3D(draft=ProjectDraft(calibration_file=calib))
    bundle = save_session(state, tmp_path / "p.aldic3d")
    calib.unlink()  # the original is gone on this machine

    monkeypatch.setattr(session_mod, "embedded_calibration_dir", lambda: tmp_path / "cache")
    loaded = load_session(bundle)
    restored = loaded.draft.calibration_file
    assert restored.is_file() and restored.name == "calib.yml"
    assert restored.read_text(encoding="utf-8") == "%YAML:1.0\nfake: 1\n"
    assert loaded.open_notes and "restored" in loaded.open_notes[0]
    again = load_session(bundle)  # reopening reuses the same restored copy
    assert again.draft.calibration_file == restored


def test_a_moved_calibration_is_found_by_name(tmp_path):
    from al_dic_3d.project.relocate import relocate_calibration

    draft = ProjectDraft(calibration_file=tmp_path / "old" / "calib.yml")
    (tmp_path / "calib.yml").write_text("x", encoding="utf-8")
    assert relocate_calibration(draft, tmp_path / "p.aldic3d") == tmp_path / "calib.yml"
    assert draft.calibration_file == tmp_path / "calib.yml"
