"""``StrainFieldSelector3D`` — field toggle grid for the strain window.

The strain post-processing window's FIELD section, in three groups of
mutually-exclusive toggle buttons (2D ``StrainFieldSelector`` idiom):

* **Displacement** U / V / W / |D| — available as soon as a run exists, so the
  effect of rigid-motion removal is visible before any strain is computed;
* **Slope** ∂w/∂x, ∂w/∂y — the out-of-plane slopes of the strain fit;
* **Strain** — the seven Green-Lagrange surface-strain invariants.

Slope and strain buttons stay disabled until a compute has populated
``RunResult.strain``. Independent of :class:`GuiSignals` — the strain window
owns its own display state.
"""

from __future__ import annotations

from al_dic.gui.theme import COLORS
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from al_dic_3d.gui.state import SLOPE_FIELDS_UI, STRAIN_FIELDS_UI, STRAIN_WINDOW_DISP_FIELDS
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
DISP_FIELD_LABELS: dict[str, str] = {"U": "U", "V": "V", "W": "W", "mag": "|D|"}
SLOPE_FIELD_LABELS: dict[str, str] = {"dwdx": "∂w/∂x", "dwdy": "∂w/∂y"}


class StrainFieldSelector3D(QWidget):
    """Grouped grid of mutually-exclusive field toggle buttons."""

    field_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._buttons: dict[str, QPushButton] = {}
        self._current: str = STRAIN_FIELDS_UI[0]

        tips = {
            "U": self.tr("U — displacement along the world X axis (left camera)"),
            "V": self.tr("V — displacement along the world Y axis (left camera)"),
            "W": self.tr("W — displacement along the world Z axis (left camera)"),
            "mag": self.tr("|D| — displacement magnitude"),
            "dwdx": self.tr("∂w/∂x — out-of-plane slope along the strain frame's x axis"),
            "dwdy": self.tr("∂w/∂y — out-of-plane slope along the strain frame's y axis"),
            # Green-Lagrange surface-strain invariants, in the strain coordinate
            # system chosen above (tangent plane / camera / specimen) — G2.1.
            "exx": self.tr("εxx — normal strain along the strain frame's x axis"),
            "eyy": self.tr("εyy — normal strain along the strain frame's y axis"),
            "exy": self.tr("εxy — in-plane shear strain (tensor component)"),
            "e1": self.tr("ε₁ — major principal strain (largest in-plane eigenvalue)"),
            "e2": self.tr("ε₂ — minor principal strain (smallest in-plane eigenvalue)"),
            "max_shear": self.tr("γ max — maximum shear strain, (ε₁ − ε₂) / 2"),
            "von_mises": self.tr("von Mises — equivalent strain (plane-stress invariant)"),
        }
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        groups = (
            (self.tr("Displacement"), STRAIN_WINDOW_DISP_FIELDS, DISP_FIELD_LABELS, 4),
            (self.tr("Slope"), SLOPE_FIELDS_UI, SLOPE_FIELD_LABELS, 2),
            (self.tr("Strain"), STRAIN_FIELDS_UI, STRAIN_FIELD_LABELS, 3),
        )
        for title, ids, labels, columns in groups:
            header = QLabel(title)
            header.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 10px;")
            layout.addWidget(header)
            grid = QGridLayout()
            grid.setSpacing(4)
            for i, field_id in enumerate(ids):
                btn = QPushButton(labels[field_id])
                btn.setCheckable(True)
                btn.setFixedHeight(28)
                btn.setToolTip(tips[field_id])
                btn.clicked.connect(lambda _=False, f=field_id: self._on_pick(f))
                grid.addWidget(btn, i // columns, i % columns)
                self._buttons[field_id] = btn
            layout.addLayout(grid)

        self._sync_checked()
        self.set_displacement_available(False)
        self.set_fields_available(False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def current_field(self) -> str:
        return self._current

    def set_current_field(self, field_id: str) -> None:
        """Programmatically activate ``field_id``; emits only on a change."""
        if field_id not in self._buttons:
            allowed = list(self._buttons)
            raise ValueError(f"unknown strain-window field {field_id!r}; allowed: {allowed}")
        if field_id == self._current:
            return
        self._current = field_id
        self._sync_checked()
        self.field_changed.emit(field_id)

    def set_fields_available(self, available: bool) -> None:
        """Strain and slope buttons: enabled once a compute has produced strain."""
        for field_id in (*SLOPE_FIELDS_UI, *STRAIN_FIELDS_UI):
            self._buttons[field_id].setEnabled(available)

    def set_displacement_available(self, available: bool) -> None:
        """Displacement buttons: enabled whenever a run result exists."""
        for field_id in STRAIN_WINDOW_DISP_FIELDS:
            self._buttons[field_id].setEnabled(available)

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
