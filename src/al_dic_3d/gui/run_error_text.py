"""User-facing text for a run that stopped with an error (GUI log + dialog).

The run worker used to show ``f"{type(exc).__name__}: {exc}"``: a failed
frame-1 stereo match read "RuntimeError: frame-1 stereo match found no valid
correspondences (0/6160 candidates matched L1->R1; ... disparity offset=None)"
followed by advice that did not help (new-user audit, 2026-11-25). The errors
a user causes and can fix are worded here in GUI terms and translated; any
other error keeps its plain message, and an unexpected exception type (a bug)
keeps its type name so a report still says what broke. ``translate`` is
thread-safe: the worker calls this off the GUI thread.
"""

from __future__ import annotations

from PySide6.QtCore import QCoreApplication

# Exception types the pipeline raises for inputs the user can fix (a missing
# file, mismatched sizes or counts, a run that matched nothing): their message
# is the whole story, so no type name is shown.
_USER_ERRORS = (OSError, ValueError, RuntimeError)


def _no_stereo_links_text(exc) -> str:
    if exc.cause == "calibration":
        median = exc.epipolar_median_px
        return QCoreApplication.translate(
            "RunErrors",
            "No point of frame 1 could be matched between the left and right images: the "
            "stereo check rejected {0} links for their distance from the epipolar line "
            "(median {1} px). The calibration probably does not match these images (a "
            "camera moved, a wrong file, or left and right swapped). Check or redo the "
            "calibration.",
        ).format(exc.rejected[1], "?" if median is None else f"{median:.1f}")
    return QCoreApplication.translate(
        "RunErrors",
        "No point of frame 1 could be matched between the left and right images. Likely "
        "causes, most likely first: (1) left and right are swapped: load the left camera's "
        "images as the left camera; (2) the calibration does not belong to these images "
        "(another rig or session, or binned or cropped images); (3) the region of interest "
        "has no speckle texture. Otherwise check the Starting Point and that both cameras "
        "see the region.",
    )


def run_error_text(exc: BaseException) -> str:
    """The message shown for a run that raised ``exc``."""
    from al_dic_3d.matching.diagnostics import NoStereoLinksError

    if isinstance(exc, NoStereoLinksError):
        return _no_stereo_links_text(exc)
    if isinstance(exc, _USER_ERRORS):
        return str(exc).strip() or type(exc).__name__
    return f"{type(exc).__name__}: {exc}"
