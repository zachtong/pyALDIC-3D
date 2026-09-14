# 9. Running

## The Run button

The **Run 3D Analysis** button at the top of the right sidebar starts the full
stereo-correspondence + triangulation pipeline (keyboard: **F5**). It is
disabled until the project is ready. If it is not ready, its tooltip reads
*Not ready — …* and the sidebar's **Ready** label and the sidebar hint spell out
what is missing (typically: load both camera folders, provide a calibration,
draw an ROI on the LEFT camera frame 1). Unseeded ROI regions do **not** block
the run — they are auto-seeded (see [Initial guess](06-initial-guess.md)).

Readiness checks that the inputs are *usable*, not only that they are set:

- the calibration file loads with the selected format (the message quotes
  the reason when it does not);
- the left and right sequences are not the same image files (for example
  one folder dropped on both cameras);
- each camera's first and last frames have the same size;
- a drawn ROI mask has the size of the images.

With no Starting Point placed, the **Ready** label adds an amber note that the
stereo offset is found automatically and frame 1 is seeded by FFT.

A **stale-result** warning — *Parameters changed since this result — re-run to
update* — appears in amber when the parameters differ from the ones that
produced the results on screen. A failed or cancelled run does not reset it,
because the results on screen are still the older ones.

## Cancelling keeps partial frames

Below Run, the red **Cancel** button is enabled only while a run is in progress.
Cancelling stops cleanly and, importantly, **keeps the frames already computed**:
frames `[0, stopped_at)` are retained and later frames are left as `NaN`. The
progress area shows *Cancelling — finishing current frame…* and then *Stopped
early — partial results kept*.

Every kept frame is still verified before it is kept (the progress label says
*verifying frame k of N (keeping the frames tracked before the stop)*), so a
cancel late in a long run can take a little while. The two cameras are
tracked one after the other, so a cancel while the **left** camera is still
being tracked keeps nothing: the right camera has not been tracked yet. The
command-line `al-dic-3d run` handles that case differently: its first Ctrl+C
tracks the right camera over the frames the left one finished, then writes
them (a second Ctrl+C aborts).

Only when **nothing** beyond the reference frame was computed does the run return
to IDLE with *Run cancelled* (there is nothing worth keeping). A cancel that
happens during the strain pass keeps the finished displacement / 3D results and
simply drops the strain.

## Progress and ETA

The **PROGRESS** section shows:

- A thin progress bar (idle label *Ready*; during a run *{pct}% — {message}*,
  in plain words such as *Preparing: matching the two cameras*, *Left camera:
  tracking frame 3 of 40*, *Right camera: verifying frame 3 of 40*,
  *assembling frame 3 of 40*).
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
  count (only when **Extra filters** is enabled).
- *Validity falls from X% (frame 1) to Y%: …* — the run kept most points at
  first and then lost them. In accumulative mode the message suggests the
  incremental mode (tracking every frame against frame 1 cannot follow large
  deformation); otherwise it suggests per-frame masks.
- *Analysis complete — F frames, median validity Z%* — the success summary,
  with *K frame(s) below T% (see above)* when frames were flagged.

Percentages count the nodes inside the ROI, not the whole mesh rectangle, so a
shaped ROI can reach 100 %.

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
Window** buttons enable once results exist. A run stopped early that kept frames
counts as finished: export and strain work on the kept frames. A failed run
leaves the previous results, if any, on screen, and shows an error dialog with
the reason.

Next: [Viewing results →](10-viewing-results.md)
