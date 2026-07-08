"""``StrainNavigator3D`` — the strain window's private playback bar.

Clone of the 2D ``StrainNavigator``: prev / play-pause / next, a speed selector,
a bold FRAME label, and a timeline slider — but driven ENTIRELY via
:meth:`set_state` and the :attr:`frame_changed` signal. It never touches
``GuiSignals.current_frame``, so scrubbing strain frames cannot move the main
window (the decoupling contract the tests enforce).
"""

from __future__ import annotations

from al_dic.gui.icons import icon_chevron_left, icon_chevron_right, icon_pause, icon_play
from al_dic.gui.theme import COLORS
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QSlider, QWidget

_SPEED_PRESETS = [("1 fps", 1000), ("2 fps", 500), ("5 fps", 200), ("10 fps", 100), ("30 fps", 33)]


class StrainNavigator3D(QWidget):
    """Bottom bar: prev / play-pause / next / speed / FRAME label / slider.

    The caller syncs the widget with :meth:`set_state` whenever the frame count
    or the externally-driven current frame changes, and reacts to user
    navigation through :attr:`frame_changed`.
    """

    frame_changed = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._n_frames = 0
        self._current = 0
        self._playing = False

        self.setFixedHeight(36)
        self.setStyleSheet(f"background: {COLORS.BG_PANEL}; border-top: 1px solid {COLORS.BORDER};")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(6)

        self._prev_btn = QPushButton()
        self._prev_btn.setFixedWidth(28)
        self._prev_btn.setIcon(icon_chevron_left())
        self._prev_btn.setToolTip(self.tr("Previous frame"))
        self._prev_btn.clicked.connect(self._on_prev)
        layout.addWidget(self._prev_btn)

        self._play_btn = QPushButton()
        self._play_btn.setFixedWidth(28)
        self._play_btn.setIcon(icon_play())
        self._play_btn.setToolTip(self.tr("Play animation"))
        self._play_btn.clicked.connect(self._on_play_toggle)
        layout.addWidget(self._play_btn)

        self._next_btn = QPushButton()
        self._next_btn.setFixedWidth(28)
        self._next_btn.setIcon(icon_chevron_right())
        self._next_btn.setToolTip(self.tr("Next frame"))
        self._next_btn.clicked.connect(self._on_next)
        layout.addWidget(self._next_btn)

        self._speed_combo = QComboBox()
        for label, _ms in _SPEED_PRESETS:
            self._speed_combo.addItem(label)
        self._speed_combo.setCurrentIndex(1)  # default 2 fps
        self._speed_combo.setFixedWidth(68)
        self._speed_combo.setToolTip(self.tr("Playback speed"))
        self._speed_combo.currentIndexChanged.connect(self._on_speed)
        layout.addWidget(self._speed_combo)

        self._label = QLabel(self.tr("FRAME 0/0"))
        self._label.setFixedWidth(90)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(
            f"color: {COLORS.TEXT_SECONDARY}; font-size: 11px; "
            f"font-weight: bold; background: transparent;"
        )
        layout.addWidget(self._label)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 0)
        self._slider.valueChanged.connect(self._on_slider)
        layout.addWidget(self._slider, stretch=1)

        self._timer = QTimer(self)
        self._timer.setInterval(_SPEED_PRESETS[1][1])
        self._timer.timeout.connect(self._on_tick)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_state(self, n_frames: int, current: int) -> None:
        """Sync the slider range and label from the owning window."""
        self._n_frames = max(0, n_frames)
        clamped = max(0, min(current, max(0, self._n_frames - 1)))
        self._current = clamped
        self._slider.blockSignals(True)
        self._slider.setRange(0, max(0, self._n_frames - 1))
        self._slider.setValue(clamped)
        self._slider.blockSignals(False)
        self._update_label()
        if self._n_frames < 2:
            self.stop_playback()

    def stop_playback(self) -> None:
        self._playing = False
        self._timer.stop()
        self._play_btn.setIcon(icon_play())
        self._play_btn.setToolTip(self.tr("Play animation"))

    # ------------------------------------------------------------------
    # Internal slots
    # ------------------------------------------------------------------

    def _on_slider(self, value: int) -> None:
        self._current = value
        self._update_label()
        self.frame_changed.emit(value)

    def _on_prev(self) -> None:
        if self._n_frames >= 1:
            self._slider.setValue(max(0, self._current - 1))

    def _on_next(self) -> None:
        if self._n_frames >= 1:
            self._slider.setValue(min(self._n_frames - 1, self._current + 1))

    def _on_play_toggle(self) -> None:
        if self._playing:
            self.stop_playback()
        elif self._n_frames >= 2:
            self._playing = True
            self._play_btn.setIcon(icon_pause())
            self._play_btn.setToolTip(self.tr("Pause animation"))
            self._timer.start()

    def _on_tick(self) -> None:
        if self._n_frames < 2:
            self.stop_playback()
            return
        self._slider.setValue((self._current + 1) % self._n_frames)

    def _on_speed(self, index: int) -> None:
        if 0 <= index < len(_SPEED_PRESETS):
            self._timer.setInterval(_SPEED_PRESETS[index][1])

    def _update_label(self) -> None:
        if self._n_frames > 0:
            self._label.setText(self.tr("FRAME {0}/{1}").format(self._current + 1, self._n_frames))
        else:
            self._label.setText(self.tr("FRAME 0/0"))
