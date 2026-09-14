"""Translate ``ProjectDraft.issues()`` codes for display (G3.4 / G3.8).

The compute layer reports readiness problems as a CLOSED SET of English
strings (English-by-contract — ``tr()`` is forbidden outside the Qt view
layer). This module is the view-side mapping: each known issue string gets a
``tr()`` catalog entry; unknown strings pass through untranslated so a new
issue is shown verbatim rather than hidden.
"""

from __future__ import annotations

import re

from PySide6.QtCore import QCoreApplication

# The parametric issue: "sequence length mismatch: {n} vs {m}".
_MISMATCH_RE = re.compile(r"^sequence length mismatch: (\d+) vs (\d+)$")
# Fix batch V (M8) content checks, see ProjectDraft.validity_issues().
_CALIB_RE = re.compile(r"^calibration file cannot be read: (.*)$", re.S)
_UNREADABLE_RE = re.compile(r"^(left|right) image not readable: (.*)$")
_SIZES_RE = re.compile(r"^(left|right) frame sizes differ: (\S+) vs (\S+)$")
_MASK_RE = re.compile(r"^ROI mask is (\S+) but the images are (\S+)$")


def _camera(cam: str) -> str:
    if cam == "left":
        return QCoreApplication.translate("Issues", "left camera")
    return QCoreApplication.translate("Issues", "right camera")


def _table() -> dict[str, str]:
    # NOTE: every call must be a literal `QCoreApplication.translate("Issues",
    # "...")` — lupdate needs BOTH the receiver spelled out (an alias parses
    # as tr(source, disambiguation)) and a literal context string.
    return {
        "calibration file not set": QCoreApplication.translate(
            "Issues", "calibration file not set"
        ),
        "left/right sequences not set": QCoreApplication.translate(
            "Issues", "left/right sequences not set"
        ),
        "need at least 2 frames": QCoreApplication.translate("Issues", "need at least 2 frames"),
        "ROI not set": QCoreApplication.translate("Issues", "ROI not set"),
        "ROI is empty (xmin<xmax, ymin<ymax required)": QCoreApplication.translate(
            "Issues", "ROI is empty (xmin<xmax, ymin<ymax required)"
        ),
        "left and right sequences use the same image files": QCoreApplication.translate(
            "Issues", "left and right sequences use the same image files"
        ),
    }


def issue_text(issue: str) -> str:
    """The translated display text for one ``draft.issues()`` entry.

    Unknown strings fall through untranslated (never hide a new issue).
    """
    known = _table().get(issue)
    if known is not None:
        return known
    m = _MISMATCH_RE.match(issue)
    if m:
        template = QCoreApplication.translate("Issues", "sequence length mismatch: {0} vs {1}")
        return template.format(m.group(1), m.group(2))
    m = _CALIB_RE.match(issue)
    if m:
        template = QCoreApplication.translate("Issues", "calibration file cannot be read: {0}")
        return template.format(m.group(1))
    m = _UNREADABLE_RE.match(issue)
    if m:
        template = QCoreApplication.translate("Issues", "{0}: image not readable: {1}")
        return template.format(_camera(m.group(1)), m.group(2))
    m = _SIZES_RE.match(issue)
    if m:
        template = QCoreApplication.translate("Issues", "{0}: frame sizes differ ({1} vs {2})")
        return template.format(_camera(m.group(1)), m.group(2), m.group(3))
    m = _MASK_RE.match(issue)
    if m:
        template = QCoreApplication.translate(
            "Issues", "ROI mask is {0} but the images are {1}: redraw or import it again"
        )
        return template.format(m.group(1), m.group(2))
    return issue


def issues_text(issues: list[str]) -> str:
    """The translated, '; '-joined display line for a full issues list."""
    return "; ".join(issue_text(i) for i in issues)
