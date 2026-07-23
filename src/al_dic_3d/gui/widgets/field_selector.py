"""``FieldSelector3D`` — toggle-button grid choosing the displayed result field.

The MAIN window shows displacement only (U / V / W / Magnitude — 3D world-frame
components); strain fields live in the dedicated Strain window (Batch C: strain
is post-processing, with its own field selector). Exactly one button is checked;
the choice is pushed to :class:`~al_dic_3d.gui.state.GuiSignals`.
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


_DISP_FIELDS = (("U", "U"), ("V", "V"), ("W", "W"), ("mag", "|D|"), ("velocity", "Vel"))


class FieldSelector3D(QWidget):
    """Labelled grid of mutually-exclusive displacement-field toggle buttons."""

    def __init__(self, signals: GuiSignals, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._signals = signals
        self._buttons: dict[str, QPushButton] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        layout.addWidget(self._group_label(self.tr("DISPLACEMENT")))
        layout.addWidget(self._grid(_DISP_FIELDS, columns=2))

        self.set_velocity_enabled(False)  # Q2: needs results (two frames)
        self._sync_checked()

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
        # Displacement = P^k − P^1 in the world frame (= left camera: X right,
        # Y down, Z toward the scene) — the tooltips spell that out (G2.1).
        tips = {
            "U": self.tr(
                "U — world-frame displacement along X (left camera's +X, image right), in mm"
            ),
            "V": self.tr(
                "V — world-frame displacement along Y (left camera's +Y, image down), in mm"
            ),
            "W": self.tr(
                "W — world-frame displacement along Z (left camera's optical "
                "axis, toward the scene): out-of-plane motion, in mm"
            ),
            "mag": self.tr("|D| — displacement magnitude √(U²+V²+W²), in mm"),
            "velocity": self.tr(
                "Velocity — per-node speed |D(k) − D(k−1)| × frame rate, in "
                "the display unit per second. Depends on the frame rate set "
                "in the UNITS section; frame 1 has no predecessor (empty)."
            ),
        }
        for i, (field_id, label) in enumerate(fields):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(28)
            if field_id in tips:
                btn.setToolTip(tips[field_id])
            btn.clicked.connect(lambda _=False, f=field_id: self._on_pick(f))
            grid.addWidget(btn, i // columns, i % columns)
            self._buttons[field_id] = btn
        return host

    def set_velocity_enabled(self, enabled: bool) -> None:
        """Q2: the Velocity field needs results; disabled it explains itself."""
        btn = self._buttons.get("velocity")
        if btn is None:
            return
        btn.setEnabled(enabled)
        if not enabled:
            btn.setToolTip(self.tr("Run an analysis first — velocity needs results."))
        else:
            btn.setToolTip(
                self.tr(
                    "Velocity — per-node speed |D(k) − D(k−1)| × frame rate, in "
                    "the display unit per second. Depends on the frame rate set "
                    "in the UNITS section; frame 1 has no predecessor (empty)."
                )
            )

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
