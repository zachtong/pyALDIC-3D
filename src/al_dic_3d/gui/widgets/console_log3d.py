"""``ConsoleLog3D`` — the 2D ConsoleLog with a context menu + replayable entries.

Extends :class:`al_dic.gui.widgets.console_log.ConsoleLog` (G3.1c): the
standard read-only QTextEdit menu (Copy / Select All) is EXTENDED with
Copy all / Save log to file… / Clear, and :meth:`append_entry` renders a
retained ``(timestamp, message, level)`` entry so the severity filter (G3.5)
can re-render history with the ORIGINAL timestamps (``append_log`` stamps the
current time, which would lie on a replay).
"""

from __future__ import annotations

from al_dic.gui.theme import COLORS
from al_dic.gui.widgets.console_log import ConsoleLog
from PySide6.QtCore import Signal
from PySide6.QtGui import QGuiApplication

_LEVEL_COLORS = {
    "info": COLORS.TEXT_SECONDARY,
    "warn": COLORS.WARNING,
    "error": COLORS.DANGER,
    "success": COLORS.SUCCESS,
}


class ConsoleLog3D(ConsoleLog):
    """ConsoleLog + context menu; save/clear are delegated to the owner."""

    save_requested = Signal()
    clear_requested = Signal()

    def append_entry(self, timestamp: str, message: str, level: str = "info") -> None:
        """Render one retained log entry (same format as ``append_log``)."""
        color = _LEVEL_COLORS.get(level, COLORS.TEXT_SECONDARY)
        self.append(f'<span style="color:{color}">{timestamp} {message}</span>')
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def contextMenuEvent(self, event) -> None:  # noqa: N802 (Qt override)
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        copy_all = menu.addAction(self.tr("Copy all"))
        copy_all.setEnabled(bool(self.toPlainText()))
        copy_all.triggered.connect(self._copy_all)
        save = menu.addAction(self.tr("Save log to file…"))
        save.triggered.connect(self.save_requested)
        clear = menu.addAction(self.tr("Clear"))
        clear.setEnabled(bool(self.toPlainText()))
        clear.triggered.connect(self.clear_requested)
        menu.exec(event.globalPos())

    def _copy_all(self) -> None:
        QGuiApplication.clipboard().setText(self.toPlainText())
