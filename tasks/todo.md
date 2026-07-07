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

## 4. GUI (pyALDIC style, i18n contract)  [DONE 60bb641]
- [x] gui/dialogs/calibration_dialog.py — pair table w/ per-image status
      (failures red w/ reason), board form (contextual per family), QThread
      worker + cached-detection recalibrate, per-pair RMS bars + dashed
      threshold, result panel, Accept -> YAML -> draft funnel
- [x] gui/dialogs/manual_params_dialog.py — intrinsics x2 + Euler/T -> YAML
- [x] left_sidebar: Calibrate from images… (primary) / Import… / Manual…
- [x] i18n: 63 new strings x 7 locales -> 191 each 100%, .qm compiled, scan clean
- [x] offscreen dialog screenshots read + visually checked (theme-consistent)

## 5. Gate + report  [DONE]
- [x] tools/calib_report.py -> reports/calib_builtin.pdf — 5 gates PASS live
      (chessboard parity / coded-target parity / YAML round-trip / i18n /
      dialog shots); 178 tests green; ruff clean

## Review (2026-07-07)
- Commits: 17ddc18 docs D12, ccc8bbc compute core, b1ea9c4 CLI, 60bb641 GUI+i18n.
- Gate numbers (synthetic, deterministic): chessboard rms 0.0145px, fx 0.003%,
  cx 0.069px, baseline 1.8um, R 0.0021deg, epipolar 0.011px, 18/18 pairs;
  coded target rms 0.036px 18/18; charuco cx 0.009px; tangential p1 exact.
- Key engineering findings (documented in code/memory): SB needs cornerSubPix
  refine on band-limited edges (14x); planar-target cx<->tangential coupling
  (zero_tangent default); pose corner-coverage + strong tilts required or cx
  degenerate; clipped border dots must be rejected; eccentricity correction
  implemented analytically (projected-disc centroid).
- OPEN: tune coded-target detector on the user's real target photos.

## C3 enhancements (user go-ahead 2026-07-07)
- [ ] calibration/printout.py — save_board_pdf(spec, path): 1:1 physical-scale
      PDF (exact mm sizing via matplotlib figsize) + spec legend + scale-check
      caption; ValueError if board exceeds the page
- [ ] calibration/verify.py — verify_known_distance(rig, det_l, det_r, spec):
      triangulate common board points (undistort P=K -> triangulatePoints),
      neighbor-distance vs true pitch -> scale error %, distance RMSE, plane
      RMS (iDICs independent-verification idiom)
- [ ] calibration/bundle.py — bundle_refine(left, right, base, image_size):
      scipy least_squares joint BA over intr L/R + stereo R,T + per-view board
      poses; robust soft_l1 per-POINT loss; uses single-camera views (mono
      residuals); sparse jacobian; concept credit aniposelib (BSD-2), original
      code
- [ ] GUI: pair-table selection -> L|R overlay preview w/ detected points;
      Print board… button; Verify with board images… button; Joint bundle
      adjustment checkbox (worker runs BA after solve, reports rms before/after)
- [ ] CLI: --bundle, --verify-left/--verify-right on calibrate
- [ ] tests: printout, verify (synthetic scale error < 0.1%), bundle gate
      (accuracy >= base; robust to injected per-point outliers; uses mono-only
      views), dialog additions
- [ ] i18n: new strings x 7 locales; full suite green; commit
