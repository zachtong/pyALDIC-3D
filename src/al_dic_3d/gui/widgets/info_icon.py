"""Shared ⓘ info icon widget (ported from the 2D app's ``info_icon.py``).

A small clickable ⓘ glyph that surfaces its tooltip on hover OR click.

Tooltip alone is fragile: touchscreens never trigger hover, and some users miss
that the icon is interactive. A click also shows the same tooltip, pinned at
the cursor, so discoverability doesn't depend on knowing the hover convention.
Used on the densest parameter rows (Solver, Temporal Search, the strain
window's Coordinate system) where the tooltip carries real decision guidance.
"""

from __future__ import annotations

from al_dic.gui.theme import COLORS
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QToolTip, QWidget


class InfoIcon(QLabel):
    """Clickable ⓘ glyph that shows its tooltip on both hover and click."""

    def __init__(self, tip: str, parent: QWidget | None = None) -> None:
        super().__init__("ⓘ", parent)  # U+24D8 CIRCLED LATIN SMALL LETTER I
        self.setToolTip(tip)
        self._tip_text = tip
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 13px; padding: 0 4px;")

    def set_tip(self, tip: str) -> None:
        """Update the tooltip text (dynamic tips, e.g. the search-cap rows)."""
        self._tip_text = tip
        self.setToolTip(tip)

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        QToolTip.showText(event.globalPosition().toPoint(), self._tip_text, self)
        super().mousePressEvent(event)


def make_info_icon(tip: str) -> InfoIcon:
    """Factory that returns a ready-to-add InfoIcon."""
    return InfoIcon(tip)


__all__ = ["InfoIcon", "make_info_icon"]
