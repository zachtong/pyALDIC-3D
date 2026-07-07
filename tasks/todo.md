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

## MMC-study adoption batch  [ALL DONE 2026-07-07: f2c509e, 4d7adfa, 37c909f, +P2-4]
Source: reference/Multi_Camera_Calibration study (3 reports in scratchpad
MMC_{detect,solve,workflow}.md). Importer fix already shipped (afe5ec9).
Measured: warped-board recovery <0.08mm RMS; jackknife std fx 0.124px /
baseline 3um; border dots recovered 0.036px (subpixel rim refit — binary-arc
bias had pushed k1 0.0006->0.0057, refit fixed it); 202 tests, 6 gates PASS.
- [x] P1-1 bundle.py board morphology (optional flag `board_morphology`):
      per-point delta blocks obj = obj0 + delta over the UNION of ids; gauge =
      2 farthest points fully fixed + 1 off-axis point z-fixed (7 constraints,
      MMC scheme); sparsity += per-view observed-point delta blocks; info +=
      board_z_range/board_max_dev + board_points array. Tests: (a) flat board
      + morphology -> deltas~0, accuracy kept; (b) ANALYTIC detections from a
      warped board (project GT warped points, no rendering) -> morphology
      recovers z-warp, rigid BA shows bias.
- [x] P1-2 stability jackknife (verify.py: stability_jackknife, drop_fraction,
      n_samples, seeded rng, returns per-param arrays + std/min/max) +
      report.py point_residuals(result, left, right) via solvePnP-composed
      reprojection; calib_report.py: residual (dx,dy) scatter panel + stability
      spread panel. Tests: shapes, small stds on clean synth, scatter finite.
- [x] P2-3 detect.py coded path: retry ladder (Otsu -> adaptive -> threshold
      sweep 60..200/35) + border-clipped dot recovery via partial-arc
      fitEllipseAMS (drop border-adjacent contour pts, need >=6 pts + arc span
      >=240deg + small radial residual; ellipse center == area center for
      full ellipses so consistent w/ ecc correction). Never centroid a clipped
      blob (old 7.7px bug class). Tests: synthetic clipped-edge pose recovers
      border ids <0.3px; solve stays accurate; retry ladder on low-contrast.
- [x] P2-4 GUI: "Optimize board shape" checkbox (needs bundle checked; worker
      passes board_morphology; result line shows z-range); Save/Load
      detections… buttons (npz via report.py save_detections/load_detections;
      re-solve w/o re-detect); pair-table adds Max-E column (from
      point_residuals); BA telemetry: bundle_refine(progress=cb) emits
      rms every ~25 nfev -> Working… line; info['cost_history'].
- [x] i18n new strings x7; full suite; commits per item; INDEX changelog;
      memory update.
- [ ] P3-5 subpixel-edge vs centroid comparison: BLOCKED on user's real target
      photos (note only).

## C3 enhancements (user go-ahead 2026-07-07)  [DONE 98198b3, 189 tests]
- [x] calibration/printout.py — 1:1 PDF + scale-check legend + page-fit guard
- [x] calibration/verify.py — known-distance verification (scale error catches
      what reprojection RMS cannot: gate proves 2% baseline error -> 2% scale
      error flagged); plane RMS flatness
- [x] calibration/bundle.py — scipy joint BA, robust per-point soft_l1, uses
      mono-only views, sparse jacobian; gates: parity accuracy kept, survives
      8px point outliers, 4 blinded right views still contribute
- [x] GUI: L|R overlay preview on row selection (auto-selects row 0 after
      solve), Print board…, Verify with board images…, BA checkbox
- [x] CLI --bundle / --verify-left / --verify-right
- [x] 11 new tests; i18n 204 x 7 100%; calib_builtin.pdf regenerated (5 PASS)
