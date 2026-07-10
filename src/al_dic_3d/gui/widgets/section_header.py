"""Uppercase sidebar section header with an optional count badge.

Extracted from ``panels/left_sidebar.py`` (file-size discipline).
"""

from __future__ import annotations

from al_dic.gui.theme import COLORS
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget


class SectionHeader(QWidget):
    """Uppercase 11px bold letter-spaced title + optional count badge."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 4)
        layout.setSpacing(6)
        label = QLabel(title)
        label.setStyleSheet(
            f"color: {COLORS.TEXT_SECONDARY}; font-size: 11px; "
            f"font-weight: bold; letter-spacing: 1px;"
        )
        layout.addWidget(label)
        self._badge = QLabel("")
        self._badge.setStyleSheet(
            f"color: {COLORS.TEXT_MUTED}; font-size: 10px; "
            f"background: {COLORS.BG_INPUT}; border-radius: 7px; padding: 1px 6px;"
        )
        self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._badge.hide()
        layout.addWidget(self._badge)
        layout.addStretch()

    def set_badge(self, text: str) -> None:
        if text:
            self._badge.setText(text)
            self._badge.show()
        else:
            self._badge.hide()
