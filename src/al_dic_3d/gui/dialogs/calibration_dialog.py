"""Built-in stereo calibration dialog (D12) — the MATLAB-calibrator workflow.

Pick synchronized L/R board images, describe the board, Calibrate (detection +
solve run in a worker thread), inspect per-pair RMS bars against a draggable
threshold, reject outliers and recalibrate (cached detections, fast), then
Accept to write the ``opencv_yaml`` and hand it to the project draft. All
numerics live in the Qt-free :mod:`al_dic_3d.calibration`; this file is view
code only (worker/bars/preview helpers: :mod:`.calibration_support`).

G3.7 polish: repeated Add picks dedupe + natural-sort, the detection preview
strip enlarges into a zoomable dialog on click, and board-parameter edits
re-run detection on the selected pair (debounced) so the preview follows the
spec live.
"""

from __future__ import annotations

import numpy as np
from al_dic.gui.theme import COLORS
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.calibration import detect_board, to_opencv_yaml
from al_dic_3d.gui import persistence
from al_dic_3d.gui.dialogs.calibration_support import (
    CalibWorker,
    DetectionZoomDialog,
    PairBars,
    int_spin,
    merge_picks,
    mm_spin,
    pair_strip,
    section_label,
    strip_to_pixmap,
)

_BOARD_CHESS, _BOARD_CHARUCO, _BOARD_CIRCLES, _BOARD_CODED = (
    "chessboard",
    "charuco",
    "circles",
    "coded",
)

# Debounce for the live re-detect preview (G3.7c): board-spec spins arrive in
# bursts while typing/scrolling; re-detecting per keystroke would stutter.
_LIVE_PREVIEW_DEBOUNCE_MS = 400


