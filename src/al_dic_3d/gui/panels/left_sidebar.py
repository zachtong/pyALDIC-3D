"""Left sidebar — dual-camera import, calibration, workflow type, ROI, parameters.

The 2D sidebar idiom (fixed 320 px, uppercase section headers with badges, a drop
zone, a file table, collapsible settings in a scroll area) applied to the 3D-DIC
workflow: TWO camera streams that must pair, a stereo calibration that must be
sane before anything else, the correspondence strategy, and the matching scale.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from al_dic.gui.theme import COLORS
from al_dic.gui.widgets.collapsible_section import CollapsibleSection
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.gui.fft_activity import fft_controls_active
from al_dic_3d.gui.panels.sidebar_images import list_images
from al_dic_3d.gui.state import GuiSignals
from al_dic_3d.gui.widgets.advanced_section import AdvancedSection3D
from al_dic_3d.gui.widgets.calibration_section import CalibrationSection3D
from al_dic_3d.gui.widgets.camera_drop_zone import CameraDropZone
from al_dic_3d.gui.widgets.info_icon import InfoIcon
from al_dic_3d.gui.widgets.init_guess_section import InitGuessSection3D
from al_dic_3d.gui.widgets.next_step_hint import NextStepHint
from al_dic_3d.gui.widgets.pair_list import PairListWidget
from al_dic_3d.gui.widgets.ref_update_section import RefUpdateSection3D
from al_dic_3d.gui.widgets.roi_toolbar import ROIToolbar
from al_dic_3d.gui.widgets.section_header import SectionHeader

if TYPE_CHECKING:
    from al_dic_3d.gui.controller import WorkflowController

# Subset Step options: powers of two only (the 2D app uses a power-of-2 combo;
# the refinement formula min_size = max(2, step // 2**level) stays integral).
_STEP_OPTIONS = (2, 4, 8, 16, 32, 64, 128)


class LeftSidebar3D(QWidget):
    """Fixed-width sidebar: IMAGES (L/R) + CALIBRATION + WORKFLOW + ROI + PARAMETERS + ADVANCED."""

    def __init__(
        self,
        controller: WorkflowController,
        signals: GuiSignals,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.controller = controller
        self.signals = signals
        self._shape_cache: tuple[str, int | None] | None = None  # (path, min(H, W))
        self.setObjectName("leftSidebar")
        self.setFixedWidth(320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ---- NEXT STEP (G3.4) -------------------------------------------------
        # Accent callout naming the next missing prerequisite; recomputed on
        # every draft-affecting signal and hidden once the draft is ready.
        self._next_hint = NextStepHint()
        layout.addWidget(self._next_hint)

        # ---- IMAGES ----------------------------------------------------------
        self._images_header = SectionHeader(self.tr("IMAGES"))
        layout.addWidget(self._images_header)

        drop_row = QWidget()
        drop_layout = QHBoxLayout(drop_row)
        drop_layout.setContentsMargins(8, 0, 8, 0)
        drop_layout.setSpacing(6)
        self._left_drop = CameraDropZone(self.tr("Drop LEFT camera\nfolder or click"))
        self._right_drop = CameraDropZone(self.tr("Drop RIGHT camera\nfolder or click"))
        drop_layout.addWidget(self._left_drop)
        drop_layout.addWidget(self._right_drop)
        layout.addWidget(drop_row)

        self._natural_sort = QCheckBox(self.tr("Natural Sort (1, 2, …, 10)"))
        self._natural_sort.setToolTip(
            self.tr(
                "Sort file names numerically (img2 before img10). Default on; "
                "turn off for strict alphabetical order. Applies to the next "
                "folder load."
            )
        )
        self._natural_sort.setChecked(True)
        self._natural_sort.setStyleSheet(
            f"QCheckBox {{ color: {COLORS.TEXT_SECONDARY}; font-size: 11px; margin: 2px 12px; }}"
        )
        layout.addWidget(self._natural_sort)

        # Pair list with right-click remove/reveal context menu (G3.1a).
        self._pair_list = PairListWidget()
        self._pair_list.currentItemChanged.connect(self._on_row_selected)
        self._pair_list.remove_rows_requested.connect(self._remove_pairs)
        self._pair_list.reveal_row_requested.connect(self._reveal_pair)
        layout.addWidget(self._pair_list)

        self._pairing_status = QLabel(self.tr("No images loaded"))
        self._pairing_status.setStyleSheet(
            f"color: {COLORS.TEXT_MUTED}; font-size: 10px; margin: 2px 12px;"
        )
        layout.addWidget(self._pairing_status)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"color: {COLORS.BORDER}; background: {COLORS.BORDER};")
        divider.setFixedHeight(1)
        layout.addSpacing(6)
        layout.addWidget(divider)
        layout.addSpacing(6)

        # ---- Collapsible settings in a scroll area ---------------------------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        container.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        sections = QVBoxLayout(container)
        sections.setContentsMargins(0, 0, 0, 0)
        sections.setSpacing(0)

        self._calib_section = CollapsibleSection(self.tr("CALIBRATION"), expanded=True)
        self._calib_section.add_widget(self._build_calibration())
        sections.addWidget(self._calib_section)

        self._workflow_section = CollapsibleSection(self.tr("WORKFLOW TYPE"), expanded=True)
        self._workflow_section.add_widget(self._build_workflow())
        sections.addWidget(self._workflow_section)

        # INITIAL GUESS below WORKFLOW TYPE (2D placement idiom): users pick the
        # seeding mode before reaching ROI drawing.
        self._init_guess_widget = InitGuessSection3D(controller, signals)
        self._init_section = CollapsibleSection(self.tr("INITIAL GUESS"), expanded=True)
        self._init_section.add_widget(self._init_guess_widget)
        sections.addWidget(self._init_section)

        self._roi_section = CollapsibleSection(self.tr("REGION OF INTEREST"), expanded=True)
        self._roi_section.add_widget(self._build_roi())
        sections.addWidget(self._roi_section)

        self._params_section = CollapsibleSection(self.tr("PARAMETERS"), expanded=True)
        self._params_section.add_widget(self._build_params())
        sections.addWidget(self._params_section)

        self._advanced_section = CollapsibleSection(self.tr("ADVANCED"), expanded=False)
        self._advanced_section.add_widget(self._build_advanced())
        sections.addWidget(self._advanced_section)

        sections.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll, stretch=1)

        # ---- wiring ----------------------------------------------------------
        self._left_drop.folder_selected.connect(lambda f: self._load_camera("L", f))
        self._right_drop.folder_selected.connect(lambda f: self._load_camera("R", f))
        self.signals.images_changed.connect(self.refresh_images)
        self.signals.images_changed.connect(self._update_search_tooltips)
        self.signals.roi_changed.connect(self._sync_roi_label)
        # G3.4: the hint tracks every draft-affecting change.
        for sig in (
            self.signals.images_changed,
            self.signals.calibration_changed,
            self.signals.roi_changed,
            self.signals.params_changed,
        ):
            sig.connect(self._refresh_next_hint)
        self._refresh_next_hint()
        # A4-1: the FFT knobs' enable-state follows the Initial-Guess / mode
        # selection (both funnel a params_changed emit through the sidebar).
        self.signals.params_changed.connect(self._refresh_fft_enable)
        self._refresh_fft_enable()

    def _refresh_next_hint(self) -> None:
        self._next_hint.refresh(self.controller.state.draft)

    # ---- pair-list context actions (G3.1a) --------------------------------------

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
        self.signals.log.emit(f"removed {len(rows)} image pair(s)", "info")
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
        """Open the row's image folder in the system file explorer."""
        import os

        draft = self.controller.state.draft
        path = None
        if 0 <= row < len(draft.left):
            path = draft.left[row]
        elif 0 <= row < len(draft.right):
            path = draft.right[row]
        if path is None:
            return
        folder = Path(path).parent
        if not folder.is_dir():
            self.signals.log.emit(f"folder does not exist: {folder}", "warning")
            return
        os.startfile(str(folder))  # noqa: S606 - open the user's own folder

    # ---- CALIBRATION ---------------------------------------------------------

    def _build_calibration(self) -> QWidget:
        # Extracted widget (file-size discipline); NOT `_calib_section`, which
        # is the CollapsibleSection wrapper. Aliases keep the historical
        # attribute names the tests and refresh_all rely on.
        self._calib_widget = CalibrationSection3D(self.controller, self.signals)
        self._calibrate_btn = self._calib_widget.calibrate_btn
        self._calib_format = self._calib_widget.format_combo
        self._calib_btn = self._calib_widget.import_btn
        self._manual_btn = self._calib_widget.manual_btn
        self._calib_status = self._calib_widget.status_label
        return self._calib_widget

    def _preview_calibration(self) -> None:
        self._calib_widget.preview()

    # ---- WORKFLOW TYPE ---------------------------------------------------------

    def _build_workflow(self) -> QWidget:
        host = QWidget()
        layout = QVBoxLayout(host)
        layout.setContentsMargins(12, 4, 12, 8)
        layout.setSpacing(6)

        self._mode_combo = QComboBox()
        self._mode_combo.addItem(self.tr("Accumulative"), "accumulative")
        self._mode_combo.addItem(self.tr("Incremental"), "incremental")
        # Tooltip text ported verbatim from the 2D workflow_type_panel (G2.1).
        self._mode_combo.setToolTip(
            self.tr(
                "Incremental: each frame is compared to the previous reference "
                "frame.\nSuitable for large accumulated deformation, required "
                "for large rotations.\n\n"
                "Accumulative: every frame is compared to frame 1.\n"
                "Accurate for small, monotonic deformation only."
            )
        )
        layout.addLayout(self._combo_row(self.tr("Tracking Mode"), self._mode_combo))

        # Q5: reference-update policy — incremental mode only (hidden otherwise).
        self._ref_update = RefUpdateSection3D(self.controller, self.signals)
        self._ref_update.set_visible_for_mode(self.controller.state.draft.reference_mode)
        layout.addWidget(self._ref_update)

        # "AL-DIC" is a brand-specific acronym kept literal across locales;
        # "Local DIC" is translatable (same convention as the 2D app).
        self._solver_combo = QComboBox()
        self._solver_combo.addItem("AL-DIC", "aldic")
        self._solver_combo.addItem(self.tr("Local DIC"), "local")
        solver_tip = self.tr(
            "Local DIC: Independent subset matching (IC-GN). Fast,\n"
            "preserves sharp local features. Best for small\n"
            "deformations or high-quality images.\n\n"
            "AL-DIC: Augmented Lagrangian with global FEM\n"
            "regularization. Enforces displacement compatibility\n"
            "between subsets. Best for large deformations, noisy\n"
            "images, or when strain accuracy matters."
        )
        self._solver_combo.setToolTip(solver_tip)
        layout.addLayout(
            self._combo_row(self.tr("Solver"), self._solver_combo, info=InfoIcon(solver_tip))
        )

        # NOTE: surface strain is post-processing now (Batch C) — computed on
        # demand in the Strain window, never during the pipeline run.
        self._quality_cb = QCheckBox(self.tr("Quality gates (ZNSSD / outliers)"))
        self._quality_cb.setToolTip(
            self.tr(
                "Post-run filters: demote points whose ZNSSD correlation,\n"
                "reprojection error or 3D-outlier distance fails the gate to\n"
                "NaN. Default off (keep every tracked point); enable for noisy\n"
                "data when a few bad points pollute the fields. The log\n"
                "reports how many points each gate removed."
            )
        )
        layout.addWidget(self._quality_cb)

        self._mode_combo.currentIndexChanged.connect(self._apply_workflow)
        self._solver_combo.currentIndexChanged.connect(self._apply_workflow)
        self._quality_cb.toggled.connect(self._apply_workflow)
        return host

    def _combo_row(self, text: str, combo: QComboBox, info: InfoIcon | None = None) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(4)
        lbl = QLabel(text)
        lbl.setFixedWidth(88)
        lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        row.addWidget(lbl)
        row.addWidget(combo, stretch=1)
        if info is not None:
            row.addWidget(info)
        return row

    def _apply_workflow(self, *_a) -> None:
        draft = self.controller.state.draft
        draft.strategy = self._strategy_combo.currentData()
        draft.reference_mode = self._mode_combo.currentData()
        draft.use_global_step = self._solver_combo.currentData() == "aldic"
        draft.quality_gate = self._quality_cb.isChecked()
        self._admm_spin.setEnabled(draft.use_global_step)
        self._ref_update.set_visible_for_mode(draft.reference_mode)  # Q5
        self.controller.state.mark_dirty()
        self.signals.params_changed.emit()

    # ---- REGION OF INTEREST ------------------------------------------------------

    def _build_roi(self) -> QWidget:
        host = QWidget()
        layout = QVBoxLayout(host)
        layout.setContentsMargins(12, 4, 12, 8)
        layout.setSpacing(6)

        hint = QLabel(
            self.tr(
                "Draw on the LEFT camera, frame 1 — all later frames and the "
                "right camera follow from it."
            )
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(
            f"background: {COLORS.BG_PANEL}; border: 1px solid {COLORS.BORDER}; "
            f"border-radius: 4px; color: {COLORS.TEXT_SECONDARY}; "
            f"font-size: 11px; padding: 6px;"
        )
        layout.addWidget(hint)

        # ROI toolbox — Add/Cut/Refine dropdown tools + Import/Save/Invert/Clear
        # (the full 2D drawing experience; the canvas rasterizes the shapes).
        self._roi_toolbar = ROIToolbar()
        layout.addWidget(self._roi_toolbar)

        # Read-only bounding-box readout of the drawn mask.
        self._roi_bbox_lbl = QLabel(self.tr("bbox: not set"))
        self._roi_bbox_lbl.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 10px;")
        layout.addWidget(self._roi_bbox_lbl)
        return host

    @property
    def roi_toolbar(self) -> ROIToolbar:
        """The main window wires this toolbar to the canvas drawing tools."""
        return self._roi_toolbar

    @property
    def init_guess_widget(self) -> InitGuessSection3D:
        """The main window wires seed placement to the canvas click tool."""
        return self._init_guess_widget

    def _sync_roi_label(self) -> None:
        roi = self.controller.state.draft.roi
        if roi is None:
            self._roi_bbox_lbl.setText(self.tr("bbox: not set"))
        else:
            self._roi_bbox_lbl.setText(
                self.tr("bbox: {0}–{1}, {2}–{3} px").format(*(int(v) for v in roi))
            )

    # ---- PARAMETERS ---------------------------------------------------------------

    def _build_params(self) -> QWidget:
        host = QWidget()
        layout = QVBoxLayout(host)
        layout.setContentsMargins(12, 4, 12, 8)
        layout.setSpacing(6)

        # Subset Size: display ODD (2*half+1 centered window, the 2D-app
        # convention) while draft.winsize keeps the engine's EVEN internal
        # value (display - 1). Snap-to-odd lives in _on_subset_display_changed.
        self._subset_spin = QSpinBox()
        self._subset_spin.setRange(5, 201)
        self._subset_spin.setSingleStep(2)
        self._subset_spin.setValue(33)  # draft default winsize=32 -> display 33
        self._subset_spin.setToolTip(
            self.tr(
                "IC-GN subset window size in pixels (odd number). Default 33.\n"
                "Larger = more robust on sparse speckle, smoother fields;\n"
                "smaller = finer spatial detail but noisier. The subset must\n"
                "span several speckles."
            )
        )
        layout.addLayout(self._param_row(self.tr("Subset Size"), self._subset_spin))

        # Subset Step: powers of two only (combo, 2D idiom).
        self._step_combo = QComboBox()
        self._step_combo.addItems([str(v) for v in _STEP_OPTIONS])
        self._step_combo.setCurrentText("16")
        self._step_combo.setToolTip(
            self.tr(
                "Node spacing in pixels (power of 2). Default 16. Smaller =\n"
                "denser measurement grid and longer runs; larger = faster but\n"
                "coarser fields. Typically ¼–½ of the Subset Size."
            )
        )
        layout.addLayout(self._param_row(self.tr("Subset Step"), self._step_combo))

        self._search_spin = QSpinBox()
        self._search_spin.setRange(4, 400)
        self._search_spin.setValue(48)
        self._search_spin.setSuffix(" px")
        layout.addLayout(self._param_row(self.tr("Stereo Search"), self._search_spin))

        # Temporal FFT seeding half-width: must cover the largest per-frame
        # motion (auto-expand only fires on boundary-clipped peaks, not on the
        # in-bounds noise peaks a decorrelated jump produces). The ⓘ mirrors
        # the (dynamic) tooltip for discoverability (G2.1).
        self._temporal_spin = QSpinBox()
        self._temporal_spin.setRange(8, 400)
        self._temporal_spin.setValue(20)
        self._temporal_spin.setSuffix(" px")
        self._temporal_info = InfoIcon("")
        layout.addLayout(
            self._param_row(
                self.tr("Temporal Search"), self._temporal_spin, info=self._temporal_info
            )
        )
        self._update_search_tooltips()

        # ---- quadtree mesh refinement (2D-app levers; default = uniform grid) ----
        refine_lbl = QLabel(self.tr("Mesh refinement"))
        refine_lbl.setStyleSheet(
            f"color: {COLORS.TEXT_SECONDARY}; font-size: 11px; font-weight: bold;"
        )
        layout.addSpacing(4)
        layout.addWidget(refine_lbl)

        self._refine_inner_cb = QCheckBox(self.tr("Refine at mask boundaries (holes)"))
        self._refine_inner_cb.setToolTip(
            self.tr(
                "Quadtree-subdivide mesh elements crossing interior mask\n"
                "holes so the mesh hugs the hole edges. Default off (uniform\n"
                "grid); enable when the ROI mask has cut-outs whose rims you\n"
                "care about."
            )
        )
        layout.addWidget(self._refine_inner_cb)
        self._refine_outer_cb = QCheckBox(self.tr("Refine at ROI edges"))
        self._refine_outer_cb.setToolTip(
            self.tr(
                "Quadtree-subdivide mesh elements along the outer ROI\n"
                "boundary. Default off; enable for curved / irregular ROI\n"
                "outlines where the uniform grid staircases."
            )
        )
        layout.addWidget(self._refine_outer_cb)

        self._refine_level_spin = QSpinBox()
        self._refine_level_spin.setRange(1, 3)
        self._refine_level_spin.setValue(1)
        self._refine_level_spin.setToolTip(
            self.tr(
                "How aggressively refined elements shrink: the minimum element\n"
                "is step / 2^level. Default 1 (light); 3 is heavy — finer\n"
                "boundary detail but many more nodes and a slower run."
            )
        )
        layout.addLayout(self._param_row(self.tr("Refinement Level"), self._refine_level_spin))

        # The refinement BRUSH moved into the ROI toolbar's "+ Refine" menu
        # (Paint / Erase / Clear Brush + radius) — 2D toolbox parity.

        self._subset_spin.valueChanged.connect(self._on_subset_display_changed)
        self._step_combo.currentTextChanged.connect(self._apply_params)
        self._search_spin.valueChanged.connect(self._apply_params)
        self._temporal_spin.valueChanged.connect(self._apply_params)
        self._refine_inner_cb.toggled.connect(self._apply_params)
        self._refine_outer_cb.toggled.connect(self._apply_params)
        self._refine_level_spin.valueChanged.connect(self._apply_params)
        return host

    # ---- ADVANCED -------------------------------------------------------------------

    def _build_advanced(self) -> QWidget:
        # Extracted widget (file-size discipline, batch Q); aliases keep the
        # historical attribute names refresh_all / _apply_* rely on.
        widget = AdvancedSection3D()
        self._strategy_combo = widget.strategy_combo
        self._admm_spin = widget.admm_spin
        self._parallel_cb = widget.parallel_cb
        self._fft_expand_cb = widget.fft_expand_cb
        self._fft_expand_base_tip = self._fft_expand_cb.toolTip()  # A4-1: base ⓘ text
        self._strategy_combo.currentIndexChanged.connect(self._apply_workflow)
        self._admm_spin.valueChanged.connect(self._apply_params)
        self._parallel_cb.toggled.connect(self._apply_params)
        self._fft_expand_cb.toggled.connect(self._apply_params)
        return widget

    def _param_row(self, text: str, widget: QWidget, info: InfoIcon | None = None) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(4)
        lbl = QLabel(text)
        lbl.setFixedWidth(96)
        lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        row.addWidget(lbl)
        row.addWidget(widget, stretch=1)
        if info is not None:
            row.addWidget(info)
        return row

    def _on_subset_display_changed(self, display_value: int) -> None:
        """Snap a typed even value to the next odd one (2D convention), then apply."""
        if display_value % 2 == 0:
            display_value += 1
            self._subset_spin.blockSignals(True)
            self._subset_spin.setValue(display_value)
            self._subset_spin.blockSignals(False)
        self._apply_params()

    def _apply_params(self, *_a) -> None:
        draft = self.controller.state.draft
        # Odd display value -> the engine's even internal winsize (display - 1).
        draft.winsize = int(self._subset_spin.value()) - 1
        draft.winstepsize = int(self._step_combo.currentText())
        # Engine invariant: winsize_min <= winstepsize (2D auto-clamps too).
        draft.winsize_min = min(8, draft.winstepsize)
        draft.stereo_search = int(self._search_spin.value())
        draft.fft_search = int(self._temporal_spin.value())
        draft.fft_auto_expand = self._fft_expand_cb.isChecked()  # Q8
        draft.admm_max_iter = int(self._admm_spin.value())
        draft.parallel_cameras = self._parallel_cb.isChecked()
        draft.refine_inner = self._refine_inner_cb.isChecked()
        draft.refine_outer = self._refine_outer_cb.isChecked()
        draft.refinement_level = int(self._refine_level_spin.value())
        self.controller.state.mark_dirty()
        self._update_search_tooltips()  # winsize feeds the search-cap formulas
        self.signals.params_changed.emit()

    # ---- search-range caps (F1.3) + temporal-FFT honesty (A4-1 / A4-2) --------------

    def _sequence_min_dim(self) -> int | None:
        """``min(H, W)`` of the first LEFT image (cached per path); None if unknown."""
        draft = self.controller.state.draft
        if not draft.left:
            self._shape_cache = None
            return None
        path = str(draft.left[0])
        if self._shape_cache is not None and self._shape_cache[0] == path:
            return self._shape_cache[1]
        try:
            import cv2

            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            min_dim = None if img is None else int(min(img.shape[:2]))
        except Exception:  # noqa: BLE001 - a bad frame must not break the sidebar
            min_dim = None
        self._shape_cache = (path, min_dim)
        return min_dim

    def _update_search_tooltips(self) -> None:
        """Static guidance + the image-derived search caps once images are loaded.

        The run-start clamp ``max(10, min(H, W) // 4 - winsize)`` only REDUCES
        the STARTING FFT radius (a warning, no hard cap); with Auto-expand on
        (the default) the engine can still grow the search to
        ``max(32, min(H, W) // 2)`` on a boundary-clipped peak (A4-2 — the old
        tooltip presented the run-start clamp as the detectable-motion cap).
        The stereo NCC window is clamped at the image borders per point.
        """
        stereo_tip = self.tr(
            "NCC search half-width (pixels) around each node for the\n"
            "left-to-right stereo match. Set larger than the largest\n"
            "expected stereo disparity."
        )
        temporal_tip = self.tr(
            "Half-width (pixels) of the temporal FFT integer search that seeds\n"
            "each per-frame match. Set comfortably larger than the expected\n"
            "inter-frame motion; with Auto-expand on (default) the engine can\n"
            "still grow the search past this on a boundary-clipped peak."
        )
        min_dim = self._sequence_min_dim()
        if min_dim is not None:
            win = int(self.controller.state.draft.winsize)
            stereo_cap = max(1, (min_dim - win) // 2)
            temporal_cap = max(10, min_dim // 4 - win)
            expand_cap = max(32, min_dim // 2)
            stereo_tip += "\n" + self.tr(
                "Current images: values above {0} px cannot widen the search\n"
                "(the window is clamped at the image borders)."
            ).format(stereo_cap)
            temporal_tip += "\n" + self.tr(
                "Current images: the engine starts the FFT search clamped to\n"
                "{0} px (max(10, min(H, W) / 4 - subset)); Auto-expand can grow\n"
                "it to {1} px (max(32, min(H, W) / 2)) on clipped peaks."
            ).format(temporal_cap, expand_cap)
        self._search_spin.setToolTip(stereo_tip)
        self._temporal_spin.setToolTip(temporal_tip)
        self._temporal_info.set_tip(temporal_tip)  # keep the ⓘ in sync (G2.1)

    def _refresh_fft_enable(self) -> None:
        """A4-1: grey out the temporal-FFT knobs when the current Initial Guess /
        Tracking Mode means the engine never runs FFT (external mesh + a non-None
        U0), so they can never masquerade as large-motion protection they do not
        give. Recomputed live on every init_guess / mode change.
        """
        active = fft_controls_active(self.controller.state.draft)
        self._temporal_spin.setEnabled(active)
        self._fft_expand_cb.setEnabled(active)
        self._update_search_tooltips()  # reset spin/ⓘ tips to base + caps
        self._fft_expand_cb.setToolTip(self._fft_expand_base_tip)
        if active:
            return
        note = "\n\n" + self.tr(
            "Inactive with the current Initial Guess / Tracking Mode: the\n"
            "temporal FFT runs only when Initial Guess = FFT, or at reference\n"
            "switches in Incremental mode; in Accumulative + Starting Point /\n"
            "Previous frame no FFT runs, so this control has no effect."
        )
        self._temporal_spin.setToolTip(self._temporal_spin.toolTip() + note)
        self._temporal_info.set_tip(self._temporal_spin.toolTip())
        self._fft_expand_cb.setToolTip(self._fft_expand_base_tip + note)

    # ---- IMAGES --------------------------------------------------------------------

    def _load_camera(self, cam: str, folder: str) -> None:
        files = list_images(folder, self._natural_sort.isChecked())
        if not files:
            self.signals.log.emit(f"no images found in {folder}", "warning")
            return
        draft = self.controller.state.draft
        if cam == "L":
            draft.left = files
        else:
            draft.right = files
        self.controller.state.mark_dirty()
        self.signals.log.emit(f"{cam}: {len(files)} images from {folder}", "info")
        self.signals.images_changed.emit()

    def refresh_images(self) -> None:
        draft = self.controller.state.draft
        # G2.9: the drop zones mirror the draft — folder name + frame count
        # with an accent border once loaded; back to the caption when empty.
        for zone, files in ((self._left_drop, draft.left), (self._right_drop, draft.right)):
            if files:
                zone.set_loaded(str(Path(files[0]).parent), len(files))
            else:
                zone.reset()
        self._pair_list.clear()
        n = max(len(draft.left), len(draft.right))
        from PySide6.QtGui import QBrush, QColor

        name_brush = QBrush(QColor(COLORS.ACCENT_HOVER))  # indigo filenames (2D idiom)
        muted_brush = QBrush(QColor(COLORS.TEXT_MUTED))
        for i in range(n):
            left = Path(draft.left[i]).name if i < len(draft.left) else "—"
            right = Path(draft.right[i]).name if i < len(draft.right) else "—"
            item = QTreeWidgetItem([f"{i:02d}", left, right])
            item.setForeground(0, muted_brush)
            item.setForeground(1, name_brush)
            item.setForeground(2, name_brush)
            self._pair_list.addTopLevelItem(item)
        self._images_header.set_badge(str(n) if n else "")

        n_l, n_r = len(draft.left), len(draft.right)
        if n_l == 0 and n_r == 0:
            self._pairing_status.setText(self.tr("No images loaded"))
            self._pairing_status.setStyleSheet(
                f"color: {COLORS.TEXT_MUTED}; font-size: 10px; margin: 2px 12px;"
            )
        elif n_l == n_r and n_l >= 2:
            self._pairing_status.setText(self.tr("Paired: {0} frames per camera").format(n_l))
            self._pairing_status.setStyleSheet(
                f"color: {COLORS.SUCCESS}; font-size: 10px; margin: 2px 12px;"
            )
        else:
            self._pairing_status.setText(
                self.tr("Mismatch: {0} left vs {1} right").format(n_l, n_r)
            )
            self._pairing_status.setStyleSheet(
                f"color: {COLORS.DANGER}; font-size: 10px; margin: 2px 12px;"
            )

    def _on_row_selected(self, current, _previous) -> None:
        if current is not None:
            idx = self._pair_list.indexOfTopLevelItem(current)
            # G1.5: clamp against the LONGER list (the expression the table is
            # built from) — during an L/R count mismatch the right camera may
            # have more rows than the left, and those must stay reachable.
            draft = self.controller.state.draft
            n = max(len(draft.left), len(draft.right), 1)
            self.signals.set_current_frame(idx, n)

    def refresh_all(self) -> None:
        """Full resync from the state (project open / new)."""
        draft = self.controller.state.draft
        widgets = (
            self._strategy_combo,
            self._mode_combo,
            self._solver_combo,
            self._quality_cb,
            self._subset_spin,
            self._step_combo,
            self._search_spin,
            self._temporal_spin,
            self._admm_spin,
            self._parallel_cb,
            self._fft_expand_cb,
            self._refine_inner_cb,
            self._refine_outer_cb,
            self._refine_level_spin,
            self._calib_format,
        )
        for w in widgets:
            w.blockSignals(True)
        self._strategy_combo.setCurrentIndex(max(0, self._strategy_combo.findData(draft.strategy)))
        self._mode_combo.setCurrentIndex(max(0, self._mode_combo.findData(draft.reference_mode)))
        self._solver_combo.setCurrentIndex(0 if draft.use_global_step else 1)
        self._quality_cb.setChecked(draft.quality_gate)
        draft.winsize = int(draft.winsize) - (int(draft.winsize) % 2)  # engine value is even
        self._subset_spin.setValue(draft.winsize + 1)  # even internal -> odd display
        # Snap legacy non-power-of-2 steps to the nearest option so the combo
        # and the draft cannot diverge silently.
        step = min(_STEP_OPTIONS, key=lambda v: abs(v - int(draft.winstepsize)))
        draft.winstepsize = step
        draft.winsize_min = min(8, step)  # engine invariant: winsize_min <= step
        self._step_combo.setCurrentText(str(step))
        self._search_spin.setValue(draft.stereo_search)
        self._temporal_spin.setValue(draft.fft_search)
        self._admm_spin.setValue(draft.admm_max_iter)
        self._admm_spin.setEnabled(draft.use_global_step)
        self._parallel_cb.setChecked(getattr(draft, "parallel_cameras", False))
        self._fft_expand_cb.setChecked(getattr(draft, "fft_auto_expand", True))
        self._refine_inner_cb.setChecked(draft.refine_inner)
        self._refine_outer_cb.setChecked(draft.refine_outer)
        self._refine_level_spin.setValue(draft.refinement_level)
        self._calib_format.setCurrentText(draft.calibration_format)
        for w in widgets:
            w.blockSignals(False)
        if draft.calibration_file is not None:
            self._preview_calibration()
        self._ref_update.refresh_from_draft()  # Q5: mode/N/frames + visibility
        self._init_guess_widget.refresh_from_draft()
        self.refresh_images()
        self._refresh_fft_enable()  # A4-1: tooltips + enable-state in one place
        self._sync_roi_label()
