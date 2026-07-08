"""Left sidebar — dual-camera import, calibration, workflow type, ROI, parameters.

The 2D sidebar idiom (fixed 320 px, uppercase section headers with badges, a drop
zone, a file table, collapsible settings in a scroll area) applied to the 3D-DIC
workflow: TWO camera streams that must pair, a stereo calibration that must be
sane before anything else, the correspondence strategy, and the matching scale.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from al_dic.gui.theme import COLORS
from al_dic.gui.widgets.collapsible_section import CollapsibleSection
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.calibration import IMPORTERS, load_calibration
from al_dic_3d.gui.state import GuiSignals
from al_dic_3d.gui.widgets.roi_toolbar import ROIToolbar

if TYPE_CHECKING:
    from al_dic_3d.gui.controller import WorkflowController

_IMAGE_EXTS = {".png", ".tif", ".tiff", ".jpg", ".jpeg", ".bmp"}


def _natural_key(name: str) -> list:
    import re

    return [int(t) if t.isdigit() else t.lower() for t in re.findall(r"\d+|\D+", name)]


def _list_images(folder: str, natural: bool) -> list[str]:
    paths = [p for p in Path(folder).iterdir() if p.suffix.lower() in _IMAGE_EXTS]
    key = (lambda p: _natural_key(p.name)) if natural else (lambda p: p.name)
    return [str(p) for p in sorted(paths, key=key)]


class _SectionHeader(QWidget):
    """Uppercase 11px bold letter-spaced title + optional count badge."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 4)
        layout.setSpacing(6)
        label = QLabel(title)
        label.setStyleSheet(
            f"color: {COLORS.TEXT_SECONDARY}; font-size: 11px; "
            f"font-weight: bold; letter-spacing: 1px;"
        )
        layout.addWidget(label)
        self._badge = QLabel("")
        self._badge.setStyleSheet(
            f"color: {COLORS.TEXT_MUTED}; font-size: 10px; "
            f"background: {COLORS.BG_INPUT}; border-radius: 7px; padding: 1px 6px;"
        )
        self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._badge.hide()
        layout.addWidget(self._badge)
        layout.addStretch()

    def set_badge(self, text: str) -> None:
        if text:
            self._badge.setText(text)
            self._badge.show()
        else:
            self._badge.hide()


class _CameraDropZone(QWidget):
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
            _CameraDropZone {{
                background: {COLORS.BG_PANEL};
                border: 1px dashed {COLORS.BORDER};
                border-radius: 6px;
            }}
            _CameraDropZone:hover {{
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
        self.setObjectName("leftSidebar")
        self.setFixedWidth(320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ---- IMAGES ----------------------------------------------------------
        self._images_header = _SectionHeader(self.tr("IMAGES"))
        layout.addWidget(self._images_header)

        drop_row = QWidget()
        drop_layout = QHBoxLayout(drop_row)
        drop_layout.setContentsMargins(8, 0, 8, 0)
        drop_layout.setSpacing(6)
        self._left_drop = _CameraDropZone(self.tr("Drop LEFT camera\nfolder or click"))
        self._right_drop = _CameraDropZone(self.tr("Drop RIGHT camera\nfolder or click"))
        drop_layout.addWidget(self._left_drop)
        drop_layout.addWidget(self._right_drop)
        layout.addWidget(drop_row)

        self._natural_sort = QCheckBox(self.tr("Natural Sort (1, 2, …, 10)"))
        self._natural_sort.setChecked(True)
        self._natural_sort.setStyleSheet(
            f"QCheckBox {{ color: {COLORS.TEXT_SECONDARY}; font-size: 11px; margin: 2px 12px; }}"
        )
        layout.addWidget(self._natural_sort)

        self._pair_list = QTreeWidget()
        self._pair_list.setHeaderLabels(["#", self.tr("Left"), self.tr("Right")])
        self._pair_list.setRootIsDecorated(False)
        self._pair_list.setColumnWidth(0, 30)
        self._pair_list.setColumnWidth(1, 128)
        self._pair_list.setMinimumHeight(80)
        self._pair_list.setMaximumHeight(200)
        self._pair_list.setStyleSheet(
            f"""
            QTreeWidget {{
                background: {COLORS.BG_SIDEBAR};
                border: none;
                font-size: 11px;
            }}
            QTreeWidget::item {{ height: 22px; }}
            QTreeWidget::item:selected {{ background: {COLORS.BG_HOVER}; }}
            QHeaderView::section {{
                background: {COLORS.BG_PANEL};
                color: {COLORS.TEXT_MUTED};
                border: none;
                border-bottom: 1px solid {COLORS.BORDER};
                padding: 3px 6px;
                font-size: 10px;
                font-weight: bold;
            }}
            """
        )
        self._pair_list.currentItemChanged.connect(self._on_row_selected)
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
        self.signals.roi_changed.connect(self._sync_roi_label)

    # ---- CALIBRATION ---------------------------------------------------------

    def _build_calibration(self) -> QWidget:
        host = QWidget()
        layout = QVBoxLayout(host)
        layout.setContentsMargins(12, 4, 12, 8)
        layout.setSpacing(6)

        # Three entry modes (D12): built-in calibrator (primary), file import
        # (alternative), manual parameters (fallback). All converge on an
        # opencv_yaml file previewed by the same QC funnel below.
        self._calibrate_btn = QPushButton(self.tr("Calibrate from images…"))
        self._calibrate_btn.setProperty("class", "btn-primary")
        self._calibrate_btn.clicked.connect(self._on_calibrate_dialog)
        layout.addWidget(self._calibrate_btn)

        row = QHBoxLayout()
        row.setSpacing(4)
        lbl = QLabel(self.tr("Format"))
        lbl.setFixedWidth(88)
        lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        row.addWidget(lbl)
        self._calib_format = QComboBox()
        self._calib_format.addItems(sorted(IMPORTERS))
        self._calib_format.setCurrentText("opencv_yaml")
        self._calib_format.currentTextChanged.connect(self._on_calib_format)
        row.addWidget(self._calib_format, stretch=1)
        layout.addLayout(row)

        self._calib_btn = QPushButton(self.tr("Import calibration…"))
        self._calib_btn.clicked.connect(self._on_calib_browse)
        layout.addWidget(self._calib_btn)

        self._manual_btn = QPushButton(self.tr("Manual parameters…"))
        self._manual_btn.clicked.connect(self._on_manual_dialog)
        layout.addWidget(self._manual_btn)

        self._calib_status = QLabel(self.tr("No calibration loaded"))
        self._calib_status.setWordWrap(True)
        self._calib_status.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(self._calib_status)
        return host

    def _on_calibrate_dialog(self) -> None:
        from al_dic_3d.gui.dialogs.calibration_dialog import CalibrationDialog

        dlg = CalibrationDialog(self)
        if dlg.exec() and dlg.saved_path:
            self._adopt_calibration_file(dlg.saved_path)

    def _on_manual_dialog(self) -> None:
        from al_dic_3d.gui.dialogs.manual_params_dialog import ManualParamsDialog

        dlg = ManualParamsDialog(self)
        if dlg.exec() and dlg.saved_path:
            self._adopt_calibration_file(dlg.saved_path)

    def _adopt_calibration_file(self, path) -> None:
        """Route a freshly written opencv_yaml through the shared QC funnel."""
        draft = self.controller.state.draft
        draft.calibration_file = Path(path)
        draft.calibration_format = "opencv_yaml"
        self._calib_format.setCurrentText("opencv_yaml")
        self.controller.state.mark_dirty()
        self._preview_calibration()
        self.signals.calibration_changed.emit()

    def _on_calib_format(self, fmt: str) -> None:
        self.controller.state.draft.calibration_format = fmt
        self.controller.state.mark_dirty()
        self.signals.calibration_changed.emit()

    def _on_calib_browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Choose calibration file"),
            "",
            self.tr("Calibration files (*.xml *.yaml *.yml *.mat *.csv *.txt *.caldat)"),
        )
        if not path:
            return
        self.controller.state.draft.calibration_file = Path(path)
        self.controller.state.mark_dirty()
        self._preview_calibration()
        self.signals.calibration_changed.emit()

    def _preview_calibration(self) -> None:
        draft = self.controller.state.draft
        try:
            rig = load_calibration(draft.calibration_file, draft.calibration_format)
        except Exception as exc:  # noqa: BLE001 - calibration errors must die HERE
            self._calib_status.setText(self.tr("Error: {0}").format(exc))
            self._calib_status.setStyleSheet(f"color: {COLORS.DANGER}; font-size: 11px;")
            self.signals.log.emit(str(exc), "error")
            return
        left = rig.cameras["L"]
        _, t = rig.pose("R")
        baseline = float(np.linalg.norm(t))
        self._calib_status.setText(
            self.tr("{0}\nfx {1:.0f}  fy {2:.0f}  |  baseline {3:.1f} mm").format(
                Path(str(draft.calibration_file)).name, left.fx, left.fy, baseline
            )
        )
        self._calib_status.setStyleSheet(f"color: {COLORS.SUCCESS}; font-size: 11px;")
        self.signals.log.emit(f"calibration loaded: baseline {baseline:.1f} mm", "success")

    # ---- WORKFLOW TYPE ---------------------------------------------------------

    def _build_workflow(self) -> QWidget:
        host = QWidget()
        layout = QVBoxLayout(host)
        layout.setContentsMargins(12, 4, 12, 8)
        layout.setSpacing(6)

        self._mode_combo = QComboBox()
        self._mode_combo.addItem(self.tr("Accumulative"), "accumulative")
        self._mode_combo.addItem(self.tr("Incremental"), "incremental")
        layout.addLayout(self._combo_row(self.tr("Tracking Mode"), self._mode_combo))

        # "AL-DIC" is a brand-specific acronym kept literal across locales;
        # "Local DIC" is translatable (same convention as the 2D app).
        self._solver_combo = QComboBox()
        self._solver_combo.addItem("AL-DIC", "aldic")
        self._solver_combo.addItem(self.tr("Local DIC"), "local")
        self._solver_combo.setToolTip(
            self.tr(
                "Local DIC: Independent subset matching (IC-GN). Fast,\n"
                "preserves sharp local features. Best for small\n"
                "deformations or high-quality images.\n\n"
                "AL-DIC: Augmented Lagrangian with global FEM\n"
                "regularization. Enforces displacement compatibility\n"
                "between subsets. Best for large deformations, noisy\n"
                "images, or when strain accuracy matters."
            )
        )
        layout.addLayout(self._combo_row(self.tr("Solver"), self._solver_combo))

        self._strain_cb = QCheckBox(self.tr("Compute surface strain"))
        self._strain_cb.setChecked(True)
        layout.addWidget(self._strain_cb)

        self._quality_cb = QCheckBox(self.tr("Quality gates (ZNSSD / outliers)"))
        layout.addWidget(self._quality_cb)

        self._mode_combo.currentIndexChanged.connect(self._apply_workflow)
        self._solver_combo.currentIndexChanged.connect(self._apply_workflow)
        self._strain_cb.toggled.connect(self._apply_workflow)
        self._quality_cb.toggled.connect(self._apply_workflow)
        return host

    def _combo_row(self, text: str, combo: QComboBox) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(4)
        lbl = QLabel(text)
        lbl.setFixedWidth(88)
        lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        row.addWidget(lbl)
        row.addWidget(combo, stretch=1)
        return row

    def _apply_workflow(self, *_a) -> None:
        draft = self.controller.state.draft
        draft.strategy = self._strategy_combo.currentData()
        draft.reference_mode = self._mode_combo.currentData()
        draft.use_global_step = self._solver_combo.currentData() == "aldic"
        draft.compute_strain = self._strain_cb.isChecked()
        draft.quality_gate = self._quality_cb.isChecked()
        self._admm_spin.setEnabled(draft.use_global_step)
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

        self._subset_spin = QSpinBox()
        self._subset_spin.setRange(8, 200)
        self._subset_spin.setSingleStep(2)
        self._subset_spin.setValue(32)
        layout.addLayout(self._param_row(self.tr("Subset Size"), self._subset_spin))

        self._step_spin = QSpinBox()
        self._step_spin.setRange(2, 256)
        self._step_spin.setValue(16)
        layout.addLayout(self._param_row(self.tr("Subset Step"), self._step_spin))

        self._search_spin = QSpinBox()
        self._search_spin.setRange(4, 400)
        self._search_spin.setValue(48)
        self._search_spin.setSuffix(" px")
        layout.addLayout(self._param_row(self.tr("Stereo Search"), self._search_spin))

        # Temporal FFT seeding half-width: must cover the largest per-frame
        # motion (auto-expand only fires on boundary-clipped peaks, not on the
        # in-bounds noise peaks a decorrelated jump produces).
        self._temporal_spin = QSpinBox()
        self._temporal_spin.setRange(8, 400)
        self._temporal_spin.setValue(20)
        self._temporal_spin.setSuffix(" px")
        layout.addLayout(self._param_row(self.tr("Temporal Search"), self._temporal_spin))

        # ---- quadtree mesh refinement (2D-app levers; default = uniform grid) ----
        refine_lbl = QLabel(self.tr("Mesh refinement"))
        refine_lbl.setStyleSheet(
            f"color: {COLORS.TEXT_SECONDARY}; font-size: 11px; font-weight: bold;"
        )
        layout.addSpacing(4)
        layout.addWidget(refine_lbl)

        self._refine_inner_cb = QCheckBox(self.tr("Refine at mask boundaries (holes)"))
        layout.addWidget(self._refine_inner_cb)
        self._refine_outer_cb = QCheckBox(self.tr("Refine at ROI edges"))
        layout.addWidget(self._refine_outer_cb)

        self._refine_level_spin = QSpinBox()
        self._refine_level_spin.setRange(1, 3)
        self._refine_level_spin.setValue(1)
        layout.addLayout(self._param_row(self.tr("Refinement Level"), self._refine_level_spin))

        # The refinement BRUSH moved into the ROI toolbar's "+ Refine" menu
        # (Paint / Erase / Clear Brush + radius) — 2D toolbox parity.

        self._subset_spin.valueChanged.connect(self._apply_params)
        self._step_spin.valueChanged.connect(self._apply_params)
        self._search_spin.valueChanged.connect(self._apply_params)
        self._temporal_spin.valueChanged.connect(self._apply_params)
        self._refine_inner_cb.toggled.connect(self._apply_params)
        self._refine_outer_cb.toggled.connect(self._apply_params)
        self._refine_level_spin.valueChanged.connect(self._apply_params)
        return host

    # ---- ADVANCED -------------------------------------------------------------------

    def _build_advanced(self) -> QWidget:
        host = QWidget()
        layout = QVBoxLayout(host)
        layout.setContentsMargins(12, 4, 12, 8)
        layout.setSpacing(6)

        self._strategy_combo = QComboBox()
        self._strategy_combo.addItem(self.tr("Track Both"), "track_both")
        self._strategy_combo.addItem(self.tr("Stereo Each Frame"), "stereo_each_frame")
        self._strategy_combo.addItem(self.tr("Reference Direct"), "ref_direct")
        layout.addLayout(self._combo_row(self.tr("Strategy"), self._strategy_combo))

        # AL-DIC global refinement cycles (ADMM under the hood; acronym hidden).
        self._admm_spin = QSpinBox()
        self._admm_spin.setRange(1, 10)
        self._admm_spin.setValue(3)
        self._admm_spin.setToolTip(
            self.tr("1 = single global pass (fastest), 3 = default, 5+ = diminishing returns")
        )
        layout.addLayout(self._param_row(self.tr("AL-DIC Iterations"), self._admm_spin))

        admm_hint = QLabel(self.tr("Only affects AL-DIC solver. Ignored by Local DIC."))
        admm_hint.setWordWrap(True)
        admm_hint.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 10px;")
        layout.addWidget(admm_hint)

        self._strategy_combo.currentIndexChanged.connect(self._apply_workflow)
        self._admm_spin.valueChanged.connect(self._apply_params)
        return host

    def _param_row(self, text: str, widget: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(4)
        lbl = QLabel(text)
        lbl.setFixedWidth(96)
        lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        row.addWidget(lbl)
        row.addWidget(widget, stretch=1)
        return row

    def _apply_params(self, *_a) -> None:
        draft = self.controller.state.draft
        draft.winsize = int(self._subset_spin.value())
        draft.winstepsize = int(self._step_spin.value())
        draft.stereo_search = int(self._search_spin.value())
        draft.fft_search = int(self._temporal_spin.value())
        draft.admm_max_iter = int(self._admm_spin.value())
        draft.refine_inner = self._refine_inner_cb.isChecked()
        draft.refine_outer = self._refine_outer_cb.isChecked()
        draft.refinement_level = int(self._refine_level_spin.value())
        self.controller.state.mark_dirty()
        self.signals.params_changed.emit()

    # ---- IMAGES --------------------------------------------------------------------

    def _load_camera(self, cam: str, folder: str) -> None:
        files = _list_images(folder, self._natural_sort.isChecked())
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
            n = max(len(self.controller.state.draft.left), 1)
            self.signals.set_current_frame(idx, n)

    def refresh_all(self) -> None:
        """Full resync from the state (project open / new)."""
        draft = self.controller.state.draft
        widgets = (
            self._strategy_combo,
            self._mode_combo,
            self._solver_combo,
            self._strain_cb,
            self._quality_cb,
            self._subset_spin,
            self._step_spin,
            self._search_spin,
            self._temporal_spin,
            self._admm_spin,
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
        self._strain_cb.setChecked(draft.compute_strain)
        self._quality_cb.setChecked(draft.quality_gate)
        self._subset_spin.setValue(draft.winsize)
        self._step_spin.setValue(draft.winstepsize)
        self._search_spin.setValue(draft.stereo_search)
        self._temporal_spin.setValue(draft.fft_search)
        self._admm_spin.setValue(draft.admm_max_iter)
        self._admm_spin.setEnabled(draft.use_global_step)
        self._refine_inner_cb.setChecked(draft.refine_inner)
        self._refine_outer_cb.setChecked(draft.refine_outer)
        self._refine_level_spin.setValue(draft.refinement_level)
        self._calib_format.setCurrentText(draft.calibration_format)
        for w in widgets:
            w.blockSignals(False)
        if draft.calibration_file is not None:
            self._preview_calibration()
        self.refresh_images()
        self._sync_roi_label()