class _ClickableLabel(QLabel):
    """QLabel emitting ``clicked`` on left release (preview enlarge, G3.7a)."""

    clicked = Signal()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class CalibrationDialog(QDialog):
    """Image pairs -> board spec -> QC'd stereo solve -> opencv_yaml."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Stereo Calibration"))
        self.setMinimumSize(900, 690)
        self.saved_path = None  # Path once the user accepts a solve

        self._files_l: list[str] = []
        self._files_r: list[str] = []
        self._detections = None  # (dl, dr) cache for fast recalibrate
        self._cached_size = None  # (w, h) from loaded detections (images optional)
        self._result = None
        self._stats = None
        self._worker: CalibWorker | None = None
        self._preview_idx: int | None = None  # pair shown in the preview strip
        self._preview_dets = None  # (det_l, det_r) behind the shown preview

        # G3.7c: debounced re-detect of the selected pair on board-spec edits.
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(_LIVE_PREVIEW_DEBOUNCE_MS)
        self._preview_timer.timeout.connect(self._refresh_live_preview)

        root = QHBoxLayout(self)
        root.setSpacing(12)
        root.addLayout(self._build_left(), stretch=3)
        root.addLayout(self._build_right(), stretch=2)
        self._connect_live_preview()
        self._on_board_changed()

    # ---- left column: images + QC ------------------------------------------

    def _build_left(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.addWidget(section_label(self.tr("CALIBRATION IMAGE PAIRS"), self))

        pick = QHBoxLayout()
        left_btn = QPushButton(self.tr("Add left images…"))
        left_btn.clicked.connect(lambda: self._pick_files("L"))
        right_btn = QPushButton(self.tr("Add right images…"))
        right_btn.clicked.connect(lambda: self._pick_files("R"))
        clear_btn = QPushButton(self.tr("Clear"))
        clear_btn.clicked.connect(self._clear_files)
        self._save_det_btn = QPushButton(self.tr("Save detections…"))
        self._save_det_btn.setEnabled(False)
        self._save_det_btn.clicked.connect(self._on_save_detections)
        load_det_btn = QPushButton(self.tr("Load detections…"))
        load_det_btn.clicked.connect(self._on_load_detections)
        for b in (left_btn, right_btn, clear_btn, self._save_det_btn, load_det_btn):
            pick.addWidget(b)
        pick.addStretch()
        col.addLayout(pick)

        self._pairs_lbl = QLabel(self.tr("No images loaded"))
        self._pairs_lbl.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 11px;")
        col.addWidget(self._pairs_lbl)

        self._table = QTreeWidget()
        self._table.setHeaderLabels(
            [
                "#",
                self.tr("Left"),
                self.tr("Right"),
                self.tr("Points"),
                self.tr("RMS L/R"),
                self.tr("Max E"),
                self.tr("Status"),
            ]
        )
        self._table.setRootIsDecorated(False)
        self._table.setColumnWidth(0, 32)
        self._table.setColumnWidth(3, 60)
        self._table.setColumnWidth(4, 90)
        self._table.setColumnWidth(5, 60)
        self._table.currentItemChanged.connect(self._on_row_selected)
        col.addWidget(self._table, stretch=1)

        col.addWidget(section_label(self.tr("SELECTED PAIR (L | R)"), self))
        self._preview = _ClickableLabel(self.tr("select a pair to preview detected points"))
        self._preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview.setFixedHeight(150)
        self._preview.setStyleSheet(
            f"background: {COLORS.BG_PANEL}; color: {COLORS.TEXT_MUTED}; font-size: 11px;"
        )
        self._preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self._preview.setToolTip(self.tr("Click to enlarge the annotated detection"))
        self._preview.clicked.connect(self._open_preview_zoom)
        col.addWidget(self._preview)

        col.addWidget(section_label(self.tr("PER-PAIR REPROJECTION ERROR"), self))
        self._bars = PairBars()
        col.addWidget(self._bars)

        reject_row = QHBoxLayout()
        thr_lbl = QLabel(self.tr("Reject threshold (px)"))
        thr_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        reject_row.addWidget(thr_lbl)
        self._thr_spin = QDoubleSpinBox()
        self._thr_spin.setRange(0.05, 50.0)
        self._thr_spin.setSingleStep(0.1)
        self._thr_spin.setValue(1.0)
        self._thr_spin.setDecimals(2)
        reject_row.addWidget(self._thr_spin)
        self._recal_btn = QPushButton(self.tr("Recalibrate"))
        self._recal_btn.setEnabled(False)
        self._recal_btn.clicked.connect(lambda: self._start(recalibrate=True))
        reject_row.addWidget(self._recal_btn)
        reject_row.addStretch()
        col.addLayout(reject_row)
        return col

    # ---- right column: board + options + results -----------------------------

    def _build_right(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.addWidget(section_label(self.tr("CALIBRATION BOARD"), self))

        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setVerticalSpacing(4)

        self._board_combo = QComboBox()
        self._board_combo.addItem(self.tr("Chessboard"), _BOARD_CHESS)
        self._board_combo.addItem(self.tr("ChArUco"), _BOARD_CHARUCO)
        self._board_combo.addItem(self.tr("Circle grid"), _BOARD_CIRCLES)
        self._board_combo.addItem(self.tr("Coded dot target (3 ring markers)"), _BOARD_CODED)
        self._board_combo.currentIndexChanged.connect(self._on_board_changed)
        grid.addWidget(QLabel(self.tr("Type")), 0, 0)
        grid.addWidget(self._board_combo, 0, 1)

        self._cols = int_spin(3, 99, 9)
        self._rows = int_spin(3, 99, 7)
        grid.addWidget(QLabel(self.tr("Columns x Rows")), 1, 0)
        cr = QHBoxLayout()
        cr.addWidget(self._cols)
        cr.addWidget(self._rows)
        grid.addLayout(cr, 1, 1)

        self._square = mm_spin(12.0)
        self._sq_lbl = QLabel(self.tr("Square size (mm)"))
        grid.addWidget(self._sq_lbl, 2, 0)
        grid.addWidget(self._square, 2, 1)

        self._marker = mm_spin(9.0)
        self._marker_lbl = QLabel(self.tr("Marker size (mm)"))
        grid.addWidget(self._marker_lbl, 3, 0)
        grid.addWidget(self._marker, 3, 1)

        self._spacing = mm_spin(12.0)
        self._sp_lbl = QLabel(self.tr("Dot pitch (mm)"))
        grid.addWidget(self._sp_lbl, 4, 0)
        grid.addWidget(self._spacing, 4, 1)

        self._dot = mm_spin(6.0)
        self._dot_lbl = QLabel(self.tr("Dot diameter (mm)"))
        grid.addWidget(self._dot_lbl, 5, 0)
        grid.addWidget(self._dot, 5, 1)

        self._asym = QCheckBox(self.tr("Asymmetric grid"))
        grid.addWidget(self._asym, 6, 1)
        self._legacy = QCheckBox(self.tr("Board printed with OpenCV < 4.7"))
        grid.addWidget(self._legacy, 7, 1)
        col.addWidget(grid_host)

        self._print_btn = QPushButton(self.tr("Print board… (1:1 PDF)"))
        self._print_btn.clicked.connect(self._on_print_board)
        col.addWidget(self._print_btn)

        col.addWidget(section_label(self.tr("SOLVER OPTIONS"), self))
        self._joint = QCheckBox(self.tr("Jointly refine intrinsics (advanced)"))
        self._tangential = QCheckBox(self.tr("Estimate tangential distortion p1/p2"))
        self._fix_k3 = QCheckBox(self.tr("Fix k3 = 0 (low-distortion lens)"))
        self._release = QCheckBox(self.tr("Release-object method (printed boards)"))
        self._ecc = QCheckBox(self.tr("Dot eccentricity correction"))
        self._ecc.setChecked(True)
        self._bundle = QCheckBox(self.tr("Joint bundle adjustment (robust, uses mono views)"))
        self._morph = QCheckBox(self.tr("Optimize board shape (printed boards)"))
        self._morph.setEnabled(False)
        self._bundle.toggled.connect(self._morph.setEnabled)
        self._bundle.toggled.connect(lambda on: not on and self._morph.setChecked(False))
        for cb in (
            self._joint,
            self._tangential,
            self._fix_k3,
            self._release,
            self._ecc,
            self._bundle,
            self._morph,
        ):
            col.addWidget(cb)

        self._calib_btn = QPushButton(self.tr("Calibrate"))
        self._calib_btn.setProperty("class", "btn-primary")
        self._calib_btn.setFixedHeight(34)
        self._calib_btn.clicked.connect(lambda: self._start(recalibrate=False))
        col.addWidget(self._calib_btn)

        self._status = QLabel("")
        self._status.setWordWrap(True)
        self._status.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 11px;")
        col.addWidget(self._status)

        col.addWidget(section_label(self.tr("RESULT"), self))
        self._result_lbl = QLabel(self.tr("No calibration yet"))
        self._result_lbl.setWordWrap(True)
        self._result_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 12px;")
        col.addWidget(self._result_lbl)

        self._verify_btn = QPushButton(self.tr("Verify with board images…"))
        self._verify_btn.setEnabled(False)
        self._verify_btn.clicked.connect(self._on_verify)
        col.addWidget(self._verify_btn)
        self._verify_lbl = QLabel("")
        self._verify_lbl.setWordWrap(True)
        self._verify_lbl.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 11px;")
        col.addWidget(self._verify_lbl)
        col.addStretch()

        buttons = QHBoxLayout()
        buttons.addStretch()
        self._accept_btn = QPushButton(self.tr("Accept && Save…"))
        self._accept_btn.setProperty("class", "btn-primary")
        self._accept_btn.setFixedHeight(32)
        self._accept_btn.setEnabled(False)
        self._accept_btn.clicked.connect(self._on_accept)
        buttons.addWidget(self._accept_btn)
        cancel = QPushButton(self.tr("Cancel"))
        cancel.setFixedHeight(32)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        col.addLayout(buttons)
        return col

    # ---- board spec -----------------------------------------------------------

    def _on_board_changed(self) -> None:
        board = self._board_combo.currentData()
        chessy = board in (_BOARD_CHESS, _BOARD_CHARUCO)
        for w in (self._square, self._sq_lbl):
            w.setVisible(chessy)
        for w in (self._marker, self._marker_lbl):
            w.setVisible(board == _BOARD_CHARUCO)
        self._legacy.setVisible(board == _BOARD_CHARUCO)
        for w in (self._spacing, self._sp_lbl, self._dot, self._dot_lbl):
            w.setVisible(not chessy)
        self._asym.setVisible(board == _BOARD_CIRCLES)
        self._ecc.setVisible(not chessy)

    def _board_spec(self):
        from al_dic_3d.calibration import (
            CharucoSpec,
            ChessboardSpec,
            CircleGridSpec,
            CodedCircleGridSpec,
        )

        board = self._board_combo.currentData()
        cols, rows = self._cols.value(), self._rows.value()
        if board == _BOARD_CHESS:
            return ChessboardSpec(cols=cols, rows=rows, square_size=self._square.value())
        if board == _BOARD_CHARUCO:
            return CharucoSpec(
                squares_x=cols,
                squares_y=rows,
                square_size=self._square.value(),
                marker_size=self._marker.value(),
                legacy_pattern=self._legacy.isChecked(),
            )
        if board == _BOARD_CIRCLES:
            return CircleGridSpec(
                cols=cols,
                rows=rows,
                spacing=self._spacing.value(),
                asymmetric=self._asym.isChecked(),
                dot_diameter=self._dot.value(),
            )
        return CodedCircleGridSpec(
            cols=cols, rows=rows, spacing=self._spacing.value(), dot_diameter=self._dot.value()
        )

    # ---- files ---------------------------------------------------------------

    def _pick_files(self, cam: str) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            self.tr("Choose {0} calibration images").format(cam),
            persistence.last_dir("calibration_images"),
            self.tr("Images (*.png *.tif *.tiff *.bmp *.jpg *.jpeg)"),
        )
        if not files:
            return
        persistence.set_last_dir("calibration_images", files[0])
        # G3.7b: repeated Add picks dedupe; the merged list is natural-sorted.
        if cam == "L":
            self._files_l = merge_picks(self._files_l, files)
        else:
            self._files_r = merge_picks(self._files_r, files)
        self._detections = None
        self._refresh_table()

    def _clear_files(self) -> None:
        self._files_l.clear()
        self._files_r.clear()
        self._detections = None
        self._cached_size = None
        self._result = None
        self._preview_idx = None
        self._preview_dets = None
        # setText drops any pixmap, restoring the placeholder caption.
        self._preview.setText(self.tr("select a pair to preview detected points"))
        self._refresh_table()

    def _refresh_table(self) -> None:
        from pathlib import Path

        self._table.clear()
        n = max(len(self._files_l), len(self._files_r))
        for k in range(n):
            item = QTreeWidgetItem(
                [
                    str(k + 1),
                    Path(self._files_l[k]).name if k < len(self._files_l) else "—",
                    Path(self._files_r[k]).name if k < len(self._files_r) else "—",
                    "",
                    "",
                    "",
                    "",
                ]
            )
            self._table.addTopLevelItem(item)
        self._save_det_btn.setEnabled(self._detections is not None)
        ok = len(self._files_l) == len(self._files_r) and self._files_l
        self._pairs_lbl.setText(
            self.tr("{0} left / {1} right images").format(len(self._files_l), len(self._files_r))
        )
        self._pairs_lbl.setStyleSheet(
            f"color: {COLORS.SUCCESS if ok else COLORS.WARNING}; font-size: 11px;"
        )

    # ---- solve ----------------------------------------------------------------

    def _start(self, *, recalibrate: bool) -> None:
        if len(self._files_l) != len(self._files_r) or len(self._files_l) < 3:
            self._set_status(self.tr("Load equal, >= 3 left/right image sets first."), warn=True)
            return
        try:
            spec = self._board_spec()
        except ValueError as exc:
            self._set_status(str(exc), warn=True)
            return
        dot_mm = getattr(spec, "dot_mm", None)
        options = dict(
            joint_refine=self._joint.isChecked(),
            zero_tangent=not self._tangential.isChecked(),
            fix_k3=self._fix_k3.isChecked(),
            release_object=self._release.isChecked(),
            reject_rms=self._thr_spin.value(),
            dot_radius_mm=(dot_mm / 2.0 if dot_mm and self._ecc.isChecked() else None),
            bundle=self._bundle.isChecked(),
            board_morphology=self._morph.isChecked(),
        )
        cached = self._detections if recalibrate else None
        self._calib_btn.setEnabled(False)
        self._recal_btn.setEnabled(False)
        self._worker = CalibWorker(
            list(self._files_l),
            list(self._files_r),
            spec,
            options,
            cached,
            image_size=(self._cached_size if recalibrate else None),
            parent=self,
        )
        self._worker.progress.connect(
            lambda msg: self._set_status(self.tr("Working… {0}").format(msg))
        )
        self._worker.finished_ok.connect(self._on_solved)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_failed(self, msg: str) -> None:
        self._calib_btn.setEnabled(True)
        self._recal_btn.setEnabled(self._detections is not None)
        self._set_status(self.tr("Calibration failed: {0}").format(msg), warn=True)

    def _on_solved(self, payload) -> None:
        dl, dr, result, stats = payload
        self._detections = (dl, dr)
        self._result = result
        self._stats = stats
        self._calib_btn.setEnabled(True)
        self._recal_btn.setEnabled(True)
        self._accept_btn.setEnabled(True)
        self._set_status("")

        pair_max = stats.get("pair_max", {})
        for k, pair in enumerate(result.pairs):
            item = self._table.topLevelItem(k)
            if item is None:
                continue
            det_l, det_r = dl[k], dr[k]
            pts = f"{det_l.n_points}/{det_r.n_points}"
            item.setText(3, pts)
            if pair.n_common and np.isfinite(pair.rms_left):
                item.setText(4, f"{pair.rms_left:.3f}/{pair.rms_right:.3f}")
            if pair.index in pair_max:
                item.setText(5, f"{pair_max[pair.index]:.3f}")
            status = self.tr("used") if pair.used else pair.note
            if not det_l.ok:
                status = self.tr("L: {0}").format(det_l.reason)
            elif not det_r.ok:
                status = self.tr("R: {0}").format(det_r.reason)
            item.setText(6, status)
            color = QColor(COLORS.TEXT_PRIMARY if pair.used else COLORS.DANGER)
            for c in range(7):
                item.setForeground(c, color)
        self._save_det_btn.setEnabled(True)

        self._verify_btn.setEnabled(True)
        if self._table.currentItem() is None and self._table.topLevelItemCount():
            self._table.setCurrentItem(self._table.topLevelItem(0))
        else:
            self._on_row_selected(self._table.currentItem())

        self._bars.set_data(result.pairs, self._thr_spin.value())
        left = result.rig.cameras["L"]
        lines = [
            self.tr("Stereo RMS {0:.3f} px | epipolar {1:.3f} px").format(
                result.rms, result.epipolar_rms
            ),
            self.tr("Baseline {0:.2f} mm | pairs {1}/{2}").format(
                result.baseline, result.n_pairs_used, len(result.pairs)
            ),
            self.tr("fx {0:.1f}  fy {1:.1f}  cx {2:.1f}  cy {3:.1f}").format(
                left.fx, left.fy, left.cx, left.cy
            ),
            self.tr("Coverage L {0:.0%} / R {1:.0%} | tilt {2:.0f}-{3:.0f}°").format(
                stats["coverage_left"],
                stats["coverage_right"],
                stats["tilt_min_deg"],
                stats["tilt_max_deg"],
            ),
        ]
        if "ba_rms_after" in stats:
            lines.append(
                self.tr("Bundle adjustment: RMS {0:.3f} -> {1:.3f} px ({2:.0f} mono views)").format(
                    stats["ba_rms_before"], stats["ba_rms_after"], stats["ba_mono_views"]
                )
            )
        if "ba_board_z_range" in stats:
            lines.append(
                self.tr("Board flatness: z-range {0:.3f} mm").format(stats["ba_board_z_range"])
            )
        for w in result.warnings:
            lines.append(self.tr("Warning: {0}").format(w))
        self._result_lbl.setText("\n".join(lines))
        self._result_lbl.setStyleSheet(f"color: {COLORS.SUCCESS}; font-size: 12px;")

    def _set_status(self, text: str, *, warn: bool = False) -> None:
        self._status.setText(text)
        color = COLORS.WARNING if warn else COLORS.TEXT_MUTED
        self._status.setStyleSheet(f"color: {color}; font-size: 11px;")

    # ---- detections persistence ------------------------------------------------

    def _on_save_detections(self) -> None:
        if self._detections is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Save detections"), "detections.npz", self.tr("NumPy detections (*.npz)")
        )
        if not path:
            return
        from al_dic_3d.calibration import save_detections
        from al_dic_3d.pathsafe import imread_unicode

        dl, dr = self._detections
        size = self._cached_size
        if size is None:
            first = imread_unicode(self._files_l[0])
            if first is not None:
                size = (first.shape[1], first.shape[0])
        out = save_detections(path, self._files_l, self._files_r, dl, dr, image_size=size)
        self._set_status(self.tr("Detections saved: {0}").format(out))

    def _on_load_detections(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Load detections"), "", self.tr("NumPy detections (*.npz)")
        )
        if not path:
            return
        from al_dic_3d.calibration import load_detections

        try:
            files_l, files_r, dl, dr, size = load_detections(path)
        except (ValueError, OSError) as exc:
            self._set_status(str(exc), warn=True)
            return
        self._files_l, self._files_r = files_l, files_r
        self._detections = (dl, dr)
        self._cached_size = size
        self._refresh_table()
        for k, (det_l, det_r) in enumerate(zip(dl, dr, strict=True)):
            item = self._table.topLevelItem(k)
            if item is not None:
                item.setText(3, f"{det_l.n_points}/{det_r.n_points}")
        self._recal_btn.setEnabled(True)
        self._set_status(
            self.tr(
                "Loaded {0} detection pairs — Recalibrate re-solves without re-detecting"
            ).format(len(dl))
        )

    # ---- preview (strip + click-to-enlarge + live re-detect, G3.7) --------------

    def _on_row_selected(self, current, _previous=None) -> None:
        if current is None:
            return
        k = self._table.indexOfTopLevelItem(current)
        if 0 <= k < min(len(self._files_l), len(self._files_r)):
            self._render_preview(k)

    def _pair_dets(self, k: int):
        """(det_l, det_r) for pair ``k`` from the solve cache (None, None if absent)."""
        dl, dr = self._detections if self._detections else (None, None)
        det_l = dl[k] if dl is not None and k < len(dl) else None
        det_r = dr[k] if dr is not None and k < len(dr) else None
        return det_l, det_r

    def _render_preview(self, k: int, dets_override=None) -> None:
        """Side-by-side L|R panel of pair ``k`` with detected points overlaid."""
        det_l, det_r = dets_override if dets_override is not None else self._pair_dets(k)
        strip = pair_strip(self._files_l[k], self._files_r[k], det_l, det_r, height=142)
        self._preview.setPixmap(strip_to_pixmap(strip))
        self._preview_idx = k
        self._preview_dets = (det_l, det_r)

    def _open_preview_zoom(self) -> None:
        """G3.7a: enlarge the preview into a zoomable full-size dialog."""
        k = self._preview_idx
        if k is None or k >= min(len(self._files_l), len(self._files_r)):
            return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            det_l, det_r = self._preview_dets or (None, None)
            strip = pair_strip(self._files_l[k], self._files_r[k], det_l, det_r, height=None)
            pixmap = strip_to_pixmap(strip)
        finally:
            QApplication.restoreOverrideCursor()
        DetectionZoomDialog(pixmap, k, self).show()

    def _connect_live_preview(self) -> None:
        """G3.7c: board-spec edits schedule a debounced preview re-detect."""
        schedule = self._schedule_live_preview
        self._board_combo.currentIndexChanged.connect(schedule)
        for spin in (self._cols, self._rows, self._square, self._marker, self._spacing, self._dot):
            spin.valueChanged.connect(schedule)
        for cb in (self._asym, self._legacy):
            cb.toggled.connect(schedule)

    def _schedule_live_preview(self, *_a) -> None:
        if self._preview_idx is not None:
            self._preview_timer.start()

    def _refresh_live_preview(self) -> None:
        """Re-detect the SELECTED pair with the current board spec (preview only)."""
        from al_dic_3d.pathsafe import imread_unicode

        k = self._preview_idx
        if k is None or k >= min(len(self._files_l), len(self._files_r)):
            return
        try:
            spec = self._board_spec()
        except ValueError:
            return  # incomplete spec — keep the last preview
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            dets = []
            for path in (self._files_l[k], self._files_r[k]):
                img = imread_unicode(path)
                dets.append(detect_board(img, spec) if img is not None else None)
            self._render_preview(k, dets_override=tuple(dets))
        except Exception:  # noqa: BLE001 - a live preview must never break the dialog
            pass
        finally:
            QApplication.restoreOverrideCursor()

    # ---- print / verify ----------------------------------------------------------

    def _on_print_board(self) -> None:
        try:
            spec = self._board_spec()
        except ValueError as exc:
            self._set_status(str(exc), warn=True)
            return
        path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Save board PDF"), "board.pdf", self.tr("PDF (*.pdf)")
        )
        if not path:
            return
        from al_dic_3d.calibration import save_board_pdf

        try:
            out = save_board_pdf(spec, path)
        except ValueError as exc:  # board exceeds the page
            self._set_status(str(exc), warn=True)
            return
        self._set_status(self.tr("Board PDF written: {0}").format(out))

    def _on_verify(self) -> None:
        """iDICs independent check: known distances on a fresh board pair."""
        from al_dic_3d.calibration import verify_known_distance
        from al_dic_3d.pathsafe import imread_unicode

        if self._result is None:
            return
        try:
            spec = self._board_spec()
        except ValueError as exc:
            self._set_status(str(exc), warn=True)
            return
        filt = self.tr("Images (*.png *.tif *.tiff *.bmp *.jpg *.jpeg)")
        path_l, _ = QFileDialog.getOpenFileName(
            self, self.tr("Choose LEFT verification image"), "", filt
        )
        if not path_l:
            return
        path_r, _ = QFileDialog.getOpenFileName(
            self, self.tr("Choose RIGHT verification image"), "", filt
        )
        if not path_r:
            return
        try:
            det_l = detect_board(imread_unicode(path_l), spec)
            det_r = detect_board(imread_unicode(path_r), spec)
            v = verify_known_distance(self._result.rig, det_l, det_r, spec)
        except (ValueError, TypeError) as exc:
            self._verify_lbl.setText(self.tr("Verification failed: {0}").format(exc))
            self._verify_lbl.setStyleSheet(f"color: {COLORS.DANGER}; font-size: 11px;")
            return
        good = abs(v.scale_error) < 1e-3
        self._verify_lbl.setText(
            self.tr(
                "Verify: pitch {0:.4f} mm vs {1:g} mm — scale error {2:.3%}, plane RMS {3:.4f} mm"
            ).format(v.pitch_measured, v.pitch_true, v.scale_error, v.plane_rms)
        )
        self._verify_lbl.setStyleSheet(
            f"color: {COLORS.SUCCESS if good else COLORS.WARNING}; font-size: 11px;"
        )

    # ---- accept ---------------------------------------------------------------

    def _on_accept(self) -> None:
        if self._result is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save calibration as"),
            "calibration.yml",
            self.tr("OpenCV YAML (*.yml *.yaml *.xml)"),
        )
        if not path:
            return
        meta = {
            "source": "al-dic-3d gui calibrate",
            "board": str(self._board_combo.currentData()),
            "rms_px": self._result.rms,
            "epipolar_rms_px": self._result.epipolar_rms,
            "n_pairs_used": self._result.n_pairs_used,
        }
        self.saved_path = to_opencv_yaml(self._result.rig, path, meta=meta)
        self.accept()
