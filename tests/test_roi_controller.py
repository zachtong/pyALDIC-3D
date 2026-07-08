"""ROIController — the Qt-free mask engine behind the ROI toolbox (Batch B).

Rasterization semantics ported from the 2D app: add = union, cut = subtract,
plus freehand strokes, invert, and PNG save/import round-trips.
"""

from __future__ import annotations

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from al_dic_3d.gui.controllers.roi_controller import (  # noqa: E402
    ROIController,
    read_mask_as_bool,
)


def test_rejects_bad_shape():
    with pytest.raises(ValueError, match="img_shape"):
        ROIController((0, 10))


def test_add_and_cut_rectangle():
    ctrl = ROIController((50, 60))
    ctrl.add_rectangle(10, 5, 30, 25, "add")
    assert ctrl.mask[5:26, 10:31].all()  # cv2.rectangle is inclusive of the corner
    assert not ctrl.mask[0:5, :].any()
    n_before = int(ctrl.mask.sum())

    ctrl.add_rectangle(20, 15, 40, 45, "cut")
    assert not ctrl.mask[15:26, 20:31].any()  # overlap removed
    assert ctrl.mask[5:15, 10:20].all()  # non-overlap survives
    assert int(ctrl.mask.sum()) < n_before


def test_add_polygon_and_cut_circle():
    ctrl = ROIController((80, 80))
    ctrl.add_polygon([(10, 10), (70, 10), (70, 70), (10, 70)], "add")
    assert ctrl.mask[40, 40]
    ctrl.add_circle(40, 40, 10, "cut")
    assert not ctrl.mask[40, 40]  # hole cut out
    assert ctrl.mask[12, 12]  # far corner untouched

    # degenerate inputs are no-ops
    ctrl2 = ROIController((20, 20))
    ctrl2.add_polygon([(1, 1), (5, 5)], "add")
    ctrl2.add_circle(10, 10, 0, "add")
    assert not ctrl2.mask.any()


def test_unknown_mode_raises():
    ctrl = ROIController((10, 10))
    with pytest.raises(ValueError, match="Unknown mode"):
        ctrl.add_rectangle(0, 0, 5, 5, "xor")


def test_stroke_segment_click_and_drag():
    ctrl = ROIController((60, 60))
    ctrl.stroke_segment(30, 30, 30, 30, radius=5, mode="add")  # click = disc
    assert ctrl.mask[30, 30] and ctrl.mask[30, 34]
    assert not ctrl.mask[30, 40]

    ctrl.stroke_segment(10, 50, 50, 50, radius=3, mode="add")  # drag = thick line
    assert ctrl.mask[50, 30]

    ctrl.stroke_segment(30, 30, 30, 30, radius=5, mode="cut")  # erase the disc
    assert not ctrl.mask[30, 30]
    assert ctrl.mask[50, 30]  # stroke elsewhere untouched


def test_invert_and_clear():
    ctrl = ROIController((10, 10))
    ctrl.add_rectangle(0, 0, 4, 4, "add")
    n = int(ctrl.mask.sum())
    ctrl.invert()
    assert int(ctrl.mask.sum()) == 100 - n
    ctrl.clear()
    assert not ctrl.mask.any()


def test_save_and_import_round_trip(tmp_path):
    ctrl = ROIController((40, 30))
    ctrl.add_circle(15, 20, 8, "add")
    path = tmp_path / "mask.png"
    ctrl.save_mask(str(path))

    loaded = ROIController((40, 30))
    loaded.import_mask(str(path))
    assert np.array_equal(loaded.mask, ctrl.mask)


def test_import_resizes_and_thresholds(tmp_path):
    # 0/1-coded uint8 mask at a different resolution: auto-threshold + resize.
    src = np.zeros((20, 20), dtype=np.uint8)
    src[5:15, 5:15] = 1
    path = tmp_path / "mask01.png"
    cv2.imwrite(str(path), src)
    mask = read_mask_as_bool(str(path), target_shape=(40, 40))
    assert mask.shape == (40, 40)
    assert mask[20, 20] and not mask[2, 2]


def test_import_missing_file_raises(tmp_path):
    ctrl = ROIController((10, 10))
    with pytest.raises(IOError):
        ctrl.import_mask(str(tmp_path / "nope.png"))
