"""``StrainParamPanel3D`` — parameters for surface-strain post-processing.

The 3D counterpart of the 2D ``StrainParamPanel``: exposes exactly the knobs of
:func:`al_dic_3d.strain3d.compute_surface_strain`:

* **Strain window** — the VSG (virtual strain gauge) side length in pixels, an
  odd spinbox. Maps to ``strain_size`` (window size in grid steps):
  ``strain_size = round((px - 1) / winstepsize) + 1`` — the inverse of
  ``strain_length = (strain_size - 1) * winstepsize + 1``. A 2D-style inline
  warning appears when the window radius is smaller than the node spacing
  (too few neighbours for the local plane fit).
* **Strain field smoothing** — Off / Light / Medium / Strong presets mapping to
  ``smooth_sigma`` = 0 / 0.5x / 1x / 2x of ``winstepsize`` (the 2D preset
  semantics: sigma scales with node spacing).
* **Coordinate system** — the key 3D control: per-node fitted tangent plane
  (default), the fixed left-camera frame, or a custom specimen frame built from
  3 picked points (``specimen_R``); the pick flow itself lives in the window.

Tracks a dirty flag so the window can show a stale hint until recompute.
"""

from __future__ import annotations

import numpy as np
from al_dic.gui.theme import COLORS
from al_dic.gui.widgets.double_spin import LocaleSafeDoubleSpinBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QWidget,
)

from al_dic_3d.gui.widgets.info_icon import InfoIcon

# Default from RunConfig: strain_size = 5 (docs/strain3d_math.md §1).
_DEFAULT_STRAIN_SIZE = 5

# Smoothing presets: label source key -> sigma as a multiple of winstepsize.
_SMOOTH_FACTORS = (0.0, 0.5, 1.0, 2.0)

# Coordinate-system codes in combo order (compute_surface_strain values).
_COORD_CODES = ("local", "camera0", "specific")

# Q3: strain-measure codes in combo order (strain3d.strain_tensor kinds).
_STRAIN_TYPE_CODES = ("green_lagrange", "infinitesimal", "almansi")

# Q4: 2D-calibrated default edge-trim coefficient (strain_edge_trim_alpha).
_DEFAULT_EDGE_TRIM_ALPHA = 0.7


