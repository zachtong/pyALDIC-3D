"""``UnitsSection3D`` — content of the collapsible UNITS sidebar section (Q1).

Adapted from the 2D ``PhysicalUnitsWidget``: the 3D pipeline is metric-native
(mm world coordinates from calibration), so there is NO pixel-size input — only
a display-unit choice and the acquisition frame rate (which feeds the Q2
velocity field). Conversion is display-layer only; data and exports stay mm.
Writes to :class:`~al_dic_3d.gui.state.GuiSignals` and emits
``display_changed``; the choice is persisted through ``view_state``.
"""

from __future__ import annotations

from al_dic.gui.widgets.double_spin import LocaleSafeDoubleSpinBox
from PySide6.QtWidgets import QComboBox, QFormLayout, QWidget

from al_dic_3d.gui.display_units import DEFAULT_UNIT, UNIT_OPTIONS
from al_dic_3d.gui.state import GuiSignals


class UnitsSection3D(QWidget):
    """Display unit combo + frame-rate spinbox, wired to GuiSignals."""

    def __init__(self, signals: GuiSignals, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._signals = signals

        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._unit_combo = QComboBox()
        for unit in UNIT_OPTIONS:
            self._unit_combo.addItem(unit)
        self._unit_combo.setCurrentText(signals.display_unit or DEFAULT_UNIT)
        self._unit_combo.setToolTip(
            self.tr(
                "Display unit for displacement and velocity values (colorbar,\n"
                "3D scalar bar). Display only — the data and every export stay\n"
                "in millimetres. Strain is dimensionless and unaffected."
            )
        )
        layout.addRow(self.tr("Display unit"), self._unit_combo)

        self._fps_spin = LocaleSafeDoubleSpinBox()
        self._fps_spin.setDecimals(3)
        # 0 = not given (fix batch V, M10): velocity is then shown per frame.
        self._fps_spin.setRange(0.0, 1e9)
        self._fps_spin.setSingleStep(1.0)
        self._fps_spin.setSpecialValueText(self.tr("not set (per frame)"))
        self._fps_spin.setValue(float(signals.frame_rate) if signals.frame_rate_known else 0.0)
        self._fps_spin.setSuffix(" fps")
        self._fps_spin.setToolTip(
            self.tr(
                "Acquisition frame rate. Used only by the Velocity field:\n"
                "velocity = |D(k) − D(k−1)| × frame rate, shown in the\n"
                "display unit per second. Leave it at 'not set' to see the\n"
                "velocity per frame."
            )
        )
        layout.addRow(self.tr("Frame rate"), self._fps_spin)

        self._unit_combo.currentTextChanged.connect(self._on_changed)
        self._fps_spin.valueChanged.connect(self._on_changed)

    # ------------------------------------------------------------------

    def _on_changed(self, *_args: object) -> None:
        self._signals.display_unit = self._unit_combo.currentText()
        fps = float(self._fps_spin.value())
        self._signals.frame_rate_known = fps > 0
        self._signals.frame_rate = fps if fps > 0 else 1.0  # per frame when not set
        self._signals.display_changed.emit()

    def apply_view_state(self, vs: dict) -> None:
        """Restore unit/frame-rate from a saved ``view_state`` (signals blocked)."""
        s = self._signals
        unit = str(vs.get("display_unit", s.display_unit))
        if unit in UNIT_OPTIONS:
            s.display_unit = unit
            self._unit_combo.blockSignals(True)
            self._unit_combo.setCurrentText(unit)
            self._unit_combo.blockSignals(False)
        fps = float(vs.get("frame_rate", s.frame_rate))
        # Sessions before fix batch V always stored 1.0 (the silent default):
        # without the explicit flag, 1.0 means "not given".
        known = bool(vs.get("frame_rate_known", fps > 0 and fps != 1.0))
        if fps > 0:
            s.frame_rate = fps if known else 1.0
            s.frame_rate_known = known
            self._fps_spin.blockSignals(True)
            self._fps_spin.setValue(fps if known else 0.0)
            self._fps_spin.blockSignals(False)
