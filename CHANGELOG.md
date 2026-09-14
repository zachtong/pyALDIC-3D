# Changelog

All notable user-facing changes to pyALDIC-3D are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and versioning follows [Semantic Versioning](https://semver.org/).

Entries are per package version (`al-dic-3d` on PyPI, `vX.Y.Z` git tags). The
`v1.x` milestones in `docs/architecture/00_INDEX.md` are internal documentation
milestones, not releases. The GitHub release notes for a tag are this file's
section for that version (see `docs/RELEASING.md`).

## [Unreleased]

A reliability release that follows a review of the whole workflow on real and
large data. Several defects made results silently worse or wrong; they are
fixed, and two result checks are stricter by default (see *Changed*). Runs start
reporting progress at once and finish sooner, the application fits laptop
screens, exports match the results on screen, and new users get a dataset to
start from (`al-dic-3d demo`).

### Fixed

#### Results

- **Per-frame masks saved as 0/255 images stalled the matching.** The engine
  multiplies the image gradients by the mask, so a mask of 255s made every
  solver step 1/255 of its size and the solver stopped next to its integer
  start. Masks are now binarized when they are read. On Stereo-DIC Challenge
  1.0 Sample 3 with its 0/255 per-frame masks, the reference frame keeps 69% of
  the nodes instead of 34% (71% lie inside the masks). The `[roi].mask` path was
  not affected.
- **Right-camera tracking failures were filled back in and shipped as valid.**
  Nodes that failed verification in the right camera were refilled from their
  neighbours, without a distance limit outside the neighbours' hull, while the
  final validity looked at the left camera only. On a synthetic 24 Mpx sequence
  37–50% of the points were reported valid with 3D errors of 10–20 mm. The
  right camera's validity now travels with its displacement (an interpolated
  point needs valid neighbours close by), and a point is valid only when both
  cameras are, in all three strategies.
- **The verification rejected correct points on strongly deformed specimens.**
  It compared subsets by translation only. It now warps the reference subset
  with the deformation the tracking measured, and keeps a borderline point when
  strong neighbours support it. With the paper's settings on the Sample 3
  sequence, which is strained to fracture, the median share of valid points
  rises from 25% to 60% of all nodes (85% of the nodes inside the ROI).
- **Wrong left–right matches were accepted on the first frame.** A match must
  now reach ZNSSD ≤ 0.6 and lie within 2 px of its epipolar line (both
  adjustable, see *Added*). On Sample 3, 102 matches with ZNSSD above 1 and a
  reprojection error of about 24 px had been accepted.
- **One blank frame failed the whole run.** A frame that decodes to zeros is
  now marked invalid and the rest of the run is kept, with the cameras tracked
  in parallel too.
- **A run cancelled during tracking kept only its first frame.** It now keeps
  every frame the tracking finished, verified.
- **The `quality` field repeated the first frame's stereo score in every
  frame**, so the quality gate could not see a tracking failure; it now holds
  each frame's tracking ZNSSD. The `stereo_each_frame` strategy applied the
  first frame's mask to every frame; it uses each frame's own mask.
- **Calibration details were dropped.** All distortion coefficients are kept
  (they were cut to five), DICe files import K4–K6, S, T and the distortion
  model, undistortion honours the camera skew, and a calibration made for a
  different image size is refused.
- **With OpenCV 4.x every 3D reconstruction failed** (an argument that only
  OpenCV 5 accepts). OpenCV 4.7 and later work again.
- **The von Mises equivalent strain counted the shear twice**, so it read 32%
  too high in uniaxial strain and 41% too high in pure shear (equal only in
  equibiaxial strain). It is now `sqrt(εxx² + εyy² − εxx·εyy + 3·εxy²)`, the
  formula of pyALDIC (2D). Sessions saved by earlier versions show the
  corrected values when opened; files exported earlier keep the old ones.
- **Strain computed after the node step was edited used the edited step** for
  its gauge size. The strain window, the canvas and the exports now all use the
  step the run was made with.
- **Smaller computation fixes.** RGBA images are converted to gray (the blue
  channel was used). `admm_max_iter = 0` means local-only (it was raised to 1).
  A strategy that rejects a parameter no longer drops all of the user's
  parameters. Frame sizes are checked for every frame. A `config.toml` in a
  folder whose name contains brackets, such as `test [1]`, finds its images.
  The strain kernels no longer fail to import when their cache folder is not
  writable.

#### Application

- **The export window could not be closed** (Close, Esc and the window's ×
  did nothing), and while it was open the application refused to quit. This
  affected 1.0.0 to 1.1.0.
- **Starting or opening a project during a run put the old run's results into
  it.** New, Open and Recent are disabled during a run, and a result is applied
  only to the project that started it.
