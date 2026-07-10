"""``StrainFieldSelector3D`` — strain-field toggle grid for the strain window.

The strain post-processing window's FIELD section: the seven Green-Lagrange
surface-strain invariants as mutually-exclusive toggle buttons (2D
``StrainFieldSelector`` idiom). Buttons stay disabled until a compute has
populated ``RunResult.strain``. Independent of :class:`GuiSignals` — the strain
window owns its own display state.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QWidget

from al_dic_3d.gui.state import STRAIN_FIELDS_UI
from al_dic_3d.gui.widgets.field_selector import apply_toggle_style

# Field id -> button label (math notation, not translated prose) — matches
# canvas_area._FIELD_LABELS for the strain family.
STRAIN_FIELD_LABELS: dict[str, str] = {
    "exx": "εxx",
    "eyy": "εyy",
    "exy": "εxy",
    "e1": "ε₁",
    "e2": "ε₂",
    "max_shear": "γ max",
    "von_mises": "von Mises",
}


class StrainFieldSelector3D(QWidget):
    """Grid of mutually-exclusive strain-field toggle buttons."""

    field_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        from PySide6.QtWidgets import QPushButton

        self._buttons: dict[str, QPushButton] = {}
        self._current: str = STRAIN_FIELDS_UI[0]

        # Green-Lagrange surface-strain invariants, in the strain coordinate
        # system chosen above (tangent plane / camera / specimen) — G2.1.
        tips = {
            "exx": self.tr("εxx — normal strain along the strain frame's x axis"),
            "eyy": self.tr("εyy — normal strain along the strain frame's y axis"),
            "exy": self.tr("εxy — in-plane shear strain (tensor component)"),
            "e1": self.tr("ε₁ — major principal strain (largest in-plane eigenvalue)"),
            "e2": self.tr("ε₂ — minor principal strain (smallest in-plane eigenvalue)"),
            "max_shear": self.tr("γ max — maximum shear strain, (ε₁ − ε₂) / 2"),
            "von_mises": self.tr("von Mises — equivalent strain (plane-stress invariant)"),
        }
        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(4)
        for i, field_id in enumerate(STRAIN_FIELDS_UI):
            btn = QPushButton(STRAIN_FIELD_LABELS[field_id])
            btn.setCheckable(True)
            btn.setFixedHeight(28)
            if field_id in tips:
                btn.setToolTip(tips[field_id])
            btn.clicked.connect(lambda _=False, f=field_id: self._on_pick(f))
            grid.addWidget(btn, i // 3, i % 3)
            self._buttons[field_id] = btn

        self._sync_checked()
        self.set_fields_available(False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def current_field(self) -> str:
        return self._current

    def set_current_field(self, field_id: str) -> None:
        """Programmatically activate ``field_id``; emits only on a change."""
        if field_id not in self._buttons:
            raise ValueError(f"unknown strain field {field_id!r}; allowed: {STRAIN_FIELDS_UI}")
        if field_id == self._current:
            return
        self._current = field_id
        self._sync_checked()
        self.field_changed.emit(field_id)

    def set_fields_available(self, available: bool) -> None:
        """Enable the buttons only once a compute has produced strain."""
        for btn in self._buttons.values():
            btn.setEnabled(available)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_pick(self, field_id: str) -> None:
        if field_id == self._current:
            self._buttons[field_id].setChecked(True)
            return
        self._current = field_id
        self._sync_checked()
        self.field_changed.emit(field_id)

    def _sync_checked(self) -> None:
        for field_id, btn in self._buttons.items():
            btn.blockSignals(True)
            btn.setChecked(field_id == self._current)
            btn.blockSignals(False)
            apply_toggle_style(btn)
