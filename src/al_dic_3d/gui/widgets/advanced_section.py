"""``AdvancedSection3D`` — content of the ADVANCED sidebar section.

Extracted from ``LeftSidebar3D`` (file-size discipline) when batch Q added the
FFT auto-expand knob (Q8): correspondence strategy, AL-DIC iteration budget,
parallel camera tracking, and the engine's clipped-peak FFT search expansion.
Pure widget container — ALL wiring/apply logic stays in the sidebar, which
aliases these widgets under their historical attribute names.
"""

from __future__ import annotations

from al_dic.gui.theme import COLORS
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

    def _row(self, text: str, widget: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(4)
        lbl = QLabel(text)
        lbl.setFixedWidth(96)
        lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        row.addWidget(lbl)
        row.addWidget(widget, stretch=1)
        return row