- **A failed save destroyed the previous session file.** Sessions are now
  written to a temporary file and swapped in. Failures to save, open or run
  show an error dialog instead of a single log line.
- **The field overlay sat 1.5–3.5 px right of and below its nodes** (half an
  overlay cell less one pixel) on the canvas, in the strain window and in
  exported images. Each value is now drawn centred on its node.
- **The strain window's Export kept exporting the old result** after a rerun or
  a strain recompute. Its export window, like the main one, now follows the
  current result.
- **The window did not fit laptop screens.** The minimum size is 960 × 600, the
  right sidebar scrolls, and the left sidebar's label column is sized from the
  font, so labels are no longer cut off ("Refinement Leve").
- **Closing the window during a run stopped the run before asking about unsaved
  changes.** It now asks first, and the window stays responsive while the run
  stops.
- **Run was offered with inputs that cannot work.** Readiness now checks that
  the calibration loads with the selected format, that the left and right
  images are not the same files, that frame sizes agree, and that an ROI mask
  fits the images. Run stays disabled until the inputs are ready.
- **A folder holding both cameras' images was loaded into each camera.** Such a
  folder is now split by file name (`L_`/`R_`, `left`/`right`, `cam0`/`cam1`,
  `cam1`/`cam2`, `_0`/`_1`, `_L`/`_R`), and identical left and right lists are
  refused.
- **Smaller fixes.** Progress messages are translated and no longer show
  internal names. Velocity is labelled per frame until a frame rate is set. The
  language menu shows the language in effect. Recent projects on a
  disconnected drive stay in the list. *Reveal* works on macOS and Linux and
  selects the file. The ROI menu arrow displays in every language. The
  calibration dialog's live preview no longer blocks the window, and file
  dialogs start in the image folder. Min/Max show the automatic range, and
  range boxes keep small strain values. The run summary gives the final
  elapsed time. The canvas and the strain window's messages are translated,
  and common run warnings (such as running without a Starting Point) are
  worded for users instead of showing internal names.
  *Save Mask*, *Save log* and *Save calibration as* proposed a bare file name,
  i.e. the working directory; they start in the images' folder or the last
  one used. The mesh-overlay control is labelled and shows its whole width
  value ("1 p." was cut off). *Associate .aldic3d files* in the installed
  application registered a command that could not open a file.

#### Export

- **The 3D sequence export and the 360° turntable wrote the same picture for
  every frame** (the view was captured before it was redrawn).
- **A video or GIF that could not be written was reported as a success.** Such
  an export now fails visibly, and partial problems are listed.
- **GIF frame rates were ignored**, and a long GIF held every frame in memory.
  GIFs are now written frame by frame with exact delays.
- **MP4 cropped odd frame sizes**; they are padded instead.
- **Data export showed no progress and could not be cancelled.** It does both
  now, and a cancelled NPZ or MAT export leaves no partial file.
- **Exports could disagree with the results on screen.** An export uses the
  parameters the run recorded rather than the current settings, the export
  window follows a new run, a µm display unit converts the color range, the
  right camera uses the same mask as the canvas, the 3D export uses the view's
  color range, ROI and camera, and 16-bit images are stretched as on the
  canvas.
- **CSV frames are numbered `frame_1`, `frame_2`, … in their own folder** (they
  were `frame000`, … directly in the output folder). A MAT variable over
  MATLAB's size limit is reported, and a format that fails no longer stops the
  others.

#### Calibration

- **Bundle adjustment on dot targets dropped the eccentricity correction.** It
  refitted the rig on the uncorrected dot centres, which brought back a scale
  bias of about -5.6 µε on a ground-truth circle grid (-0.4 µε without bundle
  adjustment). It now uses the corrected centres (-0.6 µε).
- **Bundle adjustment used the views the solve had rejected.** Misindexed
  detections, which the solve drops (two or three per camera on real photos,
  about 25 px off), still entered the bundle adjustment. The robust loss only
  damped them: on a real 43-pair set its RMS ended at 5.2 px. It now uses the
  views the solve kept (0.33 -> 0.17 px on the same set).

#### Command line

- **The first Ctrl+C** finishes the frame in flight and writes the frames
  computed so far (exit code 130); a second Ctrl+C aborts.
- **Output is plain ASCII**, so output redirected to a file no longer shows
  garbled dashes, and a code-page-437 console no longer crashes.

### Changed

- **Runs start reporting at once and finish sooner.** On a 12 Mpx pair the
  first progress message appears within a second and tracking starts after
  about 5 s; setup used to be silent for 14–34 s. The left camera's
  verification now runs while the right camera tracks, the verification uses up
  to 8 threads, the stereo seed search is threaded (about 3× faster), and the
  `ref_direct` strategy prepares its reference once. A 6-frame 12 Mpx run takes
  45 s instead of 52 s, with identical results.
