"""``AdvancedSection3D`` — content of the ADVANCED sidebar section.

Extracted from ``LeftSidebar3D`` (file-size discipline) when batch Q added the
FFT auto-expand knob (Q8): correspondence strategy, AL-DIC iteration budget,
parallel camera tracking, and the engine's clipped-peak FFT search expansion.
Fix batch V added the three result-quality thresholds that used to be
TOML-only: the tracking check (honesty gate), the stereo check and the
epipolar limit. Pure widget container — ALL wiring/apply logic stays in the
sidebar, which aliases these widgets under their historical attribute names.
"""

from __future__ import annotations

from al_dic.gui.theme import COLORS
from al_dic.gui.widgets.double_spin import LocaleSafeDoubleSpinBox
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class AdvancedSection3D(QWidget):
    """Strategy / AL-DIC iterations / parallel tracking / FFT auto-expand."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.row_labels: list[QLabel] = []  # sized together by the sidebar
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 8)
        layout.setSpacing(6)

        self.strategy_combo = QComboBox()
        self.strategy_combo.addItem(self.tr("Track Both"), "track_both")
        self.strategy_combo.addItem(self.tr("Stereo Each Frame"), "stereo_each_frame")
        self.strategy_combo.addItem(self.tr("Reference Direct"), "ref_direct")
        self.strategy_combo.setToolTip(
            self.tr(
                "How stereo correspondences are propagated through time.\n"
                "Track Both (default): match stereo once at frame 1, then\n"
                "track each camera temporally — fastest, one stereo solve.\n"
                "Stereo Each Frame: re-match stereo at every frame — robust\n"
                "when temporal tracking drifts, slower.\n"
                "Reference Direct: match every frame directly to frame 1 in\n"
                "both cameras — no drift accumulation, small motions only."
            )
        )
        layout.addLayout(self._row(self.tr("Strategy"), self.strategy_combo))

        # AL-DIC global refinement cycles (ADMM under the hood; acronym hidden).
        self.admm_spin = QSpinBox()
        self.admm_spin.setRange(1, 10)
        self.admm_spin.setValue(3)
        self.admm_spin.setToolTip(
            self.tr("1 = single global pass (fastest), 3 = default, 5+ = diminishing returns")
        )
        layout.addLayout(self._row(self.tr("AL-DIC Iterations"), self.admm_spin))

        admm_hint = QLabel(self.tr("Only affects AL-DIC solver. Ignored by Local DIC."))
        admm_hint.setWordWrap(True)
        admm_hint.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 10px;")
        layout.addWidget(admm_hint)

        # P3.6: opt-in concurrent L/R temporal tracking (track_both strategy).
        self.parallel_cb = QCheckBox(self.tr("Parallel camera tracking"))
        self.parallel_cb.setToolTip(
            self.tr(
                "Track both cameras concurrently — modest speedup (the solver "
                "already uses all cores), doubles peak memory"
            )
        )
        layout.addWidget(self.parallel_cb)

        # Q8: engine fft_auto_expand_search (default on).
        self.fft_expand_cb = QCheckBox(self.tr("Auto-expand FFT search on clipped peaks"))
        self.fft_expand_cb.setChecked(True)
        self.fft_expand_cb.setToolTip(
            self.tr(
                "When the temporal FFT integer peak lands on the search-region\n"
                "boundary, retry with a larger region (engine default on).\n"
                "Disable for strictly bounded runtimes; then Temporal Search\n"
                "must cover the largest per-frame motion by itself."
            )
        )
        layout.addWidget(self.fft_expand_cb)

        # ---- result-quality thresholds (fix batch V; were TOML-only) ----------
        checks = QLabel(self.tr("Result checks"))
        checks.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 11px; font-weight: bold;")
        layout.addSpacing(4)
        layout.addWidget(checks)
        self.gate_spin = self._threshold(
            1.0,
            4.0,
            self.tr(
                "Tracking check: every tracked point must still look like its\n"
                "frame-1 subset (correlation mismatch, 0 = perfect, 4 = worst).\n"
                "Points below 60 % of this value always pass; points up to it\n"
                "pass when their neighbours agree; the rest are dropped as\n"
                "failed tracks. Default 1.0 (correlation 0.5). Raise it (e.g.\n"
                "1.5) for very large strains, lower it for stricter results;\n"
                "0 turns the check off."
            ),
        )
        layout.addLayout(self._row(self.tr("Tracking check"), self.gate_spin))
        self.stereo_znssd_spin = self._threshold(
            0.6,
            4.0,
            self.tr(
                "Stereo check: a left/right match is kept only if its\n"
                "correlation mismatch is at most this value. Default 0.6\n"
                "(correlation 0.7); 0 turns the check off."
            ),
        )
        layout.addLayout(self._row(self.tr("Stereo check"), self.stereo_znssd_spin))
        self.epipolar_spin = self._threshold(
            2.0,
            50.0,
            self.tr(
                "Epipolar limit: a left/right match must lie within this many\n"
                "pixels of the line the calibration predicts. Default 2 px;\n"
                "raise it only for a poor calibration; 0 turns the check off."
            ),
            suffix=" px",
        )
        layout.addLayout(self._row(self.tr("Epipolar limit"), self.epipolar_spin))

    def _threshold(
        self, value: float, top: float, tip: str, suffix: str = ""
    ) -> LocaleSafeDoubleSpinBox:
        spin = LocaleSafeDoubleSpinBox()
        spin.setDecimals(2)
        spin.setRange(0.0, top)
        spin.setSingleStep(0.1)
        spin.setValue(value)
        spin.setSpecialValueText(self.tr("off"))  # shown at 0
        if suffix:
            spin.setSuffix(suffix)
        spin.setToolTip(tip)
        return spin

    def _row(self, text: str, widget: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(4)
        lbl = QLabel(text)
        self.row_labels.append(lbl)
        lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        row.addWidget(lbl)
        row.addWidget(widget, stretch=1)
        return row
