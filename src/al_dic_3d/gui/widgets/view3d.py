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

V-view robustness / cost:

* the FIRST open (importing pyvista/VTK, creating the GL window, first render:
  seconds on the GUI thread) runs under a wait cursor with a "Starting the 3D
  view…" message painted synchronously first, so the app visibly works;
* every plotter operation — the first render AND every later update — is
  guarded: a Python exception, or a VTK OpenGL/context error reported during
  the first render (remote desktop, VMs, old drivers), switches the widget to
  the translated "3D view unavailable" message instead of failing later;
* no redundant renders: pyvistaqt's 5 Hz auto-render timer is disabled (the
  view renders explicitly after each change) and a scene rebuild renders once,
  not once per ``add_mesh``.
"""

from __future__ import annotations

from contextlib import contextmanager

import numpy as np
from al_dic.gui.theme import COLORS
from numpy.typing import NDArray
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

from al_dic_3d.viz3d import build_surface_polydata

# VTK error text that means "this machine cannot render" (first render only).
_GL_FAILURE_MARKERS = (
    "opengl",
    "gl context",
    "rendering context",
    "pixel format",
    "glew",
    "glad",
    "wgl",
    "glx",
    "egl",
)


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
        self._rendered_once = False  # the first render is checked for GL failures
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

            # auto_update=False: every change renders explicitly; the default
            # 5 Hz timer re-rendered the whole scene every 200 ms.
            plotter = QtInteractor(self, auto_update=False)
            plotter.set_background(COLORS.BG_CANVAS)
            self._layout.addWidget(plotter.interactor)
            self._plotter = plotter
            return True
        except Exception as exc:  # noqa: BLE001 - degrade, never crash the app
            self._fail(exc)
            return False

    def _fail(self, exc: BaseException) -> None:
        """Switch to the unavailable message for good (no retry storm)."""
        self._failed = True
        plotter, self._plotter = self._plotter, None
        self._surf = self._actor = None
        self._field_label = self._cmap = None
        if plotter is not None:
            try:
                plotter.interactor.setVisible(False)
                plotter.close()
            except Exception:  # noqa: BLE001 - teardown of a broken GL widget
                pass
        self.show_message(self.tr("3D view unavailable: {0}").format(str(exc)[:160]))

    @contextmanager
    def _busy(self, text: str):
        """Wait cursor + a message painted NOW (before the blocking work)."""
        self.show_message(text)
        if self.isVisible():
            self._placeholder.repaint()  # synchronous: no event-loop turn needed
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            yield
        finally:
            QApplication.restoreOverrideCursor()

    # ---- update -----------------------------------------------------------------

    def show_message(self, text: str) -> None:
        self._placeholder.setText(text)
        self._placeholder.setVisible(True)

    def request_camera_reset(self) -> None:
        """Re-frame the camera on the NEXT render (call when results change)."""
        self._reset_camera_pending = True

    def camera_position(self):
        """The camera as ((position), (focal point), (view up)), or None.

        None until a surface is on screen, and while new results wait to be
        framed (the camera still belongs to the previous ones), so the 3D
        export then uses its own isometric view.
        """
        if self._plotter is None or self._surf is None or self._reset_camera_pending:
            return None
        try:
            cam = self._plotter.camera_position
            parts = (cam.position, cam.focal_point, cam.viewup)
            return tuple(tuple(float(v) for v in part) for part in parts)
        except Exception:  # noqa: BLE001 - a plotter being torn down: no camera
            return None

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
        args = (points_3d, values, field_label, cmap, vmin, vmax, rig)
        masks = (ref_coords, roi_mask, barrier_mask)
        if self._plotter is None and not self._failed:
            with self._busy(self.tr("Starting the 3D view…")):
                self._update(*args, *masks)
        else:
            self._update(*args, *masks)

    def _update(
        self,
        points_3d,
        values,
        field_label,
        cmap,
        vmin,
        vmax,
        rig,
        ref_coords,
        roi_mask,
        barrier_mask,
    ) -> None:
        if not self._ensure_plotter():
            return
        first = not self._rendered_once
        try:
            surf = build_surface_mesh(
                points_3d, values, field_label, ref_coords, roi_mask, barrier_mask
            )
        except Exception as exc:  # noqa: BLE001 - a data problem: say so, retry next frame
            self._drop_scene()
            self.show_message(self.tr("3D view unavailable: {0}").format(str(exc)[:160]))
            return
        if surf is None:
            # An empty frame must SAY so (F3.1), never render silent nothing.
            self._drop_scene()
            self.show_message(self.tr("No valid 3D points in this frame — nothing to display."))
            return
        self._placeholder.setVisible(False)
        try:
            with self._render_guard(first):
                if self._can_update_in_place(surf, field_label, cmap):
                    self._update_in_place(surf, field_label, vmin, vmax)
                else:
                    self._rebuild_scene(surf, field_label, cmap, vmin, vmax, rig)
        except Exception as exc:  # noqa: BLE001 - a broken GL context must not kill the app
            self._fail(exc)
            return
        self._rendered_once = True

    @contextmanager
    def _render_guard(self, first: bool):
        """Raise on a VTK OpenGL/context error reported by the FIRST render.

        Later renders are guarded by the caller's ``except`` only: once a
        context rendered, VTK errors are data problems, not a missing GL.
        """
        catcher_cls = None
        if first:
            try:
                from pyvista import VtkErrorCatcher as catcher_cls
            except Exception:  # noqa: BLE001 - older pyvista: Python exceptions only
                catcher_cls = None
        if catcher_cls is None:
            yield
            return
        with catcher_cls(raise_errors=False, send_to_logging=False) as catcher:
            yield
        errors = getattr(catcher, "error_events", None)
        for event in errors if errors is not None else getattr(catcher, "events", ()):
            text = str(getattr(event, "alert", "") or event).strip()
            if any(marker in text.lower() for marker in _GL_FAILURE_MARKERS):
                raise RuntimeError(text[:300])

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
        # render=False: the camera reset / restore below renders ONCE.
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
            render=False,
        )
        if rig is not None:
            try:
                for cam in ("L", "R"):
                    pose = rig.pose(cam)
                    frustum = camera_frustum_lines(*pose)
                    self._plotter.add_mesh(frustum, color=COLORS.ACCENT, line_width=2, render=False)
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
