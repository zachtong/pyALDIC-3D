"""``GuiSignals`` — the Qt signal hub between the (Qt-free) controller and the view.

The 2D app centralises view synchronisation on an ``AppState`` singleton with Qt
signals; the 3D backend keeps its state Qt-free (``AppState3D`` / ``ProjectDraft``
/ ``WorkflowController``), so this thin ``QObject`` carries ONLY the signals.
Panels connect to it; whoever mutates the state emits the matching signal.

Display state (which field / frame / camera / colormap the user is looking at)
lives here too — it is view state, not project state, though selected bits are
persisted through ``AppState3D.view_state``.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

# Field identifiers (3D-DIC): world-frame displacement components + surface strain.
DISPLACEMENT_FIELDS = ("U", "V", "W", "mag")
STRAIN_FIELDS_UI = ("exx", "eyy", "exy", "e1", "e2", "max_shear", "von_mises")


class GuiSignals(QObject):
    """Pure signal hub (no data) + the transient display state."""

    images_changed = Signal()
    calibration_changed = Signal()
    roi_changed = Signal()
    params_changed = Signal()
    frame_changed = Signal(int)
    camera_changed = Signal(str)  # "L" | "R"
    display_changed = Signal()  # field / colormap / range / opacity
    run_state_changed = Signal(str)  # "idle" | "running" | "done" | "failed"
    progress = Signal(float, str)
    results_changed = Signal()
    log = Signal(str, str)  # message, level

    def __init__(self) -> None:
        super().__init__()
        # View/display state (not persisted except through view_state).
        self.current_frame: int = 0
        self.current_camera: str = "L"
        self.show_deformed: bool = True
        self.display_field: str = "U"
        self.colormap: str = "turbo"
        self.color_auto: bool = True
        self.color_min: float = 0.0
        self.color_max: float = 1.0
        self.overlay_alpha: float = 0.85
        self.run_state: str = "idle"

    # -- mutators that keep signal emission consistent -------------------------

    def set_current_frame(self, idx: int, n_frames: int) -> None:
        idx = max(0, min(idx, max(0, n_frames - 1)))
        if idx != self.current_frame:
            self.current_frame = idx
            self.frame_changed.emit(idx)

    def set_camera(self, cam: str) -> None:
        if cam != self.current_camera:
            self.current_camera = cam
            self.camera_changed.emit(cam)

    def set_show_deformed(self, on: bool) -> None:
        """Plot geometry on the deformed frame (True) or the reference frame."""
        if on != self.show_deformed:
            self.show_deformed = on
            self.display_changed.emit()

    def set_display_field(self, field: str) -> None:
        if field != self.display_field:
            self.display_field = field
            self.display_changed.emit()

    def set_run_state(self, state: str) -> None:
        if state != self.run_state:
            self.run_state = state
            self.run_state_changed.emit(state)
