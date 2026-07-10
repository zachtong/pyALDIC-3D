"""Pair-list tree for the left sidebar — L/R filenames + context menu (G3.1a).

The QTreeWidget that shows the paired image sequences, extracted from
``LeftSidebar3D`` so the widget owns its styling, multi-selection and
right-click menu ('Remove N selected pair(s)' / 'Reveal in Explorer' — the 2D
image-list idiom). The menu only EMITS intents; the sidebar owns the draft
mutation, the results-invalidation confirm and the actual reveal.
"""

from __future__ import annotations

from al_dic.gui.theme import COLORS
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QMenu, QTreeWidget, QWidget


class PairListWidget(QTreeWidget):
    """Numbered L/R pair rows with a right-click remove/reveal menu."""

    remove_rows_requested = Signal(list)  # sorted selected row indices
    reveal_row_requested = Signal(int)  # row index to reveal in the file explorer

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setHeaderLabels(["#", self.tr("Left"), self.tr("Right")])
        self.setRootIsDecorated(False)
        self.setColumnWidth(0, 30)
        self.setColumnWidth(1, 128)
        self.setMinimumHeight(80)
        self.setMaximumHeight(200)
        # Multi-selection enables plural removal (G3.1a).
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.setStyleSheet(
            f"""
            QTreeWidget {{
                background: {COLORS.BG_SIDEBAR};
                border: none;
                font-size: 11px;
            }}
            QTreeWidget::item {{ height: 22px; }}
            QTreeWidget::item:selected {{ background: {COLORS.BG_HOVER}; }}
            QHeaderView::section {{
                background: {COLORS.BG_PANEL};
                color: {COLORS.TEXT_MUTED};
                border: none;
                border-bottom: 1px solid {COLORS.BORDER};
                padding: 3px 6px;
                font-size: 10px;
                font-weight: bold;
            }}
            """
        )

    def selected_rows(self) -> list[int]:
        """Sorted top-level row indices of the current selection."""
        return sorted(self.indexOfTopLevelItem(item) for item in self.selectedItems())

    def _show_context_menu(self, pos) -> None:
        if self.topLevelItemCount() == 0:
            return  # menu suppressed when the list is empty
        # The signal position is widget-relative; itemAt wants viewport coords.
        item = self.itemAt(self.viewport().mapFrom(self, pos))
        if item is not None and not item.isSelected():
            self.setCurrentItem(item)  # right-click selects like the 2D list
        rows = self.selected_rows()

        menu = QMenu(self)
        remove = menu.addAction(self.tr("Remove {0} selected pair(s)").format(len(rows)))
        remove.setEnabled(bool(rows))
        remove.triggered.connect(lambda: self.remove_rows_requested.emit(self.selected_rows()))
        reveal = menu.addAction(self.tr("Reveal in Explorer"))
        reveal_row = self.indexOfTopLevelItem(item) if item is not None else -1
        if reveal_row < 0 and rows:
            reveal_row = rows[0]
        reveal.setEnabled(reveal_row >= 0)
        reveal.triggered.connect(lambda _c=False, r=reveal_row: self.reveal_row_requested.emit(r))
        menu.exec(self.viewport().mapToGlobal(self.viewport().mapFrom(self, pos)))
