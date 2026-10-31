"""The mesh preview stays on the drawn ROI when the canvas is panned.

``QGraphicsView.scrollContentsBy`` scrolls the viewport with
``QWidget.scroll(dx, dy)`` unless the view repaints in full, and
``QWidget.scroll`` MOVES every child widget of the viewport by the same delta.
The mesh overlay is such a child, and it already paints through
``viewportTransform()`` (the scroll included), so every pan shifted the grid a
second time: it slid off the blue ROI by the pan distance and stayed there
until the viewport was resized. The config card, colorbar and notices are
viewport children too and were dragged along the same way.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import numpy as np
import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt  # noqa: E402
from PySide6.QtGui import QMouseEvent  # noqa: E402
from PySide6.QtWidgets import QApplication, QWidget  # noqa: E402

from al_dic_3d.gui.app import create_app  # noqa: E402

_IMG_W, _IMG_H = 400, 300
_ROI = (120, 90, 280, 210)  # x0, y0, x1, y1 of the drawn rectangle (scene px)
_MESH_RGB = (255, 0, 255)  # a color the gray image and the blue ROI never take


@pytest.fixture(scope="module")
def qapp():
    return create_app([])


@pytest.fixture(scope="module")
def frame_files(tmp_path_factory):
    import cv2

    d = tmp_path_factory.mktemp("mesh_align_frames")
    rng = np.random.default_rng(11)
    paths = []
    for k in range(2):
        img = rng.integers(60, 180, size=(_IMG_H, _IMG_W), dtype=np.uint8)
        p = d / f"L_{k:03d}.png"
        cv2.imwrite(str(p), img)
        paths.append(str(p))
    return paths


@pytest.fixture
def area(qapp, frame_files):
    """A shown canvas with a drawn ROI, its mesh preview on, zoomed in to pan."""
    from al_dic_3d.gui.controller import WorkflowController
    from al_dic_3d.gui.panels.canvas_area import CanvasArea3D
    from al_dic_3d.gui.state import GuiSignals

    controller = WorkflowController()
    signals = GuiSignals()
    signals.mesh_line_color = "#{:02x}{:02x}{:02x}".format(*_MESH_RGB)
    widget = CanvasArea3D(controller, signals)
    widget.resize(640, 520)
    widget.show()  # offscreen show: child isVisible() needs a visible ancestor
    controller.state.draft.left = list(frame_files)
    signals.images_changed.emit()
    QApplication.processEvents()

    ctrl = widget.roi_ctrl
    ctrl.add_rectangle(*_ROI)
    widget.commit_roi_mask()
    widget._generate_preview_mesh()
    assert widget.wait_mesh_preview()
    assert widget._mesh_overlay.isVisible()
    for _ in range(3):  # past Fit, so the view can scroll
        widget.canvas.zoom_in()
    QApplication.processEvents()
    yield widget
    widget.close()


def _right_drag_pan(canvas, dx: int, dy: int) -> None:
    """Pan exactly like the user: right-button drag on the viewport (G2.4)."""
    vp = canvas.viewport()
    start = QPointF(vp.width() / 2, vp.height() / 2)
    end = start + QPointF(dx, dy)
    button = Qt.MouseButton.RightButton
    no_mod = Qt.KeyboardModifier.NoModifier
    for kind, pos, buttons in (
        (QEvent.Type.MouseButtonPress, start, button),
        (QEvent.Type.MouseMove, start + QPointF(dx / 2, dy / 2), button),
        (QEvent.Type.MouseMove, end, button),
        (QEvent.Type.MouseButtonRelease, end, Qt.MouseButton.NoButton),
    ):
        event = QMouseEvent(kind, pos, vp.mapToGlobal(pos), button, buttons, no_mod)
        QApplication.sendEvent(vp, event)
    QApplication.processEvents()


def _drawn_on_viewport(area, scene_xy: np.ndarray) -> np.ndarray:
    """Where the mesh overlay paints scene points, in VIEWPORT pixels."""
    overlay = area._mesh_overlay
    vp = area.canvas.viewport()
    out = []
    for x, y in scene_xy:
        local = overlay._vt.map(QPointF(float(x), float(y)))  # overlay painter coords
        p = overlay.mapTo(vp, QPointF(local.x(), local.y()))
        out.append((p.x(), p.y()))
    return np.asarray(out)


def _image_on_viewport(area, scene_xy: np.ndarray) -> np.ndarray:
    """Where the canvas shows scene points (image / ROI pixels), in viewport pixels."""
    vt = area.canvas.viewportTransform()
    return np.asarray([(vt.map(QPointF(x, y)).x(), vt.map(QPointF(x, y)).y()) for x, y in scene_xy])


def _scrolled(area) -> tuple[int, int]:
    canvas = area.canvas
    return canvas.horizontalScrollBar().value(), canvas.verticalScrollBar().value()


def test_mesh_nodes_stay_on_the_image_after_a_pan(area):
    coords = area._hover_coords[area._hover_valid]
    assert len(coords) > 10
    before = _scrolled(area)
    _right_drag_pan(area.canvas, -60, -40)
    assert _scrolled(area) != before  # the drag really scrolled the view

    drawn = _drawn_on_viewport(area, coords)
    shown = _image_on_viewport(area, coords)
    assert np.abs(drawn - shown).max() < 0.5  # grid nodes sit on their pixels
    assert area._mesh_overlay.pos() == QPoint(0, 0)  # still covers the viewport


def test_viewport_overlays_stay_pinned_after_a_pan(area):
    vp = area.canvas.viewport()
    children = [w for w in vp.findChildren(QWidget) if w.parentWidget() is vp]
    assert area._mesh_overlay in children
    before = {id(w): w.pos() for w in children}
    _right_drag_pan(area.canvas, 50, 30)
    moved = [type(w).__name__ for w in children if w.pos() != before[id(w)]]
    assert moved == []


def test_rendered_grid_lies_inside_the_drawn_roi_after_a_pan(area):
    _right_drag_pan(area.canvas, -60, -40)
    area.canvas.fit_to_view()  # Fit after a pan used to keep the stale offset
    QApplication.processEvents()

    shot = area.canvas.viewport().grab().toImage()
    w, h = shot.width(), shot.height()
    ptr = shot.convertToFormat(shot.Format.Format_RGB888).constBits()
    stride = shot.convertToFormat(shot.Format.Format_RGB888).bytesPerLine()
    rgb = np.frombuffer(ptr, np.uint8).reshape(h, stride)[:, : 3 * w].reshape(h, w, 3)
    r, g, b = (rgb[..., i].astype(int) for i in range(3))
    grid = (r > 200) & (b > 200) & (g < 90)  # the magenta mesh lines
    ys, xs = np.nonzero(grid)
    assert xs.size > 100

    # The ROI rectangle as the canvas shows it, plus a pixel of line width.
    vt = area.canvas.viewportTransform()
    top_left = vt.map(QPointF(_ROI[0], _ROI[1]))
    bottom_right = vt.map(QPointF(_ROI[2] + 1, _ROI[3] + 1))
    tol = 2
    assert xs.min() >= top_left.x() - tol and xs.max() <= bottom_right.x() + tol
    assert ys.min() >= top_left.y() - tol and ys.max() <= bottom_right.y() + tol
