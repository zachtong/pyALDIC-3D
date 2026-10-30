"""Count the 2D engine's FFT search widenings while one camera is tracked.

al-dic widens its FFT initial-guess search whenever a correlation peak lands on
the search boundary (``20 -> 42 -> 86 ... px``, up to half the image) and says
so only through :mod:`logging`, which reaches the log file but never the GUI
log. A run that widens on every frame is several times slower with no reason
on screen; the classic cause is an incremental run whose frame-1 region no
longer covers the moved specimen at later reference frames.

:func:`record_fft_widening` attaches a handler to the engine logger for the
duration of one ``run_aldic`` call and keeps, per frame, the widest search the
engine moved to. It only reads records emitted by the calling thread (the two
cameras may track concurrently) and never raises: a reworded or reformatted
engine message only loses the count, never the run.
"""

from __future__ import annotations

import contextlib
import logging
import threading
from collections.abc import Callable, Iterator

#: The engine module that logs the widening (al-dic 0.7.x-1.0.x core/pipeline.py).
ENGINE_LOGGER = "al_dic.core.pipeline"

# Message prefixes of the engine's retry and hard-cap warnings; the new search
# radius is the LAST format argument of both (DEPENDS_ON_2D.md contract).
_WIDENING_PREFIXES = ("FFT peaks clipped at search boundary", "FFT peaks still clipped")


class FftWideningRecorder(logging.Handler):
    """Per-frame widest FFT search (px) the engine widened to, for one thread."""

    def __init__(self, frame: Callable[[], int]) -> None:
        super().__init__(level=logging.WARNING)
        self._thread = threading.get_ident()
        self._frame = frame
        self.widened: dict[int, int] = {}

    def emit(self, record: logging.LogRecord) -> None:
        if record.thread != self._thread or not str(record.msg).startswith(_WIDENING_PREFIXES):
            return
        try:
            radius = int(record.args[-1])  # type: ignore[index]
            k = int(self._frame())
        except (TypeError, ValueError, IndexError, KeyError):
            return
        self.widened[k] = max(self.widened.get(k, 0), radius)


@contextlib.contextmanager
def record_fft_widening(frame: Callable[[], int]) -> Iterator[FftWideningRecorder]:
    """Record the engine's FFT widenings of this thread; ``frame()`` names the frame."""
    logger = logging.getLogger(ENGINE_LOGGER)
    recorder = FftWideningRecorder(frame)
    logger.addHandler(recorder)
    try:
        yield recorder
    finally:
        logger.removeHandler(recorder)
