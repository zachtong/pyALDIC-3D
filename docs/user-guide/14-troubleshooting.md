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

Unseeded ROI regions do **not** block the run — they are auto-seeded, so a
partial *Starting Points* setup is fine.

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
lines localize the loss. Low stereo yield points at calibration or an
insufficient **Stereo Search**; temporal validity that decays over frames points
at motion exceeding the search / seed, decorrelation, or (for large rotation)
the wrong tracking mode — switch to **Incremental + Every Frame**
([Workflow type](05-workflow-type.md)). Enabling **Quality gates** will remove
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
  Cancelling the prompt aborts the open. See [Sessions](13-session.md).

## A run was cancelled but I still have results

That is by design: cancelling keeps the frames computed so far (later frames are
`NaN`), and only a cancel before any deformed frame finished returns to IDLE with
nothing. A cancel during strain keeps the displacement / 3D results and drops
only the strain ([Running](09-running.md)).

Back to the [index](index.md).
