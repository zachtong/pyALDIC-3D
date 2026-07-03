"""Base workflow page (Qt view layer).

A titled panel wired to the :class:`WorkflowController`. Subclasses add their
affordances in :meth:`build` and sync from the state in :meth:`refresh`. They emit
:attr:`changed` after mutating the ``AppState3D`` (draft / project / result) so the
main window can refresh navigation and the run-availability state.

Every user-facing string is a literal ``self.tr(...)`` (i18n contract).
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from al_dic_3d.gui.controller import WorkflowController


class WorkflowPage(QWidget):
    """Base page: a bold title + a wrapped description + subclass affordances."""

    changed = Signal()

    def __init__(self, controller: WorkflowController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self._root = QVBoxLayout(self)
        self._title = QLabel(self)
        self._title.setStyleSheet("font-size: 16px; font-weight: 600;")
        self._body = QLabel(self)
        self._body.setWordWrap(True)
        self._root.addWidget(self._title)
        self._root.addWidget(self._body)
        self.build()
        self._root.addStretch(1)

    def _set(self, title: str, body: str) -> None:
        self._title.setText(title)
        self._body.setText(body)

    def _add(self, widget: QWidget) -> None:
        """Add an affordance widget below the description (call during build)."""
        self._root.addWidget(widget)

    @property
    def draft(self):
        return self.controller.state.draft

    def build(self) -> None:  # pragma: no cover - overridden
        """Subclasses set the title/body and add widgets."""

    def refresh(self) -> None:
        """Sync widgets from the current state (called when the page is shown)."""
