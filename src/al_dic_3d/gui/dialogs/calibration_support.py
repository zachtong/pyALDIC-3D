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
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from al_dic_3d.calibration import calibrate_stereo, detect_board, summarize


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
            options = dict(self._options)
            bundle = options.pop("bundle", False)
            morphology = options.pop("board_morphology", False)
            result = calibrate_stereo(dl, dr, image_size, **options)
            if bundle:
                import dataclasses

                from al_dic_3d.calibration import bundle_refine

                self.progress.emit("bundle adjustment")
                new_rig, info = bundle_refine(
                    dl,
                    dr,
                    result,
                    zero_tangent=options["zero_tangent"],
                    fix_k3=options["fix_k3"],
                    board_morphology=morphology,
                    progress=self.progress.emit,
                )
                result = dataclasses.replace(result, rig=new_rig)
            stats = summarize(result, dl, dr, image_size)
            if bundle:
                stats["ba_rms_before"] = info["rms_before"]
                stats["ba_rms_after"] = info["rms_after"]
                stats["ba_mono_views"] = info["n_mono_views"]
                if "board_z_range" in info:
                    stats["ba_board_z_range"] = info["board_z_range"]
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


def overlay_panel(path: str, det, height: int | None = 142) -> np.ndarray:
    """RGB panel of one image (scaled to ``height``; None = full size) with
    the detected points drawn."""
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
    return rgb


def pair_strip(path_l: str, path_r: str, det_l, det_r, height: int | None = 142) -> np.ndarray:
    """Side-by-side L|R annotated RGB strip (``height=None`` = full size)."""
    import cv2

    panels = [overlay_panel(path_l, det_l, height), overlay_panel(path_r, det_r, height)]
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
