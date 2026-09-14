"""Left-sidebar behaviour changed by fix batch V (H5, H10, thresholds, reveal)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import numpy as np
import pytest

pytest.importorskip("PySide6")
cv2 = pytest.importorskip("cv2")

from al_dic_3d.gui.app import create_app  # noqa: E402
from al_dic_3d.gui.main_window import MainWindow3D  # noqa: E402
from al_dic_3d.gui.panels import pair_actions  # noqa: E402
from al_dic_3d.gui.panels.sidebar_images import split_stereo_names  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


@pytest.mark.parametrize(
    ("names", "pattern"),
    [
        (["L_0001.tif", "L_0002.tif", "R_0001.tif", "R_0002.tif"], "L_ / R_ prefix"),
        (["0000_0.tif", "0000_1.tif", "0001_0.tif", "0001_1.tif"], "_0 / _1 suffix"),
        (["img_cam0_01.png", "img_cam1_01.png"], "cam0 / cam1"),
        (["left_01.png", "right_01.png"], "left / right"),
        (["s_L.png", "s_R.png"], "_L / _R suffix"),
    ],
)
def test_one_folder_with_both_cameras_is_split(names, pattern):
    left, right, found = split_stereo_names(names)
    assert found == pattern
    assert len(left) == len(right) and not set(left) & set(right)


def test_a_single_camera_folder_is_not_split():
    assert split_stereo_names(["frame_0001.tif", "frame_0002.tif"]) is None
    assert split_stereo_names(["Lamp_01.png", "Rock_01.png"]) is None
    assert split_stereo_names(["L_0001.tif", "R_0001.tif", "calib.tif"]) is None


def test_dropping_one_folder_on_both_zones_loads_each_camera(qapp, tmp_path):
    for name in ("L_0001", "L_0002", "R_0001", "R_0002"):
        cv2.imwrite(str(tmp_path / f"{name}.png"), np.zeros((20, 30), np.uint8))
    win = MainWindow3D()
    win._left._load_camera("L", str(tmp_path))
    win._left._load_camera("R", str(tmp_path))
    draft = win.controller.state.draft
    assert [os.path.basename(p) for p in draft.left] == ["L_0001.png", "L_0002.png"]
    assert [os.path.basename(p) for p in draft.right] == ["R_0001.png", "R_0002.png"]
    win.close()


def test_threshold_controls_edit_the_draft(qapp):
    win = MainWindow3D()
    left = win._left
    draft = win.controller.state.draft
    left._gate_spin.setValue(1.5)
    left._stereo_znssd_spin.setValue(0.4)
    left._epipolar_spin.setValue(3.0)
    assert (draft.temporal_gate_znssd, draft.stereo_znssd_max, draft.stereo_epipolar_max_px) == (
        1.5,
        0.4,
        3.0,
    )
    draft.temporal_gate_znssd = 0.0
    left.refresh_all()
    assert left._gate_spin.value() == 0.0 and left._gate_spin.text() == "off"
    win.close()


def test_row_labels_are_never_cut(qapp):
    win = MainWindow3D()
    for lbl in win._left._row_labels:
        need = lbl.fontMetrics().horizontalAdvance(lbl.text())
        assert lbl.width() >= min(need, 132 - 6) or lbl.wordWrap()
    widths = {lbl.width() for lbl in win._left._row_labels}
    assert len(widths) == 1  # one aligned column
    win.close()


def test_per_frame_masks_are_checked_and_adopted(qapp, tmp_path):
    frames = []
    for k in range(2):
        p = tmp_path / f"L_{k}.png"
        cv2.imwrite(str(p), np.zeros((40, 60), np.uint8))
        frames.append(str(p))
    masks = []
    for k in range(2):
        m = np.zeros((40, 60), np.uint8)
        m[10:30, 15:45] = 255
        p = tmp_path / f"M_{k}.png"
        cv2.imwrite(str(p), m)
        masks.append(str(p))
    win = MainWindow3D()
    draft = win.controller.state.draft
    draft.left = frames
    section = win._left._frame_masks
    assert not section.load_folder("L", str(tmp_path), masks[:1])  # wrong count
    assert draft.left_masks is None
    assert section.load_folder("L", str(tmp_path), masks)
    assert draft.left_masks == masks
    assert draft.roi == (15, 44, 10, 29)  # no ROI drawn: the first mask is adopted
    assert "2 masks" in section._status["L"].text()
    section._clear("L")
    assert draft.left_masks is None
    win.close()


def test_reveal_selects_the_file(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(pair_actions.subprocess, "Popen", lambda args: calls.append(args))
    target = tmp_path / "L_0001.png"
    target.write_bytes(b"x")
    pair_actions.reveal_in_file_manager(target)
    import sys

    if sys.platform == "win32":
        assert calls == [["explorer", f"/select,{target}"]]
    elif sys.platform == "darwin":
        assert calls == [["open", "-R", str(target)]]
