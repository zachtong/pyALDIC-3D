# Built-in stereo calibration (C1+C2, approved 2026-07-07)

User decisions: targets = chessboard + coded dot target (3 concentric locating
circles, VIC-3D style) [+ ChArUco recommended]; scope = C1+C2 in one pass.
Research basis: 5-agent workflow (OpenCV SOTA / DIC domain / libs / our code /
MATLAB conventions), 42/44 key facts adversarially confirmed. Stack = pure
OpenCV (opencv-python-headless>=4.7, zero new binary deps). Result re-enters
the pipeline as opencv_yaml via the existing calibration_file path (RunConfig /
runner / session schema v1 untouched).

## 0. Docs first (handoff protocol)
- [x] D12 in 00_INDEX decision log (amends D2 import-only) + changelog entry
- [x] 01 §B.1 calibration scope line + §F workflow step 3 three-entry wording

## 1. Qt-free compute layer (src/al_dic_3d/calibration/)  [DONE ccc8bbc]
- [x] boards.py — 4 frozen specs + object lattices + board image generators
- [x] detect.py — SB+classic w/ cornerSubPix refine (14x on band-limited
      edges), ChArUco 4.7+ OO API, findCirclesGrid, coded-target detector
      (ring fiducials via contour hierarchy -> affine hypothesis -> homography
      lattice refine; clipped-blob rejection at borders)
- [x] solve.py — mono Extended/ROExtended (zero_tangent DEFAULT True: planar
      cx<->p1p2 coupling amplifies noise ~3x), stereo FIX_INTRINSIC default +
      joint option, rejection loop w/ 1px absolute floor, epipolar validation,
      disc-centroid eccentricity correction (dot_radius_mm, fixed-point on
      ORIGINAL measurements). stdDev order fx,fy,cx,cy,k1,k2,p1,p2,k3...
- [x] report.py — to_opencv_yaml (meta_* provenance nodes, round-trips),
      coverage_fraction, summarize
- Measured gate: chessboard rms 0.015px fx 0.003% cx 0.07px base 1.8um
  R 0.002deg; coded 18/18 rms 0.036; charuco cx 0.009; tangential p1 exact

## 2. Synthetic parity gate (tests/)  [DONE ccc8bbc]
- [x] synth_calib.py — exact back-projection renderer (undistort rays cached
      per camera), 18 coverage-designed poses (corners low-tilt, center +/-32deg),
      sigma=3 texture band-limiting, half-pixel origins (charuco origin = OUTER
      corner!)
- [x] test_calib_boards (10) + test_calibration_gate (13): all four boards,
      solve gates, rejection, RO, tangential, YAML round-trip, failure paths

## 3. CLI  [DONE]
- [x] `al-dic-3d calibrate` + tests/test_cli_calibrate.py (2)

## 4. GUI (pyALDIC style, i18n contract)
- [ ] gui/dialogs/calibration_dialog.py — pair list w/ per-image status +
      detection overlay, board spec form, QThread solve, per-view error bars +
      threshold reject/recalibrate loop, coverage heatmap, accept -> YAML ->
      draft (single QC funnel via _preview_calibration)
- [ ] gui/dialogs/manual_params_dialog.py — per-camera fx/fy/cx/cy/skew/dist +
      R (Euler deg | matrix) + T (mm) -> StereoRig -> YAML
- [ ] left_sidebar CALIBRATION: Calibrate… / Import… / Manual… buttons + resync
- [ ] i18n: extract -> fill 8 locales -> compile -> scan clean
- [ ] offscreen screenshot self-check of both dialogs

## 5. Gate + report
- [ ] tools/calib_report.py -> reports/calib_builtin.pdf (gate metrics, QC
      demos, GUI shots); pytest green; ruff clean; conventional commits

## Review
(to fill at gate)
