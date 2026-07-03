"""Results page — run summary.

The per-camera 2D field tabs, the pyvista 3D view, the strain tabs, and the QC
page are added during visual iteration (2D canvas + lazy [viz3d]); a textual
summary is functional now.
"""

from __future__ import annotations

from PySide6.QtWidgets import QLabel

from al_dic_3d.gui.pages.base import WorkflowPage
from al_dic_3d.matching.contracts import INVALID


class ResultsPage(WorkflowPage):
    def build(self) -> None:
        self._set(
            self.tr("Results"),
            self.tr("Summary of the completed run (2D / 3D / strain / QC tabs are added next)."),
        )
        self._summary = QLabel(self)
        self._summary.setWordWrap(True)
        self._add(self._summary)
        self.refresh()

    def refresh(self) -> None:
        result = self.controller.state.result
        if result is None:
            self._summary.setText(self.tr("No results yet — run the pipeline first."))
            return
        rec = result.reconstruction
        tracked = int((rec.source != INVALID).sum())
        total = rec.n_frames * rec.n_pts
        strain = self.tr("yes") if result.strain is not None else self.tr("no")
        self._summary.setText(
            self.tr(
                "Strategy: {0}\nFrames: {1}    Points: {2}\n"
                "Tracked positions: {3} / {4}\nStrain computed: {5}"
            ).format(result.strategy, rec.n_frames, rec.n_pts, tracked, total, strain)
        )
