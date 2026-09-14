"""Support widgets/helpers for the stereo calibration dialog (D12 + G3.7).

Extracted from ``calibration_dialog.py`` (file-size discipline): the detection
/ solve worker, the per-pair RMS bars, the annotated preview panel renderer,
small form helpers, the natural-sorting dedupe for repeated Add picks, and the
click-to-enlarge :class:`DetectionZoomDialog` (a zoomable ``ImageCanvas3D``
over the full-size annotated pair).
"""

from __future__ import annotations

import re

import numpy as np
from al_dic.gui.theme import COLORS
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.calibration import detect_board, run_calibration


class CalibWorker(QThread):
    """Detect (unless cached) + solve off the GUI thread."""

    progress = Signal(str)
    finished_ok = Signal(object)  # (detections_l, detections_r, StereoResult, stats)
    failed = Signal(str)

    def __init__(
        self, files_l, files_r, spec, options, detections=None, image_size=None, parent=None
    ) -> None:
        super().__init__(parent)
        self._files_l = files_l
        self._files_r = files_r
        self._spec = spec
        self._options = options
        self._detections = detections  # (dl, dr) to skip re-detection
        self._image_size = image_size  # known size lets us skip reading images

    def run(self) -> None:  # noqa: N802 (Qt override)
        from al_dic_3d.pathsafe import imread_unicode

        try:
            if self._detections is None:
                dl, dr = [], []
                for tag, files, out in (("L", self._files_l, dl), ("R", self._files_r, dr)):
                    for k, f in enumerate(files):
                        self.progress.emit(f"{tag} {k + 1}/{len(files)}")
                        img = imread_unicode(f)
                        if img is None:
                            raise ValueError(f"cannot read image: {f}")
                        out.append(detect_board(img, self._spec))
            else:
                dl, dr = self._detections
            if self._image_size is not None:
                image_size = self._image_size
            else:
                first = imread_unicode(self._files_l[0])
                if first is None:
                    raise ValueError(f"cannot read image: {self._files_l[0]}")
                image_size = (first.shape[1], first.shape[0])
            self.progress.emit("solving")
            # One pipeline with the CLI: solve, bundle adjustment (on the points
            # the solve used), diagnostics of the final calibration, summary.
            run = run_calibration(
                dl, dr, image_size, options=self._options, progress=self.progress.emit
            )
            result, stats = run.result, run.stats
            stats["diagnostics"] = run.diagnostics
            from al_dic_3d.calibration import pair_max_errors

            stats["pair_max"] = pair_max_errors(result, dl, dr)
            self.finished_ok.emit((dl, dr, result, stats))
        except Exception as exc:  # noqa: BLE001 - surfaced verbatim in the dialog
            self.failed.emit(str(exc))


