"""Per-frame mask import for each camera (fix batch V, finding H10).

The draft and the pipeline have always accepted one mask image per frame per
camera (``left_masks`` / ``right_masks``), which is how tension-to-failure tests
such as the Stereo-DIC Challenge 1.0 Sample 3 are processed, but the GUI had no
way to set them. This widget imports a folder of mask images per camera,
checks the count and the image size against that camera's frames, and, when
no ROI has been drawn, adopts the first left mask as the ROI (its bounding box
becomes the mesh region). Any non-zero pixel is valid; masks are binarized
when they load.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from al_dic.gui.theme import COLORS
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from al_dic_3d.gui.controller import WorkflowController
    from al_dic_3d.gui.state import GuiSignals


def check_masks(masks: list[str], frames: list[str]) -> str | None:
    """Why ``masks`` cannot serve ``frames`` (English, for the log), or ``None``."""
    from al_dic_3d.project.image_info import image_size

    if not masks:
        return "the folder holds no images"
    if len(masks) != len(frames):
        return f"{len(masks)} masks for {len(frames)} frames"
    want = image_size(frames[0]) if frames else None
    for path in (masks[0], masks[-1]):
        got = image_size(path)
        if got is None:
            return f"cannot read {path}"
        if want is not None and got != want:
            return f"masks are {got[0]}x{got[1]} but the images are {want[0]}x{want[1]}"
    return None


class FrameMasksSection3D(QWidget):
    """One row per camera: status, Import…, Clear."""

    def __init__(
        self,
        controller: WorkflowController,
        signals: GuiSignals,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.controller = controller
        self.signals = signals
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(4)
        title = QLabel(self.tr("Per-frame masks"))
        title.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 11px; font-weight: bold;")
        title.setToolTip(
            self.tr(
                "Optional: one mask image per frame (non-zero = valid), for\n"
                "specimens whose valid region changes, e.g. a crack or a\n"
                "boundary that moves. Without them the ROI of frame 1 is used\n"
                "for every frame."
            )
        )
        layout.addWidget(title)
        self._status: dict[str, QLabel] = {}
        for cam in ("L", "R"):
            row = QHBoxLayout()
            row.setSpacing(4)
            status = QLabel()
            status.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 10px;")
            row.addWidget(status, stretch=1)
            imp = QPushButton(self.tr("Import…"))
            imp.setToolTip(self.tr("Choose the folder holding this camera's mask images"))
            imp.clicked.connect(lambda _c=False, c=cam: self._import(c))
            row.addWidget(imp)
            clr = QPushButton(self.tr("Clear"))
            clr.clicked.connect(lambda _c=False, c=cam: self._clear(c))
            row.addWidget(clr)
            layout.addLayout(row)
            self._status[cam] = status
        signals.images_changed.connect(self.refresh)
        signals.params_changed.connect(self.refresh)
        self.refresh()

    def _camera_name(self, cam: str) -> str:
        return self.tr("Left") if cam == "L" else self.tr("Right")

    def refresh(self) -> None:
        draft = self.controller.state.draft
        for cam, attr in (("L", "left_masks"), ("R", "right_masks")):
            masks = getattr(draft, attr) or []
            if masks:
                text = self.tr("{0}: {1} masks").format(self._camera_name(cam), len(masks))
            else:
                text = self.tr("{0}: none").format(self._camera_name(cam))
            self._status[cam].setText(text)

    def _import(self, cam: str) -> None:
        from al_dic_3d.gui import persistence
        from al_dic_3d.gui.panels.sidebar_images import list_images

        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose the mask folder"), persistence.last_dir("masks")
        )
        if not folder:
            return
        persistence.set_last_dir("masks", folder)
        self.load_folder(cam, folder, list_images(folder, natural=True))

    def load_folder(self, cam: str, folder: str, masks: list[str]) -> bool:
        """Adopt ``masks`` for ``cam`` after checking them; False (and a log) if refused."""
        draft = self.controller.state.draft
        frames = draft.left if cam == "L" else draft.right
        problem = check_masks(masks, list(frames))
        if problem is not None:
            self.signals.log.emit(
                self.tr("Masks not imported for the {0} camera: {1}").format(
                    self._camera_name(cam).lower(), problem
                ),
                "warning",
            )
            return False
        if cam == "L":
            draft.left_masks = list(masks)
            if draft.roi is None and getattr(draft, "roi_mask_array", None) is None:
                self._adopt_first_mask_as_roi(masks[0])
        else:
            draft.right_masks = list(masks)
        self.controller.state.mark_dirty()
        self.signals.log.emit(
            self.tr("{0} camera: {1} per-frame masks from {2}").format(
                self._camera_name(cam), len(masks), folder
            ),
            "info",
        )
        self.signals.params_changed.emit()
        return True

    def _adopt_first_mask_as_roi(self, path: str) -> None:
        import numpy as np

        from al_dic_3d.sequence.lazy import decode_gray

        mask = np.asarray(decode_gray(path)) > 0
        if not mask.any():
            return
        ys, xs = np.nonzero(mask)
        draft = self.controller.state.draft
        draft.roi_mask_array = mask
        draft.roi = (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()))
        self.signals.roi_changed.emit()

    def _clear(self, cam: str) -> None:
        draft = self.controller.state.draft
        if cam == "L":
            draft.left_masks = None
        else:
            draft.right_masks = None
        self.controller.state.mark_dirty()
        self.signals.params_changed.emit()
