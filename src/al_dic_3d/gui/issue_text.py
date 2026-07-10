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
    return issue


def issues_text(issues: list[str]) -> str:
    """The translated, '; '-joined display line for a full issues list."""
    return "; ".join(issue_text(i) for i in issues)
