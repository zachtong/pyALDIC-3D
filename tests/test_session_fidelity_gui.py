"""Batch Z, GUI half — a reloaded session must LOOK and RUN like the saved one.

Two things are proven here that the Qt-free round-trip cannot:

* Restoring ``draft.roi_mask_array`` / ``draft.refinement_mask_array`` actually
  lights the interface back up — the canvas mask engine holds the shaped ROI
  (so the next edit does not destroy it), the blue overlay has pixels, the
  Clear-ROI menu item is live, and the mesh preview snapshot carries both masks
  (mesh preview == the mesh the run will build).
* The saved ``view_state`` is symmetric: every key the save side writes is read
  back on load. Re-capturing after a reload must reproduce the saved dict, so a
  key cannot be saved and then silently never restored — including the canvas
  display toggles (Show Grid / Show Subset / 3D View), which were not captured
  at all before this batch.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import numpy as np
import pytest

pytest.importorskip("PySide6")
cv2 = pytest.importorskip("cv2")

from PySide6.QtCore import QPoint, QPointF  # noqa: E402
from PySide6.QtWidgets import QMenu  # noqa: E402

from al_dic_3d.gui.app import create_app  # noqa: E402
from al_dic_3d.gui.main_window import MainWindow3D  # noqa: E402
from al_dic_3d.gui.panels.mesh_preview import snapshot_preview_params  # noqa: E402
from al_dic_3d.gui.view_state import VIEW_STATE_KEYS  # noqa: E402
from al_dic_3d.project.session import load_session, save_session  # noqa: E402

IMG = 200


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


@pytest.fixture(scope="module")
def scene(tmp_path_factory):
    from tests import synth_parity

    d = tmp_path_factory.mktemp("zfidelity_scene")
    return synth_parity.build_parity_scene(d, img=IMG, n_frames=3, seed=7)


def _loaded_window(scene) -> MainWindow3D:
    win = MainWindow3D()
    draft = win.controller.state.draft
    draft.left = sorted(str(p) for p in scene["dir"].glob("L_*.png"))
    draft.right = sorted(str(p) for p in scene["dir"].glob("R_*.png"))
    draft.calibration_file = scene["dir"] / "calib.yml"
    draft.calibration_format = "opencv_yaml"
    win._left.refresh_all()
    win.signals.images_changed.emit()
    return win


def _reopen(path) -> MainWindow3D:
    """A fresh window that adopted the saved session (the Open-project path)."""
    win = MainWindow3D()
    win.controller.adopt_state(load_session(path))
    win._resync_all()
    return win


def _paint_shaped_roi(area) -> np.ndarray:
    """Polygon ROI with a circular bite, committed through the canvas path."""
    ctrl = area.roi_ctrl
    assert ctrl is not None and ctrl.shape == (IMG, IMG)
    ctrl.add_polygon([(30, 30), (170, 40), (160, 150), (35, 140)], "add")
    ctrl.add_circle(100, 90, 22, "cut")
    area.commit_roi_mask()
    return np.asarray(area.controller.state.draft.roi_mask_array).copy()


def _paint_brush(area) -> np.ndarray:
    canvas = area.canvas
    area.set_refine_brush("paint", 10)
    assert canvas._ensure_brush_buffers()
    canvas._brush_stroke_to(QPointF(70.0, 70.0))
    canvas._brush_stroke_to(QPointF(130.0, 110.0))
    canvas.brush_changed.emit()
    brush = area.controller.state.draft.refinement_mask_array
    assert brush is not None
    return np.asarray(brush).copy()


def _menu_action_states(monkeypatch, area) -> dict[str, bool]:
    """Open the canvas context menu without blocking; report action -> enabled.

    ``_on_canvas_menu`` imports ``QMenu`` lazily inside the function, which is
    the seam: a subclass whose ``exec`` records instead of running a modal event
    loop (which would never return under the offscreen platform).
    """
    captured: dict[str, bool] = {}

    class RecordingMenu(QMenu):
        def exec(self, *_args, **_kwargs):  # noqa: A003 - Qt override
            captured.update({a.text(): a.isEnabled() for a in self.actions() if a.text()})
            return None

    monkeypatch.setattr("PySide6.QtWidgets.QMenu", RecordingMenu)
    area._on_canvas_menu(QPoint(0, 0))
    assert captured, "the context menu never opened"
    return captured


# ---------------------------------------------------------------------------
# Z1 — the reloaded masks light the interface back up
# ---------------------------------------------------------------------------


def test_reloaded_session_restores_the_shaped_roi_on_the_canvas(qapp, scene, tmp_path, monkeypatch):
    win = _loaded_window(scene)
    area = win._canvas_area
    mask = _paint_shaped_roi(area)
    brush = _paint_brush(area)
    signature = win.controller.state.draft.result_signature()
    path = save_session(win.controller.state, tmp_path / "canvas.aldic3d")
    win.close()

    win2 = _reopen(path)
    draft2 = win2.controller.state.draft
    area2 = win2._canvas_area

    # The single store the canvas / mesh preview / strain / export all read.
    assert draft2.roi_mask_array is not None, "shaped ROI lost — Run would use the bbox"
    assert np.array_equal(np.asarray(draft2.roi_mask_array), mask)
    assert draft2.refinement_mask_array is not None, "refinement brush lost — mesh differs"
    assert np.array_equal(np.asarray(draft2.refinement_mask_array) > 0, brush > 0)
    # Same mesh-affecting signature => the re-run builds the SAME mesh.
    assert draft2.result_signature() == signature

    # The canvas mask engine holds it, so the next edit extends the restored ROI
    # instead of replacing it (and Invert cannot invent a whole-image ROI).
    assert area2.roi_ctrl is not None
    assert np.array_equal(area2.roi_ctrl.mask, mask > 0)
    # The blue ROI overlay has pixels.
    assert not area2.canvas._roi_mask_item.pixmap().isNull()
    # Clear ROI is live in the canvas context menu.
    states = _menu_action_states(monkeypatch, area2)
    clear = [text for text in states if "ROI" in text]
    assert clear and all(states[text] for text in clear), states

    # The mesh preview (== the pipeline mesh) sees both masks.
    snap = snapshot_preview_params(draft2, IMG, IMG)
    assert snap["mask"] is not None and snap["refinement_brush"] is not None
    assert np.array_equal(snap["mask"] > 0, mask > 0)
    win2.close()


def test_editing_a_reloaded_project_extends_the_restored_masks(qapp, scene, tmp_path):
    """The next edit must EXTEND the restored masks, never replace them.

    Both the ROI and the refinement brush are edited in canvas-owned buffers.
    Restoring only the draft would leave those buffers empty, so the first
    stroke after reopening would silently throw the restored mask away — the 2D
    app's 'a restored ROI is destroyed by the first edit' bug.
    """
    win = _loaded_window(scene)
    mask = _paint_shaped_roi(win._canvas_area)
    brush = _paint_brush(win._canvas_area)
    path = save_session(win.controller.state, tmp_path / "edit.aldic3d")
    win.close()

    win2 = _reopen(path)
    area2, draft2 = win2._canvas_area, win2.controller.state.draft
    # The canvas brush buffer was seeded from the draft, so the zones are visible…
    assert area2.canvas.brush_mask() is not None, "restored brush never reached the canvas"
    assert np.array_equal(area2.canvas.brush_mask() > 0, brush > 0)

    # …and one more stroke / one more shape only ADDS to what was restored.
    area2.set_refine_brush("paint", 8)
    area2.canvas._brush_stroke_to(QPointF(40.0, 160.0))
    area2.canvas.brush_changed.emit()
    assert np.count_nonzero(np.asarray(draft2.refinement_mask_array) > 0) > int(
        np.count_nonzero(brush > 0)
    )
    assert (np.asarray(draft2.refinement_mask_array) > 0)[brush > 0].all()

    area2.roi_ctrl.add_circle(60, 60, 6, "add")
    area2.commit_roi_mask()
    assert (np.asarray(draft2.roi_mask_array) > 0)[mask > 0].all()
    win2.close()


def test_reloaded_crack_session_is_still_crack_aware(qapp, scene, tmp_path):
    """A thin-barrier ROI keeps its barrier, so the reopened run stays crack-aware."""
    from al_dic_3d.matching.crack_mesh import mask_cuts_mesh
    from al_dic_3d.runner import build_reference_mesh

    win = _loaded_window(scene)
    area = win._canvas_area
    ctrl = area.roi_ctrl
    assert ctrl is not None
    ctrl.add_rectangle(30, 30, 170, 150, "add")
    ctrl.add_rectangle(100, 30, 100, 150, "cut")  # 1-px vertical crack
    area.commit_roi_mask()
    roi = win.controller.state.draft.roi
    path = save_session(win.controller.state, tmp_path / "crack.aldic3d")
    win.close()

    win2 = _reopen(path)
    draft2 = win2.controller.state.draft
    assert draft2.roi_mask_array is not None
    restored = (np.asarray(draft2.roi_mask_array) > 0).astype(np.float64)
    mesh = build_reference_mesh(IMG, IMG, roi, winsize=16, winstepsize=8, mask=restored)
    assert mask_cuts_mesh(mesh, restored), "crack barrier lost on reload"
    win2.close()


# ---------------------------------------------------------------------------
# Z2 — view-state save/restore symmetry, canvas toggles included
# ---------------------------------------------------------------------------

# A distinctive value for every persisted view key. Show Grid defaults ON and
# Show Subset is forced off while the grid is hidden, so the grid-off case gets
# its own test below; between the two, all three toggles are proven non-default.
VIEW_DISTINCTIVE: dict[str, object] = {
    "display_field": "W",
    "colormap": "viridis",
    "color_auto": False,
    "color_min": -0.25,
    "color_max": 1.75,
    "overlay_alpha": 0.4,
    "show_deformed": False,
    "camera": "R",
    "current_frame": 2,
    "display_unit": "µm",
    "frame_rate": 12.5,
    "mesh_line_color": "#3b82f6",
    "mesh_line_width": 4,
    "show_grid": True,
    "show_subset": True,
    "view_3d": True,
}


def _apply_distinctive(win: MainWindow3D, view: dict) -> None:
    s = win.signals
    s.display_field = str(view["display_field"])
    s.colormap = str(view["colormap"])
    s.color_auto = bool(view["color_auto"])
    s.color_min = float(view["color_min"])
    s.color_max = float(view["color_max"])
    s.overlay_alpha = float(view["overlay_alpha"])
    s.show_deformed = bool(view["show_deformed"])
    s.current_camera = str(view["camera"])
    s.current_frame = int(view["current_frame"])
    s.display_unit = str(view["display_unit"])
    s.frame_rate = float(view["frame_rate"])
    s.mesh_line_color = str(view["mesh_line_color"])
    s.mesh_line_width = int(view["mesh_line_width"])
    area = win._canvas_area
    area._grid_cb.setChecked(bool(view["show_grid"]))
    area._subset_cb.setChecked(bool(view["show_subset"]))
    area._view3d_cb.setChecked(bool(view["view_3d"]))


def test_view_state_capture_covers_exactly_the_declared_keys(qapp, scene):
    """``VIEW_STATE_KEYS`` is the one list the save side is built from."""
    win = _loaded_window(scene)
    assert set(win._capture_view_state()) == set(VIEW_STATE_KEYS)
    assert set(VIEW_DISTINCTIVE) == set(VIEW_STATE_KEYS), (
        "a new view_state key needs a distinctive value here so the round-trip "
        "audit below covers it"
    )
    win.close()


def test_view_state_round_trips_through_a_session(qapp, scene, tmp_path):
    """Save -> load -> re-capture must reproduce the saved dict key for key.

    This is the asymmetry guard: a key that is written but never read back
    reverts to its default on reload and the re-captured dict diverges.
    """
    win = _loaded_window(scene)
    _apply_distinctive(win, VIEW_DISTINCTIVE)
    saved = win._capture_view_state()
    assert saved == VIEW_DISTINCTIVE  # the capture reads the live state, not defaults
    win.controller.state.view_state = saved
    path = save_session(win.controller.state, tmp_path / "view.aldic3d")
    win.close()

    win2 = _reopen(path)
    assert win2._capture_view_state() == saved
    # …and the live widgets, not just the captured dict, followed along.
    area = win2._canvas_area
    assert area._grid_cb.isChecked() is True
    assert area._subset_cb.isChecked() is True
    assert area._view3d_cb.isChecked() is True
    assert area._stack.currentIndex() == 1  # the 3D page is showing
    win2.close()


def test_canvas_toggles_off_round_trip(qapp, scene, tmp_path):
    """Show Grid off must survive too (and keep Show Subset disabled)."""
    win = _loaded_window(scene)
    view = {**VIEW_DISTINCTIVE, "show_grid": False, "show_subset": False, "view_3d": False}
    _apply_distinctive(win, view)
    win.controller.state.view_state = win._capture_view_state()
    assert win.controller.state.view_state["show_grid"] is False
    path = save_session(win.controller.state, tmp_path / "gridoff.aldic3d")
    win.close()

    win2 = _reopen(path)
    area = win2._canvas_area
    assert area._grid_cb.isChecked() is False
    assert area._subset_cb.isChecked() is False
    assert not area._subset_cb.isEnabled()  # subset follows the grid
    assert area._stack.currentIndex() == 0
    assert win2._capture_view_state()["show_grid"] is False
    win2.close()
