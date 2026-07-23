# 4. Calibration

Calibration is what makes 3D possible: it recovers each camera's **intrinsics**
(focal lengths, principal point, lens distortion) and the **extrinsics** (the
rotation and translation between the two cameras). Without it, matched pixels
cannot be triangulated to a 3D point. This is a mandatory step with **no 2D
equivalent** — pyALDIC-3D gives it a full chapter and three ways to satisfy it.

The **CALIBRATION** section of the left sidebar offers three buttons:

- **Calibrate from images…** — the built-in stereo calibrator (recommended).
- **Import calibration…** — read an existing calibration file in one of six
  formats.
- **Manual parameters…** — type intrinsics and extrinsics by hand.

A **status label** shows the current state: *No calibration loaded*, or, on
success, `filename` with `fx`, `fy`, and the `baseline` in mm. All three paths
converge on an OpenCV-YAML calibration that the run consumes.

Convention: the **left camera is the world frame** (`R = I`, `T = 0`); the
extrinsics express the right camera relative to it as `X_R = R · X_L + T`.

## Option A — the built-in stereo calibrator

Click **Calibrate from images…** to open the *Stereo Calibration* dialog. You
photograph a calibration board from many poses with the same stereo rig, load
the LEFT/RIGHT board image sets, and the app detects the board, solves the
mono + stereo geometry, runs QC, and writes the calibration.

### Board family

The **Type** combo selects the board family; the per-board parameter fields
switch with it:

| Type | Code | Parameters shown |
|------|------|------------------|
| **Chessboard** | `chessboard` | Columns × Rows (inner corners), Square size (mm) |
| **ChArUco** | `charuco` | Columns × Rows, Square size (mm), Marker size (mm), *Board printed with OpenCV < 4.7* (legacy) |
| **Circle grid** | `circles` | Columns × Rows, Dot pitch (mm), Dot diameter (mm), *Asymmetric grid* |
| **Coded dot target (3 ring markers)** | `coded` | Columns × Rows, Dot pitch (mm), Dot diameter (mm) |

Defaults: Columns **9** × Rows **7**; Square size **12.0 mm**; Marker size
**9.0 mm**; Dot pitch **12.0 mm**; Dot diameter **6.0 mm**.

### Solver options

A **SOLVER OPTIONS** group exposes the same switches the CLI has:

- **Jointly refine intrinsics (advanced)** — refine intrinsics inside the stereo
  solve.
- **Estimate tangential distortion p1/p2** — otherwise `p1 = p2 = 0`.
- **Fix k3 = 0 (low-distortion lens)** — drop the third radial term.
- **Release-object method (printed boards)** — for imprecise printed boards
  (full views only).
- **Dot eccentricity correction** — corrects the projected-circle centroid bias
  for circle / coded targets; **on by default**.
- **Joint bundle adjustment (robust, uses mono views)** — a final scipy bundle
  adjustment.
- **Optimize board shape (printed boards)** — enabled only when bundle
  adjustment is on.

A **Reject threshold (px)** spinbox (default **1.0**) controls worst-pair
rejection; a **Recalibrate** button re-solves after you change it.

### Running the calibration

Click **Calibrate**. The image-pair table shows per-pair columns **#**,
**Left**, **Right**, **Points**, **RMS L/R**, **Max E**, **Status** — poor pairs
are dropped and marked. Other buttons: **Print board… (1:1 PDF)** (print a board
to scale), **Verify with board images…**, **Save detections…** /
**Load detections…**, and finally **Accept & Save…** to write the YAML that the
run will use.

### Reading the QC report

The **RESULT** panel is the sanity check — read it before trusting a run:

- **Stereo RMS … px | epipolar … px** — reprojection and epipolar residuals.
  Sub-pixel (well under 1 px) is good.
- **Baseline … mm | pairs used/total** — the physical distance between the two
  cameras and how many board pairs survived QC.
- **fx fy cx cy** — the recovered intrinsics.
- **Coverage L / R | tilt …°** — how much of each image the board views covered,
  and the range of board tilts.
- Optional lines report the bundle-adjustment RMS change, board flatness, and
  any warnings.

If you loaded a verification pair, a **Verify** line reports the measured board
pitch versus the true pitch, the scale error, and the plane RMS in mm — the most
direct check that the calibration's absolute scale is correct.

## Option B — import an existing calibration

Click **Import calibration…** and pick the **Format**. Six importers are
supported (the sidebar's Format combo lists them alphabetically; the default is
`opencv_yaml`):

| Format id | Source |
|-----------|--------|
| `dice` | DICe OpenCV-XML camera-system file |
| `matchid` | MatchID `*.caldat` label/value table |
| `matlabcv` | MATLAB `stereoParameters` `.mat` |
| `mmc` | MMC / MultiDIC `.mat` |
| `opencorr` | OpenCorr CSV |
| `opencv_yaml` | OpenCV `cv2.FileStorage` YAML/XML |

The file dialog filter accepts `*.xml *.yaml *.yml *.mat *.csv *.txt *.caldat`.
All six normalize to the same internal `StereoRig` (left camera = world frame),
so downstream reconstruction is identical regardless of source.

## Option C — manual parameters

Click **Manual parameters…** for the *Manual Camera Parameters* dialog. It has
two camera groups — **Left camera (world frame)** and **Right camera** — each
with intrinsic fields `fx`, `fy`, `cx`, `cy`, `skew`, `k1`, `k2`, `k3`, `p1`,
`p2`, plus a stereo-extrinsics group **`X_R = R · X_L + T`** with `Rx/Ry/Rz`
(degrees) and `Tx/Ty/Tz` (mm). A live **Baseline |T|** preview shows the camera
separation.

Conventions (stated in the dialog): Euler composition `R = Rz·Ry·Rx` in degrees
(MatchID / OpenCorr convention); distortion order `k1, k2, p1, p2, k3` (OpenCV).
**Save as YAML…** writes an `opencv_yaml` file.

## The `calibrate` CLI (headless)

The same calibrator runs headless. Detect a board in synchronized L/R image
sets, solve with QC, and write an OpenCV YAML:

```bash
al-dic-3d calibrate \
  --left "cal/left_*.tif" --right "cal/right_*.tif" \
  --board chessboard --cols 9 --rows 7 --square 12.0 \
  -o calibration.yml
```

Board-specific arguments mirror the dialog: `--square` (chessboard/charuco),
`--marker` + `--dict` + `--legacy` (charuco), `--spacing` + `--dot` +
`--asymmetric` (circles/coded). Solver switches: `--joint`, `--tangential`,
`--fix-k3`, `--release-object`, `--no-ecc-correction`, `--min-pairs` (default 6),
`--bundle`. Verify against a known board with `--verify-left` / `--verify-right`.
Run `al-dic-3d calibrate -h` for the full list.

The written YAML is consumed by a run as `[calibration] file = "calibration.yml"`,
`format = "opencv_yaml"`.

## How calibration feeds the run

Whichever path you use, the sidebar records the calibration file path and format
on the project. The run loads it with `load_calibration(file, format)` to build
the `StereoRig`, then triangulates every matched L/R point pair through that rig
into a 3D world point. A wrong or low-quality calibration shows up as a bad
baseline, few valid 3D points, or physically implausible `W` — see
[Troubleshooting](14-troubleshooting.md).

Next: [Workflow type →](05-workflow-type.md)
