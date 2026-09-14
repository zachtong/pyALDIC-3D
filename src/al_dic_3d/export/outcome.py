"""Honest export bookkeeping (Qt-free): what was written, skipped and discarded.

Every media / table exporter that writes more than one file returns an
:class:`ExportOutcome` — a plain ``list`` of the written paths, so existing
callers (and tests) that ``len()``, index or compare it keep working — that
also records:

* ``cancelled`` — the export really stopped early on its stop event (a stop
  requested after the last file does NOT count: everything was written);
* ``skipped`` — frames that had nothing to draw (reported, never silently
  dropped; animations keep their timing with a background-only frame);
* ``unavailable`` — ``{camera}_{field}`` passes that produced no frame at all
  (e.g. strain requested on a strain-free result), so nothing was written;
* ``discarded`` — partial files deleted on cancel (an unfinished video is not
  a written file);
* ``warnings`` — anything else the user should hear about, as stable CODES
  (e.g. :data:`WARN_RIGHT_ROI`) the GUI turns into translated text.

Single-file writers (NPZ / MAT) raise :class:`ExportCancelled` instead: they
write to a temporary file and delete it, so a cancel leaves nothing behind.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

#: Warning code: the left ROI could not be warped into the right camera, so the
#: right-camera frames fell back to the tracked-node (hull) support.
WARN_RIGHT_ROI = "right_roi_unavailable"


class ExportCancelled(Exception):
    """A writer stopped on its cancel event; its partial output was removed."""


def stop_requested(stop_event: Any) -> bool:
    """True when a ``threading.Event``-like cancel flag is set."""
    return stop_event is not None and bool(stop_event.is_set())


def raise_if_stopped(stop_event: Any) -> None:
    """Raise :class:`ExportCancelled` when the cancel flag is set."""
    if stop_requested(stop_event):
        raise ExportCancelled("export cancelled")


def unlink_quietly(path: Path | None) -> None:
    """Delete *path* if it exists; never raises (cleanup of our own temp files)."""
    if path is None:
        return
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass


class ExportOutcome(list):
    """Written paths (``list``) + cancel / skip / discard bookkeeping."""

    def __init__(
        self,
        items: Iterable[Any] = (),
        *,
        cancelled: bool = False,
        skipped: Iterable[str] = (),
        unavailable: Iterable[str] = (),
        discarded: Iterable[Path] = (),
        warnings: Iterable[str] = (),
    ) -> None:
        super().__init__(items)
        self.cancelled = bool(cancelled)
        self.skipped: list[str] = list(skipped)
        self.unavailable: list[str] = list(unavailable)
        self.discarded: list[Path] = list(discarded)
        self.warnings: list[str] = list(warnings)

    def absorb(self, other: Iterable[Any]) -> ExportOutcome:
        """Append *other*'s files (and bookkeeping, when it is an outcome)."""
        self.extend(other)
        if isinstance(other, ExportOutcome):
            self.cancelled = self.cancelled or other.cancelled
            self.skipped += other.skipped
            self.unavailable += other.unavailable
            self.discarded += other.discarded
            self.warnings += other.warnings
        return self

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"ExportOutcome({list.__repr__(self)}, cancelled={self.cancelled}, "
            f"skipped={len(self.skipped)}, unavailable={self.unavailable}, "
            f"discarded={len(self.discarded)})"
        )
