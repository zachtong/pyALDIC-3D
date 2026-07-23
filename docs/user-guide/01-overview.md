# 1. Overview

pyALDIC-3D computes full-field **3D displacement and surface strain** from a
sequence of image *pairs* taken by a calibrated stereo camera rig. Where the 2D
platform (pyALDIC) works from one camera and assumes a planar, in-plane
specimen, pyALDIC-3D reconstructs the real 3D shape and motion of the surface,
so out-of-plane motion (`W`) and true surface strain are recovered.

## What a run computes

For each frame *k* and each mesh node, a run produces:

- **3D world coordinates** `points3D` — the reconstructed surface point in
  millimetres, in the **left-camera world frame** (`R = I`, `T = 0`).
- **3D displacement** `U`, `V`, `W` — defined simply as `P^k − P^1`
  (position now minus position on the reference frame). This makes the 3D layer
  *mode- and strategy-agnostic*: however the correspondence was found, the
  displacement is just a difference of reconstructed positions.
- **Displacement magnitude** `|D| = sqrt(U² + V² + W²)` and, in the viewer, an
  inter-frame **velocity** magnitude.
- Optional **surface strain** (`exx`, `eyy`, `exy`, principal strains `e1`/`e2`,
  max shear, von Mises) computed by a local plane-fit + Green-Lagrange
  reduction on the reconstructed point cloud — see
  [Strain post-processing](11-strain-processing.md).

Every value is `float64`; `NaN` marks an invalid / untracked / unreconstructable
node and propagates all the way to the exports.

## How it works, in one paragraph

Correlation runs on the **raw** left and right images (no rectification). A
pluggable *correspondence strategy* finds, for each node, the matching pixel in
the other camera (stereo) and in the next frame (temporal). Undistorted point
coordinates are triangulated through the calibrated rig to a 3D point. The 3D
displacement is the frame-to-frame difference of those points; strain is fitted
afterwards on the surface. You do **not** rectify images or hand-build any of
this — the app orchestrates calibration → sequence → matching → reconstruction
→ strain.

## The three-column GUI

The main window (`assets/main_page.png`) is a single window with three columns,
mirroring the 2D app's layout:

- **Left sidebar** — the workflow, top to bottom in this exact order: the
  **Images** panel (LEFT and RIGHT stereo drop zones), **Calibration**,
  **Workflow Type**, **Initial Guess**, **Region of Interest**, **Parameters**,
  and a collapsible **Advanced** section (strategy, AL-DIC iterations, parallel
  cameras, auto-expand FFT).
- **Centre canvas** — a zoom/pan viewport showing the current frame with
  overlays (ROI, mesh, seeds, and after a run the colour-mapped field). It can
  show the LEFT or the RIGHT camera.
- **Right sidebar** — the **Run** button, progress bar and ETA, **Cancel**, the
  field selector, visualization controls (colormap, range, opacity), the
  physical-units selector, the **3D View** launcher, and the console log.

## A typical session

1. **Load stereo images** — drop the LEFT frames and the RIGHT frames into their
   two drop zones; they are paired by natural sort order.
   ([Loading stereo images](03-loading-images.md))
2. **Provide a calibration** — run the built-in stereo calibrator, import one of
   six calibration-file formats, or enter parameters manually.
   ([Calibration](04-calibration.md))
3. **Choose the Workflow Type** — accumulative vs incremental, the solver, and
   (incremental only) the reference-update policy.
   ([Workflow type](05-workflow-type.md))
4. **Set the initial guess** — FFT, Previous, or place **Starting Points** for
   large motion / multi-region ROIs. ([Initial guess](06-initial-guess.md))
5. **Draw a Region of Interest** on the LEFT frame 1.
   ([Region of interest](07-region-of-interest.md))
6. **Set DIC parameters** — subset size, step, stereo/temporal search, mesh
   refinement. ([Parameters](08-parameters.md))
7. **Run** — watch progress and the failure-accounting log.
   ([Running](09-running.md))
8. **View the 3D displacement** — pick `U`/`V`/`W`/`|D|`/velocity, switch units,
   toggle deformed/reference, open the interactive **3D View**.
   ([Viewing results](10-viewing-results.md))
9. **Compute strain** in the separate Strain window (opens when the run
   finishes). ([Strain post-processing](11-strain-processing.md))
10. **Export** data, images, animations, or 3D renders.
    ([Exporting](12-export.md))
11. **Save the session** to one `.aldic3d` file so you can reopen the project
    without recomputing. ([Sessions](13-session.md))

## What pyALDIC-3D is (and is not)

pyALDIC-3D is an **independent application** with its own project format
(`.aldic3d`), its own workflow, and its own 3D visualization layer. It is built
**on top of** the pyALDIC-2D correlation engine, which it consumes as a pinned,
read-only library (`al-dic==0.7.*`) — it is not a "3D mode" bolted into the 2D
app. It currently supports a **two-camera** stereo rig; N-camera support is a
post-v1 goal.

Unlike the 2D app, pyALDIC-3D **does** require a calibration. Reconstructing 3D
points is impossible without knowing the two cameras' intrinsics and their
relative pose, so [Calibration](04-calibration.md) is a mandatory step rather
than an optional one.
