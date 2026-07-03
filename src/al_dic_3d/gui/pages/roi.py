"""ROI page — numeric region of interest on the left camera, frame 1.

Graphical drawing (reusing the 2D ROI toolbar/canvas) is added during visual
iteration; the numeric form is fully functional now.
"""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QSpinBox, QWidget

from al_dic_3d.gui.pages.base import WorkflowPage


class RoiPage(WorkflowPage):
    def build(self) -> None:
        self._set(
            self.tr("Region of interest"),
            self.tr("Set the ROI in pixels on the left camera, frame 1 (x=col, y=row)."),
        )
        form_widget = QWidget()
        form = QFormLayout(form_widget)
        self._xmin = self._spin()
        self._xmax = self._spin()
        self._ymin = self._spin()
        self._ymax = self._spin()
        form.addRow(self.tr("x min"), self._xmin)
        form.addRow(self.tr("x max"), self._xmax)
        form.addRow(self.tr("y min"), self._ymin)
        form.addRow(self.tr("y max"), self._ymax)
        self._add(form_widget)

        for spin in (self._xmin, self._xmax, self._ymin, self._ymax):
            spin.valueChanged.connect(self._on_change)
        self.refresh()

    def _spin(self) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(0, 100000)
        return spin

    def _on_change(self, _value: int) -> None:
        self.draft.roi = (
            self._xmin.value(),
            self._xmax.value(),
            self._ymin.value(),
            self._ymax.value(),
        )
        self.controller.state.mark_dirty()
        self.changed.emit()

    def refresh(self) -> None:
        roi = self.draft.roi
        if roi is None:
            return
        for spin, value in zip((self._xmin, self._xmax, self._ymin, self._ymax), roi, strict=True):
            spin.blockSignals(True)
            spin.setValue(int(value))
            spin.blockSignals(False)
