"""Help-menu dialogs (G3.9): About pyALDIC-3D + Keyboard shortcuts."""

from __future__ import annotations

from al_dic.gui.theme import COLORS
from al_dic.gui.window_chrome import enable_dark_title_bar
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_GITHUB_URL = "https://github.com/zachtong/pyALDIC-3D"


def _close_row(dialog: QDialog) -> QHBoxLayout:
    row = QHBoxLayout()
    row.addStretch()
    btn = QPushButton(dialog.tr("Close"))
    btn.setFixedHeight(30)
    btn.clicked.connect(dialog.close)
    row.addWidget(btn)
    return row


class AboutDialog(QDialog):
    """Version / description / project link / citation placeholder."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("About pyALDIC-3D"))
        enable_dark_title_bar(self)
        self.setMinimumWidth(420)

        import al_dic_3d

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        title = QLabel("pyALDIC-3D")
        title.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        version = QLabel(self.tr("Version {0}").format(al_dic_3d.__version__))
        version.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        layout.addWidget(version)
        desc = QLabel(
            self.tr(
                "Stereo (3D) digital image correlation — full-field displacement "
                "and surface strain from a calibrated camera pair."
            )
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        layout.addWidget(desc)
        link = QLabel(f'<a href="{_GITHUB_URL}" style="color:{COLORS.ACCENT};">{_GITHUB_URL}</a>')
        link.setOpenExternalLinks(True)
        link.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        layout.addWidget(link)
        citation = QLabel(self.tr("Citation: Zenodo DOI pending release."))
        citation.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(citation)
        layout.addLayout(_close_row(self))


class ShortcutsDialog(QDialog):
    """Plain list of the window-level keyboard shortcuts (G2.5 set)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Keyboard Shortcuts"))
        enable_dark_title_bar(self)
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(4)
        rows = (
            ("F5", self.tr("Run the 3D analysis")),
            ("Ctrl+0", self.tr("Fit the image to the viewport")),
            ("Ctrl+= / Ctrl+-", self.tr("Zoom in / out")),
            ("← / →", self.tr("Previous / next frame")),
            ("Space", self.tr("Play / pause (on the canvas: hold to pan)")),
            ("Ctrl+N", self.tr("New project")),
            ("Ctrl+O", self.tr("Open a project")),
            ("Ctrl+S", self.tr("Save the project")),
            ("Ctrl+Shift+S", self.tr("Save the project as…")),
            ("Esc", self.tr("Cancel the active drawing tool")),
        )
        for i, (key, desc) in enumerate(rows):
            key_lbl = QLabel(key)  # key chords are locale-invariant Qt notation
            key_lbl.setStyleSheet(
                f"color: {COLORS.TEXT_PRIMARY}; font-family: 'Consolas', monospace; "
                f"font-size: 12px;"
            )
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 12px;")
            grid.addWidget(key_lbl, i, 0)
            grid.addWidget(desc_lbl, i, 1)
        grid.setColumnStretch(1, 1)
        layout.addWidget(grid_host)
        layout.addLayout(_close_row(self))