class StrainParamPanel3D(QWidget):
    """Strain window / smoothing / coordinate-system editors with a dirty flag."""

    params_dirty = Signal()
    pick_requested = Signal()  # user clicked "Pick 3 points…"

    def __init__(self, winstepsize: int = 16, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._winstepsize = max(1, int(winstepsize))
        self._specimen_R: np.ndarray | None = None
        self._node_spacing_mm: float | None = None  # R1.4 physical readout
        self._dirty = False

        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # --- Strain window (VSG side length, px) ---
        self._win_spin = QSpinBox()
        self._win_spin.setRange(3, 2001)
        self._win_spin.setSingleStep(2)
        self._win_spin.setSuffix(" px")
        self._win_spin.setValue(self._default_window_px())
        self._win_spin.setToolTip(
            self.tr(
                "Side length, in pixels, of the square window around each node "
                "used to fit the local displacement gradient (the virtual "
                "strain gauge).\n\n"
                "• Larger window → smoother strain, lower spatial resolution.\n"
                "• Smaller window → sharper strain, more noise.\n"
                "• Must span at least 3×3 nodes: use ≥ 2 × node spacing + 1 px."
            )
        )
        layout.addRow(self.tr("Strain window"), self._win_spin)

        # R1.4 (2D 531fa3d idea): live read-only readout translating the pixel
        # VSG into the effective N×N NODE window the plane fit spans — plus
        # the physical gauge size once the window supplies the mean 3D node
        # spacing (set_node_spacing_mm). Informational only.
        self._win_readout = QLabel("")
        self._win_readout.setStyleSheet(
            f"color: {COLORS.TEXT_SECONDARY}; font-size: 10px; padding-left: 4px;"
        )
        self._win_readout.setToolTip(
            self.tr(
                "Number of mesh nodes per axis inside the square strain window "
                "— the local plane fit uses every valid node in it. The mm "
                "size maps the pixel window through the median 3D spacing of "
                "adjacent nodes on the reference surface."
            )
        )
        layout.addRow("", self._win_readout)

        # Inline warning when the gauge radius is below the node spacing
        # (fewer than 3x3 nodes fit -> the plane fit degenerates to NaN).
        self._win_warning = QLabel("")
        self._win_warning.setWordWrap(True)
        self._win_warning.setStyleSheet("color: #d97706; font-size: 10px; padding-left: 4px;")
        self._win_warning.setVisible(False)
        layout.addRow("", self._win_warning)

        # --- Strain type (Q3) ---
        self._type_combo = QComboBox()
        self._type_combo.addItem(self.tr("Green-Lagrange (default)"))
        self._type_combo.addItem(self.tr("Infinitesimal"))
        self._type_combo.addItem(self.tr("Eulerian-Almansi"))
        self._type_combo.setCurrentIndex(0)
        self._type_combo.setToolTip(
            self.tr(
                "Finite-strain measure derived from the SAME displacement-\n"
                "gradient fit, in the same tangent frame:\n"
                "Green-Lagrange E = ½(FᵀF − I) — finite strain, reference\n"
                "configuration (default).\n"
                "Infinitesimal e = ½(∇u + ∇uᵀ) — small-strain linearization.\n"
                "Eulerian-Almansi e = ½(I − F⁻ᵀF⁻¹) — finite strain, deformed\n"
                "configuration."
            )
        )
        layout.addRow(self.tr("Strain type"), self._type_combo)

        # --- Trim low-confidence edges (Q4) ---
        self._edge_trim_spin = LocaleSafeDoubleSpinBox()
        self._edge_trim_spin.setRange(0.0, 1.0)
        self._edge_trim_spin.setSingleStep(0.05)
        self._edge_trim_spin.setDecimals(2)
        self._edge_trim_spin.setValue(_DEFAULT_EDGE_TRIM_ALPHA)
        edge_tip = self.tr(
            "Hides low-confidence strain near invalid or missing nodes, where\n"
            "the strain window loses support on one side and the local plane\n"
            "fit becomes unreliable.\n"
            "Coefficient × window radius = width of the trimmed band (in px,\n"
            "on the reference grid).\n"
            "0.00 = keep every node (no trimming) · 0.70 = recommended ·\n"
            "1.00 = strictest. Displacement is never affected."
        )
        self._edge_trim_spin.setToolTip(edge_tip)
        edge_label = QWidget()
        edge_row = QHBoxLayout(edge_label)
        edge_row.setContentsMargins(0, 0, 0, 0)
        edge_row.setSpacing(2)
        edge_row.addWidget(QLabel(self.tr("Trim low-confidence edges")))
        edge_row.addWidget(InfoIcon(edge_tip))
        layout.addRow(edge_label, self._edge_trim_spin)

        # Live readout: how many nodes the current trim removed (per frame).
        self._edge_trim_readout = QLabel("")
        self._edge_trim_readout.setStyleSheet(
            f"color: {COLORS.TEXT_SECONDARY}; font-size: 10px; padding-left: 4px;"
        )
        self._edge_trim_readout.setVisible(False)
        layout.addRow("", self._edge_trim_readout)

        # --- Strain field smoothing ---
        self._smooth_combo = QComboBox()
        # Literal tr() calls per preset — pyside6-lupdate only extracts string
        # literals, so the four labels must appear verbatim (2D idiom).
        for lbl in (
            self.tr("Off"),
            self.tr("Light (σ = 0.5 × step)"),
            self.tr("Medium (σ = 1 × step)"),
            self.tr("Strong (σ = 2 × step) ⚠"),
        ):
            self._smooth_combo.addItem(lbl)
        self._smooth_combo.setCurrentIndex(0)
        self._smooth_combo.setToolTip(
            self.tr(
                "Gaussian smoothing of the displacement field before the "
                "gradient fit.\nσ is the kernel width; step = DIC node "
                "spacing.\n  Light  (0.5 × step): subtle, preserves fine "
                "features.\n  Medium (1 × step): balanced, for noisy data.\n"
                "  Strong (2 × step) ⚠: aggressive, may blur real gradients."
            )
        )
        layout.addRow(self.tr("Strain field smoothing"), self._smooth_combo)

        # --- Coordinate system (the key new 3D control) ---
        self._coord_combo = QComboBox()
        self._coord_combo.addItem(self.tr("Surface tangent plane"))
        self._coord_combo.addItem(self.tr("Left camera frame"))
        self._coord_combo.addItem(self.tr("Custom (3 points)"))
        tips = (
            self.tr(
                "Per-node tangent plane fitted to the reference surface: z is "
                "the surface normal pointing toward the camera, x is the "
                "left-camera +X projected onto the plane, y = z × x. The "
                "right default for curved specimens."
            ),
            self.tr(
                "Report strain in the fixed left-camera (world) axes. "
                "Meaningful for flat specimens aligned with the image plane."
            ),
            self.tr(
                "A fixed specimen frame built from 3 picked points on the "
                "reference image: Origin, a point along +X, and a point on "
                "the +Y side."
            ),
        )
        for i, tip in enumerate(tips):
            self._coord_combo.setItemData(i, tip, Qt.ItemDataRole.ToolTipRole)
        self._coord_combo.setCurrentIndex(0)  # DEFAULT: fitted tangent plane
        self._coord_combo.setToolTip(tips[0])
        # G2.1: ⓘ on the densest row — the icon's tip explains ALL THREE
        # options at once (the combo tooltip only describes the current one).
        combined_tip = "\n\n".join(
            f"{self._coord_combo.itemText(i)}: {tips[i]}" for i in range(len(tips))
        )
        coord_label = QWidget()
        coord_row = QHBoxLayout(coord_label)
        coord_row.setContentsMargins(0, 0, 0, 0)
        coord_row.setSpacing(2)
        coord_row.addWidget(QLabel(self.tr("Coordinate system")))
        coord_row.addWidget(InfoIcon(combined_tip))
        layout.addRow(coord_label, self._coord_combo)

        # --- 3-point specimen-frame picker (only for "specific") ---
        self._pick_btn = QPushButton(self.tr("Pick 3 points…"))
        self._pick_btn.setFixedHeight(26)
        self._pick_btn.setEnabled(False)
        self._pick_btn.setToolTip(
            self.tr(
                "Click three points on the reference image: the Origin, a point "
                "along +X, then a point on the +Y side. Each click snaps to the "
                "nearest valid mesh node. Enabled only for Custom (3 points)."
            )
        )
        self._pick_btn.clicked.connect(self.pick_requested.emit)
        layout.addRow("", self._pick_btn)

        self._pick_status = QLabel("")
        self._pick_status.setWordWrap(True)
        self._pick_status.setStyleSheet(
            f"color: {COLORS.TEXT_SECONDARY}; font-size: 10px; padding-left: 4px;"
        )
        self._pick_status.setVisible(False)
        layout.addRow("", self._pick_status)

        # --- wiring ---
        self._win_spin.valueChanged.connect(self._on_window_changed)
        self._type_combo.currentIndexChanged.connect(self._mark_dirty)  # Q3 stale hint
        self._edge_trim_spin.valueChanged.connect(self._mark_dirty)  # Q4 stale hint
        self._smooth_combo.currentIndexChanged.connect(self._mark_dirty)
        self._coord_combo.currentIndexChanged.connect(self._on_coord_changed)
        self._refresh_warning()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_override(self) -> dict[str, object]:
        """Current values as the strain-controller override dict."""
        px = int(self._win_spin.value())
        strain_size = max(3, int(round((px - 1) / self._winstepsize)) + 1)
        factor = _SMOOTH_FACTORS[self._smooth_combo.currentIndex()]
        coordinate = _COORD_CODES[self._coord_combo.currentIndex()]
        return {
            "strain_size": strain_size,
            "smooth_sigma": factor * self._winstepsize,
            "coordinate": coordinate,
            "specimen_R": self._specimen_R if coordinate == "specific" else None,
            "strain_type": _STRAIN_TYPE_CODES[self._type_combo.currentIndex()],  # Q3
            "edge_trim_alpha": float(self._edge_trim_spin.value()),  # Q4
        }

    def strain_type(self) -> str:
        return _STRAIN_TYPE_CODES[self._type_combo.currentIndex()]

    def set_strain_type(self, code: str) -> None:
        self._type_combo.setCurrentIndex(_STRAIN_TYPE_CODES.index(code))

    def set_trim_readout(self, n_trimmed: int | None, n_total: int) -> None:
        """Q4 live readout 'Trimmed: N nodes (X%)' — hidden when unavailable."""
        if n_trimmed is None or n_total <= 0:
            self._edge_trim_readout.setVisible(False)
            return
        pct = 100.0 * n_trimmed / n_total
        self._edge_trim_readout.setText(
            self.tr("Trimmed: {0} nodes ({1}%)").format(int(n_trimmed), f"{pct:.0f}")
        )
        self._edge_trim_readout.setVisible(True)

    def coordinate(self) -> str:
        return _COORD_CODES[self._coord_combo.currentIndex()]

    def set_coordinate(self, code: str) -> None:
        self._coord_combo.setCurrentIndex(_COORD_CODES.index(code))

    def compute_allowed(self) -> bool:
        """Compute requires a picked specimen frame in 'Custom (3 points)' mode."""
        return self.coordinate() != "specific" or self._specimen_R is not None

    def set_winstepsize(self, step: int) -> None:
        """Sync the node spacing used for px→steps mapping and the warning."""
        step = max(1, int(step))
        if step == self._winstepsize:
            return
        self._winstepsize = step
        self._refresh_warning()

    def set_node_spacing_mm(self, spacing: float | None) -> None:
        """Median 3D spacing of adjacent mesh nodes (mm) for the VSG readout.

        ``None`` (or a non-positive value) hides the physical part of the
        readout — the N×N node count is always shown.
        """
        valid = spacing is not None and float(spacing) > 0.0
        self._node_spacing_mm = float(spacing) if valid else None
        self._refresh_readout()

    def specimen_R(self) -> np.ndarray | None:
        return self._specimen_R

    def set_specimen_R(self, r: np.ndarray | None) -> None:
        """Store the picked specimen frame; None clears it (picks restarted)."""
        self._specimen_R = None if r is None else np.asarray(r, dtype=np.float64)
        self._mark_dirty()

    def set_pick_status(self, text: str) -> None:
        self._pick_status.setText(text)
        self._pick_status.setVisible(bool(text))

    def is_dirty(self) -> bool:
        return self._dirty

    def mark_clean(self) -> None:
        self._dirty = False

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _default_window_px(self) -> int:
        return (_DEFAULT_STRAIN_SIZE - 1) * self._winstepsize + 1

    def _on_window_changed(self, value: int) -> None:
        """Snap even inputs to the next odd integer, then mark dirty (2D idiom)."""
        if value % 2 == 0:
            self._win_spin.blockSignals(True)
            self._win_spin.setValue(value + 1)
            self._win_spin.blockSignals(False)
        self._refresh_warning()
        self._mark_dirty()

    def _on_coord_changed(self, index: int) -> None:
        specific = _COORD_CODES[index] == "specific"
        self._pick_btn.setEnabled(specific)
        if not specific:
            self.set_pick_status("")
        self._coord_combo.setToolTip(
            str(self._coord_combo.itemData(index, Qt.ItemDataRole.ToolTipRole))
        )
        self._mark_dirty()

    def _effective_nodes(self) -> int:
        """Nodes per axis the VSG spans — exactly ``strain_size``.

        The compute maps the pixel window to ``strain_size = round((px-1)/
        step)+1`` grid steps (see :meth:`get_override`), and the Chebyshev
        radius ``((N-1)*step+1)/2`` captures precisely N nodes per axis on a
        uniform grid, so the readout shows what the fit actually uses.
        """
        px = int(self._win_spin.value())
        return max(3, int(round((px - 1) / self._winstepsize)) + 1)

    def _refresh_readout(self) -> None:
        """R1.4: update the 'N×N nodes (≈ mm)' line under the VSG spinbox."""
        n = self._effective_nodes()
        text = self.tr("Strain window ≈ {0}×{1} nodes").format(n, n)
        if self._node_spacing_mm is not None:
            # Physical side of the pixel gauge: px × (mm per px on the mesh).
            side_mm = self._win_spin.value() * self._node_spacing_mm / self._winstepsize
            text += " " + self.tr("≈ {0} × {1} mm").format(f"{side_mm:.2f}", f"{side_mm:.2f}")
        self._win_readout.setText(text)

    def _refresh_warning(self) -> None:
        self._refresh_readout()  # R1.4: same triggers (init / VSG / step edits)
        rad = (self._win_spin.value() - 1) / 2.0
        step = self._winstepsize
        if rad < step:
            self._win_warning.setText(
                self.tr(
                    "⚠ Window radius ({0} px) < node spacing ({1} px); the "
                    "plane fit needs a 3×3 node gauge. Use ≥ {2} px."
                ).format(int(rad), step, 2 * step + 1)
            )
            self._win_warning.setVisible(True)
        else:
            self._win_warning.setVisible(False)

    def _mark_dirty(self, *_args: object) -> None:
        self._dirty = True
        self.params_dirty.emit()
