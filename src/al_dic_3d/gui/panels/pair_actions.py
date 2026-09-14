"""Image-pair list context actions (mixin for LeftSidebar3D).

Split out of :mod:`al_dic_3d.gui.panels.left_sidebar` (fix batch V, file-size
rule). Fix batch V also made Reveal work on every platform: it used the
Windows-only ``os.startfile`` and opened the folder rather than showing the
file; it now selects the file in Explorer and Finder and opens the folder
elsewhere.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def reveal_in_file_manager(path: Path) -> None:
    """Show ``path`` in the system file manager; select it where supported."""
    if sys.platform == "win32":
        subprocess.Popen(["explorer", f"/select,{path}"])  # noqa: S603, S607
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-R", str(path)])  # noqa: S603, S607
    else:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))


class PairActionsMixin:
    """Remove / reveal actions of the image-pair list."""

    def _remove_pairs(self, rows: list[int]) -> None:
        """Remove the selected pairs from BOTH streams; invalidate results.

        Ported 2D idiom (image_list Q6): a frame-count/index mutation makes any
        computed result meaningless, so results are dropped — after an explicit
        confirm when they exist.
        """
        draft = self.controller.state.draft
        rows = sorted({r for r in rows if 0 <= r < max(len(draft.left), len(draft.right))})
        if not rows:
            return
        had_results = self.controller.state.has_results
        if had_results and not self._confirm_invalidate_results(len(rows)):
            return
        for r in reversed(rows):  # high indices first to preserve ordering
            if r < len(draft.left):
                del draft.left[r]
            if r < len(draft.right):
                del draft.right[r]
        if had_results:
            self.controller.state.result = None
            self.signals.set_run_state("idle")
        self.controller.state.mark_dirty()
        n = max(len(draft.left), len(draft.right))
        self.signals.set_current_frame(min(self.signals.current_frame, n - 1), max(1, n))
        self.signals.log.emit(self.tr("Removed {0} image pair(s)").format(len(rows)), "info")
        self.signals.images_changed.emit()
        if had_results:
            self.signals.results_changed.emit()

    def _confirm_invalidate_results(self, n_pairs: int) -> bool:
        """Yes/No prompt: removing pairs drops the computed results (2D idiom)."""
        from PySide6.QtWidgets import QMessageBox

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(self.tr("Remove Image Pairs"))
        box.setText(
            self.tr(
                "Removing {0} pair(s) changes the sequence — the current "
                "results will be discarded. Continue?"
            ).format(n_pairs)
        )
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)
        box.button(QMessageBox.StandardButton.Yes).setText(self.tr("Yes"))
        box.button(QMessageBox.StandardButton.No).setText(self.tr("No"))
        return box.exec() == QMessageBox.StandardButton.Yes

    def _reveal_pair(self, row: int) -> None:
        """Show the row's image in the system file manager (selected where possible)."""
        draft = self.controller.state.draft
        path = None
        if 0 <= row < len(draft.left):
            path = draft.left[row]
        elif 0 <= row < len(draft.right):
            path = draft.right[row]
        if path is None:
            return
        if not Path(path).parent.is_dir():
            self.signals.log.emit(
                self.tr("Folder does not exist: {0}").format(Path(path).parent), "warning"
            )
            return
        reveal_in_file_manager(Path(path))
