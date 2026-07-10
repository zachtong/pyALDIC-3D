"""VISUALIZATION panel widgets for the strain window (extracted for file size).

A dumb layout container: it builds the deformed-frame toggle, colormap combo,
Auto-range checkbox, locale-safe Min/Max bounds (G2.2) and the opacity slider
with their G2.1 tooltips, and exposes them as public attributes. ALL wiring
(render triggers, auto-range seeding) stays in ``StrainWindow3D`` — the panel
carries no behavior, so the window's decoupling contracts are untouched.
"""

from __future__ import annotations

from al_dic.gui.widgets.double_spin import LocaleSafeDoubleSpinBox
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QWidget,
)

_COLORMAPS = ["turbo", "viridis", "jet", "coolwarm", "plasma", "inferno", "RdBu_r"]


class StrainVizPanel3D(QWidget):
    """Deformed toggle / colormap / auto range + Min/Max / opacity (no wiring)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        form = QFormLayout(self)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(6)

        self.deformed_cb = QCheckBox(self.tr("Show on deformed frame"))
        self.deformed_cb.setChecked(True)
        self.deformed_cb.setToolTip(
            self.tr(
                "When checked, overlay results on the deformed (current) frame "
                "instead of the reference frame"
            )
        )
        form.addRow(self.deformed_cb)

        self.cmap_combo = QComboBox()
        self.cmap_combo.addItems(_COLORMAPS)
        self.cmap_combo.setToolTip(
            self.tr(
                "Colormap for the strain overlay. Default turbo; pick RdBu_r "
                "or coolwarm for signed strain centered on zero."
            )
        )
        form.addRow(self.tr("Colormap"), self.cmap_combo)

        self.auto_range_cb = QCheckBox(self.tr("Auto range"))
        self.auto_range_cb.setChecked(True)
        self.auto_range_cb.setToolTip(
            self.tr(
                "Rescale the color range to each frame's data range "
                "(2–98 percentile of the visible values). Default on; uncheck "
                "to type fixed Min/Max bounds that hold across frames."
            )
        )
        form.addRow(self.auto_range_cb)

        # G2.2: locale-safe manual bounds (dot decimal accepted everywhere),
        # enabled with Auto off, seeded by the window from the rendered range.
        self.vmin_spin = LocaleSafeDoubleSpinBox()
        self.vmax_spin = LocaleSafeDoubleSpinBox()
        for spin, tip in (
            (self.vmin_spin, self.tr("Lower color-range bound (only with Auto range off)")),
            (self.vmax_spin, self.tr("Upper color-range bound (only with Auto range off)")),
        ):
            spin.setDecimals(6)
            spin.setRange(-1e9, 1e9)
            spin.setSingleStep(1e-3)
            spin.setEnabled(False)
            spin.setToolTip(tip)
        minmax = QHBoxLayout()
        minmax.setSpacing(4)
        minmax.setContentsMargins(0, 0, 0, 0)
        minmax.addWidget(QLabel(self.tr("Min")))
        minmax.addWidget(self.vmin_spin, 1)
        minmax.addWidget(QLabel(self.tr("Max")))
        minmax.addWidget(self.vmax_spin, 1)
        minmax_host = QWidget()
        minmax_host.setLayout(minmax)
        form.addRow(minmax_host)

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(85)
        self.opacity_slider.setToolTip(self.tr("Overlay opacity (0 = transparent, 100 = opaque)"))
        form.addRow(self.tr("Opacity"), self.opacity_slider)