- **Browsing results stays fluid on large images.** On a 12 Mpx, 40-frame
  result, the longest pause of the window when changing frame, field or camera,
  dragging the slider or stepping through the strain window fell from 0.25–3.2 s
  to under 0.1 s. Frames load and overlays render in the background while the
  previous image stays up, the deformed view reuses one triangulation per
  camera, slider drags are coalesced, and the crack-aware 3D view renders a
  frame in 8–16 ms instead of 2.4–2.6 s. Scrubbing every frame of three fields
  grows memory by 0.35 GB instead of 1.16 GB. The first opening of the 3D view
  still takes about 0.8 s (loading the 3D libraries) and now says so.
- **Invalid nodes show as gaps everywhere.** With an ROI drawn, the overlay used
  to smooth over invalid nodes; triangles that touch one are now transparent,
  as they already were without an ROI and in the 3D view. The canvas and the 3D
  view also hide the same edge-trimmed strain nodes as the strain window and
  the exports.
- **Less memory, projected more accurately.** Masks are cached as bytes and
  frames in their stored type, and only the first and last mask are read
  before the run. The pre-run memory check now counts the setup and
  verification buffers and the refined mesh: 4.83 GiB projected against
  4.72 GiB measured on a 12 Mpx run.
- **The validity percentage counts only the nodes inside the ROI**, so a
  masked specimen can reach 100%.
- **When validity collapses in accumulative mode, the run summary suggests
  incremental mode.**
- **Dependencies.** `al-dic` 0.7.2 up to 0.8.x. One OpenCV package,
  `opencv-python` (do not also install `opencv-python-headless`). `numba`,
  `matplotlib` and `pillow` are declared directly. The development status is
  Beta.
- The *Quality gates* option is now called *Extra filters (correlation,
  outliers)*.

### Added

- **`al-dic-3d demo OUT`** writes a synthetic stereo dataset with an analytic
  ground truth (images, calibration and `config.toml`); `--run` also runs it
  and reports the error. The README Quick Start uses it.
- **`al-dic-3d self-test`** checks an installation end to end and names the
  part that fails.
- **Automatic disparity estimate.** Without a Starting Point, the stereo
  search is centred by a few probe matches that are checked against the
  epipolar geometry, so a rig with a large disparity is still matched
  completely (synthetic 12 Mpx rig: 100% of the nodes on the first frame
  instead of 76%). An **Auto-place** button places a Starting Point, and
  readiness shows an amber note while none is placed.
- **ADVANCED › Result checks** sets the tracking check threshold, the stereo
  check threshold and the epipolar limit.
- **Per-frame mask import** in the Region of Interest section (a folder with
  one mask per frame).
- **Portable sessions.** The calibration file is stored inside the `.aldic3d`
  file and restored when the original is missing, a moved calibration is
  searched for, and a project whose images are missing can still be opened to
  view and export its results.
- **A log file and crash reports** for the installed application
  (`%LOCALAPPDATA%\pyALDIC-3D\logs`), and an error dialog for unexpected
  errors.
- **Background kernel compilation** at startup, so the first run no longer
  waits about 23 s.
- **Help › User Guide**, and translations for the widgets shared with pyALDIC
  (the console, collapsible sections).
- **Velocity as an exportable field**, and Auto / Min / Max color controls in
  the 3D export.
- The Windows installer is built and self-tested by CI, and no longer bundles
  unused TBB and UCRT libraries.

## [1.1.0] — 2026-07-31

Long runs are faster and no longer look hung. The results of a completed run
are bit-identical to 1.0.2.

### Changed

- **The honesty gate is 3.3× faster.** After tracking, every node of every
  frame is re-verified against frame 0 before it is shipped. On a 400-frame,
  5-megapixel sequence that check took about three times as long as the
  tracking it verifies; it now runs at 0.90 s per frame instead of 2.97 s,
  which saves about 27 minutes on a 400-frame two-camera run. The deformed
  image is now spline-filtered once per frame instead of once per chunk of
  points, and the chunks are evaluated on a small thread pool (at most four
  threads) that shares the existing memory budget, so peak memory is
  unchanged.

### Fixed

- **The default two-camera run showed no progress while it tracked.** With
  the cameras tracked one after the other (the default), the progress bar
  stood still for the whole tracking phase and then jumped during assembly.
  It now advances through the left camera, then the right camera, then
  assembly. The `stereo_each_frame` and `ref_direct` strategies had the same
  gap and are fixed too.
- **The verification pass is visible and responds to Cancel.** It reports
  "verifying frame k/N" instead of leaving the bar frozen, and Cancel takes
  effect after the frame being verified rather than after the whole pass.
  Frames the verification never reached are dropped from a cancelled run
  instead of being reported as verified.
