"""Shared Qt rendering helpers for result overlays.

Fields render as a DENSE continuous overlay via
:class:`~al_dic_3d.gui.controllers.viz_controller.VizController3D`; this module
keeps the colormapped-scatter routine used for the optional "Show Points"
node markers drawn on TOP of the dense field. Qt view layer; no user-facing
strings.
"""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap


def scatter_field_pixmap(
    pts: np.ndarray,
    vals: np.ndarray,
    width: int,
    height: int,
    *,
    cmap_name: str,
    vmin: float,
    vmax: float,
    radius: float,
) -> QPixmap | None:
    """Colormapped scatter of ``vals`` at image positions ``pts`` on a clear pixmap.

    Args:
        pts: ``(n, 2)`` pixel positions; non-finite rows are skipped.
        vals: ``(n,)`` field values; NaN nodes are skipped (invalid propagates).
        width / height: pixmap size in pixels (the image scene rect).
        cmap_name: matplotlib colormap name.
        vmin / vmax: color range (``vmax <= vmin`` degrades to a unit span).
        radius: dot radius in pixels.

    Returns:
        The transparent-background pixmap, or ``None`` when the size is empty.
    """
    from matplotlib import colormaps

    if width <= 0 or height <= 0:
        return None
    span = (vmax - vmin) or 1.0

    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)

    cmap = colormaps[cmap_name]
    finite = np.isfinite(pts).all(axis=1) & np.isfinite(vals)
    norm = np.clip((vals[finite] - vmin) / span, 0.0, 1.0)
    rgba = (cmap(norm) * 255).astype(np.uint8)
    for (x, y), (r, g, b, _a) in zip(pts[finite], rgba, strict=True):
        painter.setBrush(QColor(int(r), int(g), int(b)))
        painter.drawEllipse(
            int(round(x - radius)),
            int(round(y - radius)),
            int(round(2 * radius)),
            int(round(2 * radius)),
        )
    painter.end()
    return pixmap
