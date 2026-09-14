"""The dense overlay sits on its nodes, in the canvases and in exported images.

Grid sample (i, j) is evaluated at image pixel (xg[j], yg[i]) and drawn as an
``out_step``-pixel block. Both the canvas (a pixmap placed at the first sample)
and the exporter (a resize pasted at the first sample) put the block's corner
there, so every value showed (out_step - 1) / 2 px right of and below its node
(fix batch V review: 1.5 px at the default step, 3.5 px at step 32).
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import numpy as np
import pytest

from al_dic_3d.export.render import _composite_overlay
from al_dic_3d.viz3d.raster import overlay_origin

XG = np.array([10.0, 14.0, 18.0])
YG = np.array([20.0, 24.0, 28.0])
STEP = 4


def _coverage(rgba: np.ndarray, step: int = STEP) -> np.ndarray:
    composed = _composite_overlay(np.zeros((60, 60, 3), np.uint8), rgba, XG, YG, step, 1.0)
    return composed[:, :, 2] > 0  # red channel (BGR) = drawn overlay


def _rgba(opaque: np.ndarray) -> np.ndarray:
    rgba = np.zeros((*opaque.shape, 4), np.uint8)
    rgba[opaque] = (255, 0, 0, 255)
    return rgba


def test_overlay_origin_centres_each_block_on_its_sample():
    assert overlay_origin(XG, YG, 4) == (8.5, 18.5)
    assert overlay_origin(XG, YG, 1) == (10.0, 20.0)  # one pixel per sample: no shift


def test_an_exported_block_is_centred_on_its_sample():
    one = np.zeros((3, 3), bool)
    one[1, 2] = True  # the sample at image pixel (x=18, y=24)
    ys, xs = np.nonzero(_coverage(_rgba(one)))
    assert xs.mean() == pytest.approx(18.0) and ys.mean() == pytest.approx(24.0)
    assert xs.min() + xs.max() == 2 * 18 and ys.min() + ys.max() == 2 * 24
    assert xs.max() - xs.min() <= STEP  # no wider than one block


def test_an_exported_field_is_symmetric_about_its_samples():
    ys, xs = np.nonzero(_coverage(_rgba(np.ones((3, 3), bool))))
    assert (xs.min() + xs.max()) / 2 == pytest.approx(14.0)
    assert (ys.min() + ys.max()) / 2 == pytest.approx(24.0)
    # Half a step beyond the outer samples, as a block per sample implies.
    assert xs.min() >= 10 - STEP / 2 and xs.max() <= 18 + STEP / 2


def test_both_canvases_place_the_overlay_at_the_origin(qapp_windows):
    from PySide6.QtGui import QPixmap

    main, strain = qapp_windows
    pixmap = QPixmap(3, 3)
    main._canvas_area._apply_overlay("viridis", 0.0, 1.0, "U (mm)", (pixmap, XG, YG, STEP))
    item = main._canvas_area._canvas._overlay_item
    assert (item.pos().x(), item.pos().y()) == overlay_origin(XG, YG, STEP)
    assert item.scale() == STEP
    strain._apply_strain_overlay("viridis", 0.0, 1.0, "exx", (pixmap, XG, YG, STEP))
    item = strain._canvas._overlay_item
    assert (item.pos().x(), item.pos().y()) == overlay_origin(XG, YG, STEP)


@pytest.fixture
def qapp_windows():
    pytest.importorskip("PySide6")
    from al_dic_3d.gui.app import create_app
    from al_dic_3d.gui.controller import WorkflowController
    from al_dic_3d.gui.main_window import MainWindow3D
    from al_dic_3d.gui.state import GuiSignals
    from al_dic_3d.gui.strain_window import StrainWindow3D

    create_app([])
    main = MainWindow3D()
    strain = StrainWindow3D(WorkflowController(), GuiSignals())
    yield main, strain
    strain.close()
    main.close()
