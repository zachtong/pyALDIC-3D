"""ROI page — draw the region of interest on the left camera, frame 1.

Drag on the image to draw the ROI, or type exact pixel bounds; the two stay in
sync and write the draft's ``roi``.
"""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QSpinBox, QWidget

from al_dic_3d.gui.pages.base import WorkflowPage
from al_dic_3d.gui.widgets import ImageView


class RoiPage(WorkflowPage):
    def build(self) -> None:
        self._set(
            self.tr("Region of interest"),
            self.tr("Drag on the left frame 1 to draw the ROI, or type exact bounds below."),
        )
        self._view = ImageView(editable_roi=True)
        self._add(self._view)

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

        self._view.roi_changed.connect(self._on_draw)
        for spin in self._spins():
            spin.valueChanged.connect(self._on_spin)
        self.refresh()

    def _spins(self):
        return (self._xmin, self._xmax, self._ymin, self._ymax)

    def _spin(self) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(0, 100000)
        return spin

    def _set_spins(self, roi: tuple[int, int, int, int]) -> None:
        for spin, value in zip(self._spins(), roi, strict=True):
            spin.blockSignals(True)
            spin.setValue(int(value))
            spin.blockSignals(False)

    def _commit(self, roi: tuple[int, int, int, int]) -> None:
        self.draft.roi = roi
        self.controller.state.mark_dirty()
        self.changed.emit()

    def _on_draw(self, roi: tuple[int, int, int, int]) -> None:
        self._set_spins(roi)
        self._commit(roi)

    def _on_spin(self, _value: int) -> None:
        roi = (self._xmin.value(), self._xmax.value(), self._ymin.value(), self._ymax.value())
        self._view.set_roi(roi)
        self._commit(roi)

    def refresh(self) -> None:
        if self.draft.left:
            try:
                self._view.set_image_file(self.draft.left[0])
            except Exception:  # noqa: BLE001 - a bad image should not crash the page
                self._view.clear_image()
        else:
            self._view.clear_image()
        if self.draft.roi is not None:
            self._set_spins(self.draft.roi)
            self._view.set_roi(self.draft.roi)
