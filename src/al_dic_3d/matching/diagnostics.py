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
stereo matches, ``"cross"`` for S3's direct L1->Rk matches. A temporal row also
carries ``"search_px": int`` on frames where the engine widened its FFT
initial-guess search (the widest search it moved to).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from al_dic_3d.matching.contracts import CorrespondenceSet, DisparityField
    from al_dic_3d.matching.temporal import TemporalField

#: Frames whose final correspondence validity falls below this fraction are
#: reported as warnings by the run summary (CLI + GUI log).
LOW_VALIDITY_FRAC = 0.7

#: A camera whose FFT search the engine widened on at least this many frames gets
#: a log line: once (frame 1, a large first motion) is normal; on most reference
#: switches it means the reference region no longer fits the specimen.
WIDENING_MIN_FRAMES = 3

#: The reason string attached to honesty-gate kills (kept in one place so the
#: GUI/CLI wording matches the row payload).
GATE_NOTE = "validity gate: correlation vs frame 1 failed"


# Frames on which the 2D engine solved no node (fix batch V): the frame is
# invalidated, the rest of the track is kept.
ZERO_FILL_NOTE = "engine solved no node on this frame (frame invalidated)"


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
    zero_filled = set(getattr(tf, "zero_filled", ()) or ())
    for k in range(tf.n_frames):
        n_gated = 0 if tf.n_gated is None else int(tf.n_gated[k])
        if k in zero_filled:
            note = ZERO_FILL_NOTE
        else:
            note = GATE_NOTE if n_gated else ""
        row = frame_row(k, cam, n_pts, int(tf.valid[k].sum()), n_gated=n_gated, note=note)
        search = int((getattr(tf, "fft_widened", None) or {}).get(k, 0))
        rows.append({**row, "search_px": search} if search else row)
    return rows


def stereo_rows(
    disp: DisparityField,
    note: str = "frame-1 stereo match",
    rejected: tuple[int, int] = (0, 0),
) -> list[dict]:
    """The cross-camera stereo match row (NCC seed + IC-GN reject count).

    ``rejected`` = ``(n_znssd, n_epipolar)`` links the acceptance check removed
    after IC-GN converged (fix batch V); they count as the row's ``n_gated`` and
    are named in the note so the log can say why the links were dropped.
    """
    n = int(disp.valid.shape[0])
    n_z, n_e = int(rejected[0]), int(rejected[1])
    if n_z or n_e:
        note = f"{note}; rejected {n_z} (ZNSSD) + {n_e} (epipolar)"
    return [
        frame_row(disp.frame_idx, "stereo", n, int(disp.valid.sum()), n_gated=n_z + n_e, note=note)
    ]


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
    # cam -> frames on which the engine widened its FFT search; widest search (px)
    fft_widened_by_cam: dict[str, int] = field(default_factory=dict)
    fft_max_search_px: int = 0

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
            "fft_widened_by_cam": {str(c): int(n) for c, n in self.fft_widened_by_cam.items()},
            "fft_max_search_px": int(self.fft_max_search_px),
        }


def summarize_run(
    cs: CorrespondenceSet,
    points_3d: NDArray[np.float64] | None = None,
    low: float = LOW_VALIDITY_FRAC,
    n_eligible: int | None = None,
) -> RunSummary:
    """Derive the post-run summary from the FINAL correspondence (+ optional 3D).

    Validity counts the positions the user actually gets: finite reconstructed
    points when ``points_3d`` is given (post quality gates / outlier removal),
    else finite positions in both cameras.

    ``n_eligible``: the number of mesh nodes that CAN be valid — those inside
    the ROI (``RunResult.meta["n_pts_in_roi"]``). The mesh covers the ROI's
    bounding box, so without it a shaped ROI's out-of-mask nodes deflated every
    percentage (fix batch V). ``None`` falls back to all nodes.
    """
    if points_3d is not None:
        valid = np.isfinite(np.asarray(points_3d, dtype=np.float64)).all(axis=2)
    else:
        valid = np.isfinite(cs.xL).all(axis=2) & np.isfinite(cs.xR).all(axis=2)
    n_frames, n_pts = valid.shape
    denom = n_pts if not n_eligible else max(1, min(int(n_eligible), n_pts))
    frac = valid.sum(axis=1) / denom if n_pts else np.zeros(n_frames)

    rows = tuple(getattr(cs, "diagnostics", ()) or ())
    stereo = next((r for r in rows if r.get("cam") == "stereo" and r.get("frame") == 0), None)
    gated: dict[str, int] = {}
    widened: dict[str, int] = {}
    max_search = 0
    for r in rows:
        cam = str(r.get("cam", "?"))
        if int(r.get("n_gated", 0)):
            gated[cam] = gated.get(cam, 0) + int(r["n_gated"])
        if int(r.get("search_px", 0)):
            widened[cam] = widened.get(cam, 0) + 1
            max_search = max(max_search, int(r["search_px"]))

    return RunSummary(
        n_frames=int(n_frames),
        n_pts=int(n_pts),
        valid_frac=tuple(float(f) for f in frac),
        median_valid_frac=float(np.median(frac)) if n_frames else 0.0,
        low_frames=tuple(int(k) for k in range(n_frames) if frac[k] < low),
        all_empty=not bool(valid.any()),
        stereo_n_pts=(
            None
            if stereo is None
            else int(stereo["n_pts"])
            if not n_eligible
            else min(int(stereo["n_pts"]), denom)
        ),
        stereo_n_valid=None if stereo is None else int(stereo["n_valid"]),
        gated_by_cam=gated,
        fft_widened_by_cam=widened,
        fft_max_search_px=max_search,
    )


