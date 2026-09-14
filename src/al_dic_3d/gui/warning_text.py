"""User-facing text for the run-time warnings the console log shows.

The run worker forwards every warning a run raises to the log. The common ones
are phrased for users and translated here (fix batch V, H2 / M10: a seedless
run logged "init_guess='seed' but no seed point was placed ..."); any other
warning is shown unchanged, so nothing is hidden. ``translate`` is thread-safe:
the worker calls this off the GUI thread.
"""

from __future__ import annotations

import re

from PySide6.QtCore import QCoreApplication

_NO_SEED = "init_guess='seed' but no seed point was placed"
_FFT_CLAMP_RE = re.compile(r"^Auto-scaled FFT search region: (\d+) -> (\d+) \(image (\d+)x(\d+)\)$")


def warning_text(message: str) -> str:
    """The console text for one run-time warning."""
    text = str(message).strip()
    if text.startswith(_NO_SEED):
        return QCoreApplication.translate(
            "RunWarnings",
            "No Starting Point placed: frame 1 is seeded by an FFT search "
            "(place a point for large first-frame motion)",
        )
    m = _FFT_CLAMP_RE.match(text)
    if m:
        old, new, height, width = m.groups()
        return QCoreApplication.translate(
            "RunWarnings",
            "FFT search range reduced from {0} to {1} px to fit the {2} × {3} px images",
        ).format(old, new, width, height)
    return text
