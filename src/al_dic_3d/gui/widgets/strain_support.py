"""Support classes for the strain window (extracted for file size).

``PickCanvas`` — the read-only canvas with the 3-point pick click mode;
``ZoomBar`` — the Fit / live-readout / in / out toolbar over a canvas (G2.4);
``StrainWorker`` — the background strain-compute QThread (with per-frame
progress relay and a cooperative cancel event, P3.5). All are pure plumbing
with no window state, so they live here; ``StrainWindow3D`` wires them.
"""

from __future__ import annotations

import threading

from al_dic.gui.icons import icon_maximize, icon_zoom_in, icon_zoom_out
from al_dic.gui.theme import COLORS
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

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


class ZoomBar(QWidget):
    """Fit / live zoom readout / in / out toolbar wired to a canvas (G2.4).

    Extracted verbatim from ``StrainWindow3D`` (file-size discipline, P3.5):
    the readout button follows ``canvas.view_changed`` and clicking it resets
    to 100%. ``zoom_btn`` stays public for the window's historical alias.
    """

    def __init__(self, canvas: ImageCanvas3D, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setStyleSheet(
            f"background: {COLORS.BG_PANEL}; border-bottom: 1px solid {COLORS.BORDER};"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(4)
        btn_fit = QPushButton(self.tr("Fit"))
        btn_fit.setToolTip(self.tr("Fit image to viewport"))
        btn_fit.setFixedWidth(60)
        btn_fit.setIcon(icon_maximize())
        # G2.4: live zoom readout — the label follows the zoom percent.
        self.zoom_btn = QPushButton("100%")
        self.zoom_btn.setToolTip(
            self.tr(
                "Current zoom — click to reset to 100% (1:1 pixels).\n"
                "Wheel: zoom · Right/middle drag: pan · Space: pan mode"
            )
        )
        self.zoom_btn.setFixedWidth(60)
        btn_in = QPushButton()
        btn_in.setToolTip(self.tr("Zoom in"))
        btn_in.setFixedWidth(28)
        btn_in.setIcon(icon_zoom_in())
        btn_out = QPushButton()
        btn_out.setToolTip(self.tr("Zoom out"))
        btn_out.setFixedWidth(28)
        btn_out.setIcon(icon_zoom_out())
        for b in (btn_fit, self.zoom_btn, btn_in, btn_out):
            layout.addWidget(b)
        layout.addStretch()

        btn_fit.clicked.connect(canvas.fit_to_view)
        self.zoom_btn.clicked.connect(canvas.zoom_to_100)
        btn_in.clicked.connect(canvas.zoom_in)
        btn_out.clicked.connect(canvas.zoom_out)
        canvas.view_changed.connect(
            lambda: self.zoom_btn.setText(f"{canvas.zoom_level * 100:.0f}%")
        )


class StrainWorker(QThread):
    """Background strain compute; state writeback happens in the window's slot.

    P3.5: relays the compute's per-frame ``(fraction, message)`` ticks as the
    ``progress`` signal and carries a cooperative cancel event —
    :meth:`request_stop` makes the compute abort at the next frame boundary,
    emitting ``cancelled`` instead of ``failed``.
    """

    finished_ok = Signal(object)  # StrainResult3D
    failed = Signal(str)
    cancelled = Signal()
    progress = Signal(float, str)  # (fraction 0..1, message) per frame

    def __init__(self, ctrl, override: dict) -> None:
        super().__init__()
        self._ctrl = ctrl
        self._override = override
        self._stop_event = threading.Event()

    def request_stop(self) -> None:
        """Ask the compute to stop at the next per-frame checkpoint."""
        self._stop_event.set()

    def run(self) -> None:  # QThread entry point (worker thread)
        try:
            strain = self._ctrl.compute(
                self._override,
                progress_cb=lambda frac, msg: self.progress.emit(frac, msg),
                stop_event=self._stop_event,
            )
            self.finished_ok.emit(strain)
        except Exception as exc:  # noqa: BLE001 - report any failure to the UI
            if self._stop_event.is_set():
                self.cancelled.emit()
                return
            import traceback

            traceback.print_exc()  # full traceback to stderr (F3.1)
            self.failed.emit(f"{type(exc).__name__}: {exc}")
