"""``ConfigOverlay3D`` — top-left canvas card summarising the run configuration.

The 3D analogue of the 2D ``CanvasConfigOverlay``: a small semi-transparent panel
pinned to the canvas corner showing the decisions that shape a run — MODE,
SOLVER, SUBSET — updating live as the sidebar changes. Visible once both
sequences are loaded.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from al_dic.gui.theme import COLORS
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from al_dic_3d.gui.controller import WorkflowController


class ConfigOverlay3D(QFrame):
    """Labelled MODE / SOLVER / SUBSET rows pinned to the canvas top-left."""

    MARGIN = 12

    def __init__(self, controller: WorkflowController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setStyleSheet(
            f"background-color: rgba(16, 20, 24, 215); "
            f"border: 1px solid {COLORS.BORDER}; "
            f"border-radius: 6px;"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(3)

        self._mode_lbl = self._make_row(layout, self.tr("Mode"))
        self._solver_lbl = self._make_row(layout, self.tr("Solver"))
        self._subset_lbl = self._make_row(layout, self.tr("Subset"))
        self.adjustSize()
        self.refresh()

    def _make_row(self, layout: QVBoxLayout, key: str) -> QLabel:
        row = QWidget()
        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)

        key_lbl = QLabel(key.upper())
        key_lbl.setStyleSheet(
            f"color: {COLORS.TEXT_SECONDARY}; font-size: 9px; "
            f"font-weight: bold; letter-spacing: 1px; background: transparent;"
        )
        row_layout.addWidget(key_lbl)

        val_lbl = QLabel("—")
        val_lbl.setStyleSheet(
            f"color: {COLORS.TEXT_PRIMARY}; font-size: 12px; "
            f"font-weight: bold; background: transparent;"
        )
        row_layout.addWidget(val_lbl)
        layout.addWidget(row)
        return val_lbl

    def refresh(self) -> None:
        draft = self._controller.state.draft
        if len(draft.left) < 2:
            self.setVisible(False)
            return
        mode = draft.reference_mode
        self._mode_lbl.setText(
            self.tr("Accumulative") if mode == "accumulative" else self.tr("Incremental")
        )
        self._solver_lbl.setText(
            self.tr("ADMM ({0} iter)").format(draft.admm_max_iter)
            if draft.use_global_step
            else self.tr("Local DIC")
        )
        self._subset_lbl.setText(f"{draft.winsize} / {draft.winstepsize} px")
        self.adjustSize()
        self.setVisible(True)
        self.reposition()

    def reposition(self) -> None:
        if self.parentWidget() is not None:
            self.move(self.MARGIN, self.MARGIN)
