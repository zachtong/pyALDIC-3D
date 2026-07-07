"""Manual camera-parameter entry dialog (D12 fallback entry mode).

Type per-camera intrinsics (fx/fy/cx/cy/skew + k1/k2/k3/p1/p2) and the stereo
extrinsics (Euler Z-Y-X degrees + T in mm, ``X_R = R @ X_L + T``, left camera =
world), preview the baseline, and save as ``opencv_yaml`` — the same funnel as
the built-in calibrator and the importers.
"""

from __future__ import annotations

import numpy as np
from al_dic.gui.theme import COLORS
from PySide6.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.calibration import (
    CameraIntrinsics,
    StereoRig,
    euler_to_rotation,
    to_opencv_yaml,
)

_INTR_FIELDS = (
    # (attr, label, default, decimals, range)
    ("fx", "fx (px)", 2000.0, 3, (0.001, 1e7)),
    ("fy", "fy (px)", 2000.0, 3, (0.001, 1e7)),
    ("cx", "cx (px)", 1024.0, 3, (-1e6, 1e6)),
    ("cy", "cy (px)", 768.0, 3, (-1e6, 1e6)),
    ("skew", "skew", 0.0, 4, (-1e4, 1e4)),
    ("k1", "k1", 0.0, 6, (-10.0, 10.0)),
    ("k2", "k2", 0.0, 6, (-10.0, 10.0)),
    ("k3", "k3", 0.0, 6, (-10.0, 10.0)),
    ("p1", "p1", 0.0, 6, (-1.0, 1.0)),
    ("p2", "p2", 0.0, 6, (-1.0, 1.0)),
)


class ManualParamsDialog(QDialog):
    """Fallback entry: type the calibration, save it as opencv_yaml."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Manual Camera Parameters"))
        self.setMinimumWidth(640)
        self.saved_path = None

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        cams = QHBoxLayout()
        self._left = self._camera_group(self.tr("Left camera (world frame)"))
        self._right = self._camera_group(self.tr("Right camera"))
        cams.addWidget(self._left[0])
        cams.addWidget(self._right[0])
        layout.addLayout(cams)

        ext = QGroupBox(self.tr("Stereo extrinsics  (X_R = R · X_L + T)"))
        grid = QGridLayout(ext)
        self._angles: list[QDoubleSpinBox] = []
        for j, name in enumerate(("Rx", "Ry", "Rz")):
            grid.addWidget(QLabel(self.tr("{0} (deg)").format(name)), 0, 2 * j)
            spin = _spin(0.0, 4, (-360.0, 360.0))
            spin.valueChanged.connect(self._refresh_preview)
            grid.addWidget(spin, 0, 2 * j + 1)
            self._angles.append(spin)
        self._trans: list[QDoubleSpinBox] = []
        for j, name in enumerate(("Tx", "Ty", "Tz")):
            grid.addWidget(QLabel(self.tr("{0} (mm)").format(name)), 1, 2 * j)
            spin = _spin(0.0, 4, (-1e6, 1e6))
            spin.valueChanged.connect(self._refresh_preview)
            grid.addWidget(spin, 1, 2 * j + 1)
            self._trans.append(spin)
        layout.addWidget(ext)

        note = QLabel(
            self.tr(
                "Euler composition R = Rz·Ry·Rx in degrees (MatchID/OpenCorr convention); "
                "distortion order k1, k2, p1, p2, k3 (OpenCV)."
            )
        )
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 10px;")
        layout.addWidget(note)

        self._preview = QLabel("")
        self._preview.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(self._preview)

        buttons = QHBoxLayout()
        buttons.addStretch()
        save_btn = QPushButton(self.tr("Save as YAML…"))
        save_btn.setProperty("class", "btn-primary")
        save_btn.setFixedHeight(32)
        save_btn.clicked.connect(self._on_save)
        buttons.addWidget(save_btn)
        cancel = QPushButton(self.tr("Cancel"))
        cancel.setFixedHeight(32)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        layout.addLayout(buttons)
        self._refresh_preview()

    def _camera_group(self, title: str) -> tuple[QGroupBox, dict[str, QDoubleSpinBox]]:
        group = QGroupBox(title)
        grid = QGridLayout(group)
        grid.setVerticalSpacing(3)
        spins: dict[str, QDoubleSpinBox] = {}
        for i, (attr, label, default, decimals, rng) in enumerate(_INTR_FIELDS):
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
            grid.addWidget(lbl, i, 0)
            spin = _spin(default, decimals, rng)
            grid.addWidget(spin, i, 1)
            spins[attr] = spin
        return group, spins

    def _rig(self) -> StereoRig:
        def intr(spins: dict[str, QDoubleSpinBox]) -> CameraIntrinsics:
            return CameraIntrinsics(**{attr: s.value() for attr, s in spins.items()})

        R = euler_to_rotation(
            self._angles[0].value(), self._angles[1].value(), self._angles[2].value()
        )
        T = np.array([s.value() for s in self._trans], dtype=np.float64)
        return StereoRig(
            cameras={"L": intr(self._left[1]), "R": intr(self._right[1])},
            extrinsics={("L", "R"): (R, T)},
        )

    def _refresh_preview(self) -> None:
        baseline = float(np.linalg.norm([s.value() for s in self._trans]))
        self._preview.setText(self.tr("Baseline |T| = {0:.2f} mm").format(baseline))

    def _on_save(self) -> None:
        baseline = float(np.linalg.norm([s.value() for s in self._trans]))
        if baseline <= 0.0:
            self._preview.setText(self.tr("Baseline is zero — enter the translation T first."))
            self._preview.setStyleSheet(f"color: {COLORS.WARNING}; font-size: 11px;")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save calibration as"),
            "calibration.yml",
            self.tr("OpenCV YAML (*.yml *.yaml *.xml)"),
        )
        if not path:
            return
        self.saved_path = to_opencv_yaml(self._rig(), path, meta={"source": "al-dic-3d gui manual"})
        self.accept()


def _spin(value: float, decimals: int, rng: tuple[float, float]) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(*rng)
    s.setDecimals(decimals)
    s.setValue(value)
    s.setKeyboardTracking(False)
    return s