- **The progress bar no longer moves backwards** near the end of each
  camera's tracking.

## [1.0.2] — 2026-07-30

### Fixed

- **Python 3.10: browsing results could crash the display.** As soon as a
  display cache was full and evicted its oldest entry (for example while
  scrubbing through a long sequence), the eviction raised `KeyError` and took
  the frame prefetcher down with it. Python 3.11 and later were not affected.
- **macOS: tracking both cameras in parallel aborted the application.** On
  macOS, Numba's threading layer kills the process when two threads run
  parallel kernels at the same time. There the opt-in parallel-camera option
  now warns once and tracks the cameras one after the other; its measured
  gain on macOS was only about 1.1×.

## [1.0.1] — 2026-07-30

### Fixed

- **1.0.0 could not start on Python 3.10.** The configuration reader used
  `tomllib`, which only joined the standard library in Python 3.11, so every
  command (`al-dic-3d run`, `calibrate`, `gui`) failed at import on 3.10.
  Python 3.10 now uses the API-identical `tomli` backport, which is installed
  automatically.

## [1.0.0] — 2026-07-30

First public release: a desktop application and headless CLI for stereo
(two-camera) Digital Image Correlation, built on the correlation engine of the
pyALDIC 2D platform (`al-dic`). Published on PyPI (`pip install al-dic-3d`),
as a Windows installer on the GitHub release, and archived on Zenodo
([10.5281/zenodo.21696564](https://doi.org/10.5281/zenodo.21696564)).

### Added

- **Built-in stereo calibration** from chessboard, ChArUco, circle-grid or
  coded circular-target image pairs, with per-image reprojection QC, worst-pair
  rejection, epipolar validation, optional bundle adjustment, a printable board
  PDF and a known-distance scale check. Existing calibrations can be imported
  from six formats (MATLAB/OpenCV, MatchID, MMC, DICe, OpenCorr, OpenCV YAML)
  or typed in by hand.
- **Metric 3D shape, displacement and surface strain.** Every node is
  triangulated into millimetres (left camera at the origin). Surface strain is
  available as Green–Lagrange, infinitesimal or Euler–Almansi, in three
  coordinate systems, with trimming of low-confidence edge nodes.
- **Three correspondence strategies** (`track_both`, `stereo_each_frame`,
  `ref_direct`); accumulative or incremental tracking with Every-Frame /
  Every-N / Custom reference update; Starting-Points seed propagation, FFT or
  previous-frame initial guess; quadtree mesh refinement.
- **The honesty gate:** every tracked node of every frame is re-verified
  against frame 0 and set to `NaN` when it fails, so a solver that "converged"
  on a decorrelated pattern cannot ship a plausible but wrong field.
- **Crack-aware stereo DIC:** a thin barrier drawn into the region of interest
  cuts the mesh, keeps strain neighbourhoods on one side of the crack, and
  blanks rendering across it on the canvas, in exports and in the 3D view.
- **Desktop GUI** with an interactive 3D view, a strain window, velocity and
  display-unit options, and `.aldic3d` session files that keep images,
  calibration, masks, parameters, view state and computed results. An optional
  Windows file association opens them by double-click.
- **Export** to NPZ, MATLAB `.mat`, CSV, PLY and VTU/PVD time series, field
  images, MP4/GIF animations and offscreen 3D-view sequences, plus a
  parameters JSON with every run.
- **Eight interface languages:** English, Simplified Chinese, Traditional
  Chinese, Japanese, Korean, German, French and Spanish.
- **Headless CLI:** `al-dic-3d run config.toml`, `al-dic-3d calibrate` and
  `al-dic-3d gui [SESSION]`.
- **Large jobs:** frames stream from disk instead of being held in memory, a
  memory check runs before a job starts, and Cancel keeps the frames that were
  already computed.
- **Folders with non-ASCII names** (for example Chinese, Japanese or Korean)
  work for images, masks, calibration files and exports.
- **A plain `pip install al-dic-3d` is full-featured:** the GUI and the 3D
  view are core dependencies. The `[gui]` and `[viz3d]` extras remain as
  aliases.
- **Windows installer** (`pyALDIC-3D-1.0.0-win64-setup.exe`) for machines
  without Python: a per-user install that needs no administrator rights. It is
  not code-signed, so SmartScreen asks for confirmation on first run.

[Unreleased]: https://github.com/zachtong/pyALDIC-3D/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/zachtong/pyALDIC-3D/compare/v1.0.2...v1.1.0
[1.0.2]: https://github.com/zachtong/pyALDIC-3D/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/zachtong/pyALDIC-3D/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/zachtong/pyALDIC-3D/releases/tag/v1.0.0
