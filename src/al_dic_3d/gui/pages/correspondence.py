"""Correspondence page — strategy + parameters.

The frame-1 stereo-match preview (disparity + ZNSSD) is added with the canvas
during visual iteration; the settings form is functional now.
"""

from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QSpinBox, QWidget

from al_dic_3d.gui.pages.base import WorkflowPage

_STRATEGIES = ("track_both", "stereo_each_frame", "ref_direct")
_MODES = ("accumulative", "incremental")


class CorrespondencePage(WorkflowPage):
    def build(self) -> None:
        self._set(
            self.tr("Correspondence settings"),
            self.tr("Choose the strategy (default track_both) and its parameters."),
        )
        form_widget = QWidget()
        form = QFormLayout(form_widget)
        self._strategy = QComboBox()
        self._strategy.addItems(_STRATEGIES)  # strategy identifiers, not user prose
        self._mode = QComboBox()
        self._mode.addItems(_MODES)
        self._winsize = self._spin(8, 200)
        self._winstep = self._spin(2, 128)
        self._search = self._spin(4, 400)
        self._strain_size = self._spin(3, 51)
        form.addRow(self.tr("Strategy"), self._strategy)
        form.addRow(self.tr("Reference mode"), self._mode)
        form.addRow(self.tr("Subset (winsize)"), self._winsize)
        form.addRow(self.tr("Node step (winstepsize)"), self._winstep)
        form.addRow(self.tr("Stereo search"), self._search)
        form.addRow(self.tr("Strain size"), self._strain_size)
        self._add(form_widget)

        self._quality = QCheckBox(
            self.tr("Enable quality gates (ZNSSD / reprojection / 3D outliers)")
        )
        self._strain = QCheckBox(self.tr("Compute surface strain"))
        self._add(self._quality)
        self._add(self._strain)

        self._strategy.currentTextChanged.connect(self._apply)
        self._mode.currentTextChanged.connect(self._apply)
        for spin in (self._winsize, self._winstep, self._search, self._strain_size):
            spin.valueChanged.connect(self._apply)
        self._quality.toggled.connect(self._apply)
        self._strain.toggled.connect(self._apply)
        self.refresh()

    def _spin(self, lo: int, hi: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(lo, hi)
        return spin

    def _widgets(self):
        return (
            self._strategy,
            self._mode,
            self._winsize,
            self._winstep,
            self._search,
            self._strain_size,
            self._quality,
            self._strain,
        )

    def _apply(self, *_args) -> None:
        draft = self.draft
        draft.strategy = self._strategy.currentText()
        draft.reference_mode = self._mode.currentText()
        draft.winsize = self._winsize.value()
        draft.winstepsize = self._winstep.value()
        draft.stereo_search = self._search.value()
        draft.strain_size = self._strain_size.value()
        draft.quality_gate = self._quality.isChecked()
        draft.compute_strain = self._strain.isChecked()
        self.controller.state.mark_dirty()
        self.changed.emit()

    def refresh(self) -> None:
        draft = self.draft
        for widget in self._widgets():
            widget.blockSignals(True)
        self._strategy.setCurrentText(draft.strategy)
        self._mode.setCurrentText(draft.reference_mode)
        self._winsize.setValue(draft.winsize)
        self._winstep.setValue(draft.winstepsize)
        self._search.setValue(draft.stereo_search)
        self._strain_size.setValue(draft.strain_size)
        self._quality.setChecked(draft.quality_gate)
        self._strain.setChecked(draft.compute_strain)
        for widget in self._widgets():
            widget.blockSignals(False)
