"""ROI toolbar — Add/Cut/Refine dropdown buttons with shape popup menus.

Ported from the 2D app (``al_dic.gui.widgets.roi_toolbar``) with 3D adaptations:
Batch Import is dropped (the 3D contract has ONE ROI, drawn on the left camera's
frame 1) and the Refine brush menu hosts the quadtree refinement brush that used
to live in the PARAMETERS section.

Layout:
    Row 1: [+ Add ^]  [scissors Cut ^]  [+ Refine ^]  — dropdown selectors
    Row 2: [Import]                                   — mask file import
    Row 3: [Save] [Invert] [Clear]                    — utility buttons

Each Add/Cut click opens a popup menu (Polygon / Rectangle / Circle /
Circle 3-point). Selecting a shape activates one-shot drawing mode — the tool
auto-resets to "select" after completing one shape (``deactivate``).
"""

from __future__ import annotations

from al_dic.gui.theme import COLORS
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)


class ROIToolbar(QWidget):
    """Add/Cut/Refine dropdown toolbar with Import/Save/Invert/Clear utilities."""

    # Emitted when user selects a shape from Add or Cut menu: (shape, mode)
    # shape: "rect", "polygon", "circle", "circle3" — mode: "add" or "cut"
    draw_requested = Signal(str, str)

    # Emitted when clear is clicked
    clear_requested = Signal()

    # Emitted when a mask file is imported (path)
    import_requested = Signal(str)

    # Emitted when save is clicked
    save_requested = Signal()

    # Emitted when invert is clicked
    invert_requested = Signal()

    # Refinement-brush signals: (mode, radius_px) — mode is "paint" or "erase"
    brush_requested = Signal(str, int)
    brush_clear_requested = Signal()
    # Emitted live whenever the radius spinbox changes, so the canvas
    # can update its active brush radius without re-clicking Paint/Erase.
    brush_radius_changed = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._active_mode: str | None = None  # "add"/"cut"/"brush_*" while drawing

        layout = QGridLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        # --- Row 1: Add / Cut / Refine dropdown buttons ---
        self._btn_add = QPushButton(self.tr("+ Add") + "  ▴")
        self._btn_add.setToolTip(
            self.tr("Add region to the Region of Interest (Polygon / Rectangle / Circle)")
        )
        self._btn_add.setFixedHeight(30)

        self._btn_cut = QPushButton("✂ " + self.tr("Cut") + "  ▴")
        self._btn_cut.setToolTip(
            self.tr("Cut region from the Region of Interest (Polygon / Rectangle / Circle)")
        )
        self._btn_cut.setFixedHeight(30)

        self._btn_refine = QPushButton(self.tr("+ Refine") + "  ▴")
        self._btn_refine.setToolTip(
            self.tr(
                "Paint extra mesh-refinement zones with a brush\n"
                "(on the LEFT camera, frame 1 — the reference mesh geometry)"
            )
        )
        self._btn_refine.setFixedHeight(30)

        layout.addWidget(self._btn_add, 0, 0)
        layout.addWidget(self._btn_cut, 0, 1)
        layout.addWidget(self._btn_refine, 0, 2)

        # Build popup menus
        self._add_menu = self._build_shape_menu("add")
        self._cut_menu = self._build_shape_menu("cut")
        self._brush_menu = self._build_brush_menu()

        self._btn_add.clicked.connect(lambda: self._popup_above(self._btn_add, self._add_menu))
        self._btn_cut.clicked.connect(lambda: self._popup_above(self._btn_cut, self._cut_menu))
        self._btn_refine.clicked.connect(
            lambda: self._popup_above(self._btn_refine, self._brush_menu)
        )

        # --- Row 2: Import ---
        self._btn_import = QPushButton(self.tr("Import"))
        self._btn_import.setToolTip(self.tr("Import mask from image file"))
        self._btn_import.setFixedHeight(26)
        self._btn_import.clicked.connect(self._on_import)
        layout.addWidget(self._btn_import, 1, 0, 1, 3)

        # --- Row 3: Save / Invert / Clear ---
        action_row = QHBoxLayout()
        action_row.setSpacing(4)

        self._btn_save = QPushButton(self.tr("Save"))
        self._btn_save.setToolTip(self.tr("Save current mask to PNG file"))
        self._btn_save.setFixedHeight(26)
        self._btn_save.clicked.connect(lambda: self.save_requested.emit())
        action_row.addWidget(self._btn_save)

        self._btn_invert = QPushButton(self.tr("Invert"))
        self._btn_invert.setToolTip(self.tr("Invert the Region of Interest mask"))
        self._btn_invert.setFixedHeight(26)
        self._btn_invert.clicked.connect(lambda: self.invert_requested.emit())
        action_row.addWidget(self._btn_invert)

        self._btn_clear = QPushButton(self.tr("Clear"))
        self._btn_clear.setToolTip(self.tr("Clear all Region of Interest masks"))
        self._btn_clear.setFixedHeight(26)
        self._btn_clear.clicked.connect(lambda: self.clear_requested.emit())
        action_row.addWidget(self._btn_clear)

        layout.addLayout(action_row, 2, 0, 1, 3)

        # Lock all utility button geometry to prevent layout jitter
        # when stylesheets change on the row-0 buttons.
        _util_style = (
            f"QPushButton {{ background: {COLORS.BG_INPUT}; "
            f"color: {COLORS.TEXT_PRIMARY}; border: 1px solid {COLORS.BORDER}; "
            f"{self._GEOM} }}"
        )
        for btn in (self._btn_import, self._btn_save, self._btn_invert, self._btn_clear):
            btn.setStyleSheet(_util_style)

        # Apply initial styling
        self._update_button_styles()

    # ------------------------------------------------------------------ menus

    def _build_shape_menu(self, mode: str) -> QMenu:
        """Create a popup menu with Polygon / Rectangle / Circle actions."""
        menu = QMenu(self)
        menu.addAction(
            "⬟  " + self.tr("Polygon"),
            lambda: self._on_shape_selected("polygon", mode),
        )
        menu.addAction(
            "□  " + self.tr("Rectangle"),
            lambda: self._on_shape_selected("rect", mode),
        )
        menu.addAction(
            "○  " + self.tr("Circle"),
            lambda: self._on_shape_selected("circle", mode),
        )
        menu.addAction(
            "◌  " + self.tr("Circle (3-point)"),
            lambda: self._on_shape_selected("circle3", mode),
        )
        return menu

    def _build_brush_menu(self) -> QMenu:
        """Create the Refine brush popup menu (radius + Paint/Erase + Clear)."""
        menu = QMenu(self)

        # Radius row: label + spinbox embedded via QWidgetAction
        radius_widget = QWidget()
        radius_layout = QHBoxLayout(radius_widget)
        radius_layout.setContentsMargins(8, 4, 8, 4)
        radius_layout.setSpacing(6)
        radius_layout.addWidget(QLabel(self.tr("Radius")))
        self._brush_radius_spin = QSpinBox()
        self._brush_radius_spin.setRange(2, 500)
        self._brush_radius_spin.setValue(16)
        self._brush_radius_spin.setSuffix(" px")
        # Live-update the canvas radius so the user does not have to
        # re-click Paint/Erase after changing the spinbox.
        self._brush_radius_spin.valueChanged.connect(
            lambda v: self.brush_radius_changed.emit(int(v))
        )
        radius_layout.addWidget(self._brush_radius_spin)
        radius_action = QWidgetAction(menu)
        radius_action.setDefaultWidget(radius_widget)
        menu.addAction(radius_action)

        menu.addSeparator()
        menu.addAction(
            "✎  " + self.tr("Paint"),
            lambda: self._on_brush_selected("paint", self._brush_radius_spin.value()),
        )
        menu.addAction(
            "✖  " + self.tr("Erase"),
            lambda: self._on_brush_selected("erase", self._brush_radius_spin.value()),
        )
        menu.addSeparator()

        # Clear button as QWidgetAction so we can keep a public ref for tests
        clear_widget = QWidget()
        clear_layout = QVBoxLayout(clear_widget)
        clear_layout.setContentsMargins(8, 4, 8, 4)
        self._brush_clear_btn = QPushButton(self.tr("Clear Brush"))
        self._brush_clear_btn.clicked.connect(lambda: self.brush_clear_requested.emit())
        clear_layout.addWidget(self._brush_clear_btn)
        clear_action = QWidgetAction(menu)
        clear_action.setDefaultWidget(clear_widget)
        menu.addAction(clear_action)

        return menu

    def _popup_above(self, button: QPushButton, menu: QMenu) -> None:
        """Show ``menu`` popping ABOVE ``button`` (the sidebar sits low)."""
        pos = button.mapToGlobal(button.rect().topLeft())
        pos.setY(pos.y() - menu.sizeHint().height())
        menu.popup(pos)

    # ------------------------------------------------------------------ slots

    def _on_shape_selected(self, shape: str, mode: str) -> None:
        """Handle shape selection from popup menu."""
        self._active_mode = mode
        self._update_button_styles()
        self.draw_requested.emit(shape, mode)

    def _on_brush_selected(self, mode: str, radius: int) -> None:
        """Handle Paint / Erase selection from the brush popup."""
        self._active_mode = "brush_paint" if mode == "paint" else "brush_erase"
        self._update_button_styles()
        self.brush_requested.emit(mode, int(radius))

    def deactivate(self) -> None:
        """Reset the active state — called when drawing finishes or is canceled."""
        self._active_mode = None
        self._update_button_styles()

    def _on_import(self) -> None:
        """Open file dialog and emit import signal with selected path."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Import Mask Image"),
            "",
            self.tr("Images (*.png *.bmp *.tif *.tiff *.jpg *.jpeg);;All Files (*)"),
        )
        if path:
            self.import_requested.emit(path)

    # ------------------------------------------------------------------ styles

    # Shared geometry tokens — keep padding/margin identical across all
    # states so that Qt never recalculates sizeHint on style switches.
    _GEOM = "border-radius: 4px; padding: 2px 4px; margin: 0px;"

    _BASE_STYLE = (
        f"QPushButton {{ background: {COLORS.BG_INPUT}; "
        f"color: {COLORS.TEXT_PRIMARY}; border: 1px solid {COLORS.BORDER}; "
        f"{_GEOM} }} "
        f"QPushButton:disabled {{ background: {COLORS.BG_DARKEST}; "
        f"color: {COLORS.TEXT_MUTED}; "
        f"border: 1px dashed {COLORS.TEXT_MUTED}; }}"
    )

    def _make_active_style(self, bg: str, fg: str = "#ffffff") -> str:
        return (
            f"QPushButton {{ background: {bg}; color: {fg}; border: 1px solid {bg}; {self._GEOM} }}"
        )

    def _update_button_styles(self) -> None:
        """Update Add/Cut/Refine button highlight based on active mode."""
        # Reset all to a consistent base style (never use empty string —
        # that triggers Qt style-engine fallback and causes layout jitter).
        self._btn_add.setStyleSheet(self._BASE_STYLE)
        self._btn_cut.setStyleSheet(self._BASE_STYLE)
        self._btn_refine.setStyleSheet(self._BASE_STYLE)

        if self._active_mode == "add":
            self._btn_add.setStyleSheet(self._make_active_style(COLORS.ACCENT))
        elif self._active_mode == "cut":
            self._btn_cut.setStyleSheet(self._make_active_style(COLORS.DANGER))
        elif self._active_mode in ("brush_paint", "brush_erase"):
            color = "#14dcc8" if self._active_mode == "brush_paint" else "#0a8a7a"
            self._btn_refine.setStyleSheet(self._make_active_style(color, "#001417"))
