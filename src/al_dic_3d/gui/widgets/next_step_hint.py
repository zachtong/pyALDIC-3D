"""Next-step hint callout for the left sidebar (G3.4, the 2D ROIHint analog).

A small accent-bordered banner naming the next missing prerequisite, driven by
``draft.issues()`` (the compute layer's English-by-contract codes) so the hint
can never disagree with the Run button's readiness. Hidden once the draft is
ready to run.
"""

from __future__ import annotations

from al_dic.gui.theme import COLORS
from PySide6.QtWidgets import QLabel, QWidget

from al_dic_3d.gui.issue_text import issue_text

_IMAGE_STAGE = ("sequence length mismatch", "need at least 2 frames")


class NextStepHint(QLabel):
    """Accent-left-border callout: 'what to do next' from the draft's issues."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWordWrap(True)
        self.setStyleSheet(
            f"background: {COLORS.BG_PANEL}; color: {COLORS.TEXT_SECONDARY}; "
            f"border-left: 3px solid {COLORS.ACCENT}; border-radius: 4px; "
            f"font-size: 11px; padding: 6px 8px; margin: 6px 8px 2px 8px;"
        )
        self.hide()

    def refresh(self, draft) -> None:
        """Recompute the message from ``draft.issues()``; hide when ready."""
        message = self.message_for(draft.issues())
        if message is None:
            self.hide()
            return
        self.setText(message)
        self.show()

    def message_for(self, issues: list[str]) -> str | None:
        """The hint text for an issues list (None = ready, hide the hint)."""
        if not issues:
            return None
        # Workflow order: images -> calibration -> ROI (draft.issues() lists
        # calibration first, but images are the first thing a user loads).
        if "left/right sequences not set" in issues:
            return self.tr("Load the left and right camera folders")
        for issue in issues:
            if issue.startswith(_IMAGE_STAGE):
                return issue_text(issue)  # mismatch / too-few-frames details
        if "calibration file not set" in issues:
            return self.tr("Calibrate from images or import a calibration")
        return self.tr("Draw the ROI on the left camera, frame 1")
