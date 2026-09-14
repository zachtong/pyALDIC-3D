"""Translated text for the calibration diagnostics' findings.

The compute layer (:mod:`al_dic_3d.calibration.diagnostics`) gives every
finding a stable code, the camera and the numbers; the sentences shown in the
GUI are built from those through the i18n pipeline, so they translate like any
other text. A code this module does not know falls back to the finding's
English message: a new check is never silent.
"""

from __future__ import annotations

from collections.abc import Mapping

from al_dic.gui.theme import COLORS
from PySide6.QtCore import QCoreApplication

from al_dic_3d.calibration.diagnostics import (
    EXTRAPOLATION_CHECK_SKIPPED,
    EXTRAPOLATION_UNDETERMINED,
    LENS_MODEL_INADEQUATE,
    LOW_COVERAGE,
    MODEL_CHECK_SKIPPED,
    SEVERITY_WARNING,
    CalibrationDiagnostics,
    Finding,
)


def _number(values: Mapping, key: str) -> float:
    try:
        return float(values.get(key, float("nan")))
    except (TypeError, ValueError):
        return float("nan")


def finding_text(finding: Finding) -> str:
    """One finding as a translated sentence built from its code and values."""
    cam, v = finding.camera, finding.values
    if finding.code == EXTRAPOLATION_UNDETERMINED and v.get("chosen_model") == "k3 fixed":
        return QCoreApplication.translate(
            "CalibrationFindings",
            "Camera {0}: the board reached {1:.0%} of the image-corner radius. Beyond it "
            "the lens model is a guess: two equally good fits differ by up to {2:.2f} px "
            "there. With k3 fixed, the corners are right only if the lens has no k3 "
            "distortion: add views with the board near the image corners, or keep the "
            "region of interest inside the covered area.",
        ).format(cam, _number(v, "cover_ratio"), _number(v, "disagreement_outside_px"))
    if finding.code == EXTRAPOLATION_UNDETERMINED:
        return QCoreApplication.translate(
            "CalibrationFindings",
            "Camera {0}: the board reached {1:.0%} of the image-corner radius. Beyond it "
            "the lens model is a guess: two equally good fits differ by up to {2:.2f} px "
            "there. Add views with the board near the image corners, keep the region of "
            "interest inside the covered area, or fix k3 for a low-distortion lens.",
        ).format(cam, _number(v, "cover_ratio"), _number(v, "disagreement_outside_px"))
    if finding.code == LOW_COVERAGE:
        return QCoreApplication.translate(
            "CalibrationFindings",
            "Camera {0}: the board reached {1:.0%} of the image-corner radius; the lens "
            "model is fitted only inside that radius.",
        ).format(cam, _number(v, "cover_ratio"))
    if finding.code == LENS_MODEL_INADEQUATE and v.get("board_refined"):
        return QCoreApplication.translate(
            "CalibrationFindings",
            "Camera {0}: the residuals follow a pattern the lens model does not explain "
            "(binned excess {1:.1f}, fitted field {2:.1f} × noise; about 1 when the model "
            "fits), although the board shape is already optimised. A lens the model cannot "
            "describe, a board that bends differently from view to view, or detector bias "
            "can cause this.",
        ).format(cam, _number(v, "residual_excess"), _number(v, "residual_field_ratio"))
    if finding.code == LENS_MODEL_INADEQUATE:
        return QCoreApplication.translate(
            "CalibrationFindings",
            "Camera {0}: the residuals follow a pattern the lens model does not explain "
            "(binned excess {1:.1f}, fitted field {2:.1f} × noise; about 1 when the model "
            "fits). Often the board is the cause (not flat, or its points not exactly where "
            "the board description puts them): tick Joint bundle adjustment and Optimize "
            "board shape. A lens the model cannot describe or detector bias can also cause "
            "this.",
        ).format(cam, _number(v, "residual_excess"), _number(v, "residual_field_ratio"))
    if finding.code == EXTRAPOLATION_CHECK_SKIPPED:
        return QCoreApplication.translate(
            "CalibrationFindings",
            "Camera {0}: the extrapolation check was skipped (too few usable views).",
        ).format(cam)
    if finding.code == MODEL_CHECK_SKIPPED:
        cells = _number(v, "cells")
        return QCoreApplication.translate(
            "CalibrationFindings",
            "Camera {0}: the lens-model check was skipped: the points fill only {1} image cells.",
        ).format(cam, int(cells) if cells == cells else 0)
    return finding.message_en


def findings_lines(diagnostics: CalibrationDiagnostics | None) -> list[str]:
    """Every finding as a result-panel line, warnings marked."""
    if diagnostics is None:
        return []
    lines = []
    for finding in diagnostics.findings:
        text = finding_text(finding)
        if finding.severity == SEVERITY_WARNING:
            text = QCoreApplication.translate("CalibrationFindings", "Warning: {0}").format(text)
        lines.append(text)
    return lines


def result_colour(diagnostics: CalibrationDiagnostics | None) -> str:
    """The result text colour: amber when any finding is a warning, else green."""
    if diagnostics is not None and diagnostics.worst_severity == SEVERITY_WARNING:
        return COLORS.WARNING
    return COLORS.SUCCESS
