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

## 1. Qt-free compute layer (src/al_dic_3d/calibration/)
- [ ] boards.py — frozen specs: ChessboardSpec / CharucoSpec / CircleGridSpec /
      CodedCircleGridSpec; object-point builders; board image generators
      (print + synthetic rendering)
- [ ] detect.py — detect_board(image, spec) -> BoardDetection(image_points,
      object_points, ids, ok, reason, sharpness); SB detector w/ classic
      fallback (never mixed per set), CharucoDetector (4.7+ OO API,
      setLegacyPattern option), findCirclesGrid + tuned blob detector,
      custom coded-target detector (blob -> ring fiducials via contour
      hierarchy -> lattice indexing -> subpixel refine)
- [ ] solve.py — calibrate_mono (calibrateCameraExtended | ROExtended for
      printed boards; model flag policy), calibrate_stereo (per-cam intrinsics
      -> stereoCalibrateExtended CALIB_FIX_INTRINSIC default, joint refine
      optional), auto worst-view rejection loop (k*median), epipolar-distance
      validation -> (StereoRig, CalibrationReport)
      NOTE stdDeviationsIntrinsics order: fx,fy,cx,cy,k1,k2,p1,p2,k3..k6,s1..s4,tx,ty
- [ ] report.py — CalibrationReport (per-view RMS, coverage, pose diversity,
      std devs, dropped views + reasons, epipolar err) + to_opencv_yaml writer
      (provenance as extra YAML nodes) round-tripping via from_opencv_yaml

## 2. Synthetic parity gate (tests/)
- [ ] synth_calib.py — render calib image sets via planar homography, known
      K/dist/R/T ground truth, all four board types
- [ ] test_calib_boards / test_calib_detect / test_calib_solve — recover truth
      within tolerance; rejection behavior; failure paths; YAML round-trip

## 3. CLI
- [ ] `al-dic-3d calibrate` subcommand (reserved seam in cli.py) -> YAML + report

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
