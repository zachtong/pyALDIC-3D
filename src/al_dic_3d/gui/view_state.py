"""Saved ``view_state`` -> live display-state application (G3.10 / batch Q).

Extracted from ``RightSidebar3D`` (file-size discipline): pure widget/signal
synchronisation with NO user-facing strings, applied when a project opens.
Pushes the dict into ``GuiSignals`` AND the sidebar's widgets (signals
blocked), then emits ONE ``display_changed``.
"""

from __future__ import annotations


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
