"""Translate pipeline progress messages for the progress label (fix batch V, M10).

The compute layer reports progress in English by contract (``tr()`` is not
allowed outside the view), and the sidebar used to show those strings raw:
internal names such as ``track_both frame 3/40`` and engine section codes
such as ``Frame 3/40: S4 done (local ICGN, 2.1s)``. This module maps the known
message shapes onto translated, plain-language text; an unknown message is
shown unchanged, so nothing is ever hidden.
"""

from __future__ import annotations

import re

from PySide6.QtCore import QCoreApplication

_CAMERA_RE = re.compile(r"^(L|R): (.*)$", re.S)
_ENGINE_FRAME_RE = re.compile(r"^Frame (\d+)/(\d+)\b")
_VERIFY_RE = re.compile(
    r"^verifying frame (\d+)/(\d+)( \(keeping the frames tracked before the stop\))?$"
)
_ASSEMBLE_RE = re.compile(r"^(?:track_both frame|stereo_each_frame|ref_direct) (\d+)/(\d+)$")
_STRAIN_RE = re.compile(r"^strain frame (\d+)/(\d+)$")
_STEREO_SETUP_RE = re.compile(r"^Setup: frame-1 stereo match at (\d+) nodes$")


def _fixed() -> dict[str, str]:
    # Literal translate() calls so lupdate extracts every string.
    return {
        "Setup: checking the sequence and building the reference mesh": QCoreApplication.translate(
            "Progress", "Preparing: checking the images and building the mesh"
        ),
        "Setup: left-camera initial guess": QCoreApplication.translate(
            "Progress", "Preparing: initial guess for the left camera"
        ),
        "Setup: right-camera mesh and initial guess": QCoreApplication.translate(
            "Progress", "Preparing: mesh and initial guess for the right camera"
        ),
        "Setup: frame-1 stereo disparity prior": QCoreApplication.translate(
            "Progress", "Preparing: estimating the stereo offset"
        ),
        "temporal track complete": QCoreApplication.translate("Progress", "tracking complete"),
        "Section 2b: Normalizing images...": QCoreApplication.translate(
            "Progress", "normalizing images"
        ),
        "Computing cumulative displacements...": QCoreApplication.translate(
            "Progress", "composing displacements"
        ),
        "Composing cumulative displacements...": QCoreApplication.translate(
            "Progress", "composing displacements"
        ),
        "Assembling results...": QCoreApplication.translate("Progress", "assembling results"),
        "Pipeline complete.": QCoreApplication.translate("Progress", "tracking complete"),
    }


def progress_text(message: str) -> str:
    """The display text for one pipeline progress message."""
    m = _CAMERA_RE.match(message)
    if m:
        camera = (
            QCoreApplication.translate("Progress", "Left camera")
            if m.group(1) == "L"
            else QCoreApplication.translate("Progress", "Right camera")
        )
        return QCoreApplication.translate("Progress", "{0}: {1}").format(
            camera, progress_text(m.group(2))
        )
    fixed = _fixed().get(message)
    if fixed is not None:
        return fixed
    m = _ENGINE_FRAME_RE.match(message)
    if m:
        return QCoreApplication.translate("Progress", "tracking frame {0} of {1}").format(
            m.group(1), m.group(2)
        )
    m = _VERIFY_RE.match(message)
    if m:
        if m.group(3):
            template = QCoreApplication.translate(
                "Progress",
                "verifying frame {0} of {1} (keeping the frames tracked before the stop)",
            )
        else:
            template = QCoreApplication.translate("Progress", "verifying frame {0} of {1}")
        return template.format(m.group(1), m.group(2))
    m = _ASSEMBLE_RE.match(message)
    if m:
        return QCoreApplication.translate("Progress", "assembling frame {0} of {1}").format(
            m.group(1), m.group(2)
        )
    m = _STRAIN_RE.match(message)
    if m:
        return QCoreApplication.translate("Progress", "strain: frame {0} of {1}").format(
            m.group(1), m.group(2)
        )
    m = _STEREO_SETUP_RE.match(message)
    if m:
        return QCoreApplication.translate(
            "Progress", "Preparing: matching the two cameras at {0} nodes"
        ).format(m.group(1))
    return message
