"""Support classes for the strain window (extracted for file size).

``PickCanvas`` — the read-only canvas with the 3-point pick click mode; and
``StrainWorker`` — the background strain-compute QThread. Both are pure
plumbing with no window state, so they live here; ``StrainWindow3D`` wires
them.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread, Signal

from al_dic_3d.gui.widgets.image_view import ImageCanvas3D


class PickCanvas(ImageCanvas3D):
    """Read-only canvas with an optional 3-point pick mode (no ROI tools armed)."""

    point_picked = Signal(float, float)  # scene (x, y) of a left click in pick mode

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._pick_mode = False

    def set_pick_mode(self, on: bool) -> None:
        self._pick_mode = bool(on)
        self.setCursor(Qt.CursorShape.CrossCursor if on else Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if self._pick_mode and event.button() == Qt.MouseButton.LeftButton:
            sp = self.mapToScene(event.position().toPoint())
            self.point_picked.emit(sp.x(), sp.y())
            return
        super().mousePressEvent(event)


class StrainWorker(QThread):
    """Background strain compute; state writeback happens in the window's slot."""

    finished_ok = Signal(object)  # StrainResult3D
    failed = Signal(str)

    def __init__(self, ctrl, override: dict) -> None:
        super().__init__()
        self._ctrl = ctrl
        self._override = override

    def run(self) -> None:  # QThread entry point (worker thread)
        try:
            self.finished_ok.emit(self._ctrl.compute(self._override))
        except Exception as exc:  # noqa: BLE001 - report any failure to the UI
            import traceback

            traceback.print_exc()  # full traceback to stderr (F3.1)
            self.failed.emit(f"{type(exc).__name__}: {exc}")
