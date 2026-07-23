"""Robustness batch R1 — GUI-level regression tests (offscreen).

R1.1: opening a ``.aldic3d`` whose images moved auto-relocates them (prompting
as last resort; cancel aborts the open and leaves the current state untouched).
R1.2: Export enablement after a session load WITH results — the main-window
button (2D 03f30fc) and the strain window opened with results present
(2D 01ed129: export follows results, not strain).
R1.4: the strain window's VSG readout — effective N×N node window plus the
physical size from the mean 3D node spacing.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

from pathlib import Path

import pytest

pytest.importorskip("PySide6")
pytest.importorskip("cv2")

from al_dic_3d.gui.app import create_app  # noqa: E402
from al_dic_3d.gui.controller import WorkflowController  # noqa: E402
from al_dic_3d.gui.main_window import MainWindow3D  # noqa: E402
from al_dic_3d.gui.state import GuiSignals  # noqa: E402
from al_dic_3d.gui.strain_window import StrainWindow3D  # noqa: E402
from al_dic_3d.gui.widgets.strain_param_panel import StrainParamPanel3D  # noqa: E402
from al_dic_3d.project import AppState3D, save_session  # noqa: E402
from al_dic_3d.project.draft import ProjectDraft  # noqa: E402
from tests.test_strain_window import _synthetic_result  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


NAMES = ["f_0001.png", "f_0002.png", "f_0003.png"]


def _write_frames(directory: Path, names: list[str]) -> list[str]:
    directory.mkdir(parents=True, exist_ok=True)
    out = []
    for name in names:
        p = directory / name
        p.write_bytes(b"png")
        out.append(str(p))
    return out


def _save_moved_session(tmp_path: Path) -> Path:
    """Session whose draft points at a gone folder; real frames sit next to it."""
    _write_frames(tmp_path / "left", NAMES)
    _write_frames(tmp_path / "right", NAMES)
    draft = ProjectDraft(
        left=[str(Path("C:/gone/proj/left") / n) for n in NAMES],
        right=[str(Path("C:/gone/proj/right") / n) for n in NAMES],
    )
    return save_session(AppState3D(draft=draft), tmp_path / "moved.aldic3d")


# ---------------------------------------------------------------------------
# R1.1 — session image auto-relocate on open
# ---------------------------------------------------------------------------


def test_open_project_auto_relocates_moved_images(qapp, tmp_path):
    session = _save_moved_session(tmp_path)
    win = MainWindow3D()
    logs: list[tuple[str, str]] = []
    win.signals.log.connect(lambda m, lvl: logs.append((m, lvl)))

    win._open_project_path(str(session))

    state = win.controller.state
    assert state.project_path == session  # the open went through
    assert state.draft.left == [str(tmp_path / "left" / n) for n in NAMES]
    assert state.draft.right == [str(tmp_path / "right" / n) for n in NAMES]
    assert state.dirty  # the rewritten draft must reach the next save
    relocation_logs = [m for m, lvl in logs if "relocated" in m and lvl == "info"]
    assert len(relocation_logs) == 2  # one info line per camera
    assert "camera-L" in relocation_logs[0]
    win.close()


def test_open_project_cancelled_locate_aborts(qapp, tmp_path):
    # No frames anywhere and the (conftest-stubbed) prompt returns None:
    # the open aborts and the CURRENT state stays untouched.
    draft = ProjectDraft(left=[str(Path("C:/gone/x") / n) for n in NAMES], right=[])
    session = save_session(AppState3D(draft=draft), tmp_path / "lost.aldic3d")

    win = MainWindow3D()
    logs: list[tuple[str, str]] = []
    win.signals.log.connect(lambda m, lvl: logs.append((m, lvl)))
    win._open_project_path(str(session))

    assert win.controller.state.project_path is None  # loaded state NOT adopted
    assert win.controller.state.draft.left == []
    assert any("open cancelled" in m and lvl == "warn" for m, lvl in logs)
    win.close()


def test_open_project_prompt_picks_folder(qapp, tmp_path, monkeypatch):
    # Auto-find cannot see the folder (it is outside the session dir); the
    # user's picked directory is validated and adopted.
    elsewhere = tmp_path / "elsewhere"
    _write_frames(elsewhere, NAMES)
    draft = ProjectDraft(left=[str(Path("C:/gone/x") / n) for n in NAMES], right=[])
    session_dir = tmp_path / "sess"
    session_dir.mkdir()
    session = save_session(AppState3D(draft=draft), session_dir / "p.aldic3d")

    prompts: list[tuple[str, bool]] = []

    def fake_prompt(self, camera, old_dir, is_retry):
        prompts.append((camera, is_retry))
        return str(elsewhere)

    monkeypatch.setattr(MainWindow3D, "_prompt_locate_images", fake_prompt)
    win = MainWindow3D()
    win._open_project_path(str(session))

    assert prompts == [("L", False)]
    assert win.controller.state.draft.left == [str(elsewhere / n) for n in NAMES]
    assert win.controller.state.project_path == session
    win.close()


def test_open_project_intact_paths_skip_relocation(qapp, tmp_path, monkeypatch):
    left = _write_frames(tmp_path / "L", NAMES)
    right = _write_frames(tmp_path / "R", NAMES)
    session = save_session(
        AppState3D(draft=ProjectDraft(left=left, right=right)), tmp_path / "ok.aldic3d"
    )

    def boom(self, camera, old_dir, is_retry):
        raise AssertionError("no prompt expected when every path exists")

    monkeypatch.setattr(MainWindow3D, "_prompt_locate_images", boom)
    win = MainWindow3D()
    win._open_project_path(str(session))
    assert win.controller.state.draft.left == left
    assert not win.controller.state.dirty  # untouched load stays clean
    win.close()


# ---------------------------------------------------------------------------
# R1.2 — Export enablement after a session load with results
# ---------------------------------------------------------------------------


def test_main_export_enabled_after_session_load_with_results(qapp, tmp_path):
    session = save_session(
        AppState3D(result=_synthetic_result(), workflow_step=6), tmp_path / "res.aldic3d"
    )
    win = MainWindow3D()
    assert not win._right._export_btn.isEnabled()  # fresh window: no results

    win._open_project_path(str(session))

    assert win.controller.state.has_results
    assert win._right._export_btn.isEnabled()  # 2D 03f30fc regression
    assert win._right._strain_window_btn.isEnabled()
    win.close()


def test_strain_window_export_enabled_when_opened_with_results(qapp):
    # 2D 01ed129: the strain window opens the SAME export dialog as the main
    # window — displacement is exportable before strain is computed, so a
    # strain-only gate must not lock Export when results are present.
    ctrl = WorkflowController()
    ctrl.state.draft.winstepsize = 16
    ctrl.state.result = _synthetic_result()  # results, strain=None
    win = StrainWindow3D(ctrl, GuiSignals())
    assert win._export_btn.isEnabled()
    # Locale-proof tooltip check: test_i18n installs the zh_CN translator on
    # the shared QApplication, so compare through tr(), not a raw substring.
    assert win._export_btn.toolTip() == win.tr(
        "Export displacement and strain results to NPZ / MAT / CSV"
    )
    win.close()


def test_strain_window_export_disabled_without_results(qapp):
    win = StrainWindow3D(WorkflowController(), GuiSignals())
    assert not win._export_btn.isEnabled()
    win.close()


def test_strain_window_export_enabled_via_main_window_after_load(qapp, tmp_path):
    session = save_session(AppState3D(result=_synthetic_result()), tmp_path / "sw.aldic3d")
    win = MainWindow3D()
    win._open_project_path(str(session))
    win._right.open_strain_window_requested.emit()
    sw = win._strain_window
    assert sw is not None and sw._export_btn.isEnabled()
    win.close()


# ---------------------------------------------------------------------------
# R1.4 — VSG N×N node / mm readout in the strain parameter panel
# ---------------------------------------------------------------------------


def test_vsg_readout_shows_effective_node_window(qapp):
    panel = StrainParamPanel3D(winstepsize=16)
    # Default 65 px = (5-1)*16+1 -> the plane fit spans 5x5 nodes.
    assert "5×5" in panel._win_readout.text()
    assert panel._win_readout.isVisible() or panel._win_readout.text()
    panel._win_spin.setValue(33)  # (33-1)/16+1 = 3 -> 3x3
    assert "3×3" in panel._win_readout.text()
    panel._win_spin.setValue(97)  # (97-1)/16+1 = 7 -> 7x7
    assert "7×7" in panel._win_readout.text()
    panel.deleteLater()


def test_vsg_readout_tracks_winstepsize(qapp):
    panel = StrainParamPanel3D(winstepsize=16)
    panel._win_spin.setValue(65)
    panel.set_winstepsize(8)  # 65 px now spans (65-1)/8+1 = 9 nodes
    assert "9×9" in panel._win_readout.text()
    panel.deleteLater()


def test_vsg_readout_mm_appears_with_node_spacing(qapp):
    panel = StrainParamPanel3D(winstepsize=16)
    assert "mm" not in panel._win_readout.text()  # spacing unknown yet
    panel.set_node_spacing_mm(2.0)
    text = panel._win_readout.text()
    # 65 px window at 16 px/node and 2 mm/node -> 65 * 2/16 = 8.125 mm across
    # (rendered "8.12": round-half-even on the exactly-representable 8.125).
    assert "mm" in text and "8.12" in text
    panel.set_node_spacing_mm(None)
    assert "mm" not in panel._win_readout.text()
    panel.deleteLater()


def test_strain_window_wires_node_spacing_from_result(qapp):
    ctrl = WorkflowController()
    ctrl.state.draft.winstepsize = 16
    ctrl.state.result = _synthetic_result()  # 3D grid spacing = 2 mm
    win = StrainWindow3D(ctrl, GuiSignals())
    assert "mm" in win.param_panel()._win_readout.text()
    win.close()


def test_strain_window_no_spacing_without_result(qapp):
    win = StrainWindow3D(WorkflowController(), GuiSignals())
    assert "mm" not in win.param_panel()._win_readout.text()
    win.close()
