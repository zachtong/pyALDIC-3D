"""Qt-free run diagnostics — every silent failure path becomes countable (F3.1).

The matching layer kills points quietly by design (``NaN`` = invalid): the
temporal honesty gate invalidates decorrelated nodes, the frame-1 stereo match
rejects NCC/IC-GN failures, per-frame cross/stereo matches drop non-converged
points, and the optional quality gates demote more. Each of those is the RIGHT
behavior for the data — but the user must be able to SEE it happened. This
module defines the plain, JSON-serializable diagnostics rows the strategies
attach to ``CorrespondenceSet.diagnostics``, and the post-run summary that the
CLI prints and the GUI writes into its log console.

Row schema (``dict``, plain types only, safe for ``json.dumps`` and the
parameters export)::

    {"frame": int, "cam": str, "n_pts": int, "n_valid": int,
     "n_gated": int, "note": str}

``cam`` is ``"L"`` / ``"R"`` for temporal tracks, ``"stereo"`` for cross-camera
stereo matches, ``"cross"`` for S3's direct L1->Rk matches.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from al_dic_3d.matching.contracts import CorrespondenceSet, DisparityField
    from al_dic_3d.matching.temporal import TemporalField

#: Frames whose final correspondence validity falls below this fraction are
#: reported as warnings by the run summary (CLI + GUI log).
LOW_VALIDITY_FRAC = 0.7

#: The reason string attached to honesty-gate kills (kept in one place so the
#: GUI/CLI wording matches the row payload).
GATE_NOTE = "validity gate: correlation vs frame 1 failed"


def frame_row(
    frame: int, cam: str, n_pts: int, n_valid: int, n_gated: int = 0, note: str = ""
) -> dict:
    """One JSON-serializable diagnostics row (plain Python types only)."""
    return {
        "frame": int(frame),
        "cam": str(cam),
        "n_pts": int(n_pts),
        "n_valid": int(n_valid),
        "n_gated": int(n_gated),
        "note": str(note),
    }


def temporal_rows(cam: str, tf: TemporalField) -> list[dict]:
    """Per-frame rows for one camera's temporal track (validity + gate kills)."""
    n_pts = int(tf.valid.shape[1])
    rows: list[dict] = []
    for k in range(tf.n_frames):
        n_gated = 0 if tf.n_gated is None else int(tf.n_gated[k])
        rows.append(
            frame_row(
                k,
                cam,
                n_pts,
                int(tf.valid[k].sum()),
                n_gated=n_gated,
                note=GATE_NOTE if n_gated else "",
            )
        )
    return rows


def stereo_rows(disp: DisparityField, note: str = "frame-1 stereo match") -> list[dict]:
    """The cross-camera stereo match row (NCC seed + IC-GN reject count)."""
    n = int(disp.valid.shape[0])
    return [frame_row(disp.frame_idx, "stereo", n, int(disp.valid.sum()), note=note)]


# --- post-run summary ---------------------------------------------------------


@dataclass(frozen=True)
class RunSummary:
    """Numeric post-run summary — formatting (tr()/print) is the caller's job."""

    n_frames: int
    n_pts: int
    valid_frac: tuple[float, ...]  # final per-frame correspondence validity
    median_valid_frac: float
    low_frames: tuple[int, ...]  # frames below LOW_VALIDITY_FRAC
    all_empty: bool  # EVERY frame ended 0% valid
    stereo_n_pts: int | None  # frame-1 stereo match candidates (None: no row)
    stereo_n_valid: int | None
    gated_by_cam: dict[str, int]  # cam -> total node-frames killed by the gate

    def to_meta(self) -> dict:
        """Plain JSON-serializable dict for ``RunResult.meta['summary']``."""
        return {
            "n_frames": int(self.n_frames),
            "n_pts": int(self.n_pts),
            "valid_frac": [round(float(f), 6) for f in self.valid_frac],
            "median_valid_frac": round(float(self.median_valid_frac), 6),
            "low_frames": [int(k) for k in self.low_frames],
            "all_empty": bool(self.all_empty),
            "stereo_n_pts": None if self.stereo_n_pts is None else int(self.stereo_n_pts),
            "stereo_n_valid": None if self.stereo_n_valid is None else int(self.stereo_n_valid),
            "gated_by_cam": {str(c): int(n) for c, n in self.gated_by_cam.items()},
        }


