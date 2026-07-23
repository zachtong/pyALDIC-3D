"""``MeshAppearanceControls`` — mesh-overlay line color + width (Q8).

Compact toolbar variant of the 2D ``MeshAppearanceWidget``: a color-swatch
button opening ``QColorDialog`` and a 1–8 px width spinbox. Writes to
:class:`~al_dic_3d.gui.state.GuiSignals` (``mesh_line_color`` /
``mesh_line_width``, persisted through ``view_state``) and emits
``display_changed``; the canvas pushes the values into ``MeshOverlay``.
Resyncs itself on ``display_changed`` so a view-state restore lands here too.
"""

from __future__ import annotations

from al_dic.gui.theme import COLORS
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QHBoxLayout, QPushButton, QSpinBox, QWidget

from al_dic_3d.gui.state import GuiSignals


class MeshAppearanceControls(QWidget):
    """Color swatch + width spin for the mesh preview overlay."""

    def __init__(self, signals: GuiSignals, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._signals = signals

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._color_btn = QPushButton()
        self._color_btn.setFixedSize(24, 18)
        self._color_btn.setToolTip(self.tr("Mesh overlay line color — click to choose"))
        self._color_btn.clicked.connect(self._pick_color)
        layout.addWidget(self._color_btn)

        self._width_spin = QSpinBox()
        self._width_spin.setRange(1, 8)
        self._width_spin.setValue(int(signals.mesh_line_width))
        self._width_spin.setSuffix(" px")
        self._width_spin.setFixedWidth(56)
        self._width_spin.setToolTip(self.tr("Mesh overlay line width (screen pixels)"))
        self._width_spin.valueChanged.connect(self._on_width_changed)
        layout.addWidget(self._width_spin)

        self._set_button_color(signals.mesh_line_color)
        # A view-state restore writes GuiSignals directly and emits ONE
        # display_changed — resync the controls from there (blocked).
        signals.display_changed.connect(self._sync_from_signals)

    # ------------------------------------------------------------------

    def _sync_from_signals(self) -> None:
        self._set_button_color(self._signals.mesh_line_color)
        if self._width_spin.value() != int(self._signals.mesh_line_width):
            self._width_spin.blockSignals(True)
            self._width_spin.setValue(int(self._signals.mesh_line_width))
            self._width_spin.blockSignals(False)

    def _set_button_color(self, hex_color: str) -> None:
        self._color_btn.setStyleSheet(
            f"QPushButton {{ background: {hex_color}; "
            f"border: 1px solid {COLORS.BORDER}; border-radius: 3px; }}"
        )

    def _pick_color(self) -> None:
        initial = QColor(self._signals.mesh_line_color)
        color = QColorDialog.getColor(initial, self, self.tr("Choose mesh line color"))
        if not color.isValid():
            return
        self._signals.mesh_line_color = color.name()  # "#rrggbb"
        self._set_button_color(color.name())
        self._signals.display_changed.emit()

    def _on_width_changed(self, value: int) -> None:
        self._signals.mesh_line_width = int(value)
        self._signals.display_changed.emit()
