"""``RigidMotionPanel3D`` — the Strain window's RIGID MOTION controls (widgets only).

Mode, fit-region tools and the per-frame table. Behavior-free like the other
extracted strain-window panels: every signal is wired in
:mod:`al_dic_3d.gui.strain_rigid_motion`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from al_dic.gui.theme import COLORS
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from al_dic_3d.gui.controllers.rigid_motion_controller import RigidMotionRow

MODES = ("off", "translation", "rigid")
_TABLE_HEIGHT = 150


class RigidMotionPanel3D(QWidget):
    """Rigid-motion mode, fit-region tools, status line and per-frame table."""

    mode_changed = Signal(str)
    draw_requested = Signal(str, str)  # shape ("rect" | "polygon"), mode ("add" | "cut")
    use_all_requested = Signal()
    show_region_toggled = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        row = QHBoxLayout()
        row.addWidget(QLabel(self.tr("Remove")))
        self._mode = QComboBox()
        for code, text in zip(
            MODES,
            (self.tr("Off"), self.tr("Translation only"), self.tr("Translation + rotation")),
            strict=True,
        ):
            self._mode.addItem(text, code)
        self._mode.setToolTip(
            self.tr(
                "Remove each frame's best-fit rigid-body motion (relative to frame 1)\n"
                "from the displacement everywhere: the field maps, the 3D view,\n"
                "the strain and every export. Green-Lagrange strain is unchanged\n"
                "by it; the displacement and the slopes ∂w/∂x, ∂w/∂y are not."
            )
        )
        self._mode.currentIndexChanged.connect(lambda _i: self.mode_changed.emit(self.mode()))
        row.addWidget(self._mode, 1)
        layout.addLayout(row)

        self._region_lbl = QLabel("")
        self._region_lbl.setWordWrap(True)
        self._region_lbl.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(self._region_lbl)

        grid = QGridLayout()
        grid.setSpacing(4)
        self._tool_buttons: list[QPushButton] = []
        tools = (
            ("rect", "add", self.tr("+ Rectangle")),
            ("polygon", "add", self.tr("+ Polygon")),
            ("rect", "cut", self.tr("− Rectangle")),
            ("polygon", "cut", self.tr("− Polygon")),
        )
        for i, (shape, mode, text) in enumerate(tools):
            btn = QPushButton(text)
            btn.setFixedHeight(26)
            btn.setToolTip(
                self.tr("Add an area to the fit region (drawn on frame 1)")
                if mode == "add"
                else self.tr("Remove an area from the fit region")
            )
            btn.clicked.connect(lambda _=False, s=shape, m=mode: self.draw_requested.emit(s, m))
            grid.addWidget(btn, i // 2, i % 2)
            self._tool_buttons.append(btn)
        layout.addLayout(grid)

        self._all_btn = QPushButton(self.tr("Use all valid points"))
        self._all_btn.setFixedHeight(26)
        self._all_btn.setToolTip(self.tr("Clear the drawn region: fit on every valid point"))
        self._all_btn.clicked.connect(self.use_all_requested.emit)
        layout.addWidget(self._all_btn)

        self._show_cb = QCheckBox(self.tr("Show fit region"))
        self._show_cb.setChecked(True)
        self._show_cb.toggled.connect(self.show_region_toggled.emit)
        layout.addWidget(self._show_cb)

        self._status = QLabel("")
        self._status.setWordWrap(True)
        layout.addWidget(self._status)

        legend = QLabel(
            self.tr(
                "Per frame: shift of the fitted points' centroid ΔX/ΔY/ΔZ (µm), "
                "rotation θ (mrad), fit residual RMS (µm), points used N."
            )
        )
        legend.setWordWrap(True)
        legend.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; font-size: 10px;")
        layout.addWidget(legend)

        self._table = QTableWidget(0, 7)
        self._table.setHorizontalHeaderLabels(["#", "ΔX", "ΔY", "ΔZ", "θ", "RMS", "N"])
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setStyleSheet("font-size: 10px;")
        self._table.setFixedHeight(_TABLE_HEIGHT)
        layout.addWidget(self._table)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def mode(self) -> str:
        return str(self._mode.currentData())

    def set_mode(self, mode: str) -> None:
        """Show ``mode`` without emitting ``mode_changed``."""
        idx = self._mode.findData(mode)
        self._mode.blockSignals(True)
        self._mode.setCurrentIndex(max(0, idx))
        self._mode.blockSignals(False)

    def region_shown(self) -> bool:
        return self._show_cb.isChecked()

    def set_region_text(self, text: str) -> None:
        self._region_lbl.setText(text)

    def set_status(self, text: str, warning: bool = False) -> None:
        color = COLORS.WARNING if warning else COLORS.TEXT_SECONDARY
        self._status.setStyleSheet(f"color: {color}; font-size: 11px;")
        self._status.setText(text)

    def status_text(self) -> str:
        return self._status.text()

    def set_controls_enabled(self, enabled: bool) -> None:
        self._mode.setEnabled(enabled)
        for btn in (*self._tool_buttons, self._all_btn):
            btn.setEnabled(enabled)

    def set_tools_enabled(self, enabled: bool) -> None:
        """The region tools need a run result to draw on."""
        for btn in (*self._tool_buttons, self._all_btn):
            btn.setEnabled(enabled)

    def set_rows(self, rows: list[RigidMotionRow], not_fitted: str) -> None:
        """Fill the per-frame table; a frame that could not be fitted shows dashes."""
        self._table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            ok = row.status in ("ok", "reference")
            values = (
                [str(row.frame)]
                + [f"{v:.2f}" if ok else "—" for v in row.shift_um]
                + [f"{row.angle_mrad:.3f}" if ok else "—", f"{row.rms_um:.2f}" if ok else "—"]
                + [str(row.n_used)]
            )
            for c, text in enumerate(values):
                item = QTableWidgetItem(text)
                if not ok:
                    item.setToolTip(not_fitted.format(row.status))
                self._table.setItem(r, c, item)

    def row_count(self) -> int:
        return self._table.rowCount()

    def cell_text(self, row: int, col: int) -> str:
        item = self._table.item(row, col)
        return "" if item is None else item.text()

    def set_current_frame(self, frame_idx: int) -> None:
        if 0 <= frame_idx < self._table.rowCount():
            self._table.selectRow(frame_idx)
