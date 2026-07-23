"""``RefUpdateSection3D`` — incremental reference-update policy controls (Q5).

2D pattern (``pipeline_controller`` inc_ref_mode wiring): in Incremental mode
the reference frame normally advances every frame; updating it only every N
frames (or at hand-picked frames) trades drift accumulation against
decorrelation. Visible ONLY when Tracking Mode = Incremental; writes
``draft.ref_update_mode`` / ``ref_update_n`` / ``ref_update_frames``, which the
runner turns into an engine ``FrameSchedule``
(:func:`al_dic_3d.matching.temporal.build_frame_schedule`).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from al_dic.gui.theme import COLORS
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.gui.state import GuiSignals

if TYPE_CHECKING:
    from al_dic_3d.gui.controller import WorkflowController

_FRAME_LIST_RE = re.compile(r"^\s*\d+(\s*,\s*\d+)*\s*$")


class RefUpdateSection3D(QWidget):
    """Reference Update combo + per-mode editors, bound to the draft."""

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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        row = QHBoxLayout()
        row.setSpacing(4)
        lbl = QLabel(self.tr("Reference Update"))
        lbl.setFixedWidth(88)
        lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        row.addWidget(lbl)
        self._mode_combo = QComboBox()
        self._mode_combo.addItem(self.tr("Every Frame"), "every_frame")
        self._mode_combo.addItem(self.tr("Every N Frames"), "every_n")
        self._mode_combo.addItem(self.tr("Custom Frames"), "custom")
        self._mode_combo.setToolTip(
            self.tr(
                "How often the incremental reference frame advances.\n"
                "Every Frame (default): frame k matches against k−1 — tracks\n"
                "large accumulated deformation, but drift can accumulate.\n"
                "Every N Frames: the reference advances only every N frames —\n"
                "less drift, needs correlation to survive N frames of motion.\n"
                "Custom Frames: reference updates exactly at the listed frames."
            )
        )
        row.addWidget(self._mode_combo, stretch=1)
        layout.addLayout(row)

        n_row = QHBoxLayout()
        n_row.setSpacing(4)
        self._n_lbl = QLabel(self.tr("Update every"))
        self._n_lbl.setFixedWidth(88)
        self._n_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        n_row.addWidget(self._n_lbl)
        self._n_spin = QSpinBox()
        self._n_spin.setRange(2, 100)
        self._n_spin.setValue(2)
        self._n_spin.setSuffix(self.tr(" frames"))
        self._n_spin.setToolTip(
            self.tr("Reference-update interval N: frames k use the last reference at i·N < k")
        )
        n_row.addWidget(self._n_spin, stretch=1)
        layout.addLayout(n_row)

        self._frames_edit = QLineEdit()
        self._frames_edit.setPlaceholderText(self.tr("e.g. 5, 10, 20 (0-based frame indices)"))
        self._frames_edit.setToolTip(
            self.tr(
                "Comma-separated 0-based frame indices that become reference\n"
                "frames (frame 0 always is one). The last frame cannot be a\n"
                "reference."
            )
        )
        layout.addWidget(self._frames_edit)

        self._frames_hint = QLabel("")
        self._frames_hint.setWordWrap(True)
        self._frames_hint.setStyleSheet("color: #d97706; font-size: 10px;")
        self._frames_hint.setVisible(False)
        layout.addWidget(self._frames_hint)

        self._mode_combo.currentIndexChanged.connect(self._apply)
        self._n_spin.valueChanged.connect(self._apply)
        self._frames_edit.editingFinished.connect(self._apply)
        self._sync_editor_visibility()

    # ------------------------------------------------------------------

    def parse_frames(self) -> list[int] | None:
        """The validated custom frame list, or None when the text is invalid."""
        text = self._frames_edit.text().strip()
        if not text or not _FRAME_LIST_RE.match(text):
            return None
        return sorted({int(tok) for tok in text.split(",")})

    def _sync_editor_visibility(self) -> None:
        mode = self._mode_combo.currentData()
        for w in (self._n_lbl, self._n_spin):
            w.setVisible(mode == "every_n")
        self._frames_edit.setVisible(mode == "custom")
        self._frames_hint.setVisible(
            mode == "custom" and bool(self._frames_edit.text().strip()) and not self.parse_frames()
        )

    def _apply(self, *_args: object) -> None:
        draft = self.controller.state.draft
        mode = self._mode_combo.currentData()
        draft.ref_update_mode = mode
        draft.ref_update_n = int(self._n_spin.value())
        if mode == "custom":
            frames = self.parse_frames()
            draft.ref_update_frames = frames
            self._frames_hint.setText(
                self.tr("Enter comma-separated 0-based frame numbers, e.g. 5, 10, 20")
            )
        else:
            draft.ref_update_frames = None
        self._sync_editor_visibility()
        self.controller.state.mark_dirty()
        self.signals.params_changed.emit()

    def set_visible_for_mode(self, reference_mode: str) -> None:
        """Show the whole block only in Incremental tracking mode."""
        self.setVisible(reference_mode == "incremental")

    def refresh_from_draft(self) -> None:
        """Project open / new: mirror the draft without re-emitting signals."""
        draft = self.controller.state.draft
        for w in (self._mode_combo, self._n_spin, self._frames_edit):
            w.blockSignals(True)
        idx = self._mode_combo.findData(draft.ref_update_mode)
        self._mode_combo.setCurrentIndex(max(0, idx))
        self._n_spin.setValue(max(2, int(draft.ref_update_n)))
        frames = draft.ref_update_frames
        self._frames_edit.setText(", ".join(str(f) for f in frames) if frames else "")
        for w in (self._mode_combo, self._n_spin, self._frames_edit):
            w.blockSignals(False)
        self.set_visible_for_mode(draft.reference_mode)
        self._sync_editor_visibility()
