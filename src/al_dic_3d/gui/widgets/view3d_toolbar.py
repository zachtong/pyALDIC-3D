"""``View3DToolbar`` — the 3D View's controls (widgets only; wired in ``View3D``).

Row 1, the view: Reset and the specimen-aligned presets (Camera / Normal / Side /
Iso), Save image. Row 2, what is drawn: the deformation magnification (with an
Auto pick and an out-of-plane-only switch), the reference shape, the camera
frusta and the surface shading.
"""

from __future__ import annotations

from dataclasses import dataclass

from al_dic.gui.theme import COLORS
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.viz3d.view_setup import MAGNIFICATIONS


@dataclass(frozen=True)
class View3DOptions:
    magnification: float = 1.0
    normal_only: bool = False
    show_reference: bool = False
    show_cameras: bool = False
    shading: bool = True


class View3DToolbar(QWidget):
    """Compact two-row toolbar above the 3D viewport."""

    preset_requested = Signal(str)  # "camera" | "normal" | "side" | "iso"
    save_requested = Signal()
    auto_requested = Signal()
    options_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 2)
        root.setSpacing(3)

        views = QHBoxLayout()
        views.setSpacing(4)
        presets = (
            ("camera", self.tr("Reset"), self.tr("Back to the view from the left camera, framed")),
            ("camera", self.tr("Camera"), self.tr("Look from the left camera (as in the images)")),
            ("normal", self.tr("Normal"), self.tr("Look straight at the specimen surface")),
            ("side", self.tr("Side"), self.tr("Edge-on: the out-of-plane profile")),
            ("iso", self.tr("Iso"), self.tr("Oblique view of the specimen")),
        )
        for name, text, tip in presets:
            views.addWidget(
                self._button(text, tip, lambda _=False, n=name: self.preset_requested.emit(n))
            )
        views.addStretch(1)
        views.addWidget(
            self._button(
                self.tr("Save image…"),
                self.tr("Save the 3D view as a PNG image"),
                self.save_requested.emit,
            )
        )
        root.addLayout(views)

        shows = QHBoxLayout()
        shows.setSpacing(6)
        shows.addWidget(QLabel(self.tr("Deformation ×")))
        self._mag = QComboBox()
        for m in MAGNIFICATIONS:
            self._mag.addItem(f"{m:g}", float(m))
        self._mag.setToolTip(
            self.tr(
                "Exaggerate the displacement in the 3D geometry (reference shape plus\n"
                "factor × displacement) so a micron-scale change is visible. The\n"
                "colours always show the true values."
            )
        )
        self._mag.currentIndexChanged.connect(lambda _i: self.options_changed.emit())
        shows.addWidget(self._mag)
        shows.addWidget(
            self._button(
                self.tr("Auto"),
                self.tr("Pick a factor that makes the change visible"),
                self.auto_requested.emit,
            )
        )
        self._normal_only = self._check(
            self.tr("Out-of-plane only"),
            self.tr(
                "Exaggerate only the displacement along the specimen normal\n"
                "(in-plane noise stays at true scale)"
            ),
            False,
        )
        self._reference = self._check(
            self.tr("Reference shape"), self.tr("Show the frame-1 surface as a wireframe"), False
        )
        self._cameras = self._check(
            self.tr("Cameras"), self.tr("Show the two camera frusta (zooms the view out)"), False
        )
        self._shading = self._check(
            self.tr("Shading"),
            self.tr("Light the surface so its shape reads; off shows the exact colormap colours"),
            True,
        )
        for box in (self._normal_only, self._reference, self._cameras, self._shading):
            shows.addWidget(box)
        shows.addStretch(1)
        root.addLayout(shows)
        self.setStyleSheet(
            f"QLabel, QCheckBox {{ color: {COLORS.TEXT_SECONDARY}; font-size: 11px; }}"
        )

    def _button(self, text: str, tip: str, slot) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(24)
        btn.setToolTip(tip)
        btn.clicked.connect(slot)
        return btn

    def _check(self, text: str, tip: str, on: bool) -> QCheckBox:
        box = QCheckBox(text)
        box.setToolTip(tip)
        box.setChecked(on)
        box.toggled.connect(lambda _c: self.options_changed.emit())
        return box

    # ---- state ------------------------------------------------------------------

    def options(self) -> View3DOptions:
        return View3DOptions(
            magnification=float(self._mag.currentData()),
            normal_only=self._normal_only.isChecked(),
            show_reference=self._reference.isChecked(),
            show_cameras=self._cameras.isChecked(),
            shading=self._shading.isChecked(),
        )

    def set_magnification(self, factor: float) -> None:
        """Select ``factor`` (one of MAGNIFICATIONS); emits ``options_changed`` on a change."""
        idx = self._mag.findData(float(factor))
        if idx >= 0:
            self._mag.setCurrentIndex(idx)
