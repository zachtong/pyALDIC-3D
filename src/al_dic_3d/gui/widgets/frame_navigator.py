"""``FrameNavigator3D`` — bottom playback bar (2D ``FrameNavigator`` idiom).

Prev / play / next buttons, a playback-speed selector, a bold ``FRAME N/M``
label, and a timeline slider — wired to :class:`GuiSignals` instead of the 2D
AppState singleton (the 3D backend stays Qt-free).
"""

from __future__ import annotations

from al_dic.gui.icons import icon_chevron_left, icon_chevron_right, icon_pause, icon_play
from al_dic.gui.theme import COLORS
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QSlider, QWidget

from al_dic_3d.gui.state import GuiSignals

_SPEED_PRESETS = [("1 fps", 1000), ("2 fps", 500), ("5 fps", 200), ("10 fps", 100), ("30 fps", 33)]


class FrameNavigator3D(QWidget):
    """Bottom bar: prev/play/next, speed, FRAME label, slider."""

    def __init__(self, signals: GuiSignals, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._signals = signals
        self._n_frames = 0
        self._playing = False

        self.setFixedHeight(36)
        self.setStyleSheet(f"background: {COLORS.BG_PANEL}; border-top: 1px solid {COLORS.BORDER};")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(6)

        self._prev_btn = QPushButton()
        self._prev_btn.setFixedWidth(28)
        self._prev_btn.setIcon(icon_chevron_left())
        self._prev_btn.setToolTip(self.tr("Previous frame (←)"))
        self._prev_btn.clicked.connect(lambda: self._step(-1))
        layout.addWidget(self._prev_btn)

        self._play_btn = QPushButton()
        self._play_btn.setFixedWidth(28)
        self._play_btn.setIcon(icon_play())
        self._play_btn.setToolTip(self.tr("Play animation (Space)"))
        self._play_btn.clicked.connect(self._toggle_play)
        layout.addWidget(self._play_btn)

        self._next_btn = QPushButton()
        self._next_btn.setFixedWidth(28)
        self._next_btn.setIcon(icon_chevron_right())
        self._next_btn.setToolTip(self.tr("Next frame (→)"))
        self._next_btn.clicked.connect(lambda: self._step(1))
        layout.addWidget(self._next_btn)

        self._speed_combo = QComboBox()
        for label, _ms in _SPEED_PRESETS:
            self._speed_combo.addItem(label)
        self._speed_combo.setCurrentIndex(1)
        self._speed_combo.setFixedWidth(68)
        self._speed_combo.setToolTip(self.tr("Playback speed (frames per second). Default 2 fps."))
        self._speed_combo.currentIndexChanged.connect(self._on_speed)
        layout.addWidget(self._speed_combo)

        self._label = QLabel()
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
        self._timer.timeout.connect(self._tick)

        self._signals.frame_changed.connect(self._on_frame_changed)
        self._update_label(0)

    def set_frame_count(self, n: int) -> None:
        self._n_frames = n
        self._slider.blockSignals(True)
        self._slider.setRange(0, max(0, n - 1))
        self._slider.blockSignals(False)
        self._stop()
        self._update_label(self._signals.current_frame)

    def toggle_playback(self) -> None:
        """Public play/pause toggle for the Space shortcut (G2.5)."""
        self._toggle_play()

    def _step(self, delta: int) -> None:
        self._signals.set_current_frame(self._signals.current_frame + delta, self._n_frames)

    def _on_slider(self, value: int) -> None:
        self._signals.set_current_frame(value, self._n_frames)

    def _on_frame_changed(self, idx: int) -> None:
        self._slider.blockSignals(True)
        self._slider.setValue(idx)
        self._slider.blockSignals(False)
        self._update_label(idx)

    def _toggle_play(self) -> None:
        if self._playing:
            self._stop()
        elif self._n_frames >= 2:
            self._playing = True
            self._play_btn.setIcon(icon_pause())
            self._play_btn.setToolTip(self.tr("Pause animation (Space)"))
            self._timer.start()

    def _stop(self) -> None:
        self._playing = False
        self._timer.stop()
        self._play_btn.setIcon(icon_play())
        self._play_btn.setToolTip(self.tr("Play animation (Space)"))

    def _tick(self) -> None:
        if self._n_frames < 2:
            self._stop()
            return
        nxt = self._signals.current_frame + 1
        self._signals.set_current_frame(0 if nxt >= self._n_frames else nxt, self._n_frames)

    def _on_speed(self, index: int) -> None:
        if 0 <= index < len(_SPEED_PRESETS):
            self._timer.setInterval(_SPEED_PRESETS[index][1])

    def _update_label(self, idx: int) -> None:
        if self._n_frames > 0:
            self._label.setText(self.tr("FRAME {0}/{1}").format(idx + 1, self._n_frames))
        else:
            self._label.setText(self.tr("FRAME 0/0"))
