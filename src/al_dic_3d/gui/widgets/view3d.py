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

Display (the overnight 3D-view rework): a toolbar (:class:`View3DToolbar`) with
specimen-aligned view presets and Reset, PNG save, deformation magnification
(true-scale colours on an exaggerated shape, optionally out-of-plane only), the
reference shape, the camera frusta (off by default: they zoomed the specimen
down to a speck) and lit, smooth shading; the first framing looks from the left
camera with image-up up, on the surface only; an orientation triad; pyvista's
stray key bindings removed. The geometry/camera math is Qt-free and shared with
the exports (:mod:`al_dic_3d.viz3d.view_setup`).
"""

from __future__ import annotations

from contextlib import contextmanager

import numpy as np
from al_dic.gui.theme import COLORS
from numpy.typing import NDArray
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QStackedLayout, QVBoxLayout, QWidget

from al_dic_3d.gui.widgets.view3d_toolbar import View3DOptions, View3DToolbar
from al_dic_3d.viz3d import build_surface_polydata
from al_dic_3d.viz3d.view_setup import (
    auto_magnification,
    frustum_size,
    magnify,
    preset_camera,
    safe_clim,
    scalar_bar_args,
    tick_format,
)

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

# pyvista key bindings that break the embedded view (see View3D._configure_plotter).
_UNSAFE_KEYS = ("q", "v", "b", "C")


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

    Two pages: a message (no results, unavailable GL, empty frame) and the
    scene (toolbar + viewport) — a message never leaves a stale surface on
    screen. P2.4 incremental updates: ONE surface actor is kept between frames;
    when the topology, field, colormap and display options are unchanged, points
    and scalars are updated in place, otherwise the scene is rebuilt with the
    user's camera PRESERVED. The camera is (re)framed — from the left camera,
    on the surface only — on the first render after results change.

    The scene's actors are tracked and removed one by one: ``plotter.clear()``
    would also remove the light kit and leave the surface unlit.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._stack = QStackedLayout(self)
        self._stack.setContentsMargins(0, 0, 0, 0)
        self._plotter = None
        self._failed = False
        self._rendered_once = False  # the first render is checked for GL failures
        # Incremental-update state (P2.4).
        self._surf = None  # the live pv.PolyData shown by _actor
        self._actor = None
        self._extras: list = []  # reference shape, frusta, note: removed with the scene
        self._scene_key: tuple | None = None  # what a rebuild depends on besides topology
        self._reset_camera_pending = True
        self._last: tuple | None = None  # last update_view inputs (options re-render)
        self._placeholder = QLabel(
            self.tr("3D view — run an analysis to see the reconstructed surface.")
        )
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet(
            f"color: {COLORS.TEXT_MUTED}; font-size: 13px; background: {COLORS.BG_CANVAS};"
        )
        self._stack.addWidget(self._placeholder)
        self._scene_page = QWidget()
        self._scene_layout = QVBoxLayout(self._scene_page)
        self._scene_layout.setContentsMargins(0, 0, 0, 0)
        self._scene_layout.setSpacing(0)
        self._toolbar = View3DToolbar()
        self._toolbar.preset_requested.connect(self.apply_preset)
        self._toolbar.save_requested.connect(self._save_image)
        self._toolbar.auto_requested.connect(self._auto_magnification)
        self._toolbar.options_changed.connect(self._rerender)
        self._scene_layout.addWidget(self._toolbar)
        self._stack.addWidget(self._scene_page)
        self._stack.setCurrentWidget(self._placeholder)

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
            self._scene_layout.addWidget(plotter.interactor, 1)
            self._plotter = plotter
            self._configure_plotter(plotter)
            return True
        except Exception as exc:  # noqa: BLE001 - degrade, never crash the app
            self._fail(exc)
            return False

    @staticmethod
    def _configure_plotter(plotter) -> None:
        """Drop pyvista's stray key bindings; add the orientation triad."""
        # 'q' prepares the plotter for closing (the view then dies), 'v' jumps to
        # an isometric view from behind, 'b' / 'C' arm point / cell picking.
        for key in _UNSAFE_KEYS:
            try:
                plotter.clear_events_for_key(key)
            except Exception:  # noqa: BLE001 - an older pyvista: keep its keys
                pass
        try:
            plotter.add_axes(interactive=False, color=COLORS.TEXT_SECONDARY)
        except Exception:  # noqa: BLE001 - the triad is decoration only
            pass

    def _fail(self, exc: BaseException) -> None:
        """Switch to the unavailable message for good (no retry storm)."""
        self._failed = True
        plotter, self._plotter = self._plotter, None
        self._surf = self._actor = None
        self._extras = []
        self._scene_key = None
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

    # ---- public API -------------------------------------------------------------

    def show_message(self, text: str) -> None:
        """Show ``text`` instead of the scene (the scene page is hidden, not shown stale)."""
        self._placeholder.setText(text)
        self._stack.setCurrentWidget(self._placeholder)

    def request_camera_reset(self) -> None:
        """Re-frame the camera on the NEXT render (call when results change)."""
        self._reset_camera_pending = True

    def options(self) -> View3DOptions:
        return self._toolbar.options()

    def camera_position(self):
        """The camera as ((position), (focal point), (view up)), or None.

        None until a surface is on screen, and while new results wait to be
        framed (the camera still belongs to the previous ones), so the 3D
        export then uses its own default view.
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
        ref_points: NDArray | None = None,
        note: str = "",
    ) -> None:
        """Re-render the surface for one frame (called on frame/field changes).

        ``ref_points`` (the frame-1 surface) enables the deformation
        magnification and the reference shape; ``note`` is a short corner text
        (e.g. that rigid motion is removed). ``barrier_mask`` (Batch C item 4)
        drops cells bridging a thin crack; ``None`` leaves the surface unchanged.
        """
        self._last = (
            points_3d,
            values,
            {
                "field_label": field_label,
                "cmap": cmap,
                "vmin": vmin,
                "vmax": vmax,
                "rig": rig,
                "ref_coords": ref_coords,
                "roi_mask": roi_mask,
                "barrier_mask": barrier_mask,
                "ref_points": ref_points,
                "note": note,
            },
        )
        if self._plotter is None and not self._failed:
            with self._busy(self.tr("Starting the 3D view…")):
                self._update(points_3d, values, **self._last[2])
        else:
            self._update(points_3d, values, **self._last[2])

    def apply_preset(self, name: str) -> None:
        """Point the camera per a preset (specimen-aligned) and frame the surface."""
        if self._plotter is None or self._surf is None:
            return
        camera = preset_camera(name, np.asarray(self._surf.points))
        if camera is None:
            return
        try:
            self._plotter.camera_position = camera
            self._plotter.reset_camera(bounds=self._surf.bounds)  # renders
        except Exception as exc:  # noqa: BLE001 - a broken GL context must not kill the app
            self._fail(exc)

    # ---- update -----------------------------------------------------------------

    def _update(
        self,
        points_3d,
        values,
        *,
        field_label,
        cmap,
        vmin,
        vmax,
        rig,
        ref_coords,
        roi_mask,
        barrier_mask,
        ref_points,
        note,
    ) -> None:
        if not self._ensure_plotter():
            return
        first = not self._rendered_once
        vmin, vmax = safe_clim(vmin, vmax)  # frame 1 is all zeros: never an empty range
        opts = self._toolbar.options()
        geometry = points_3d
        if ref_points is not None:
            geometry = magnify(
                ref_points, points_3d, opts.magnification, normal_only=opts.normal_only
            )
        try:
            surf = build_surface_mesh(
                geometry, values, field_label, ref_coords, roi_mask, barrier_mask
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
        self._stack.setCurrentWidget(self._scene_page)
        key = (field_label, cmap, tick_format(vmin, vmax), note, opts, ref_points is not None)
        try:
            with self._render_guard(first):
                if self._can_update_in_place(surf, key):
                    self._update_in_place(surf, field_label, vmin, vmax)
                else:
                    extras = (rig, ref_points, ref_coords, roi_mask, barrier_mask, note)
                    self._rebuild_scene(surf, key, vmin, vmax, extras)
        except Exception as exc:  # noqa: BLE001 - a broken GL context must not kill the app
            self._fail(exc)
            return
        self._rendered_once = True

    def _rerender(self) -> None:
        """A display option changed: rebuild the scene from the last inputs."""
        self._scene_key = None
        if self._last is not None and self._plotter is not None:
            self._update(self._last[0], self._last[1], **self._last[2])

    def _auto_magnification(self) -> None:
        if self._last is None or self._last[2]["ref_points"] is None:
            return
        factor = auto_magnification(
            self._last[2]["ref_points"],
            self._last[0],
            normal_only=self._toolbar.options().normal_only,
        )
        self._toolbar.set_magnification(factor)

    def _save_image(self) -> None:
        if self._plotter is None or self._surf is None:
            return
        from PySide6.QtWidgets import QFileDialog

        from al_dic_3d.gui import persistence
        from al_dic_3d.pathsafe import imwrite_unicode

        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save 3D view image"),
            persistence.suggested_save_path("view3d.png", "export"),
            self.tr("PNG image (*.png)"),
        )
        if not path:
            return
        try:
            img = self._plotter.screenshot(return_img=True)  # RGB
            imwrite_unicode(path, np.ascontiguousarray(img[:, :, ::-1]))  # unicode-safe
        except Exception as exc:  # noqa: BLE001 - report, never crash
            self.show_message(self.tr("Could not save the image: {0}").format(str(exc)[:160]))

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

    def _can_update_in_place(self, surf, key: tuple) -> bool:
        """Same topology + same field/colormap/options -> points/scalars-only update.

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
            and self._scene_key == key
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
        # The near/far planes do not follow moved points on their own: a magnified
        # or deforming surface would be cut at the old clipping range.
        self._plotter.reset_camera_clipping_range()
        self._plotter.render()

    def _rebuild_scene(self, surf, key: tuple, vmin: float, vmax: float, extras: tuple) -> None:
        """Full rebuild (topology/field/colormap/options changed) — camera preserved."""
        field_label, cmap, _fmt, _note, opts, _has_ref = key
        rig, ref_points, ref_coords, roi_mask, barrier_mask, note = extras
        camera = None if self._reset_camera_pending else self._plotter.camera_position
        self._remove_scene()
        lit = {"ambient": 0.3, "diffuse": 0.7, "specular": 0.1} if opts.shading else {}
        # render=False everywhere: the camera reset / restore below renders ONCE.
        self._actor = self._plotter.add_mesh(
            surf,
            scalars=field_label,
            cmap=cmap,
            clim=(vmin, vmax),
            show_edges=False,
            lighting=opts.shading,
            smooth_shading=opts.shading,
            scalar_bar_args=scalar_bar_args(field_label, COLORS.TEXT_PRIMARY, vmin, vmax),
            render=False,
            **lit,
        )
        self._add_extras(opts, rig, ref_points, ref_coords, roi_mask, barrier_mask, note, surf)
        self._surf = surf
        self._scene_key = key
        if camera is None:
            framing = preset_camera("camera", np.asarray(surf.points))
            if framing is not None:
                self._plotter.camera_position = framing
            self._plotter.reset_camera(bounds=surf.bounds)  # frames the surface only; renders
            self._reset_camera_pending = False
        else:
            self._plotter.camera_position = camera

    def _add_extras(self, opts, rig, ref_points, ref_coords, roi_mask, barrier_mask, note, surf):
        if opts.show_reference and ref_points is not None:
            try:
                ghost = build_surface_mesh(
                    ref_points, np.zeros(len(ref_points)), "ref", ref_coords, roi_mask, barrier_mask
                )
                if ghost is not None:
                    self._extras.append(
                        self._plotter.add_mesh(
                            ghost,
                            style="wireframe",
                            color=COLORS.TEXT_MUTED,
                            opacity=0.35,
                            lighting=False,
                            render=False,
                        )
                    )
            except Exception:  # noqa: BLE001 - the reference shape is decoration only
                pass
        if opts.show_cameras and rig is not None:
            try:
                size = frustum_size(np.asarray(surf.points))
                for cam in ("L", "R"):
                    frustum = camera_frustum_lines(*rig.pose(cam), size=size)
                    self._extras.append(
                        self._plotter.add_mesh(
                            frustum, color=COLORS.ACCENT, line_width=2, render=False
                        )
                    )
            except Exception:  # noqa: BLE001 - frusta are decoration only
                pass
        if note:
            try:
                self._extras.append(
                    self._plotter.add_text(
                        note, position="upper_left", font_size=9, color=COLORS.TEXT_SECONDARY
                    )
                )
            except Exception:  # noqa: BLE001 - the note is decoration only
                pass

    def _remove_scene(self) -> None:
        """Remove our actors and scalar bar — never the lights (``clear()`` would)."""
        for actor in [self._actor, *self._extras]:
            if actor is not None:
                self._plotter.remove_actor(actor, render=False)
        self._actor = None
        self._extras = []
        try:
            self._plotter.scalar_bars.clear()
        except Exception:  # noqa: BLE001 - nothing to remove
            pass

    def _drop_scene(self) -> None:
        if self._plotter is not None:
            self._remove_scene()
        self._surf = None
        self._actor = None
        self._scene_key = None
