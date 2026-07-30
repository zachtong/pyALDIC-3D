"""``view_state`` <-> live display state (G3.10 / batch Q / batch Z).

Extracted from ``RightSidebar3D`` (file-size discipline): pure widget/signal
synchronisation with NO user-facing strings. :func:`capture` snapshots the live
display state when a project is saved; :func:`apply_to_sidebar` pushes a saved
dict into ``GuiSignals`` AND the sidebar's widgets (signals blocked), then emits
ONE ``display_changed``. :func:`apply_to_canvas` does the same for the central
panel's toolbar toggles — it lives here rather than on ``CanvasArea3D`` for the
same reason ``apply_to_sidebar`` does: file-size discipline on the panels.

Batch Z: both directions derive from :data:`VIEW_STATE_KEYS`. A key that is
saved but never read back silently reverts to its default on every reload (the
bug 2D hit with ``show_subset_window``), so the fidelity test asserts the
capture covers exactly this list and that a session round trip reproduces it.
"""

from __future__ import annotations

# Toolbar toggles owned by CanvasArea3D (Show Grid / Show Subset / 3D View).
CANVAS_VIEW_KEYS = ("show_grid", "show_subset", "view_3d")

# Every key a saved view_state carries.
VIEW_STATE_KEYS = (
    "display_field",
    "colormap",
    "color_auto",
    "color_min",
    "color_max",
    "overlay_alpha",
    "show_deformed",
    "camera",
    "current_frame",
    "display_unit",  # Q1
    "frame_rate",  # Q1/Q2
    "mesh_line_color",  # Q8
    "mesh_line_width",  # Q8
    *CANVAS_VIEW_KEYS,  # Z2
)


def capture_canvas(canvas) -> dict:
    """The central canvas's share of a ``view_state``: :data:`CANVAS_VIEW_KEYS`."""
    return {
        "show_grid": canvas._grid_cb.isChecked(),
        "show_subset": canvas._subset_cb.isChecked(),
        "view_3d": canvas._view3d_cb.isChecked(),
    }


def apply_to_canvas(canvas, vs: dict) -> None:
    """Restore the canvas toolbar toggles from a saved ``view_state``.

    Signals are deliberately NOT blocked: each toggle owns real side effects
    (the mesh-preview build, the subset-hover enable, the 2D/3D page switch)
    that the restored view must actually have. Show Grid goes first because
    hiding it forces Show Subset off, and the 3D page last so it renders with the
    field/colormap the sidebar has already restored.
    """
    grid, subset, view3d = canvas._grid_cb, canvas._subset_cb, canvas._view3d_cb
    grid.setChecked(bool(vs.get("show_grid", grid.isChecked())))
    if grid.isChecked():  # else the grid toggle already forced Show Subset off
        subset.setChecked(bool(vs.get("show_subset", subset.isChecked())))
    view3d.setChecked(bool(vs.get("view_3d", view3d.isChecked())))


def capture(signals, canvas) -> dict:
    """Snapshot the live display state as a persistable ``view_state`` dict.

    Keys are exactly :data:`VIEW_STATE_KEYS`: the sidebar/``GuiSignals`` half
    below plus :func:`capture_canvas`.
    """
    s = signals
    vs = {
        "display_field": str(s.display_field),
        "colormap": str(s.colormap),
        "color_auto": bool(s.color_auto),
        "color_min": float(s.color_min),
        "color_max": float(s.color_max),
        "overlay_alpha": float(s.overlay_alpha),
        "show_deformed": bool(s.show_deformed),
        "camera": str(s.current_camera),
        "current_frame": int(s.current_frame),
        "display_unit": str(s.display_unit),
        "frame_rate": float(s.frame_rate),
        "mesh_line_color": str(s.mesh_line_color),
        "mesh_line_width": int(s.mesh_line_width),
    }
    vs.update(capture_canvas(canvas))
    return vs


def set_blocked(widget, setter) -> None:
    """Run ``setter(widget)`` with the widget's signals blocked."""
    widget.blockSignals(True)
    try:
        setter(widget)
    finally:
        widget.blockSignals(False)


def apply_to_sidebar(sidebar, vs: dict, n_frames: int) -> None:
    """Apply a saved ``view_state`` dict through the right sidebar's widgets."""
    s = sidebar.signals
    s.display_field = str(vs.get("display_field", s.display_field))
    sidebar._field_selector._sync_checked()
    cmap = str(vs.get("colormap", s.colormap))
    if sidebar._cmap_combo.findText(cmap) != -1:
        s.colormap = cmap
        set_blocked(sidebar._cmap_combo, lambda w: w.setCurrentText(cmap))
    s.color_min = float(vs.get("color_min", s.color_min))
    s.color_max = float(vs.get("color_max", s.color_max))
    set_blocked(sidebar._vmin_spin, lambda w: w.setValue(s.color_min))
    set_blocked(sidebar._vmax_spin, lambda w: w.setValue(s.color_max))
    s.color_auto = bool(vs.get("color_auto", s.color_auto))
    set_blocked(sidebar._auto_range_cb, lambda w: w.setChecked(s.color_auto))
    sidebar._vmin_spin.setEnabled(not s.color_auto)
    sidebar._vmax_spin.setEnabled(not s.color_auto)
    s.overlay_alpha = float(vs.get("overlay_alpha", s.overlay_alpha))
    set_blocked(sidebar._opacity_slider, lambda w: w.setValue(int(s.overlay_alpha * 100)))
    s.show_deformed = bool(vs.get("show_deformed", s.show_deformed))
    set_blocked(sidebar._deformed_cb, lambda w: w.setChecked(s.show_deformed))
    sidebar._units.apply_view_state(vs)  # Q1: display unit + frame rate
    # Q8: mesh-overlay appearance — the canvas controls resync from the
    # signals on the display_changed emitted below.
    s.mesh_line_color = str(vs.get("mesh_line_color", s.mesh_line_color))
    s.mesh_line_width = int(vs.get("mesh_line_width", s.mesh_line_width))
    cam = str(vs.get("camera", s.current_camera))
    if cam in ("L", "R"):
        sidebar._pick_camera(cam)  # no-op emit when unchanged; renders otherwise
    s.set_current_frame(int(vs.get("current_frame", s.current_frame)), max(1, n_frames))
    s.display_changed.emit()