def widening_advice(summary: RunSummary) -> dict[str, int]:
    """Cameras (-> widened frame count) whose FFT search widened on many frames.

    The engine widens its FFT initial-guess search when a correlation peak lands
    on the search boundary, and reports it only to the log file. Measured on a
    specimen pulled to failure, incremental every frame without per-frame
    masks: the frame-1 region reused at each reference frame put subsets on the
    moved specimen's edge, 56-128 nodes per frame hit the boundary (0 with
    per-frame masks) and the search climbed 20 -> 702 px on every frame, about
    five times slower.
    """
    return {
        cam: n for cam, n in sorted(summary.fft_widened_by_cam.items()) if n >= WIDENING_MIN_FRAMES
    }


def collapse_advice(
    summary: RunSummary,
    reference_mode: str | None,
    ref_update_mode: str | None = None,
    per_frame_masks: bool = False,
) -> str | None:
    """``"incremental"`` / ``"fewer_updates"`` / ``"masks"`` when validity collapses.

    Fix batch V: on a specimen pulled to failure the GUI defaults (every frame
    tracked against frame 1) keep ~70 % of the nodes in frame 1 and ~2 % from
    frame 10 on, and nothing told the user why. A collapse is the first
    deformed frame reasonably valid (>= 30 %) and some later frame below a
    quarter of it.

    * accumulative -> the incremental mode;
    * incremental with a reference update every frame, or with per-frame masks
      already given -> fewer updates (or accumulative): each update adds a small
      tracking error that sums over the sequence, and with per-frame masks the
      engine drops the mesh cells outside each new reference's mask for good
      (a notched specimen pulled to failure, 136 frames: every frame + masks
      kept 21 % of the points at the end, accumulative 82 %);
    * incremental with rare updates and no per-frame masks -> per-frame masks
      (a valid region that changes, e.g. a crack).

    ``ref_update_mode=None`` (a result saved before it was recorded) reads as
    the default, every frame.
    """
    vf = summary.valid_frac
    if len(vf) < 3 or vf[1] < 0.3 or min(vf[2:]) >= 0.25 * vf[1]:
        return None
    if reference_mode == "accumulative":
        return "incremental"
    if ref_update_mode in (None, "every_frame") or per_frame_masks:
        return "fewer_updates"
    return "masks"


def summary_lines(
    summary: RunSummary, gates: dict | None = None, stopped: dict | None = None
) -> list[tuple[str, str]]:
    """English ``(level, message)`` lines for headless consumers (CLI, logs).

    The GUI builds its own tr()-wrapped equivalent from the same
    :class:`RunSummary` numbers; this stays Qt-free by contract. ``stopped``
    accepts the run meta (or any dict with ``stopped_early`` /
    ``stopped_at_frame`` / ``stop_reason``) and prepends the R2 partial-run
    banner: frames ``[0, stopped_at_frame)`` were kept, the rest are NaN.
    """
    lines: list[tuple[str, str]] = []
    if stopped and stopped.get("stopped_early"):
        k = int(stopped.get("stopped_at_frame") or 0)
        lines.append(
            (
                "warning",
                f"stopped early at frame {k}/{summary.n_frames} — "
                f"kept {k} computed frames (later frames are empty)",
            )
        )
    elif stopped and stopped.get("stop_reason"):
        lines.append(("warning", f"run interrupted: {stopped['stop_reason']}"))
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
    run_params = (stopped or {}).get("run_params") or {}
    for cam, n in widening_advice(summary).items():
        head = (
            f"camera {cam}: the initial-guess search had to widen on {n} frames "
            f"(up to {summary.fft_max_search_px} px), which slows the run"
        )
        if run_params.get("per_frame_masks"):
            tail = "; if the motion between reference frames is that large, raise fft_search"
        else:
            tail = (
                "; in incremental mode this usually means the frame-1 region no longer "
                "covers the specimen at later reference frames: give per-frame masks "
                '(left_mask / right_mask) or use reference_mode = "accumulative"'
            )
        lines.append(("warning", head + tail))
    advice = collapse_advice(
        summary,
        run_params.get("reference_mode"),
        run_params.get("ref_update_mode"),
        bool(run_params.get("per_frame_masks", False)),
    )
    if advice is not None:
        worst = min(summary.valid_frac[2:]) * 100
        start = summary.valid_frac[1] * 100
        if advice == "incremental":
            text = (
                f"validity falls from {start:.0f}% (frame 1) to {worst:.0f}%: tracking every "
                "frame against frame 1 cannot follow large deformation; try "
                'reference_mode = "incremental" (GUI: WORKFLOW TYPE > Incremental)'
            )
        elif advice == "fewer_updates":
            text = (
                f"validity falls from {start:.0f}% (frame 1) to {worst:.0f}%: every reference "
                "update adds a small tracking error and these add up over a long sequence; "
                'try fewer updates (ref_update_mode = "every_n", e.g. ref_update_n = 10) '
                'or reference_mode = "accumulative"'
            )
        else:
            text = (
                f"validity falls from {start:.0f}% (frame 1) to {worst:.0f}%: if the valid "
                "region changes during the test (cracks, failure), give per-frame masks"
            )
        lines.append(("warning", text))
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
