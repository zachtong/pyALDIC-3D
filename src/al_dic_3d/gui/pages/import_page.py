"""Import page — load the left / right image sequences and validate pairing."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.gui.pages.base import WorkflowPage
from al_dic_3d.gui.widgets import ImageView


class ImportPage(WorkflowPage):
    def build(self) -> None:
        self._set(
            self.tr("Import left / right sequences"),
            self.tr("Load the two camera image streams; frame-count pairing is validated."),
        )
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)

        self._left_list = QListWidget()
        self._right_list = QListWidget()
        self._left_view = ImageView()
        self._right_view = ImageView()
        left_col = self._camera_column(
            self.tr("Left camera"), self._left_list, self._left_view, self._add_left
        )
        right_col = self._camera_column(
            self.tr("Right camera"), self._right_list, self._right_view, self._add_right
        )
        layout.addWidget(left_col)
        layout.addWidget(right_col)
        self._add(row)

        self._pairing = QLabel(self)
        self._add(self._pairing)
        clear = QPushButton(self.tr("Clear sequences"))
        clear.clicked.connect(self._clear)
        self._add(clear)
        self.refresh()

    def _camera_column(self, title: str, lst: QListWidget, view: ImageView, adder) -> QWidget:
        col = QWidget()
        layout = QVBoxLayout(col)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(title))
        lst.setMaximumHeight(120)
        layout.addWidget(lst)
        button = QPushButton(self.tr("Add images…"))
        button.clicked.connect(adder)
        layout.addWidget(button)
        layout.addWidget(view, stretch=1)
        return col

    def _pick(self) -> list[str]:
        files, _ = QFileDialog.getOpenFileNames(
            self, self.tr("Select images"), "", self.tr("Images (*.png *.tif *.tiff *.jpg *.bmp)")
        )
        return sorted(files)

    def _add_left(self) -> None:
        files = self._pick()
        if files:
            self.draft.left = files
            self._touch()

    def _add_right(self) -> None:
        files = self._pick()
        if files:
            self.draft.right = files
            self._touch()

    def _clear(self) -> None:
        self.draft.left = []
        self.draft.right = []
        self._touch()

    def _touch(self) -> None:
        self.controller.state.mark_dirty()
        self.changed.emit()
        self.refresh()

    def refresh(self) -> None:
        self._left_list.clear()
        self._left_list.addItems([Path(p).name for p in self.draft.left])
        self._right_list.clear()
        self._right_list.addItems([Path(p).name for p in self.draft.right])
        self._preview(self._left_view, self.draft.left)
        self._preview(self._right_view, self.draft.right)
        n_left, n_right = len(self.draft.left), len(self.draft.right)
        if n_left == 0 and n_right == 0:
            self._pairing.setText(self.tr("No images loaded"))
        elif n_left == n_right and n_left >= 2:
            self._pairing.setText(self.tr("Paired: {0} frames per camera").format(n_left))
        else:
            self._pairing.setText(
                self.tr("Mismatch: {0} left vs {1} right").format(n_left, n_right)
            )

    def _preview(self, view: ImageView, files: list[str]) -> None:
        if files:
            try:
                view.set_image_file(files[0])
            except Exception:  # noqa: BLE001 - a bad image should not crash the page
                view.clear_image()
        else:
            view.clear_image()
