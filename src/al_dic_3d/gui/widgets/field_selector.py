"""``FieldSelector3D`` — toggle-button grid choosing the displayed result field.

Mirrors the 2D strain window's FIELD section: a DISPLACEMENT group (U / V / W /
Magnitude — 3D world-frame components) and a STRAIN group (Green-Lagrange surface
strain invariants). Exactly one button is checked; the choice is pushed to
:class:`~al_dic_3d.gui.state.GuiSignals`.
"""

from __future__ import annotations

from al_dic.gui.theme import COLORS
from PySide6.QtWidgets import QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from al_dic_3d.gui.state import GuiSignals


# (field_id, label) — labels are math notation, not translated prose.
def apply_toggle_style(btn: QPushButton) -> None:
    """Active/inactive toggle styling (the 2D FieldSelector idiom)."""
    if btn.isChecked():
        btn.setStyleSheet(
            f"background: {COLORS.ACCENT}; color: white; "
            f"border: none; border-radius: 4px; font-weight: bold;"
        )
    else:
        btn.setStyleSheet(
            f"background: {COLORS.BG_INPUT}; color: {COLORS.TEXT_SECONDARY}; "
            f"border: 1px solid {COLORS.BORDER}; border-radius: 4px;"
        )


_DISP_FIELDS = (("U", "U"), ("V", "V"), ("W", "W"), ("mag", "|D|"))
_STRAIN_FIELDS = (
    ("exx", "εxx"),
    ("eyy", "εyy"),
    ("exy", "εxy"),
    ("e1", "ε₁"),
    ("e2", "ε₂"),
    ("max_shear", "γ max"),
    ("von_mises", "von Mises"),
)


class FieldSelector3D(QWidget):
    """Two labelled grids of mutually-exclusive field toggle buttons."""

    def __init__(self, signals: GuiSignals, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._signals = signals
        self._buttons: dict[str, QPushButton] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        layout.addWidget(self._group_label(self.tr("DISPLACEMENT")))
        layout.addWidget(self._grid(_DISP_FIELDS, columns=2))
        self._strain_label = self._group_label(self.tr("STRAIN"))
        layout.addWidget(self._strain_label)
        self._strain_grid = self._grid(_STRAIN_FIELDS, columns=3)
        layout.addWidget(self._strain_grid)

        self._sync_checked()
        self.set_strain_available(False)

    def _group_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {COLORS.TEXT_MUTED}; font-size: 10px; font-weight: bold; letter-spacing: 1px;"
        )
        return lbl

    def _grid(self, fields: tuple, columns: int) -> QWidget:
        host = QWidget()
        grid = QGridLayout(host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(4)
        for i, (field_id, label) in enumerate(fields):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda _=False, f=field_id: self._on_pick(f))
            grid.addWidget(btn, i // columns, i % columns)
            self._buttons[field_id] = btn
        return host

    def _on_pick(self, field_id: str) -> None:
        self._signals.set_display_field(field_id)
        self._sync_checked()

    def _sync_checked(self) -> None:
        active = self._signals.display_field
        for field_id, btn in self._buttons.items():
            btn.blockSignals(True)
            btn.setChecked(field_id == active)
            btn.blockSignals(False)
            apply_toggle_style(btn)

    def set_strain_available(self, available: bool) -> None:
        """Enable/disable the strain group (strain may not have been computed)."""
        self._strain_label.setVisible(True)
        for field_id, _label in _STRAIN_FIELDS:
            self._buttons[field_id].setEnabled(available)
