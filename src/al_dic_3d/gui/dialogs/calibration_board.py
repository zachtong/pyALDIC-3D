"""The board form of the calibration dialog (split out for the 800-line cap).

A wrong board description is the commonest reason a first calibration fails
or, worse, succeeds with a wrong scale. So the form says what each board's
size counts (inner corners, squares or dots), remembers the last board
between sessions (a lab calibrates the same board again and again; the 12 mm
default silently scaled every result of a 10 mm board), and words the
"board not found" failure as what to check first.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QLabel, QWidget

from al_dic_3d.gui import persistence
from al_dic_3d.gui.dialogs.calibration_support import int_spin, mm_spin

BOARD_CHESS, BOARD_CHARUCO, BOARD_CIRCLES, BOARD_CODED = (
    "chessboard",
    "charuco",
    "circles",
    "coded",
)
_SETTINGS_GROUP = "calibration_board"
_SPINS = ("cols", "rows", "square", "marker", "spacing", "dot")
_CHECKS = ("asym", "legacy")


def _as_bool(value: object) -> bool:
    return str(value).strip().lower() in ("true", "1", "yes")


class BoardFormMixin:
    """Board type and size widgets, the spec they describe, and their memory.

    Builds ``_board_combo``, ``_count_lbl``, ``_cols`` / ``_rows``,
    ``_square`` / ``_sq_lbl``, ``_marker`` / ``_marker_lbl``, ``_spacing`` /
    ``_sp_lbl``, ``_dot`` / ``_dot_lbl``, ``_asym`` and ``_legacy``; uses the
    dialog's ``_ecc`` checkbox (solver options) once that exists.
    """

    def _build_board_form(self) -> QWidget:
        host = QWidget()
        grid = QGridLayout(host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setVerticalSpacing(4)

        self._board_combo = QComboBox()
        self._board_combo.addItem(self.tr("Chessboard"), BOARD_CHESS)
        self._board_combo.addItem(self.tr("ChArUco"), BOARD_CHARUCO)
        self._board_combo.addItem(self.tr("Circle grid"), BOARD_CIRCLES)
        self._board_combo.addItem(self.tr("Coded dot target (3 ring markers)"), BOARD_CODED)
        self._board_combo.currentIndexChanged.connect(self._on_board_changed)
        grid.addWidget(QLabel(self.tr("Type")), 0, 0)
        grid.addWidget(self._board_combo, 0, 1)

        self._cols = int_spin(3, 99, 9)
        self._rows = int_spin(3, 99, 7)
        self._count_lbl = QLabel()
        grid.addWidget(self._count_lbl, 1, 0)
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
        return host

    # ---- per-type form ---------------------------------------------------------

    def _on_board_changed(self) -> None:
        board = self._board_combo.currentData()
        chessy = board in (BOARD_CHESS, BOARD_CHARUCO)
        for w in (self._square, self._sq_lbl):
            w.setVisible(chessy)
        for w in (self._marker, self._marker_lbl):
            w.setVisible(board == BOARD_CHARUCO)
        self._legacy.setVisible(board == BOARD_CHARUCO)
        for w in (self._spacing, self._sp_lbl, self._dot, self._dot_lbl):
            w.setVisible(not chessy)
        self._asym.setVisible(board == BOARD_CIRCLES)
        if hasattr(self, "_ecc"):
            self._ecc.setVisible(not chessy)
        if board == BOARD_CHESS:
            self._count_lbl.setText(self.tr("Inner corners (columns x rows)"))
        elif board == BOARD_CHARUCO:
            self._count_lbl.setText(self.tr("Squares (columns x rows)"))
        else:
            self._count_lbl.setText(self.tr("Dots (columns x rows)"))
        for spin in (self._cols, self._rows):
            spin.setToolTip(self._count_hint())

    def _count_hint(self) -> str:
        """What the board's size counts: the first thing to check when it is not found."""
        board = self._board_combo.currentData()
        if board == BOARD_CHESS:
            return self.tr(
                "For a chessboard, count the INNER corners: a board of 10 x 8 squares has 9 x 7."
            )
        if board == BOARD_CHARUCO:
            return self.tr(
                "For ChArUco, count the SQUARES (not the inner corners), and check the "
                "marker size and the OpenCV < 4.7 setting."
            )
        return self.tr("For a dot grid, count the DOTS in one row and in one column.")

    def _board_spec(self):
        from al_dic_3d.calibration import (
            CharucoSpec,
            ChessboardSpec,
            CircleGridSpec,
            CodedCircleGridSpec,
        )

        board = self._board_combo.currentData()
        cols, rows = self._cols.value(), self._rows.value()
        if board == BOARD_CHESS:
            return ChessboardSpec(cols=cols, rows=rows, square_size=self._square.value())
        if board == BOARD_CHARUCO:
            return CharucoSpec(
                squares_x=cols,
                squares_y=rows,
                square_size=self._square.value(),
                marker_size=self._marker.value(),
                legacy_pattern=self._legacy.isChecked(),
            )
        if board == BOARD_CIRCLES:
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

    # ---- memory between sessions --------------------------------------------------

    def _form_widgets(self) -> dict:
        """The stored keys and their widgets (attribute ``_<key>`` on the dialog)."""
        return {key: getattr(self, f"_{key}") for key in (*_SPINS, *_CHECKS)}

    def _remember_board(self) -> None:
        """Store the board type and every board field for the next session."""
        widgets = self._form_widgets()
        values: dict[str, object] = {"board": str(self._board_combo.currentData())}
        values.update({key: widgets[key].value() for key in _SPINS})
        values.update({key: bool(widgets[key].isChecked()) for key in _CHECKS})
        persistence.set_group_values(_SETTINGS_GROUP, values)

    def _restore_board(self) -> None:
        """Bring back the last session's board; a value that does not parse keeps its default."""
        values = persistence.group_values(_SETTINGS_GROUP)
        index = self._board_combo.findData(values.get("board"))
        if index >= 0:
            self._board_combo.setCurrentIndex(index)
        widgets = self._form_widgets()
        for key in _SPINS:
            try:
                value = float(values[key])
            except (KeyError, TypeError, ValueError):
                continue
            if not math.isfinite(value):
                continue
            widgets[key].setValue(int(round(value)) if key in ("cols", "rows") else value)
        for key in _CHECKS:
            if key in values:
                widgets[key].setChecked(_as_bool(values[key]))

    # ---- what to check when the board is not found ----------------------------------

    def _shortfall_text(self, left, right, min_pairs: int) -> str | None:
        """Translated counterpart of ``batch_detect.detection_shortfall``."""
        from al_dic_3d.calibration.batch_detect import count_detections

        count = count_detections(left, right)
        if count.pairs >= min_pairs or count.total_pairs < min_pairs:
            return None
        if count.images == 0:
            lead = self.tr("The board was not found in any image.")
        else:
            lead = self.tr(
                "The board was found in both images of only {0} of {1} pairs (the solve needs {2})."
            ).format(count.pairs, count.total_pairs, min_pairs)
        return f"{lead} {self._count_hint()}"

    def _mixed_size_text(self, error) -> str:
        """A ``MixedImageSizeError`` in the user's language."""
        from pathlib import Path

        camera = (
            QCoreApplication.translate("Issues", "left camera")
            if error.camera == "left"
            else QCoreApplication.translate("Issues", "right camera")
        )
        return self.tr(
            "{0}: the board images are not all the same size ({1} is {2}, {3} is {4}). "
            "Use images of one size for each camera."
        ).format(
            camera,
            Path(error.path).name,
            f"{error.size[0]}x{error.size[1]}",
            Path(error.first_path).name,
            f"{error.first_size[0]}x{error.first_size[1]}",
        )
