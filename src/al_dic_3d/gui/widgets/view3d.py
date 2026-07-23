"""``View3D`` — interactive 3D surface view (pyvista, lazy ``[viz3d]`` extra).

Shows the reconstructed surface at the current frame colored by the selected
field, plus the two camera frusta. The surface is the SHARED
:func:`al_dic_3d.viz3d.build_surface_polydata` (F3.2): regular-grid quad
connectivity from the reference grid with the drawn ROI mask knocked out
(holes render as holes, matching the 2D dense view), and an edge-capped
triangulated fallback that can never span a hole. The heavy pyvista/VTK
import happens lazily on first use; if the extra is missing or the machine
has no usable OpenGL context, the widget degrades to a styled message instead
of crashing (this also keeps headless test runs safe).

``build_surface_mesh`` / ``camera_frustum_lines`` are pure (no GL) and unit-
testable without a display.
"""

from __future__ import annotations

import numpy as np
from al_dic.gui.theme import COLORS
from numpy.typing import NDArray
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from al_dic_3d.viz3d import build_surface_polydata


def build_surface_mesh(
    points_3d: NDArray,
    values: NDArray,
    name: str,
    ref_coords: NDArray | None = None,
    roi_mask: NDArray | None = None,
    barrier_mask: NDArray | None = None,
):
    """Surface (``pv.PolyData``) from finite 3D points + scalars.

    Thin alias over the shared :func:`al_dic_3d.viz3d.build_surface_polydata`
    (kept for the existing import sites/tests): quad mesh over ``ref_coords``
    with ``roi_mask`` holes preserved, edge-capped Delaunay fallback, point
    cloud as last resort; ``None`` when fewer than 3 usable points exist.
    ``barrier_mask`` (Batch C item 4) drops cells whose edges bridge a thin
    crack; ``None`` (crack-free default) keeps the surface byte-identical.
    """
    return build_surface_polydata(points_3d, values, name, ref_coords, roi_mask, barrier_mask)


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
    """Lazy pyvista viewport with graceful degradation.

    P2.4 incremental updates: ONE surface actor is kept between frames. When
    the new frame's mesh topology matches (same points/cells/faces) and the
    field + colormap are unchanged, points and scalars are updated in place
    (pyvista's animation idiom) instead of clear+add_mesh; otherwise the scene
    is rebuilt but the user's camera is PRESERVED. ``reset_camera`` runs only
    on the first render after results change (:meth:`request_camera_reset`).
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._plotter = None
        self._failed = False
        # Incremental-update state (P2.4).
        self._surf = None  # the live pv.PolyData shown by _actor
        self._actor = None
        self._field_label: str | None = None
        self._cmap: str | None = None
        self._reset_camera_pending = True
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

    def request_camera_reset(self) -> None:
        """Re-frame the camera on the NEXT render (call when results change)."""
        self._reset_camera_pending = True

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
        ref_coords: NDArray | None = None,
        roi_mask: NDArray | None = None,
        barrier_mask: NDArray | None = None,
    ) -> None:
        """Re-render the surface for one frame (called on frame/field changes).

        ``barrier_mask`` (Batch C item 4) drops cells bridging a thin crack;
        ``None`` (crack-free default) leaves the surface unchanged.
        """
        if not self._ensure_plotter():
            return
        surf = build_surface_mesh(
            points_3d, values, field_label, ref_coords, roi_mask, barrier_mask
        )
        if surf is None:
            # An empty frame must SAY so (F3.1), never render silent nothing.
            self._drop_scene()
            self.show_message(self.tr("No valid 3D points in this frame — nothing to display."))
            return
        self._placeholder.setVisible(False)
        if self._can_update_in_place(surf, field_label, cmap):
            self._update_in_place(surf, field_label, vmin, vmax)
        else:
            self._rebuild_scene(surf, field_label, cmap, vmin, vmax, rig)

    # -- P2.4 render paths -------------------------------------------------------

    def _can_update_in_place(self, surf, field_label: str, cmap: str) -> bool:
        """Same topology + same field/colormap -> points/scalars-only update.

        Faces are compared exactly (cheap memcmp): equal counts with different
        connectivity (a shifted NaN pattern) must take the rebuild path. A
        pending camera reset (new results) also forces the rebuild path so the
        re-frame actually happens.
        """
        old = self._surf
        return (
            not self._reset_camera_pending
            and old is not None
            and self._actor is not None
            and self._field_label == field_label
            and self._cmap == cmap
            and old.n_points == surf.n_points
            and old.n_cells == surf.n_cells
            and np.array_equal(old.faces, surf.faces)
        )

    def _update_in_place(self, surf, field_label: str, vmin: float, vmax: float) -> None:
        """Frame scrub fast path: mutate the live actor's mesh, keep the camera."""
        self._surf.points[:] = surf.points  # pyvista marks the VTK array modified
        self._surf[field_label][:] = surf[field_label]
        try:  # clim follows the frame's range; LUT range keeps the bar in sync
            self._actor.mapper.scalar_range = (float(vmin), float(vmax))
            self._actor.mapper.lookup_table.scalar_range = (float(vmin), float(vmax))
        except Exception:  # noqa: BLE001 - colorbar range is decoration-level
            pass
        self._plotter.render()

    def _rebuild_scene(self, surf, field_label, cmap, vmin, vmax, rig) -> None:
        """Full rebuild (topology/field/colormap changed) — camera preserved."""
        camera = None if self._reset_camera_pending else self._plotter.camera_position
        self._plotter.clear()
        self._actor = self._plotter.add_mesh(
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
        self._surf = surf
        self._field_label = field_label
        self._cmap = cmap
        if camera is None:
            self._plotter.reset_camera()
            self._reset_camera_pending = False
        else:
            self._plotter.camera_position = camera

    def _drop_scene(self) -> None:
        self._surf = None
        self._actor = None
        self._field_label = None
        self._cmap = None
        if self._plotter is not None:
            self._plotter.clear()
