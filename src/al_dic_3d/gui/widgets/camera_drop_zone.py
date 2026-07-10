"""Compact per-camera folder drop zone (extracted from the left sidebar).

One dashed-border zone per camera stream (LEFT / RIGHT); clicking opens a
folder picker, dropping a folder (or any file inside it) selects that folder.
After a load the zone shows the folder name + frame count with an accent
border (G2.9) — the caller syncs this from the draft via :meth:`set_loaded`
/ :meth:`reset`, so a new/opened project always reflects the truth.
"""

from __future__ import annotations

from pathlib import Path

from al_dic.gui.theme import COLORS
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileDialog, QLabel, QVBoxLayout, QWidget

_STYLE_EMPTY = """
    CameraDropZone {{
        background: {bg_panel};
        border: 1px dashed {border};
        border-radius: 6px;
    }}
    CameraDropZone:hover {{
        border-color: {accent};
        background: {bg_input};
    }}
"""

_STYLE_LOADED = """
    CameraDropZone {{
        background: {bg_panel};
        border: 1px solid {accent};
        border-radius: 6px;
    }}
    CameraDropZone:hover {{
        border-color: {accent};
        background: {bg_input};
    }}
"""


class CameraDropZone(QWidget):
    """Compact drop zone for ONE camera folder (dashed border, hover accent)."""

    folder_selected = Signal(str)

    def __init__(self, caption: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._caption = caption
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(64)
        # Custom QWidget subclasses do not paint QSS background/border without this.
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(2)
        icon = QLabel("\U0001f4c2")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 16px; background: transparent;")
        layout.addWidget(icon)
        self._text = QLabel(caption)
        self._text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._text.setStyleSheet(
            f"color: {COLORS.TEXT_MUTED}; font-size: 10px; background: transparent;"
        )
        layout.addWidget(self._text)
        self.reset()

    # ---- loaded-state feedback (G2.9) -----------------------------------------

    def set_loaded(self, folder: str, n_frames: int) -> None:
        """Show '<folder name> · N frames' with an accent border; tooltip = full path."""
        self._text.setText(Path(folder).name + "\n" + self.tr("{0} frames").format(int(n_frames)))
        self._text.setStyleSheet(
            f"color: {COLORS.TEXT_SECONDARY}; font-size: 10px; background: transparent;"
        )
        self.setStyleSheet(
            _STYLE_LOADED.format(
                bg_panel=COLORS.BG_PANEL, accent=COLORS.ACCENT, bg_input=COLORS.BG_INPUT
            )
        )
        self.setToolTip(str(folder))

    def reset(self) -> None:
        """Back to the empty-state caption, dashed border and help tooltip."""
        self._text.setText(self._caption)
        self._text.setStyleSheet(
            f"color: {COLORS.TEXT_MUTED}; font-size: 10px; background: transparent;"
        )
        self.setStyleSheet(
            _STYLE_EMPTY.format(
                bg_panel=COLORS.BG_PANEL,
                border=COLORS.BORDER,
                accent=COLORS.ACCENT,
                bg_input=COLORS.BG_INPUT,
            )
        )
        self.setToolTip(
            self.tr(
                "Click to pick this camera's image folder, or drag the folder "
                "here. Both cameras need the same number of frames."
            )
        )

    # ---- input events -----------------------------------------------------------

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
