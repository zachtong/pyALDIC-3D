# Changelog

All notable user-facing changes to pyALDIC-3D are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and versioning follows [Semantic Versioning](https://semver.org/).

Entries are per package version (`al-dic-3d` on PyPI, `vX.Y.Z` git tags). The
GitHub release notes for a tag are this file's section for that version.

## [Unreleased]

### Changed

- **Chessboard calibration is 13 to 49 times faster on large images.** For 25
  pairs of 10 MB images (4096 × 2448) the calibration took 6 minutes and now
  takes 18 seconds; 25 pairs of 20 MP images went from 9.5 minutes to 12
  seconds. The board is first searched on reduced copies of each image, and
  its corners are then refined at full resolution exactly as before, so the
  corners agree with the old ones to within 0.0005 px and the same images are
  detected. Boards the reduced copies cannot confirm (for example a corner at
  the image edge) are searched at full resolution as before. Images are now
  detected several at a time, in the dialog and in `al-dic-3d calibrate`, and
  the full-resolution search is limited in memory: it needed up to 6 GB per
  20 MP image, which could slow a 16 GB computer to a crawl.
- **DIC runs are about 15 to 25 % faster, with identical results.** The 2D
  engine smooths every displacement field with a Gaussian whose reach, on the
  regular grids pyALDIC-3D uses, covers only the node itself, so it returned
  its input unchanged while taking about half of the engine's time. It is now
  skipped wherever that can be proven for the mesh (refined meshes keep it).
  Measured on 20-frame runs: 34 to 28 s at 5 Mpx, 177 to 149 s at 12 Mpx; on
  a real notched specimen the 3D points are identical to the last bit.
- **The calibration dialog guards against a wrong board description.** It
  remembers the board type and its values between sessions, and the result
  shows how far the board was from the left camera, so a wrongly entered
  square size shows up as an implausible distance (447-524 mm with the right
  12 mm square, 372-437 mm with 10 mm entered). The size fields say what they
  count for each board type (inner corners, squares or dots), and a
  calibration needs at least 6 pairs before it starts.
- **A run warns when the left and right images stop belonging together.** If
  from some frame on the matched points leave their epipolar lines (an image
  missing from one camera, cameras out of sync), the run log names the first
  such frame. A right image missing from the middle of a synthetic test used
  to give 100 % valid points with 20 times the 3D error and no warning.
- **A run warns when a camera has probably moved since the calibration.** The
  run log now warns when the matched left and right points lie a median of
  more than 0.5 px from their epipolar lines (healthy real rigs: 0.02 to
  0.25 px). A right camera turned by 1.5° after calibrating gave 0.8 px and
  8.6 % too large displacements, with no warning before.
- **The user guide has a checklist for calibrating your own rig**: lock the
  optics and leave the rig alone, keep the two views roughly symmetric, count
  a chessboard's inner corners, measure the printed square with calipers, and
  how to take the pictures. The guide no longer presents **Verify** as a check
  of the absolute scale: it compares against the square size you entered, so a
  wrongly entered size passes it.

### Fixed

- **A run on images that do not match the calibration is refused before it
  starts.** The built-in calibration now records each camera's image size, and
  Run is blocked when the images differ (binned or cropped images need their
  own calibration). Such runs used to finish with wrong 3D points.
- **When no point can be matched between the two cameras, the message names
  the likely causes**: left and right swapped, a calibration from other images,
  or no speckle texture in the region. It used to advise loosening the stereo
  check, which then produced an empty result.
- **A calibration that finds no board says why.** Each image's detection
  result stays in the table, and when the board is found in too few images the
  dialog and `al-dic-3d calibrate` explain how to count it (a chessboard of
  10 × 8 squares has 9 × 7 inner corners). It used to say only "need >= 3
  usable views to calibrate, got 0".
- **Board images of different sizes are refused**, naming the image that
  differs; two cameras of different resolutions are each calibrated at their
  own size (the left camera's size was used for both).
- **Importing a calibration in the wrong format is refused with the reason
  first** and the format the file looks like ("it looks like a DICe XML file:
  choose the format 'dice'"). Picking a file selects its format when the file
  makes it clear, and a calibration with a zero focal length or baseline is
  refused; the OpenCorr reader used to accept any text file with all zeros.
- **Closing the calibration dialog asks before discarding an unsaved
  calibration**, and its warnings are shown in amber instead of green.
- **The memory check estimates dense and incremental runs correctly.** It
  underestimated them two to four times (5 GB predicted, 19 GB used for an
  incremental 12 Mpx run), so such runs could push a lab computer into
  swapping; it now predicts runs with the default settings within 15 %.
- **Engine warnings about points whose motion had to be extrapolated or that
  stopped being tracked now appear in the run summary**, not only in the log
  file.
- **The memory warning tells GUI users what to change in the GUI** (fewer
  frames, a coarser subset step, a smaller region) instead of a configuration
  key.
- **The GUI run log numbers frames from 1**, like the rest of the GUI. A
  cancelled run ends with a partial-result warning instead of "Analysis
  complete", and frames it never computed are no longer listed as 0 % valid.
- **`al-dic-3d run` prints a one-line error for mistakes in the input** (a
  missing file, mismatched images) instead of a Python traceback; `--debug`
  shows the traceback.

## [1.4.2] — 2026-11-25

Four accuracy fixes. Track Both no longer adds strain along free edges,
notches and holes. Stereo Each Frame no longer adds random out-of-plane scatter
on every frame. The tracking check now drops points that sit next to a region
that stopped correlating, which it used to ship up to 1.5 px off. The built-in
calibration also no longer throws away good views along with a bad one.

### Fixed

- **A bad calibration view no longer takes good views with it.** When one
  view is badly wrong (a misdetected or misnumbered board), the first solve is
  distorted, and some good views can then exceed the rejection threshold too.
  Every view above the threshold used to be rejected at once, so those good
  views were lost. Now only the worst view is rejected, the solve repeats
  without it, and the others are judged again. Stereo pairs are rejected the
  same way. With OpenCV 5.1 on Linux and macOS this happened on a single bad
  view out of twelve: two good views were rejected with it. On four real
  calibration sets on Windows, the same views are rejected as before and the
  results are unchanged.

- **Points next to a region that stopped correlating are no longer shipped up
  to 1.5 px off.** When part of a subset covers a region that stops correlating
  in a later frame (glare, an occlusion, lost paint), the solver can settle 0.5
  to 1.5 px away from where that subset correlates best, while the correlation
  still looks acceptable (0.7 to 0.85). The tracking check only looked at the
  correlation, so these points passed, and in the right camera the error became
  a depth error. Every point that does not correlate near-perfectly must now
  also sit where its subset correlates best. The tolerance is at least 0.25 px
  and grows where noise or a small subset makes that position less certain, so
  correct points on noisy images still pass. On a synthetic stereo pair with
  part of the right images replaced, the largest 3D displacement error fell
  from 2.9 to 0.6 mm. On real tests the check drops 0.005 % of the tracked
  points of a notched specimen pulled to failure and 0.03 % on a D-shaped
  specimen, and the tracking check takes 10 to 20 % longer.

- **Strain no longer reads high along free edges when both cameras are
  tracked.** The right camera is tracked on its own grid, and its motion is
  then carried to each stereo point. A point near a free edge can lie up to one
  node step past the right grid's last node, and it used to get that node's
  motion unchanged. That drops the displacement gradient, so under large strain
  the left and right positions disagreed by 1 to 4 px. The mismatch became a
  depth error, and Green-Lagrange strain gained a ½(∂W/∂Y)² term, which is
  never negative, along every edge, notch and hole. Those points now get a
  local affine fit of the nearby right-camera nodes, which keeps the gradient
  and is exact for a linear field. On a notched specimen pulled to failure,
  that term fell from 0.071 to 0.006 within 4 px of the edge, the right camera's
  edge error fell from 0.67 to 0.20 px (the left camera's is 0.22 px), and the
  stripes along the notches and the hole are gone.
- **Stereo Each Frame puts each right-camera point where its left point really
  is.** This strategy matches the two cameras again at every frame, at left
  positions that tracking gives to a fraction of a pixel. The match was solved
  at the nearest whole pixel, and its result was then used for the exact
  position. That leaves out how much the left-to-right mapping stretches over
  the sub-pixel step, so every frame's right point was off by up to half a
  pixel times that stretch (about 0.05 px, and up to 0.1 px where the two views
  differ most). The error changes at random from point to point and from frame
  to frame, so it showed up as scatter in the out-of-plane displacement. The
  match now evaluates the solved local warp at the exact position. On a
  synthetic curved specimen with known motion, the out-of-plane displacement
  scatter fell from 64 to 21 µm and the median 3D displacement error from 40 to
  17 µm. Track Both and Reference Direct match at whole pixels, so this fix
  does not change them.

## [1.4.1] — 2026-10-31

Incremental runs keep their points: on a notched specimen pulled to failure
they now hold 98.6 % of the points on average, against 63 % in 1.4.0. The run
log also says what the stereo check rejected and when the calibration does not
match the images, which came out of
[#1](https://github.com/zachtong/pyALDIC-3D/issues/1).

### Changed

- **al-dic 1.0.4 or newer is required** (was 0.7.2), and the Windows installer
  ships 1.0.4. That release trims the mesh pyALDIC-3D passes it from scratch at
  every reference frame (see Fixed).
- **In incremental mode the Tracking check verifies each step against the
  frame it was tracked from**, not against frame 1. Each step adds a small
  position error. The check against frame 1 removed points once that error
  had summed to about 1.5 px, although the engine was still tracking them.
  On a notched specimen pulled to failure (136 frames, a reference update every
  frame), the run now keeps 98.6 % of the points on average instead of 76 %
  (frame 132: 7131 of 7599 instead of 2445). It also keeps the necking region
  that accumulative tracking loses. A step that loses the pattern still fails,
  and the rest of that point's track goes with it. Accumulative runs are
  checked exactly as before. After an incremental collapse, the run log now
  suggests updating the reference every frame, not less often.

### Fixed

- **The mesh preview stays on the drawn ROI after the view is panned.**
  Panning, by dragging with the right or middle mouse button, holding Space and
  dragging, or with the arrow keys, moved the grid by the pan distance a second
  time. It then sat beside the ROI until the window was resized. The colour
  bar, the configuration card and the canvas hints drifted the same way, in
  the main window and in the Strain window.
- **Incremental runs with per-frame masks keep the material that moves past
  the frame-1 outline.** There were two causes:
  - Each reference frame trimmed the analysis mesh again from the previous
    trim, so cells removed by an earlier, narrower mask never came back. The
    2D engine fixed this in al-dic 1.0.4.
  - The mesh covered only the frame-1 region, so material that a later
    reference mask placed outside it had no cells to be tracked in. The mesh
    now also covers every reference frame's mask. It grows by whole grid
    steps, so the frame-1 points stay exactly where they were, and the extra
    points outside the frame-1 mask are invalid from the start.

  On a notched specimen pulled to failure (136 frames, a reference update
  every frame), mean validity rose from 63 % to 76 % (frame 132: 1616 →
  2445 of 7599 points). The step-wise Tracking check (see Changed) recovers
  the rest. Runs without per-frame masks, and accumulative runs, keep the same
  mesh as before.
- **The run log explains the stereo check.** Links that the frame-1 stereo
  check rejected were reported as *Camera stereo: validity gate removed N
  node-frames (correlation vs frame 1 failed)*. That check compares the two
  cameras, not a frame with frame 1, and the log never named the setting to
  change. The log now gives a separate line for links rejected by weak
  left-right correlation and for links rejected by epipolar distance. When
  many fail the correlation check, it advises raising **Stereo check**: on a
  rough surface seen at a 29° stereo angle, the default had removed 810 of 2008
  correct links. When many lie off their epipolar lines, it reports their
  median distance and says the calibration probably does not match the images.
- **A run whose stereo links all fail the epipolar check names the
  calibration.** It stopped with "check the seed point / disparity prior and
  stereo overlap" even when every link had been found and then rejected for its
  distance from the epipolar line. The error now gives the median distance
  (17.6 px for a calibration off by 0.04°) and points at the calibration; when
  weak correlation removed the links, it names **Stereo check** instead.
- **The 3D outlier filter no longer prints "All-NaN slice encountered"**
  warnings. With **Extra filters** on, a point whose neighbours were all invalid
  triggered the warning on every run. Such points still stay valid, and results
  are unchanged.

## [1.4.0] — 2026-10-30

### Added

- **Rigid-body motion can be removed from the results** (Strain window, RIGID
  MOTION; config `[rigid_motion].mode` / `.region_mask`). Each frame's
  best-fit translation, or translation and rotation, relative to frame 1 is
  removed from the displacement everywhere: the main window's field maps and
  3D view, the Strain window, the strain computed afterwards and every export.
  The fit uses all valid points or a region drawn with rectangle and polygon
  tools (shown in amber), and a per-frame table lists the removed shift,
  rotation, fit residual and points used. Labels and exported figures say
  *· rigid motion removed*, the archive adds the fit (`rbm_*`) and the measured
  `points3D_raw` (archive schema 4), and the project keeps the measured data
  and re-applies the setting when it opens. Green-Lagrange strain is unchanged
  by the removal; the displacement and the out-of-plane slopes are not.
- **The 3D View has its own toolbar** (canvas, 3D View). View presets aligned to
  the specimen (Camera, Normal, Side, Iso) and Reset, a PNG save, a deformation
  magnification with an Auto pick and an out-of-plane-only switch (the colours
  keep the true values), the frame-1 reference shape as a wireframe, the camera
  frusta on demand and a shading switch, plus an orientation triad. The 3D
  exports (Export, 3D View) follow the view's magnification and shading, are
  lit like it, and without a 3D View camera frame the surface from the left
  camera instead of an isometric view from behind.
- **The Strain window shows displacement and out-of-plane slopes** (FIELD).
  `U`, `V`, `W` and `|D|` are available as soon as a run exists, and the
  slopes `∂w/∂x`, `∂w/∂y` of the strain fit (in mrad) once strain is computed.

### Changed

- **The Epipolar Band defaults to 15 px instead of 3 px** (PARAMETERS; config
  `[matching].stereo_band_px`). The left/right search covers 15 px to each
  side of the epipolar line, so it still reaches the matching patch when the
  calibration is a few pixels off; the Epipolar limit then decides whether the
  link is kept. New projects, and config files without the key, use 15 px; a
  saved project keeps the width it was saved with. On Stereo-DIC Challenge 1.0
  Sample 3 (25,000 nodes) the search takes 16 % less time than the square
  window (3 px: 20 % less) and finds the same links. On a periodic pattern
  finer than the band across the line, set a narrower band.

### Fixed

- **The application no longer aborts on Python 3.10 and 3.11.** PySide6 6.12.0
  miscounts references on every interface signal. From Python 3.12 that is
  harmless, but on 3.10 and 3.11 the interpreter aborted after a few thousand
  signals (*Fatal Python error: deallocating None*), within minutes of use.
  That PySide6 release is no longer installed below Python 3.12, and a test
  catches a release that brings the bug back.
- **The 3D View shows the specimen properly.** It opened looking at the back of
  the specimen with the image upside down, framed on the camera frusta so the
  surface was a speck, and unlit — a scene rebuild removed the lights. It now
  opens from the left camera with image-up up, framed on the surface, lit and
  smoothly shaded; the scalar bar fits and labels its ticks to the range; an
  all-zero first frame no longer collapses the colour range; a message (no
  results, field not available) replaces the scene instead of sitting under a
  stale one; and pyvista's stray keys are gone ('q' used to break the view).
- **The drawn ROI no longer covers the results** (canvas toolbar, new **Show
  ROI** toggle). The blue ROI and the cyan refinement zones stayed on top of
  every view after a run — tinting the field, and sitting at their frame-1 place
  on deformed frames and on the right camera — with no way to hide them short of
  clearing the ROI. They now show only on the left camera's frame 1, switch off
  when an analysis finishes, come back when you draw, and the toggle is saved
  with the project.
- **The run log's advice after a validity collapse in incremental mode.** When
  an incremental run with the reference updated every frame lost most of its
  points, the log advised importing per-frame masks — also when they were
  already imported. Each reference update adds a small tracking error and, over
  a long sequence, these errors add up, so the log now suggests fewer updates
  (**Every N Frames**) or **Accumulative**. The run records its reference-update
  policy and whether per-frame masks were used (in the parameters export too).
  The user guide no longer calls **Incremental + Every Frame** the safe default.
- **A run that widens its search on every frame now says so.** The engine
  widens its FFT initial-guess search when a correlation peak hits the search
  boundary, and reported it only in the log file. An incremental run without
  per-frame masks on a moving specimen widened to 702 px on every frame, about
  five times slower, with no reason on screen. The run log now names the
  camera, the number of frames and the widest search, and says what to do.
- The test suite no longer depends on how OpenCV rounds on a given computer.
  A test compared two exact copies of the same patch, and the last bit of the
  arithmetic chose between them, so it failed on some machines.

## [1.3.0] — 2026-10-29

The right camera now follows the region of interest drawn on the left one, so a
region drawn on the left camera alone no longer costs whole frames on a dark
background, and the left/right match is searched along each point's epipolar
line. Both came out of verifying the fix for
[#1](https://github.com/zachtong/pyALDIC-3D/issues/1).

### Fixed

- **With the region of interest on the left camera only, the right camera
  could lose whole frames.** The right camera tracked the whole bounding box
  of its frame-1 matches, background included. On a dark, nearly textureless
  background a few background nodes landed their FFT peak on the search
  boundary, the engine then widened the search for every node up to half the
  image, and the first deformed frame (in incremental mode: any frame) solved
  no node. 1.2.x dropped that frame; a two-frame run, and 1.1.0, stopped with
  "2D engine solved NO nodes". The right camera now tracks the left region seen
  through the frame-1 match, on the same frames as the left, plus a rim of half
  a subset or one node step, whichever is larger
  ([#1](https://github.com/zachtong/pyALDIC-3D/issues/1)). On a synthetic strip
  like the one in #1 the first deformed frame keeps 98 % of its points instead
  of none (accumulative; 91 % in incremental mode). Right-camera masks you
  import are used as given. Runs without right-camera masks track fewer right
  nodes than before, so their points can move by a few hundredths of a
  millimetre; coverage and accuracy are unchanged on the synthetic tests.

### Added

- **Epipolar band for the frame-1 stereo search.** Each node's left/right match
  is searched along its epipolar line, within **Epipolar Band** pixels of it
  (PARAMETERS, default 3 px, never narrower than the Epipolar limit; config
  `[matching].stereo_band_px`) and **Stereo Search** pixels along it, instead
  of in a square window. A look-alike patch off the line can no longer be
  picked, and on Stereo-DIC Challenge 1.0 Sample 3 the seed search takes
  0.70 s instead of 0.93 s for 25,000 nodes, with the same links. 0 restores
  the square window; so does turning the Epipolar limit off. The unused
  `epipolar_seed` field of `CorrespondenceConfig` is replaced by
  `stereo_band_px`.

## [1.2.1] — 2026-10-28

1.2.0 shipped without its Windows installer; this release adds it. The
application is the same as 1.2.0 apart from the parallel-camera fix below.

### Fixed

- **The Windows installer could not be built.** SciPy 1.18 imports part of
  its array support dynamically, the installer build left that module out,
  and the packaged application could not run its computations, so the build
  stopped at its self-test. The module is now included and the packaged
  application passes its self-test again.
- **Parallel camera tracking could crash the program on Linux.** When neither
  OpenMP nor TBB is available, numba falls back to a threading layer that
  aborts when both cameras run their solver at the same time. This was handled
  on macOS only; Linux without OpenMP (libgomp) crashed. The option now checks
  numba's threading layer on every system and, without a safe one, tracks the
  two cameras one after the other with a warning. Results are identical either
  way, and the option is off by default.
- The test suite passes with OpenCV 4.x again (a test helper used an argument
  only OpenCV 5 accepts).

## [1.2.0] — 2026-10-28

A reliability release that follows a review of the whole workflow on real and
large data. Several defects made results silently worse or wrong; they are
fixed, and two result checks are stricter by default (see *Changed*). Runs start
reporting progress at once and finish sooner, the application fits laptop
screens, exports match the results on screen, and new users get a real dataset
to learn on (`quickstart/`).

### Fixed

#### Results

- **A region of interest dropped the points that moved out of it.** The ROI is
  drawn on frame 1 but was applied as the mask of every frame, and a point
  whose tracked position lands outside a frame's mask is discarded. A specimen
  that moved therefore lost the points near its edges, and a narrow one could
  lose them all ([#1](https://github.com/zachtong/pyALDIC-3D/issues/1)). The
  ROI now applies to the reference frames only, as in pyALDIC (2D); this covers
  the ROI drawn in the application and `[roi].mask`. On Stereo-DIC Challenge 1.0
  Sample 3 (two frames 8 px apart, accumulative, a drawn rectangle) 99.7% of the
  points stay valid instead of 93.0%. In incremental mode every later reference
  frame still reuses the frame-1 outline; import per-frame masks when the
  specimen moves far beyond it.
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

- **Coded dot targets are measured more precisely.** Each dot centre is now
  refined by a weighted centroid over an elliptical window of 1.45 dot radii,
  with the background (a plane, so uneven light does not pull the centre) and
  its noise subtracted, instead of the intensity centroid inside the dot's
  binary outline. On ground-truth images the centres moved from 0.017 px to
  0.0007 px of the true disc centroid without image noise, and from 0.017 to
  0.004 px with 1.5 grey levels of noise, fiducial and ordinary dots alike. On
  real calibration photos, with the board's own shape taken out, the leftover
  error fell by about a third (Challenge 1.0 Sample 1) and by more than half
  (Challenge 2.0, 0.08-0.11 to 0.03-0.04 px); on a third set (Challenge 1.0
  Sample 5, large dots) it stayed within 4%. The same views and points are
  detected as before. Circle grids and chessboards are unchanged. Detection
  takes about 50-60 ms more per 5 Mpx image.
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
- **Dependencies.** `al-dic` 0.7.2 up to 1.0.x (tested with 0.7.2, 0.8.0,
  0.9.0, 0.10.0 and 1.0.3), so pyALDIC-3D installs next to the current
  pyALDIC (2D). One OpenCV package,
  `opencv-python` (do not also install `opencv-python-headless`). `numba`,
  `matplotlib` and `pillow` are declared directly. The development status is
  Beta.
- The *Quality gates* option is now called *Extra filters (correlation,
  outliers)*.

### Added

- **A real dataset to learn on.** The repository's `quickstart/` folder holds
  three image pairs of Stereo-DIC Challenge 1.0 Sample 3 (a D-shaped specimen
  stretched in tension) with their calibration, a mask of the specimen in every
  image and a `config.toml`. Its README walks through the analysis in the
  application step by step and lists the results to expect; the README Quick
  Start points to it.
- **Calibration checks.** Every calibration now reports, per camera, how far
  the board reached and whether the lens model is determined beyond that (a
  warning when two equally good fits, k3 free and k3 fixed, differ by more
  than 0.3 px there), and whether the residuals show a pattern the lens model
  does not explain. They appear in the calibration dialog (translated, with the
  covered radius drawn on the preview and the result text amber on a warning),
  in `al-dic-3d calibrate`'s output (with `--strict` to fail on a warning) and
  as `meta_*` entries in the saved calibration. On ground-truth images they
  flagged every camera whose corners were off by 0.3 px or more, and no camera
  whose lens the model describes. The checks judge a calibration against the
  board it was fitted with (the refined points after *Optimize board shape* or
  the release-object method), and their advice follows your choices (k3 fixed,
  board shape already optimised).
- **`al-dic-3d calibrate --board-shape`** optimises the board shape in the
  bundle adjustment (and implies `--bundle`), like the dialog's *Optimize board
  shape*.
- **`al-dic-3d demo OUT`** writes a synthetic stereo dataset with an analytic
  ground truth (images, calibration and `config.toml`); `--run` also runs it
  and reports the error.
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

[Unreleased]: https://github.com/zachtong/pyALDIC-3D/compare/v1.4.2...HEAD
[1.4.2]: https://github.com/zachtong/pyALDIC-3D/compare/v1.4.1...v1.4.2
[1.4.1]: https://github.com/zachtong/pyALDIC-3D/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/zachtong/pyALDIC-3D/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/zachtong/pyALDIC-3D/compare/v1.2.1...v1.3.0
[1.2.1]: https://github.com/zachtong/pyALDIC-3D/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/zachtong/pyALDIC-3D/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/zachtong/pyALDIC-3D/compare/v1.0.2...v1.1.0
[1.0.2]: https://github.com/zachtong/pyALDIC-3D/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/zachtong/pyALDIC-3D/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/zachtong/pyALDIC-3D/releases/tag/v1.0.0