class PairBars(QWidget):
    """Per-pair worst-camera RMS bars with a threshold line (MATLAB idiom)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pairs = ()  # tuple[PairQC, ...]
        self._threshold = 1.0
        self.setMinimumHeight(96)

    def set_data(self, pairs, threshold: float) -> None:
        self._pairs = tuple(pairs)
        self._threshold = float(threshold)
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802 (Qt override)
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(COLORS.BG_PANEL))
        if not self._pairs:
            p.setPen(QColor(COLORS.TEXT_MUTED))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.tr("no solve yet"))
            p.end()
            return
        vals = [
            0.0 if not np.isfinite(max(q.rms_left, q.rms_right)) else max(q.rms_left, q.rms_right)
            for q in self._pairs
        ]
        top = max(max(vals), self._threshold) * 1.25 or 1.0
        w, h = self.width(), self.height()
        margin, base = 4, h - 14
        bw = max(3.0, (w - 2 * margin) / max(1, len(vals)) - 2)
        for k, (q, v) in enumerate(zip(self._pairs, vals, strict=True)):
            x = margin + k * (bw + 2)
            bh = (v / top) * (base - 6)
            color = QColor(COLORS.ACCENT) if q.used else QColor(COLORS.DANGER)
            p.fillRect(int(x), int(base - bh), int(bw), int(max(1.0, bh)), color)
        y_thr = base - (self._threshold / top) * (base - 6)
        pen = QPen(QColor(COLORS.WARNING))
        pen.setStyle(Qt.PenStyle.DashLine)
        p.setPen(pen)
        p.drawLine(margin, int(y_thr), w - margin, int(y_thr))
        p.setPen(QColor(COLORS.TEXT_MUTED))
        p.drawText(6, h - 2, self.tr("worst-camera RMS per pair; dashed = reject threshold"))
        p.end()


# ---------------------------------------------------------------------------
# Annotated preview rendering + click-to-enlarge (G3.7a)
# ---------------------------------------------------------------------------


def overlay_panel(
    path: str, det, height: int | None = 142, outline: np.ndarray | None = None
) -> np.ndarray:
    """RGB panel of one image (scaled to ``height``; None = full size) with
    the detected points drawn, and ``outline`` (``(n, 2)`` px, closed) in amber:
    the radius the calibration points covered, when the calibration is solved."""
    import cv2

    from al_dic_3d.calibration.detect import to_gray_u8
    from al_dic_3d.pathsafe import imread_unicode

    fallback = max(1, height or 142)
    img = imread_unicode(path)
    if img is None:
        return np.full((fallback, fallback, 3), 20, dtype=np.uint8)
    gray = to_gray_u8(img)
    if height is None:
        scale, small = 1.0, gray
    else:
        scale = height / gray.shape[0]
        small = cv2.resize(
            gray, (max(1, int(gray.shape[1] * scale)), height), interpolation=cv2.INTER_AREA
        )
    rgb = cv2.cvtColor(small, cv2.COLOR_GRAY2RGB)
    if det is not None and det.ok:
        radius = 3 if height is not None else max(3, int(round(gray.shape[0] / 300)))
        for x, y in det.image_points * scale:
            cv2.circle(rgb, (int(round(x)), int(round(y))), radius, (74, 222, 128), 1, cv2.LINE_AA)
    if outline is not None and len(outline) > 2:
        pts = np.round(np.asarray(outline, np.float64) * scale).astype(np.int32)
        width = 1 if height is not None else max(1, int(round(gray.shape[0] / 600)))
        cv2.polylines(rgb, [pts.reshape(-1, 1, 2)], True, (251, 191, 36), width, cv2.LINE_AA)
    return rgb


def pair_strip(
    path_l: str, path_r: str, det_l, det_r, height: int | None = 142, outlines=None
) -> np.ndarray:
    """Side-by-side L|R annotated RGB strip (``height=None`` = full size).

    ``outlines`` maps ``"L"`` / ``"R"`` to the covered-radius outline in pixels.
    """
    import cv2

    outlines = outlines or {}
    panels = [
        overlay_panel(path_l, det_l, height, outlines.get("L")),
        overlay_panel(path_r, det_r, height, outlines.get("R")),
    ]
    h = max(p.shape[0] for p in panels)
    gap = np.full((h, 6, 3), 20, dtype=np.uint8)
    padded = [
        cv2.copyMakeBorder(p, 0, h - p.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(20, 20, 20))
        for p in panels
    ]
    return np.ascontiguousarray(np.hstack([padded[0], gap, padded[1]]))


def strip_to_pixmap(strip: np.ndarray) -> QPixmap:
    image = QImage(
        strip.data, strip.shape[1], strip.shape[0], 3 * strip.shape[1], QImage.Format_RGB888
    )
    return QPixmap.fromImage(image.copy())


class DetectionFilesMixin:
    """Save / load the detections of a calibration dialog (split out for the 800-line cap).

    Uses the dialog's ``_detections``, ``_files_l`` / ``_files_r``,
    ``_cached_size``, ``_default_dir``, ``_set_status``, ``_refresh_table``,
    ``_table`` and ``_recal_btn``.
    """

    def _on_save_detections(self) -> None:
        if self._detections is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save detections"),
            str(self._default_dir() / "detections.npz"),
            self.tr("NumPy detections (*.npz)"),
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
            self,
            self.tr("Load detections"),
            str(self._default_dir()),
            self.tr("NumPy detections (*.npz)"),
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


class DetectionZoomDialog(QDialog):
    """Resizable, zoomable full-size view of one annotated detection pair."""

    def __init__(self, pixmap: QPixmap, pair_index: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        from al_dic.gui.window_chrome import enable_dark_title_bar

        from al_dic_3d.gui.widgets.image_view import ImageCanvas3D

        self.setWindowTitle(self.tr("Detection preview — pair {0}").format(pair_index + 1))
        enable_dark_title_bar(self)
        self.resize(960, 560)
        self.setSizeGripEnabled(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        self.canvas = ImageCanvas3D()
        self.canvas.set_image_pixmap(f"detection-pair-{pair_index}", pixmap)
        layout.addWidget(self.canvas)
        hint = QLabel(self.tr("Wheel: zoom · Right/middle drag: pan"))
        hint.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 10px;")
        layout.addWidget(hint)


# ---------------------------------------------------------------------------
# File-pick merging (G3.7b) + small form helpers
# ---------------------------------------------------------------------------


def _natural_key(name: str) -> list:
    return [int(t) if t.isdigit() else t.lower() for t in re.findall(r"\d+|\D+", name)]


def merge_picks(existing: list[str], picked: list[str]) -> list[str]:
    """Dedupe repeated Add picks and natural-sort the merged list (G3.7b)."""
    from pathlib import Path

    merged = list(dict.fromkeys([*existing, *picked]))  # order-stable dedupe
    merged.sort(key=lambda p: _natural_key(Path(p).name))
    return merged


def section_label(text: str, parent: QWidget) -> QLabel:
    lbl = QLabel(text, parent)
    lbl.setStyleSheet(
        f"color: {COLORS.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; letter-spacing: 1px;"
    )
    return lbl


def int_spin(lo: int, hi: int, value: int) -> QSpinBox:
    s = QSpinBox()
    s.setRange(lo, hi)
    s.setValue(value)
    return s


def mm_spin(value: float) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(0.01, 10000.0)
    s.setDecimals(3)
    s.setValue(value)
    return s
