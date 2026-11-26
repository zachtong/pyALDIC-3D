# 14. Troubleshooting

This chapter covers the common failure modes, adapted from the 2D app plus the
issues specific to stereo / 3D.

## "Run 3D Analysis" is disabled

The button stays disabled until the project is ready; its tooltip and the
sidebar hint name what is missing. Usual causes:

- **Both camera folders not loaded**, or the two sequences have different lengths
  (*Mismatch: N left vs M right*) — see [Loading images](03-loading-images.md).
- **No calibration** — run *Calibrate from images…*, import one, or enter manual
  parameters ([Calibration](04-calibration.md)).
- **No Region of Interest** on the LEFT camera, frame 1
  ([Region of interest](07-region-of-interest.md)).
- **An input that is set but not usable** — the message names it: a
  calibration file that does not load with the selected format, left and right
  sequences that are the same files, frames of different sizes within a
  camera, unreadable images, or an ROI mask drawn for images of another size.
- **Images of another size than the calibration** — *left camera: the
  calibration was made for 1920x1200 images, but the images are 960x600…*.
  Binned or cropped images need their own calibration: a calibration describes
  the pixels it was made from, and on other pixels every 3D point comes out
  wrong. Calibrate again from board images taken with the same binning / crop
  (or load the full-size images). The check needs the image size in the
  calibration file: DICe files and the YAML the built-in calibrator now
  writes carry it. A YAML written by an earlier version has none, so the check
  is skipped for it; calibrating again writes a file that has it.

Unseeded ROI regions do **not** block the run — they are auto-seeded, so a
partial *Starting Points* setup is fine.

## "No point of frame 1 could be matched between the left and right images"

The run stops at the first step, matching the two cameras on frame 1, because
no point passed. When the message lists **likely causes**, nothing correlated
between the two views; check them in this order:

1. **Left and right are swapped.** The left camera's images must be loaded as
   the left camera (the calibration's camera 1). Swap the two folders.
2. **The calibration does not belong to these images**: another rig, another
   session, or images that were binned or cropped after calibrating. Load the
   calibration made for this setup, or calibrate again.
3. **The region of interest has no speckle texture** (a bare or saturated
   area). Move the ROI onto the speckle pattern.

Otherwise check the Starting Point and that both cameras see the region. Do
not raise **Stereo check** for this: with no link accepted, a looser check
only accepts wrong links (an empty "complete" run). When the message says
instead that the links were rejected **for their distance from the epipolar
line**, the calibration does not match the images (a camera moved, a wrong
file, or left and right swapped): check or redo the calibration.

## "This run would need about N GB of memory"

The run is refused before it starts because its projected peak memory exceeds
70 % of the RAM currently available. Analyse fewer frames, choose a coarser
**PARAMETERS > Subset Step**, or draw a smaller region of interest; closing
other applications also helps. From the command line the same refusal names
the config switch `ignore_memory_check = true` under `[advanced]`, which runs
anyway at the risk of swapping.

## The run produced no valid points

The canvas shows *Analysis produced no valid points — nothing to display. See
the log.* and the log records *No valid points in ANY frame…*. Work through, in
order:

1. **Calibration sanity.** Re-open the calibration QC (or the printed
   `_parameters` JSON). A plausible **baseline** (the physical camera separation
   in mm), sub-pixel **stereo RMS** and **epipolar RMS**, and a verify **scale
   error** near zero are the first things to confirm. A bad calibration
   triangulates matched pixels to nonsense and every point fails the
   reconstruction. If you imported a calibration, confirm you picked the right
   **Format** — a format mismatch silently garbles the intrinsics/extrinsics.
2. **ROI and masks.** Confirm the ROI actually covers textured specimen on the
   LEFT frame 1, and is larger than a couple of subset steps.
3. **Seeding.** In *Starting Points* mode, a seed in a low-texture region can
   fail its template match. Move seeds into well-speckled areas, or switch the
   initial guess to **FFT**.
4. **Search ranges.** Too-small **Stereo Search** clips the disparity; too-small
   **Temporal Search** (where FFT applies) clips the motion. Read the log for
   *stereo match* yields and per-frame validity.

## Low match fraction / few valid points

The log's *Frame-1 stereo match: X/Y points matched (Z%)* and per-frame validity
lines localize the loss. A low stereo yield has three usual causes, and the
*Stereo check removed …* line tells them apart:

- Many links fail the **Stereo check** for weak left-right correlation while
  others pass: a rough surface or a large stereo angle. Raise **Stereo check**
  (for example to 1.0). When *no* link passes, see the section above instead.
- The links fail the **Epipolar limit**, at a large median distance from their
  epipolar lines: the calibration does not match the images. Check or redo it.
  When no link survives, the run stops with that diagnosis.
- Few links are found at all: the disparity varies more than **Stereo Search**
  covers. Placing a Starting Point helps.

## "A camera has probably moved since the calibration"

The log warns *The frame-1 stereo links lie a median X px from their epipolar
lines (a calibration that fits the images gives under 0.3 px)…* when the links
pass the stereo check but sit consistently off their epipolar lines. Healthy
runs measure 0.02-0.25 px; the warning starts at 0.5 px. A camera that was
bumped, refocused or re-aimed after calibrating causes it: in a test where the
right camera was turned by 1.5 degrees, the median was 0.8 px and the
displacement magnitudes came out 8.6 % too large, with nothing else in the log
looking wrong. **Recalibrate the rig as it stands now** (and lock the camera
mounts and lenses before calibrating).

Temporal validity
that decays over frames points at motion exceeding the search / seed,
decorrelation, or (for large deformation or rotation) the wrong tracking mode —
switch to **Incremental** ([Workflow type](05-workflow-type.md)); the log
suggests this when validity collapses in accumulative mode. If validity decays
in incremental mode instead, update the reference every frame (the motion
between reference frames may be too large), and import per-frame masks when the
specimen moves far or cracks (the log suggests both). For a
specimen strained close to failure, raising **ADVANCED > Result checks >
Tracking check** (for example to 1.5) keeps more of the strongly deformed
points ([Parameters](08-parameters.md)). Enabling **Extra filters** will remove
more points, but every removal is counted in the log, so you can see whether a
gate (ZNSSD / reprojection / 3D-outlier) is doing the culling.

## Strain map is blank / exported strain is all NaN

The displacement looks fine, but after **Compute Strain** the overlay is empty
and exported strain reads `NaN`. With the default settings this almost always
means **edge-trim removed every node**. A node is trimmed when its distance to
the boundary is below `alpha × VSG-radius`. With the default **Strain window**
65 px (radius 32 px) and **Trim low-confidence edges** `alpha = 0.70`, the trim
band is ~22 px, so a region thinner than ~44 px — or a VSG size raised too high —
loses *all* of its nodes. The **Trimmed: N nodes (M%)** readout reads 100% in
that case.

Fixes (any one):

- **Reduce the Strain window** so `alpha × radius` stays below the region's
  half-thickness.
- **Lower Trim low-confidence edges** toward `0` (setting it to `0` disables
  trimming entirely).

Conversely, a VSG **smaller** than the node spacing fails differently: the plane
fit has too few neighbours and an inline warning tells you to raise the window to
at least a 3×3 node gauge.

## Large rotation gives crazy strain values

You are probably using **Infinitesimal** strain with a rotation beyond ~2°.
Infinitesimal strain reports rigid rotation as false strain (`cos θ − 1`). Switch
the strain type to **Green-Lagrange**, which is exactly zero under any rigid
rotation ([Strain post-processing](11-strain-processing.md)).

## The 3D View is empty or unavailable

- *3D view — run an analysis to see the reconstructed surface.* — the 3D View
  needs results; run first.
- If checking **3D View** does nothing or errors, the interactive viewer needs
  a working OpenGL context (pyvista / VTK ship with the package since v1.0.0).
  On headless or remote sessions without GPU/OpenGL, the 3D view degrades to an
  explanatory placeholder — use the 2D field canvas and the image/animation
  exports instead. If pyvista is missing (a stripped custom install), restore
  it with `pip install pyvista pyvistaqt`.

## Physically implausible W (out-of-plane)

If `W` is huge or the reconstructed surface is warped, suspect the calibration:
a wrong baseline scales all of Z, and swapped left/right cameras or a
mis-imported format tilts the surface. Re-verify the calibration against a
known-distance board.

## A session file won't open

- **Not a `.aldic3d` bundle (expected a zip)** — the file is corrupt or not a
  session bundle; `.aldic3d` files are zip archives and should not be hand-edited.
- **Unsupported schema version** — the file was saved by a newer pyALDIC-3D than
  you are running. Upgrade.
- **Images not found** — this is not a fatal error: the app auto-relocates moved
  image folders and, failing that, prompts you to *Locate Images* per camera.
  If you cancel that, **Open anyway** opens the project with its results
  viewable and exportable. See [Sessions](13-session.md).

## A run was cancelled but I still have results

That is by design: cancelling keeps the frames computed so far (later frames are
`NaN`), and only a cancel before any deformed frame finished returns to IDLE with
nothing. The log then ends with *Partial result — k of n frames computed,
median validity Z%*; the frames after the stop are not counted or flagged. A
cancel during strain keeps the displacement / 3D results and drops only the
strain ([Running](09-running.md)).

## The command line prints "error: …" and stops

`al-dic-3d run` reports an input it cannot use (a missing file, images of
another size than the calibration, a left/right frame-count mismatch, a run
that matched nothing) in one `error:` line and exits with code 2. The message
says what to change; the sections above explain each one. For a bug report,
run the same command with `--debug`, which prints the full Python traceback.

## The application crashed or shows an error dialog

An unexpected error opens a dialog with the details, and the installed
(Windows installer) application also writes them to a log file:

- `%LOCALAPPDATA%\pyALDIC-3D\logs\pyALDIC-3D.log` — messages and Python
  errors (on macOS / Linux: `~/pyALDIC-3D/logs/`);
- `pyALDIC-3D-crash.log` in the same folder — a native crash (for example in
  the 3D renderer), which cannot show a dialog.

Attach both files to a bug report. To see the output live, start
`pyaldic3d-cli.exe gui` from a terminal. `al-dic-3d self-test` checks the
installation itself (images, videos, translations, kernels, a small stereo
run, a 3D render) and names the part that fails.

On Python 3.10 or 3.11, a crash reading *Fatal Python error: deallocating
None* (or *deallocating True or False*) comes from PySide6 6.12.0, which
miscounts references on every interface signal. Current versions of
pyALDIC-3D do not install that release there. In an existing environment, run
`pip install "PySide6!=6.12.0"`, or use Python 3.12 or newer, where it is
harmless.

## The first run takes much longer

The numerical kernels are compiled once per installation. The application
does this in the background a couple of seconds after it opens (the log says
*Preparing compute kernels in the background…* and later *Compute kernels
ready*); a run started before that finishes waits for the compilation.

## Every frame of an incremental run is slow

The log ends with *Camera L: the initial-guess search had to widen on N frames
(up to R px)*. At every incremental reference switch the initial guess comes
from an FFT search. Without per-frame masks, each reference frame reuses the
region drawn on frame 1. Once the specimen has moved, that region puts subsets
on its edge, their correlation peaks hit the search boundary, and the search
grows step by step, up to half the image, on every frame. On a specimen pulled
to failure this made each frame about five times slower. Import per-frame
masks ([Region of interest](07-region-of-interest.md)), or use
**Accumulative** ([Workflow type](05-workflow-type.md)). With per-frame masks
already imported, the motion between reference frames really is that large:
raise **Temporal Search** ([Parameters](08-parameters.md)).

Back to the [index](index.md).
