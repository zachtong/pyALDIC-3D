"""The on-screen "rigid motion removed" wording, shared by every label that shows it.

One helper so the main canvas colorbar, the 3D scalar bar, the strain window and
the exported figures all say the same thing whenever the displayed result has its
rigid motion removed. The translation context is written out literally in every
call: ``lupdate`` only extracts literal contexts.
"""

from __future__ import annotations

from PySide6.QtCore import QCoreApplication


def mode_name(mode: str) -> str:
    """User-facing name of a rigid-motion mode."""
    if mode == "translation":
        return QCoreApplication.translate("RigidMotion", "translation")
    if mode == "rigid":
        return QCoreApplication.translate("RigidMotion", "translation + rotation")
    if mode == "off":
        return QCoreApplication.translate("RigidMotion", "off")
    return mode


def rigid_motion_label_suffix(result) -> str:
    """``" · rigid motion removed (mode)"`` for a corrected result, else ``""``."""
    state = getattr(result, "rigid_motion", None) if result is not None else None
    if state is None:
        return ""
    return QCoreApplication.translate("RigidMotion", " · rigid motion removed ({0})").format(
        mode_name(state.fit.mode)
    )
