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

New-user path: the board form says what each size counts and remembers the
last board (:mod:`.calibration_board`); the table shows every image's
detection even when the solve fails, and a board found in too few images is
reported as what to check first; each camera keeps its own image size; the
result names the range of board distances (a wrong square size shows as a
wrong distance); Cancel asks before discarding an unsaved calibration.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from al_dic.gui.theme import COLORS
from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.calibration import MixedImageSizeError, detect_board, to_opencv_yaml
from al_dic_3d.calibration.diagnostics import coverage_outline
from al_dic_3d.calibration.solve import MIN_STEREO_PAIRS
from al_dic_3d.gui import persistence
from al_dic_3d.gui.calibration_findings import findings_lines, result_colour
from al_dic_3d.gui.dialogs.calibration_board import BoardFormMixin
from al_dic_3d.gui.dialogs.calibration_support import (
    CalibWorker,
    DetectionFilesMixin,
    DetectionZoomDialog,
    PairBars,
    fill_pair_row,
    merge_picks,
    pair_strip,
    section_label,
    strip_to_pixmap,
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


class _PreviewRelay(QObject):
    """Carries a background detection result back to the GUI thread."""

    done = Signal(int, int, object)  # generation, pair index, (det_l, det_r)


class CalibrationDialog(BoardFormMixin, DetectionFilesMixin, QDialog):
    """Image pairs -> board spec -> QC'd stereo solve -> opencv_yaml."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Stereo Calibration"))
        self.setMinimumSize(900, 690)
        self.saved_path = None  # Path once the user accepts a solve

        self._files_l: list[str] = []
        self._files_r: list[str] = []
        self._detections = None  # (dl, dr) cache for fast recalibrate
        self._cached_sizes = None  # ((w, h) left, (w, h) right): Recalibrate reads no image
        self._result = None
        self._diagnostics = None  # the calibration diagnostics of the last solve
        self._stats = None
        self._worker: CalibWorker | None = None
        self._preview_idx: int | None = None  # pair shown in the preview strip
        self._preview_dets = None  # (det_l, det_r) behind the shown preview

        # Fix batch V: the live re-detect runs on one background thread (it
        # used to block the GUI for a full two-image board detection); only the
        # newest request is shown.
        self._preview_gen = 0
        self._preview_pool = None
        self._preview_relay = _PreviewRelay(self)
        self._preview_relay.done.connect(self._on_live_preview_done)
        # G3.7c: debounced re-detect of the selected pair on board-spec edits.
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(_LIVE_PREVIEW_DEBOUNCE_MS)
        self._preview_timer.timeout.connect(self._refresh_live_preview)

        root = QHBoxLayout(self)
        root.setSpacing(12)
        root.addLayout(self._build_left(), stretch=3)
        root.addLayout(self._build_right(), stretch=2)
        self._restore_board()  # the last session's board, before the live preview listens
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
        col.addWidget(self._build_board_form())

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
        self._cached_sizes = None
        self._refresh_table()

    def _clear_files(self) -> None:
        self._files_l.clear()
        self._files_r.clear()
        self._detections = None
        self._cached_sizes = None
        self._result = None
        self._diagnostics = None
        self._preview_idx = None
        self._preview_dets = None
        # setText drops any pixmap, restoring the placeholder caption.
        self._preview.setText(self.tr("select a pair to preview detected points"))
        self._refresh_table()

    def _refresh_table(self) -> None:
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
        n_l, n_r = len(self._files_l), len(self._files_r)
        if n_l != n_r or n_l < MIN_STEREO_PAIRS:  # the solve needs this many usable pairs
            self._set_status(
                self.tr(
                    "Load the same number of left and right images, at least {0} pairs: "
                    "the solve needs {0} usable pairs."
                ).format(MIN_STEREO_PAIRS),
                warn=True,
            )
            return
        try:
            spec = self._board_spec()
        except ValueError as exc:
            self._set_status(str(exc), warn=True)
            return
        self._remember_board()
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
            image_sizes=(self._cached_sizes if recalibrate else None),
            parent=self,
        )
        self._worker.progress.connect(
            lambda msg: self._set_status(self.tr("Working… {0}").format(msg))
        )
        self._worker.detected.connect(self._on_detected)
        self._worker.finished_ok.connect(self._on_solved)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _detection_status(self, det_l, det_r) -> str:
        if not det_l.ok:
            return self.tr("L: {0}").format(det_l.reason)
        if not det_r.ok:
            return self.tr("R: {0}").format(det_r.reason)
        return ""

    def _on_detected(self, payload) -> None:
        """Fresh detections, before the solve: each image's result shows even if it fails."""
        dl, dr = payload
        self._detections = (dl, dr)
        self._cached_sizes = None  # the solve sets them
        self._result = self._diagnostics = None  # a new image set: the old solve is void
        self._accept_btn.setEnabled(False)
        self._verify_btn.setEnabled(False)
        self._bars.set_data((), self._thr_spin.value())
        self._result_lbl.setText(self.tr("No calibration yet"))
        self._result_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 12px;")
        for k, (det_l, det_r) in enumerate(zip(dl, dr, strict=False)):
            item = self._table.topLevelItem(k)
            if item is not None:
                for column in (4, 5):
                    item.setText(column, "")
                fill_pair_row(
                    item, det_l, det_r, self._detection_status(det_l, det_r), det_l.ok and det_r.ok
                )
        self._save_det_btn.setEnabled(True)

    def _on_failed(self, msg: str) -> None:
        error = getattr(self._worker, "error", None)
        shortfall = None
        if isinstance(error, MixedImageSizeError):
            text = self._mixed_size_text(error)
        else:
            if self._detections is not None:
                shortfall = self._shortfall_text(*self._detections, MIN_STEREO_PAIRS)
            text = shortfall or self.tr("Calibration failed: {0}").format(msg)
        self._calib_btn.setEnabled(True)
        # Re-solving detections that do not show the board would fail again.
        self._recal_btn.setEnabled(self._detections is not None and shortfall is None)
        self._set_status(text, warn=True)

    def _on_solved(self, payload) -> None:
        dl, dr, result, stats = payload
        self._diagnostics = stats.pop("diagnostics", None)
        self._detections = (dl, dr)
        self._result = result
        self._stats = stats
        # Each camera's size from the solve: Recalibrate and Save detections read no image.
        self._cached_sizes = tuple(
            (result.rig.cameras[cam].width, result.rig.cameras[cam].height) for cam in ("L", "R")
        )
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
            if pair.n_common and np.isfinite(pair.rms_left):
                item.setText(4, f"{pair.rms_left:.3f}/{pair.rms_right:.3f}")
            if pair.index in pair_max:
                item.setText(5, f"{pair_max[pair.index]:.3f}")
            status = self._detection_status(det_l, det_r) or (
                self.tr("used") if pair.used else pair.note
            )
            fill_pair_row(item, det_l, det_r, status, pair.used)
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
        ]
        lo, hi = stats.get("distance_min", np.nan), stats.get("distance_max", np.nan)
        if np.isfinite(lo) and np.isfinite(hi):  # a wrong square size shows as a wrong distance
            lines.append(
                self.tr("Board distance from the left camera {0:.0f}-{1:.0f} mm").format(lo, hi)
            )
        lines += [
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
        lines += findings_lines(self._diagnostics)  # WP6: translated from code + values
        self._result_lbl.setText("\n".join(lines))
        colour = result_colour(self._diagnostics, warnings=result.warnings)
        self._result_lbl.setStyleSheet(f"color: {colour}; font-size: 12px;")

    def _set_status(self, text: str, *, warn: bool = False) -> None:
        self._status.setText(text)
        color = COLORS.WARNING if warn else COLORS.TEXT_MUTED
        self._status.setStyleSheet(f"color: {color}; font-size: 11px;")

    # ---- detections persistence ------------------------------------------------

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

    def _coverage_outlines(self) -> dict:
        """Covered-radius outline per camera (px) once solved, else empty."""
        diag, result = getattr(self, "_diagnostics", None), self._result
        if diag is None or result is None:
            return {}
        return {
            cam: coverage_outline(result.rig.cameras[cam], d.r_cover)
            for cam, d in diag.cameras.items()
        }

    def _render_preview(self, k: int, dets_override=None) -> None:
        """Side-by-side L|R panel of pair ``k`` with detected points overlaid."""
        det_l, det_r = dets_override if dets_override is not None else self._pair_dets(k)
        strip = pair_strip(
            self._files_l[k], self._files_r[k], det_l, det_r, 142, self._coverage_outlines()
        )
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
            strip = pair_strip(
                self._files_l[k], self._files_r[k], det_l, det_r, None, self._coverage_outlines()
            )
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

    def _default_dir(self) -> Path:
        """Where file dialogs start: the board images' folder, else the last one.

        Fix batch V: they proposed a bare file name, i.e. the process's working
        directory (the same fix 2D made in 0.8.0).
        """
        from al_dic_3d.gui import persistence

        if self._files_l:
            return Path(self._files_l[0]).parent
        return Path(persistence.last_dir("calibration") or Path.home())

    def _refresh_live_preview(self) -> None:
        """Re-detect the SELECTED pair with the current board spec, off the GUI thread."""
        from al_dic_3d.pathsafe import imread_unicode

        k = self._preview_idx
        if k is None or k >= min(len(self._files_l), len(self._files_r)):
            return
        try:
            spec = self._board_spec()
        except ValueError:
            return  # incomplete spec — keep the last preview
        self._preview_gen += 1
        gen, paths = self._preview_gen, (self._files_l[k], self._files_r[k])
        if self._preview_pool is None:
            from concurrent.futures import ThreadPoolExecutor

            self._preview_pool = ThreadPoolExecutor(max_workers=1)

        def job() -> None:
            try:
                dets = []
                for path in paths:
                    img = imread_unicode(path)
                    dets.append(detect_board(img, spec) if img is not None else None)
                self._preview_relay.done.emit(gen, k, tuple(dets))
            except Exception:  # noqa: BLE001 - a live preview must never break the dialog
                return

        self._preview_pool.submit(job)

    def _on_live_preview_done(self, gen: int, k: int, dets: object) -> None:
        if gen != self._preview_gen or k != self._preview_idx:
            return  # superseded by a newer edit or another selected pair
        try:
            self._render_preview(k, dets_override=dets)
        except Exception:  # noqa: BLE001 - a live preview must never break the dialog
            pass

    # ---- print / verify ----------------------------------------------------------

    def _on_print_board(self) -> None:
        try:
            spec = self._board_spec()
        except ValueError as exc:
            self._set_status(str(exc), warn=True)
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save board PDF"),
            str(self._default_dir() / "board.pdf"),
            self.tr("PDF (*.pdf)"),
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
            self, self.tr("Choose LEFT verification image"), str(self._default_dir()), filt
        )
        if not path_l:
            return
        path_r, _ = QFileDialog.getOpenFileName(
            self, self.tr("Choose RIGHT verification image"), str(Path(path_l).parent), filt
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
            str(self._default_dir() / "calibration.yml"),
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
        if self._diagnostics is not None:  # WP6: the findings travel with the file
            meta.update(self._diagnostics.summary())
        self.saved_path = to_opencv_yaml(self._result.rig, path, meta=meta)
        self.accept()

    def reject(self) -> None:
        """Cancel, Esc and the close button: ask before a finished calibration is lost."""
        if self._result is not None and self.saved_path is None and not self._confirm_discard():
            return
        super().reject()

    def _confirm_discard(self) -> bool:
        """True when the user agrees to discard the unsaved calibration (tests stub it)."""
        reply = QMessageBox.question(
            self,
            self.tr("Discard calibration?"),
            self.tr("This calibration has not been saved. Close the dialog and discard it?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes
