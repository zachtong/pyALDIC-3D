# UX + PERF AUDIT PLAN (2026-07-09, PM review + stress tests; PENDING USER APPROVAL)
# === UX track ===
# G1 safety/correctness (~half day): unsaved-changes guard (dirty bit EXISTS but never read);
#   close-during-run destroys live QThread -> prompt+stop+wait; ROI wrong-view trap -> auto-jump
#   to L/frame-1 like seed does; setMinimumSize 1420x800 breaks 1366x768 laptops -> ~1100x700 +
#   clamp to screen; pair-list frame jump uses len(left) only; export Open Folder can throw;
#   global sys.excepthook -> GUI console (2D port)
# G2 high-frequency UX (~1 day): tooltip full pass 49 -> ~170 widgets (2D teaching-quality bar +
#   stateful disabled-tooltips + InfoIcon port); manual Min/Max color range (2D ColorRange port,
#   the DIC-staple fixed-colorbar) + percentile [2,98] auto-range (regression vs 2D); trackpad pan
#   (space/right-drag) + zoom % readout + zoom clamp; keyboard shortcuts EXCEEDING 2D (F5 run,
#   arrows frames, Space play, Ctrl+0 fit, Esc); cancel feedback (indeterminate bar + 'finishing
#   current frame'); stale-params amber hint after run; Ctrl+S saves to project_path + windowTitle
#   [*] modified star; drop zones show loaded folder+count; ETA ELAPSED/REMAINING port
# G3 polish (~1 day): context menus (pair list remove/reveal, canvas fit/copy/clear, log);
#   window geometry + splitter persistence + recent-files menu (EXCEEDS 2D); canvas empty-state
#   quickstart hint; 3D next-step hint widget (ROIHint analog: which of calib/images/ROI/run is
#   next); log severity filter + save button (EXCEEDS 2D); strain auto-open only first run;
#   calibration dialog (click-to-enlarge preview, dedupe adds, natural sort, threshold live);
#   i18n readiness strings; Help/About (version/DOI); view_state save/restore; language
#   QActionGroup
# === PERF track (stress-tested: 12MP 2-frame = 6.5GB peak (16x transient); 200f x 5MP projected
#     ~32GB = OOM on 16-32GB machines; scrub = 100-300ms/frame GUI freeze) ===
# P1 OOM prevention (~1 day): share ONE ones-mask (one-liner, -8GB/cam @200f); lazy
#   NormalizingLazyProvider passed to run_aldic (engine docstring supports providers; kills eager
#   float64 x2 copies, -24GB @200f) VERIFY provider protocol carefully; _znssd chunked over points
#   (1.4GB -> ~0.15GB transient per frame, winsize-64 5.6GB -> bounded); RAM pre-check fail-fast
#   in run_pipeline (70% available rule, actionable sizing message)
# P2 GUI responsiveness (~1 day): LRU caps on viz caches (interp/support/pixmap ~24-48 entries;
#   was unbounded, 15+GB theoretical); background frame-decode prefetcher (fix 100-300ms scrub);
#   mesh preview build -> worker; 3D view: update actor points/scalars + KEEP camera (stop
#   reset_camera per frame); session save/load: stream into zip (no BytesIO double-buffer,
#   ZIP_STORED for npz member) + QThread + progress + 'save without results' option
# P3 throughput (~half day + strain vectorization separate): animation clear_frame_caches inside
#   frame loop (one-liner); render3d single-plotter sequence; npz/mat superset: stack views not
#   copies + drop strain double-write + build once for npz+mat; resample_to_points Delaunay reuse;
#   strain3d vectorized neighbor fits + progress/cancel hook; optional parallel L/R tracks (~2x)

# ROUND-2 USER AMENDMENTS (2026-07-08, all approved, "do everything, time no object"):
# [1] Starting Points = DEFAULT init strategy; ONE click on LEFT camera suffices.
#     Explain 'disparity prior' to user: auto template-match of the seed/anchors
#     L->R to find the big stereo offset (S2: true disparity ~290px vs +-80 search
#     around 0 -> false locks, 16% scale error). Seed point can drive BOTH temporal
#     seeding and the stereo offset.
# [2] CORRECTED: step size = POWERS OF 2 only (combo 2,4,...,128/256?); subset size
#     = ODD ONLY with snap-to-nearest-odd (2D convention: display odd 11-201,
#     internal even = odd-1). Follow 2D exactly.
# [3] Do NOT invent the cap UI; investigate how the 2D GUI handles search-range
#     limits (2D spin is 4-512 step 2) and mirror its approach.

# GUI REVIEW ROUND 2 (user 8 points, 2026-07-08) - VERIFIED, PLAN PENDING APPROVAL
# F1 quick (~half day): [2] subset size spin -> even 2..128 (warn <8 accuracy);
#   [3] search caps: engine clamps fft_search to max(10, img_min/4 - winsize) SILENTLY
#   -> dynamic spinbox max on image load + tooltip + visible log when clamped;
#   [6] remove Show Points (redundant w/ Show Grid node dots);
#   [8] remove blue ROI bbox rect (keep mask fill only);
#   [4a] dense-support triangles get edge-length cap (~2.5x step) so node-free ROI
#   holes stop being spanned (L and R both)
# F1 DONE 2026-07-08 (not committed): odd subset 5-201 snap-to-odd (draft.winsize
#   stays even = display-1); step combo 2..128 powers of 2 (+winsize_min auto-clamp
#   min(8, step), 2D parity); F1.3 = 2D approach mirrored (2D does NOT cap the spin;
#   engine warning now forwarded to GUI log via RunWorker showwarning capture +
#   formula tooltips on both search spins); Show Points + node-dot layer +
#   gui/rendering.py + ROI bbox rect removed; fieldmap edge cap 2.5x mesh_step
#   (median-NN fallback) + unit test. 299 tests green, i18n 100% (6 new strings x 7),
#   scan clean, gui_screenshot OK.
# F2 (~1 day): [1] INITIAL GUESS section port from 2D (Starting Points / FFT every
#   frame / FFT on ref update / Previous frame) -> map to engine switches
#   (init_fft_search_method, fft_auto_expand, seed pass-through; VERIFY engine
#   exposure first); include stereo disparity-prior auto-estimation option (S2
#   lesson); assess warm-start-freeze vs FFT-every-frame accuracy/cost tradeoffs;
#   [4b] right camera support = left ROI mask warped through frame-1 disparity
# F3 (~1 day): [7] failure-reporting audit end-to-end: per-frame diagnostics
#   (valid%, gated%, reasons) into RunResult.meta -> post-run log summary table +
#   warnings for low-validity frames; worker exceptions with full context to log;
#   honesty-gate kills must be VISIBLE; [5] 3D view root-cause (quad path vs
#   delaunay fallback with holed ROI; canvas ref_coords pass-through) + rebuild;
#   3D View toolbar button -> checkbox next to Show Grid/Show Subset
# F3 DONE 2026-07-08 (not committed): [7] matching/diagnostics.py (rows on
#   CorrespondenceSet.diagnostics -> meta diagnostics/summary/gates, JSON-safe);
#   honesty gate returns per-frame kill counts (TemporalField.n_gated); all 3
#   strategies attach rows + loud all-invalid frame-1 stereo guard w/ params;
#   CLI prints summary_lines (exit 1 on all-empty); GUI _on_done writes tr()'d
#   summary (stereo rate / gate kills w/ reason / low-validity frames / gate
#   demotions / verdict); RunWorker+StrainWorker emit ExcType: msg + traceback
#   to stderr; 'warning' level alias now colored; strain LOG auto-expands on
#   error; empty result -> canvas notice + View3D message + log error.
#   [5] ROOT CAUSE: canvas _render_3d never passed the drawn ROI mask (holes
#   only survived if points were NaN; Delaunay fallback spanned them) ->
#   shared viz3d.build_surface_polydata (quads + filter_cells_by_mask +
#   edge-capped tri fallback, used by View3D AND export/render3d); 3D auto
#   range now = 2D visible_values contract (per-frame, writes shared signals;
#   stable-range helper removed); 3D View button -> QCheckBox by Show Subset.
#   331 tests green, ruff clean, i18n 472x7 100% + scan clean, gui_screenshot
#   OK (summary lines + zh_CN verified in shots).

# GUI PARITY PLAN (user 6-point review 2026-07-08; investigated via 4 readers)
# Batch A - quick wins (~half day): items 1+2+3+6
- [ ] A1 Solver combo 'AL-DIC'/'Local DIC' in WORKFLOW TYPE (2D: workflow_type_panel.py:70-91,
      tooltip verbatim); replaces the 'AL-DIC global step (ADMM)' checkbox; maps to
      draft.use_global_step
- [ ] A2 NEW 'ADVANCED' CollapsibleSection (collapsed): 'AL-DIC Iterations' spin 1-10 moved here
      (label hides the ADMM acronym, greyed under Local DIC + hint line, 2D advanced_tuning_widget)
      + move strategy combo here too (user: not user-facing for now)
- [ ] A3 Step size: combo 4/8/16/32 -> QSpinBox 2..256 (2D uses combo [4..64]; user wants 2-256)
- [ ] A4 Config overlay rows -> MODE / SOLVER / SUBSET only (drop STRATEGY);
      SOLVER = 'Local DIC' | 'ADMM (N iter)' (2D canvas_config_overlay.py:97-103);
      SUBSET = 'w / s px'
- [ ] A5 'Show on deformed frame' checkbox (FIELD section, default ON; 2D right_sidebar.py:138-148):
      ref mode = frame-0 background + points at xL[0]/xR[0], values still frame k
      (canvas_area.py:226-236 + line 317); auto colorbar from visible nodes
- [ ] A6 i18n round + screenshots + tests
# Batch B - ROI toolbox + mesh preview (~1 day): item 4
- [ ] B1 Port 2D ROIController (Qt-free cv2 mask engine: rect/polygon/circle/circle3, add/cut,
      brush paint/erase, import/invert/save) as al_dic_3d copy; ROI = left-cam frame-1 BOOLEAN MASK
      (draft mask array -> build() writes PNG -> runner mask0 + bbox roi)
- [ ] B2 Port ROIToolbar (+Add/Cut menus, Refine brush w/ radius, Import/Save/Invert/Clear)
- [ ] B3 Port MeshOverlay (viewport child QWidget, prebuilt QPainterPath, cosmetic pens; edges
      white 1px, node dots green 3px cap 4000) + preview mesh via runner._build_reference_mesh
      logic, 300ms debounce on params_changed
- [ ] B4 'Show Grid' (default ON) + 'Show Subset' (hover yellow dashed square = winsize, snapped
      to nearest node) toggles on canvas toolbar; ~40 i18n strings
# Batch C - strain as post-processing (~1 day): item 5
- [ ] C1 Pipeline always compute_strain=False; remove checkbox from WORKFLOW TYPE
- [ ] C2 StrainWindow3D (lightweight v1: params + Compute button + QThread progress + dirty hint;
      display stays in main field selector) - params: strain window size, smoothing, (fit method);
      writeback dataclasses.replace(result, strain=...) + results_changed
- [ ] C3 Auto-open on run DONE + sidebar button (2D app.py:908-937); fix EXISTING bug: strain
      buttons not re-enabled on project open (route set_strain_available off results_changed)
# open question for user: strain window full 2D clone (own canvas+navigator) vs lightweight v1

# EXECUTION (user 2026-07-07 approved): A) AL global step DEFAULT ON
# (stereo stays local ICGN = MATLAB anchor); B) quadtree refinement wired
# 2D-pyALDIC style: default OFF, checkable refine_inner / refine_outer /
# BRUSH-drawn mask / refinement level (min_elem = max(2, step//2**level)).
# Static frame-1 refined mesh at RUNNER level (no per-frame policy into
# run_aldic — drift guard + mesh-built-once invariant).
- [x] A1 primitives: make_dicpara(use_global_step=True, admm_max_iter=3)
- [x] A2 RunConfig [matching] use_global_step/admm_max_iter + strategies
      pass-through + contract test (para flags asserted)
- [x] A3 GUI PARAMETERS: 'AL-DIC global step' checkbox (default on) +
      ADMM iterations spin (1-10, default 3) + draft/session + i18n
- [x] B1 runner: if any refine option on -> al_dic build_refinement_policy
      + refine_mesh ONCE on frame-1 mask/ROI -> static refined mesh
- [x] B2 RunConfig [matching] refine_inner/refine_outer/refinement_level
      (+ refinement_mask path option); draft fields; session round-trip
- [x] B3 GUI: two checkboxes + level spin + BRUSH paint mode on canvas
      (paint strokes -> mask overlay -> draft.refinement_mask)
- [ ] C re-gate: full pytest, S3 parity (ADMM ON + refined mesh),
      runtime delta measured; INDEX changelog; memory

# INVESTIGATION (user 2026-07-07): do our 3D backend calls exercise the
# ALDIC core features — Augmented-Lagrangian/ADMM solver, window
# splitting, adaptive mesh refinement — all ported to Python in al_dic?
# Suspicion: make_local_dicpara runs LOCAL-ONLY ICGN (no AL global step),
# no refinement_policy (established), window-splitting unknown.
# Deliverable: feature matrix (MATLAB trusted path | al_dic availability |
# our 3D usage | gap) + adoption plan. Workflow: 3 parallel readers.
#
# AUDIT VERDICT (2026-07-07, 3 reports in scratchpad AUDIT_{ours,engine,matlab}.md):
# 1) AL/ADMM: MATLAB temporal = FULL ALDIC (Subpb1+Subpb2 FEM, max 2 ADMM iters,
#    UseGlobal default true; STEREO is ICGN-only even in MATLAB). al_dic: fully
#    implemented, ON by default (use_global_step=True, admm_max_iter=3, beta
#    auto-tune). OURS: OFF — make_local_dicpara hardcodes use_global_step=False;
#    admm_max_iter=1 is a validator placebo (memory note '0=local-only' is
#    OUTDATED: 0 fails validation; real switch = use_global_step).
#    => GAP: temporal tracks must run the global step. Stereo stays local (OK).
# 2) WINDOW SPLITTING: subset SUBDIVISION exists in NEITHER port. MATLAB
#    actually GROWS subsets near mask (funICGNQuadtree; abandon >=40% masked,
#    hole-mark >60%); winsizeMin is a MESH param. al_dic equivalent = always-on
#    masked-subset CC gating (coverage<50% -> mark_hole; winsize_list per-node
#    infra exists but always uniform). => our layer already inherits the
#    Python guard; true per-node winsize adaptation = 2D-repo feature (D11).
# 3) QUADTREE REFINEMENT: MATLAB refines mask-boundary elements to winsizeMin
#    (stereo once; temporal per-frame but identical in acc mode). al_dic:
#    IMPLEMENTED (RefinementPolicy/build_refinement_policy/qrefine_r), OFF by
#    default. OURS: unused + bbox uniform grid wastes 2/3 nodes.
#    => GAP: build refined STATIC frame-1 mesh at runner level (mask criteria,
#    min_element_size=winsize_min) — keeps our mesh-built-once invariant and
#    our strategies' 'corr points ARE mesh nodes' contract; do NOT pass
#    refinement_policy into run_aldic (per-frame re-trim would trip
#    temporal_track's drift guard); inc-mode per-frame remesh deferred.
# PLAN (pending user green light — changes results/runtime, full re-gate):
#  P0-a config [matching] use_global_step=true(default)/admm_max_iter=3 ->
#       make_dicpara; strategies pass through; stereo unchanged; contract test.
#  P0-b runner mesh: quadtree-refined in-mask mesh (al_dic refine_mesh) ->
#       denser boundary-conforming points (parity w/ MATLAB 3987-node style).
#  Re-run ALL gates (S3 parity, synthetic suites); measure runtime delta.

# MATLAB real-data parity gates (user 2026-07-07: "自己去搜索我的电脑里的
# 3d aldic MATLAB版本里面的案例来测试" — user away from computer, full autonomy)

FINDINGS (../3D-Stereo-ALDIC, READ-ONLY):
- tests/run_pipeline_test.m = NON-INTERACTIVE regression harness on
  examples/Stereo_DIC_Challenge_1.0_S3 (3 frames 0000-0002, DICe calib,
  winsize=32 winstepsize=32, DICIncOrNot=1 INCREMENTAL, quadtree+masks,
  ClusterNo=1, NewFFTSearchDistance=[60,60], images loaded TRANSPOSED ');
  baseline at tests/baseline/baseline.mat (v7.3 -> needs h5py).
- PROBLEM: S3 Images_Stereo_Sample3_images/ has only Right/ — Left/ MISSING
  (masks L+R both present). Search machine for the Left set; else fall back.
- Complete datasets: tests/D_shape (One_folder + Seperate_folders, images+
  masks+calibration_DICe.xml+results), examples/pig_heart (Left/Right+masks+
  DICe calib), Stereo_DIC_Challenge_2.1_Bespoke.
- MATLAB R2023b installed at /c/Program Files/MATLAB/R2023b — can run
  `matlab -batch` with OUR driver script (addpath their repo READ-ONLY,
  save outputs to OUR side; mexw64 already compiled).

PROGRESS 2026-07-07 (tools/matlab_parity.py; PARITY_MODE env acc|inc):
- [x] h5py installed; baseline.mat read (3987 pts; disp: U med 0.095/0.179mm,
      V 0.408/0.832, W 0.076/0.132 for frames 1/2; reproj 0.104/0.085/0.503)
- [x] S3 Left images FOUND: ../3D_ALDIC_unused/Examples/Image_Stereo_Sample3/
      (right frames byte-identical to 3D repo); consumed read-only in place
- [x] runner already supports masks; FIXED sequence pairing validator (DICe
      naming 0000_0/0000_1: trailing digits = CAMERA; now leading-index
      fallback; sequence tests 10 pass) — NOT YET COMMITTED
- [x] harness runs end-to-end; our raw fields saved reports/parity_s3/s3_ours.npz;
      config reports/parity_s3/s3_parity.toml
- MEASURED (533 finite pts vs their 3987; scale ~0.06mm/px):
  frame0 static Z: 30um median vs MATLAB — STEREO+CALIB+TRIANGULATION GOOD
  frame1 (identical acc & inc, as expected): U slope -0.13, V +0.61, W +11.9
    -> FIRST TEMPORAL STEP WRONG in both modes; W x12 amplification =
    left/right temporal pairing inconsistency (disparity error -> depth blow)
  frame2 inc: U med 1.95mm slopes +13 (INC COMPOSITION BLOWS UP — bug #2);
  frame2 acc: U 0.14 V 0.64 W 0.37 (better but still >> signal)
  our reproj 0.000/0.001/0.001 px (two-view DLT self-consistency, not a QC)
- [x] NEXT-1 DONE — ROOT CAUSE LOCALIZED: xL/xR tracks saved; LEFT camera
      temporal displacement is EXACTLY ZERO (uL frame1 med/std = 0.000/0.000)
      while RIGHT tracks fine (uR = (+0.93,-6.95)px, physically right).
      One frozen ray => V halved, W x12 blow-up = the observed 3D signature.
      Inputs verified distinct (per-frame sums differ). track_both code is
      correct (xl_k = coords_L + tf_L.u_accum[k]); so run_aldic returned
      all-zero U_accum for the LEFT call only. L vs R call difference:
      LEFT uses EXTERNAL mesh_L (runner-built) + para_L(img_ref_mask=L1 mask,
      roi=bbox(coords_L)+margin); RIGHT uses its own build_grid_mesh(para_R).
      Suspect: engine degenerate branch for external-mesh + img_ref_mask.
      NOTE ALSO frame2-acc: uR only -7.35px (should be ~2x -6.95) => right
      acc tracking also lags at frame 3; and inc composition blow-up = bug #2.
- [x] ROOT CAUSE #1 FIXED: strategies never forwarded per-frame masks into
      temporal_track -> background-heavy bbox mesh -> FFT garbage-peak zone
      escalation (20->600px) poisoned in-mask nodes -> ICGN all-NaN -> 2D
      engine SILENTLY ZERO-FILLED (UserWarning only) -> frozen left camera.
      Fix: _common.mask_stream() + masks= in all 3 strategies' temporal_track
      calls; temporal.py promotes the engine's 'All nodes are NaN' warning to
      RuntimeError (never trust a frozen camera again).
- [x] P1 GATE ACHIEVED (frame 0->1, real data): U med 1.2um p95 3.2 slope
      +0.999 | V 1.0um/3.1 +1.005 | W 5.8um/18 +0.850 | Z 30um — the
      promised um-level MATLAB parity on real data. Gate assertions added to
      tools/matlab_parity.py (exits nonzero on fail).
- [x] FRAME-3 ARBITRATED INVALID AS BASELINE: template matching (multi-
      location, both cameras) shows the TRUE 0->2 motion is ~(-8..-95,
      -52..-64)px, heavily deforming/decorrelating (scores 0.16-0.76), i.e.
      ~10x the MATLAB baseline's claim (-13px = suspicious exact 2x of
      frame 2) and their own frame-3 reproj jumps to 0.503px -> the MATLAB
      run failed that frame too. Frame index 2 reported but NOT gated.
- [ ] OPEN NEXT: inc-mode composition (bug #2, blows up on real data even
      frame 2); frame-3 challenge = the test target (true increment ~-56px
      fits inside 60px search in inc mode -> fixed inc could BEAT the MATLAB
      baseline there). Template-truth anchors: L0[380,800]->L2 (-8,-64)@0.76.
- [ ] commit fixes + harness; INDEX changelog; memory; parity report PDF

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