def summarize_run(
    cs: CorrespondenceSet,
    points_3d: NDArray[np.float64] | None = None,
    low: float = LOW_VALIDITY_FRAC,
) -> RunSummary:
    """Derive the post-run summary from the FINAL correspondence (+ optional 3D).

    Validity counts the positions the user actually gets: finite reconstructed
    points when ``points_3d`` is given (post quality gates / outlier removal),
    else finite positions in both cameras.
    """
    if points_3d is not None:
        valid = np.isfinite(np.asarray(points_3d, dtype=np.float64)).all(axis=2)
    else:
        valid = np.isfinite(cs.xL).all(axis=2) & np.isfinite(cs.xR).all(axis=2)
    n_frames, n_pts = valid.shape
    frac = valid.mean(axis=1) if n_pts else np.zeros(n_frames)

    rows = tuple(getattr(cs, "diagnostics", ()) or ())
    stereo = next((r for r in rows if r.get("cam") == "stereo" and r.get("frame") == 0), None)
    gated: dict[str, int] = {}
    for r in rows:
        if int(r.get("n_gated", 0)):
            cam = str(r.get("cam", "?"))
            gated[cam] = gated.get(cam, 0) + int(r["n_gated"])

    return RunSummary(
        n_frames=int(n_frames),
        n_pts=int(n_pts),
        valid_frac=tuple(float(f) for f in frac),
        median_valid_frac=float(np.median(frac)) if n_frames else 0.0,
        low_frames=tuple(int(k) for k in range(n_frames) if frac[k] < low),
        all_empty=not bool(valid.any()),
        stereo_n_pts=None if stereo is None else int(stereo["n_pts"]),
        stereo_n_valid=None if stereo is None else int(stereo["n_valid"]),
        gated_by_cam=gated,
    )


def summary_lines(summary: RunSummary, gates: dict | None = None) -> list[tuple[str, str]]:
    """English ``(level, message)`` lines for headless consumers (CLI, logs).

    The GUI builds its own tr()-wrapped equivalent from the same
    :class:`RunSummary` numbers; this stays Qt-free by contract.
    """
    lines: list[tuple[str, str]] = []
    if summary.stereo_n_pts:
        frac = summary.stereo_n_valid / summary.stereo_n_pts
        level = "warning" if frac < LOW_VALIDITY_FRAC else "info"
        lines.append(
            (
                level,
                f"frame-1 stereo match: {summary.stereo_n_valid}/{summary.stereo_n_pts} "
                f"points matched ({frac * 100:.0f}%)",
            )
        )
    for cam, n in sorted(summary.gated_by_cam.items()):
        lines.append(
            (
                "warning",
                f"camera {cam}: {n} node-frames removed ({GATE_NOTE})",
            )
        )
    for k in summary.low_frames:
        lines.append(
            (
                "warning",
                f"frame {k}: only {summary.valid_frac[k] * 100:.0f}% of points valid",
            )
        )
    if gates:
        for key, label in (
            ("znssd_demoted", "quality gate (ZNSSD)"),
            ("reproj_demoted", "reprojection gate"),
            ("outliers_removed", "3D outlier filter"),
        ):
            n = int(gates.get(key, 0))
            if n:
                lines.append(("info", f"{label} removed {n} positions"))
    if summary.all_empty:
        lines.append(
            (
                "error",
                "no valid points in ANY frame — the run produced an empty result "
                "(check ROI/masks/seeding and the messages above)",
            )
        )
    else:
        lines.append(
            (
                "info",
                f"analysis complete — {summary.n_frames} frames, median validity "
                f"{summary.median_valid_frac * 100:.0f}%, {len(summary.low_frames)} "
                f"frame(s) below {LOW_VALIDITY_FRAC * 100:.0f}%",
            )
        )
    return lines
