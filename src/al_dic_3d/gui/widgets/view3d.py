"""``View3D`` — interactive 3D surface view (pyvista, lazy ``[viz3d]`` extra).

Shows the reconstructed surface at the current frame as a triangulated point
cloud colored by the selected field, plus the two camera frusta. The heavy
pyvista/VTK import happens lazily on first use; if the extra is missing or the
machine has no usable OpenGL context, the widget degrades to a styled message
instead of crashing (this also keeps headless test runs safe).

``build_surface_mesh`` / ``camera_frustum_lines`` are pure (no GL) and unit-
testable without a display.
"""

from __future__ import annotations

import numpy as np
from al_dic.gui.theme import COLORS
from numpy.typing import NDArray
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


def build_surface_mesh(points_3d: NDArray, values: NDArray, name: str):
    """Triangulated surface (``pv.PolyData``) from finite 3D points + scalars.

    Returns ``None`` when fewer than 3 finite points exist (nothing to render).
    """
    import pyvista as pv

    pts = np.asarray(points_3d, dtype=np.float64).reshape(-1, 3)
    vals = np.asarray(values, dtype=np.float64).reshape(-1)
    finite = np.isfinite(pts).all(axis=1) & np.isfinite(vals)
    if finite.sum() < 3:
        return None
    cloud = pv.PolyData(pts[finite])
    cloud[name] = vals[finite]
    surf = cloud.delaunay_2d()
    return surf if surf.n_cells > 0 else cloud


def camera_frustum_lines(R: NDArray, T: NDArray, *, size: float = 60.0, aspect: float = 0.75):
    """Wireframe frustum (``pv.PolyData`` lines) for a camera with world->cam pose.

    The apex sits at the camera center ``-R^T T``; four edges extend toward the
    scene through a ``size``-wide virtual image plane.
    """
    import pyvista as pv

    R = np.asarray(R, dtype=np.float64)
    T = np.asarray(T, dtype=np.float64).reshape(3)
    center = -R.T @ T
    # Camera-frame corner directions (z forward), rotated into world.
    w, h = size, size * aspect
    corners_cam = np.array(
        [[-w, -h, 2 * size], [w, -h, 2 * size], [w, h, 2 * size], [-w, h, 2 * size]]
    )
    corners = corners_cam @ R + center  # R^T @ c, row-wise
    points = np.vstack([center[None, :], corners])
    lines = []
    for i in range(1, 5):
        lines += [2, 0, i]  # apex -> corner
    for a, b in zip([1, 2, 3, 4], [2, 3, 4, 1], strict=True):
        lines += [2, a, b]  # image-plane ring
    mesh = pv.PolyData(points)
    mesh.lines = np.asarray(lines)
    return mesh


class View3D(QWidget):
    """Lazy pyvista viewport with graceful degradation."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._plotter = None
        self._failed = False
        self._placeholder = QLabel(
            self.tr("3D view — run an analysis to see the reconstructed surface.")
        )
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet(
            f"color: {COLORS.TEXT_MUTED}; font-size: 13px; background: {COLORS.BG_CANVAS};"
        )
        self._layout.addWidget(self._placeholder)

    # ---- plotter lifecycle ----------------------------------------------------

    def _ensure_plotter(self) -> bool:
        if self._plotter is not None:
            return True
        if self._failed:
            return False
        try:
            from pyvistaqt import QtInteractor

            self._plotter = QtInteractor(self)
            self._plotter.set_background(COLORS.BG_CANVAS)
            self._layout.addWidget(self._plotter.interactor)
            return True
        except Exception as exc:  # noqa: BLE001 - degrade, never crash the app
            self._failed = True
            self._placeholder.setText(self.tr("3D view unavailable: {0}").format(str(exc)[:160]))
            return False

    # ---- update -----------------------------------------------------------------

    def show_message(self, text: str) -> None:
        self._placeholder.setText(text)
        self._placeholder.setVisible(True)

    def update_view(
        self,
        points_3d: NDArray,
        values: NDArray,
        *,
        field_label: str,
        cmap: str,
        vmin: float,
        vmax: float,
        rig=None,
    ) -> None:
        """Re-render the surface for one frame (called on frame/field changes)."""
        if not self._ensure_plotter():
            return
        surf = build_surface_mesh(points_3d, values, field_label)
        self._plotter.clear()
        if surf is None:
            return
        self._placeholder.setVisible(False)
        self._plotter.add_mesh(
            surf,
            scalars=field_label,
            cmap=cmap,
            clim=(vmin, vmax),
            show_edges=False,
            scalar_bar_args={
                "title": field_label,
                "color": COLORS.TEXT_PRIMARY,
                "vertical": True,
            },
        )
        if rig is not None:
            try:
                for cam in ("L", "R"):
                    pose = rig.pose(cam)
                    frustum = camera_frustum_lines(*pose)
                    self._plotter.add_mesh(frustum, color=COLORS.ACCENT, line_width=2)
            except Exception:  # noqa: BLE001 - frusta are decoration only
                pass
        self._plotter.reset_camera()
