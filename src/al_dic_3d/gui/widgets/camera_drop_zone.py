"""Compact per-camera folder drop zone (extracted from the left sidebar).

One dashed-border zone per camera stream (LEFT / RIGHT); clicking opens a
folder picker, dropping a folder (or any file inside it) selects that folder.
"""

from __future__ import annotations

from pathlib import Path

from al_dic.gui.theme import COLORS
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileDialog, QLabel, QVBoxLayout, QWidget


class CameraDropZone(QWidget):
    """Compact drop zone for ONE camera folder (dashed border, hover accent)."""

    folder_selected = Signal(str)

    def __init__(self, caption: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(64)
        # Custom QWidget subclasses do not paint QSS background/border without this.
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            f"""
            CameraDropZone {{
                background: {COLORS.BG_PANEL};
                border: 1px dashed {COLORS.BORDER};
                border-radius: 6px;
            }}
            CameraDropZone:hover {{
                border-color: {COLORS.ACCENT};
                background: {COLORS.BG_INPUT};
            }}
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(2)
        icon = QLabel("\U0001f4c2")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 16px; background: transparent;")
        layout.addWidget(icon)
        text = QLabel(caption)
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 10px; background: transparent;")
        layout.addWidget(text)

    def mousePressEvent(self, _event) -> None:  # noqa: N802 (Qt override)
        folder = QFileDialog.getExistingDirectory(self, self.tr("Select image folder"), "")
        if folder:
            self.folder_selected.emit(folder)

    def dragEnterEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802 (Qt override)
        urls = event.mimeData().urls()
        if not urls:
            return
        path = Path(urls[0].toLocalFile())
        self.folder_selected.emit(str(path if path.is_dir() else path.parent))
