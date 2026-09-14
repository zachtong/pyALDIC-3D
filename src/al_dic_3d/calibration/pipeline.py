"""One calibration pipeline for the CLI and the GUI (Qt-free).

``al-dic-3d calibrate`` and the GUI's calibration worker used to repeat the
same sequence, so a check added to one could be forgotten in the other
(calibration diagnostics brief 2026-09-14, section 5.2). Both now call
:func:`run_calibration`:

1. ``calibrate_stereo``;
2. optional ``bundle_refine``, on the detections the solve used (for dot
   targets the eccentricity-corrected centres);
3. ``diagnose_calibration`` on the final calibration, with the board it was
   fitted with: the refined board points after the bundle adjustment's board
   shape or the release-object solve, the nominal lattice otherwise;
4. ``summarize``, including the diagnostics' numbers and finding codes.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace

import numpy as np
from numpy.typing import NDArray

from al_dic_3d.calibration.bundle import bundle_refine
from al_dic_3d.calibration.detect import BoardDetection
from al_dic_3d.calibration.diagnostics import (
    CalibrationDiagnostics,
    DiagnosticThresholds,
    diagnose_calibration,
)
from al_dic_3d.calibration.report import summarize
from al_dic_3d.calibration.solve import StereoResult, calibrate_stereo

# The solve options the diagnostics' alternative mono fits repeat.
_MONO_OPTIONS = ("fix_k3", "zero_tangent", "fix_aspect", "release_object")


@dataclass(frozen=True)
class CalibrationRun:
    """Everything one calibration produced."""

    result: StereoResult  # ``rig`` is the final calibration (after bundle adjustment)
    diagnostics: CalibrationDiagnostics
    stats: dict[str, float | int | str]  # ``summarize`` plus the bundle numbers
    bundle_info: dict | None = None  # ``bundle_refine``'s info when it ran


def with_board(
    detections: Sequence[BoardDetection],
    ids: NDArray[np.int64],
    points: NDArray[np.float64],
) -> list[BoardDetection]:
    """``detections`` with their object points replaced by a refined board, by point id.

    A view with a point the refined board lacks is marked unusable: its points
    were not part of the board-shape fit.
    """
    lut = {int(i): np.asarray(p, np.float64) for i, p in zip(ids, points, strict=True)}
    out: list[BoardDetection] = []
    for det in detections:
        if not det.ok:
            out.append(det)
            continue
        try:
            obj = np.array([lut[int(i)] for i in det.ids], np.float64).reshape(-1, 3)
        except KeyError:
            reason = "a point outside the refined board"
            out.append(BoardDetection(ok=False, method=det.method, reason=reason))
            continue
        out.append(replace(det, object_points=obj))
    return out


def _fitted_board(
    result: StereoResult,
    bundle_info: dict | None,
    joint_refine: bool,
    left: Sequence[BoardDetection],
    right: Sequence[BoardDetection],
) -> tuple[Sequence[BoardDetection], Sequence[BoardDetection], bool]:
    """The detections with the board the final rig was fitted with, and whether it is refined.

    Real photos (brief section 7.4): judged against the nominal lattice, a
    board-shape optimisation would leave the lens-model check blaming the lens
    for the board's own error.
    """
    if bundle_info is not None:  # the bundle adjustment produced the final rig
        if "board_points" not in bundle_info:
            return left, right, False
        ids, pts = bundle_info["board_ids"], bundle_info["board_points"]
        return with_board(left, ids, pts), with_board(right, ids, pts), True
    if joint_refine:  # the stereo solve refitted the intrinsics on the nominal board
        return left, right, False
    out, refined = [], False
    for cam, dets in (("L", left), ("R", right)):
        mono = result.mono.get(cam)
        if mono is not None and mono.board_points is not None:  # release-object solve
            dets = with_board(dets, mono.board_ids, mono.board_points)
            refined = True
        out.append(dets)
    return out[0], out[1], refined


def run_calibration(
    left: Sequence[BoardDetection],
    right: Sequence[BoardDetection],
    image_size: tuple[int, int],
    *,
    options: Mapping | None = None,
    thresholds: DiagnosticThresholds | None = None,
    progress: Callable[[str], None] | None = None,
) -> CalibrationRun:
    """Solve, optionally bundle-adjust, diagnose and summarize one stereo calibration.

    ``options`` holds ``calibrate_stereo``'s keywords plus ``bundle`` and
    ``board_morphology`` (both False by default). ``progress`` receives short
    English stage names. Raises ``ValueError`` like ``calibrate_stereo``.
    """
    opts = dict(options or {})
    bundle = bool(opts.pop("bundle", False))
    morphology = bool(opts.pop("board_morphology", False))
    say = progress or (lambda _stage: None)
    result = calibrate_stereo(left, right, image_size, **opts)
    used_l = result.detections.get("L", left)
    used_r = result.detections.get("R", right)
    info = None
    if bundle:
        say("bundle adjustment")
        rig, info = bundle_refine(
            used_l,
            used_r,
            result,
            zero_tangent=opts.get("zero_tangent", True),
            fix_k3=opts.get("fix_k3", False),
            board_morphology=morphology,
            progress=progress,
        )
        result = replace(result, rig=rig)
    say("diagnostics")
    diag_l, diag_r, refined = _fitted_board(
        result, info, bool(opts.get("joint_refine", False)), used_l, used_r
    )
    mono_options = {key: opts[key] for key in _MONO_OPTIONS if key in opts}
    if refined:
        # The alternative fits take the refined board as it is; the solve's own
        # mono fits (nominal board) cannot stand in for one of them.
        mono_options["release_object"] = False
    diagnostics = diagnose_calibration(
        result.rig,
        diag_l,
        diag_r,
        image_size,
        mono=None if refined else result.mono,
        thresholds=thresholds,
        **mono_options,
    )
    stats = summarize(result, left, right, image_size, diagnostics=diagnostics)
    if info is not None:
        stats["ba_rms_before"] = info["rms_before"]
        stats["ba_rms_after"] = info["rms_after"]
        stats["ba_mono_views"] = info["n_mono_views"]
        if "board_z_range" in info:
            stats["ba_board_z_range"] = info["board_z_range"]
    return CalibrationRun(result, diagnostics, stats, info)
