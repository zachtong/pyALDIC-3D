# 9. Running

## The Run button

The **Run 3D Analysis** button at the top of the right sidebar starts the full
stereo-correspondence + triangulation pipeline (keyboard: **F5**). It is
disabled until the project is ready. If it is not ready, its tooltip reads
*Not ready — …* and the sidebar's **Ready** label and the sidebar hint spell out
what is missing (typically: load both camera folders, provide a calibration,
draw an ROI on the LEFT camera frame 1). Unseeded ROI regions do **not** block
the run — they are auto-seeded (see [Initial guess](06-initial-guess.md)).

A **stale-result** warning — *Parameters changed since this result — re-run to
update* — appears in amber when you edit parameters after a run, so you know the
displayed field is out of date.

## Cancelling keeps partial frames

Below Run, the red **Cancel** button is enabled only while a run is in progress.
Cancelling stops cleanly and, importantly, **keeps the frames already computed**:
frames `[0, stopped_at)` are retained and later frames are left as `NaN`. The
progress area shows *Cancelling — finishing current frame…* and then *Stopped
early — partial results kept*.

Only when **nothing** beyond the reference frame was computed does the run return
to IDLE with *Run cancelled* (there is nothing worth keeping). A cancel that
happens during the strain pass keeps the finished displacement / 3D results and
simply drops the strain.

## Progress and ETA

The **PROGRESS** section shows:

- A thin progress bar (idle label *Ready*; during a run *{pct}% — {message}*).
- **ELAPSED** and **REMAINING** timestamps, updated each second (REMAINING is a
  linear ETA from elapsed ÷ fraction done).

## The failure-accounting log

The console **LOG** at the bottom of the right sidebar is the run's honest
ledger. Every gate and every silent kill becomes a line, so a run that produces
few points tells you *why*. Representative messages:

- *Frame-1 stereo match: X/Y points matched (Z%)* — the initial stereo yield.
- *Camera L: validity gate removed N node-frames (correlation vs frame 1
  failed)* — temporal correlation failures.
- *Frame k: only Z% of points valid* — a per-frame low-validity warning.
- *Quality gate (ZNSSD) removed N positions* / *Reprojection gate removed N
  positions* / *3D outlier filter removed N positions* — each quality gate's
  count (only when Quality gates is enabled).
- *Analysis complete — F frames, median validity Z%, K frame(s) below T%* — the
  success summary.

You can filter the log by severity (**All messages** / **Info** /
**Warnings + errors** / **Errors only**), **Save…** it to a text file, or
**Clear** it. The log retains up to 2000 lines.

## Empty-result handling

If a run produces **zero** finite points in every frame, it is treated as a
failure even though the pipeline ran to the end. The log records *No valid points
in ANY frame — the run produced an empty result. Check ROI, masks and seeding
(details above).*, and the canvas shows a red notice: *Analysis produced no valid
points — nothing to display. See the log.* See
[Troubleshooting](14-troubleshooting.md) for the usual causes (bad calibration,
too-small ROI, seeds in low-texture regions).

## Completion

When a run finishes cleanly, the **Strain Post-Processing** window opens
automatically **the first time** (later runs do not steal focus — a log line
notes it is available from the sidebar). The **Export Results** and **Open Strain
Window** buttons enable once results exist. A cancelled or failed run does not
open the strain window and leaves Export disabled.

Next: [Viewing results →](10-viewing-results.md)
