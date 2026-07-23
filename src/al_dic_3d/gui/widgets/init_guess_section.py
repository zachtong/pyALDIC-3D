"""INITIAL GUESS sidebar section — the 2D tri-mode idiom, 3D single-seed twist.

Three radios (2D ``InitGuessWidget`` layout, adapted): **Starting Point**
(DEFAULT — the user clicks ONE point on the LEFT camera, frame 1; the software
template-matches its neighborhood into the right frame 1 for the stereo offset
and into frame 2 for the motion seed), **FFT (cross-correlation)** (the engine's
frame-1 FFT seeding — pre-F2 behavior), and **Previous frame** (pure warm-start
chain; tooltip warns about the silent-freeze risk). Maps to
``draft.init_guess`` / ``draft.seed_point``; the exact engine semantics live in
:mod:`al_dic_3d.matching.seed`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from al_dic.gui.theme import COLORS
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.gui.state import GuiSignals

if TYPE_CHECKING:
    from al_dic_3d.gui.controller import WorkflowController


class InitGuessSection3D(QWidget):
    """Starting Point / FFT / Previous frame radios + the seed placement tools."""

    # Emitted when the "Place point…" toggle changes; the main window arms /
    # disarms the canvas seed click tool (and jumps to LEFT frame 1).
    place_seed_toggled = Signal(bool)
    # Emitted when the user clicks "Clear" to drop the seed point.
    clear_seed_requested = Signal()

    def __init__(
        self,
        controller: WorkflowController,
        signals: GuiSignals,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.controller = controller
        self.signals = signals
        self._building = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 8)
        layout.setSpacing(6)

        # ---- Starting Points (DEFAULT) ---------------------------------------
        self._rb_seed = QRadioButton(self.tr("Starting Points"))
        self._rb_seed.setToolTip(
            self.tr(
                "Click one or more points on the LEFT camera, frame 1 — at least\n"
                "one per connected ROI region. Each point's neighborhood is matched\n"
                "automatically into the right camera (stereo offset) and into\n"
                "frame 2 (motion seed), then a first-order deformation field is\n"
                "propagated to every mesh node — no search tuning needed. Best for\n"
                "wide stereo baselines, large first-frame motion, or discontinuous\n"
                "fields. If no point is placed, the run falls back to FFT."
            )
        )
        layout.addWidget(self._rb_seed)

        self._seed_panel = QWidget()
        seed_layout = QVBoxLayout(self._seed_panel)
        seed_layout.setContentsMargins(18, 0, 0, 2)
        seed_layout.setSpacing(4)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        self._btn_place = QPushButton(self.tr("Place points…"))
        self._btn_place.setCheckable(True)
        self._btn_place.setToolTip(
            self.tr(
                "Enter placement mode on the canvas. Left-click the LEFT camera,\n"
                "frame 1 to ADD a point; right-click removes the nearest; Esc exits."
            )
        )
        btn_row.addWidget(self._btn_place, stretch=2)
        self._btn_clear = QPushButton(self.tr("Clear"))
        self._btn_clear.setToolTip(self.tr("Remove all Starting Points"))
        btn_row.addWidget(self._btn_clear, stretch=1)
        seed_layout.addLayout(btn_row)
        self._seed_status = QLabel("")
        self._seed_status.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 10px;")
        seed_layout.addWidget(self._seed_status)
        layout.addWidget(self._seed_panel)

        # ---- FFT (cross-correlation) ------------------------------------------
        self._rb_fft = QRadioButton(self.tr("FFT (cross-correlation)"))
        self._rb_fft.setToolTip(
            self.tr(
                "Full-grid cross-correlation seeds frame 1 (and every reference\n"
                "switch in incremental mode); later frames warm-start from the\n"
                "previous solution. Robust default — the search radius is the\n"
                "Temporal Search parameter."
            )
        )
        layout.addWidget(self._rb_fft)

        # ---- Previous frame ----------------------------------------------------
        self._rb_prev = QRadioButton(self.tr("Previous frame"))
        self._rb_prev.setToolTip(
            self.tr(
                "Start every frame from the previous frame's solution — no\n"
                "cross-correlation at all. Fastest; can silently freeze on large\n"
                "motion or decorrelation — the validity gate will flag affected\n"
                "frames."
            )
        )
        layout.addWidget(self._rb_prev)

        # ---- wiring -------------------------------------------------------------
        self._rb_seed.toggled.connect(self._apply_mode)
        self._rb_fft.toggled.connect(self._apply_mode)
        self._rb_prev.toggled.connect(self._apply_mode)
        self._btn_place.toggled.connect(self._on_place_toggled)
        self._btn_clear.clicked.connect(self.clear_seed_requested.emit)
        self.signals.params_changed.connect(self._refresh_seed_status)
        # Region readiness depends on the ROI mask too (drawing disconnected
        # blobs changes the region count), so refresh on ROI edits as well.
        self.signals.roi_changed.connect(self._refresh_seed_status)

        self.refresh_from_draft()

    # ---- UI -> draft ------------------------------------------------------------

    def _apply_mode(self) -> None:
        if self._building:
            return
        draft = self.controller.state.draft
        if self._rb_seed.isChecked():
            draft.init_guess = "seed"
        elif self._rb_prev.isChecked():
            draft.init_guess = "previous"
        else:
            draft.init_guess = "fft"
        self._seed_panel.setVisible(self._rb_seed.isChecked())
        self.controller.state.mark_dirty()
        self.signals.params_changed.emit()

    def _on_place_toggled(self, active: bool) -> None:
        if self._building:
            return
        self.set_seed_mode_active(active, emit=False)
        self.place_seed_toggled.emit(active)

    # ---- draft -> UI --------------------------------------------------------------

    def set_seed_mode_active(self, active: bool, emit: bool = True) -> None:
        """Sync the toggle button with the canvas tool state (2D idiom)."""
        if not emit:
            self._btn_place.blockSignals(True)
        self._btn_place.setChecked(active)
        if not emit:
            self._btn_place.blockSignals(False)
        self._btn_place.setText(
            self.tr("Placing… (click to exit)") if active else self.tr("Place points…")
        )

    def _region_readiness(self, draft) -> tuple[int, int]:
        """``(#regions seeded, #ROI regions)`` for the readiness readout (Batch S).

        Computed from the SAME node-region logic the runner enforces
        (:func:`al_dic_3d.matching.seed_propagation.seed_region_readiness_mesh`:
        build the reference grid, keep only components with area > 20 AND >= 2
        mesh nodes, attribute seeds by node-snapping), so the GUI count can never
        disagree with the actual propagation. A drawn ROI mask feeds the mesh
        build directly; a bbox-only ROI is a single region. ``(0, 0)`` when no
        ROI is set yet.
        """
        import numpy as np

        from al_dic_3d.matching.seed_propagation import seed_region_readiness_mesh

        mask = getattr(draft, "roi_mask_array", None)
        if mask is not None:
            return seed_region_readiness_mesh(
                np.asarray(mask, dtype=float),
                draft.seed_points,
                winsize=draft.winsize,
                winstepsize=draft.winstepsize,
                winsize_min=draft.winsize_min,
            )
        if draft.roi is not None:
            return (1 if draft.seed_points else 0, 1)
        return (0, 0)

    def _refresh_seed_status(self) -> None:
        draft = self.controller.state.draft
        n = len(draft.seed_points)
        if n == 0:
            self._seed_status.setText(self.tr("No points placed — FFT fallback at run"))
            return
        seeded, total = self._region_readiness(draft)
        if total <= 0:
            self._seed_status.setText(self.tr("{0} point(s) placed").format(n))
        elif seeded >= total:
            self._seed_status.setText(
                self.tr("{0} point(s) · {1}/{2} regions ready").format(n, seeded, total)
            )
        else:
            # Honest readout: the run does NOT require a seed per region — the
            # runner auto-seeds every region left empty (build_seed_u0
            # auto_fill=True). Advise, don't nag that the run is blocked.
            self._seed_status.setText(
                self.tr("{0} point(s) · {1}/{2} regions seeded — rest auto-seeded at run").format(
                    n, seeded, total
                )
            )

    def refresh_from_draft(self) -> None:
        """Full resync from the draft (project open / new)."""
        self._building = True
        draft = self.controller.state.draft
        mode = getattr(draft, "init_guess", "seed")
        self._rb_seed.setChecked(mode == "seed")
        self._rb_fft.setChecked(mode == "fft")
        self._rb_prev.setChecked(mode == "previous")
        self._seed_panel.setVisible(mode == "seed")
        self.set_seed_mode_active(False, emit=False)
        self._refresh_seed_status()
        self._building = False
