# 分阶段执行指令（Coding-Model Phase Prompts）v1.2

> 用法（Claude Code）：本仓库根目录的 **`CLAUDE.md` 会自动加载**，其中已包含下面的
> Master Preamble 内容（身份、仓库位置、不变量、工程规则）。所以每个开发会话你**只需
> 粘贴对应的 Phase Prompt**（下方 ```text 块），不必再粘贴 Preamble。
>
> 用法（其它 harness / API 调 Opus 等）：CLAUDE.md 不会自动加载时，把 §Master
> Preamble 全文 + 对应 Phase Prompt 一起粘贴。
>
> 所有 ```text 块均为**流式排版、可直接复制**（无句中人为换行）。
> 一个阶段一个会话；每阶段结束于门禁（测试 + 指标 + PDF 报告），经用户确认后才开下一阶段。
> 与 `01_technical_baseline.md`、`02_correspondence_strategies.md` 冲突时以文档为准。

---

## Master Preamble

> 【Claude Code 场景可跳过粘贴——已在 CLAUDE.md 自动加载。此处保留供其它 harness 使用。】

```text
You are implementing pyALDIC-3D, a stereo-DIC desktop application. It is an INDEPENDENT application (own repo, own project schema, own state management, own workflow controllers, own 3D visualization layer) built ON TOP of the pyALDIC-2D platform, which it consumes as a library. The architecture is already decided and documented — it is NOT yours to change. Read first: docs/architecture/00_INDEX.md (decisions D1-D11 + handoff protocol), 01_technical_baseline.md, 02_correspondence_strategies.md.

REPOSITORY LOCATIONS — verify at session start. The reference repos are how you consult the 2D engine and the algorithm; if you cannot find them, STOP and ask the user rather than guessing or reinventing. Your workspace is the pyALDIC-3D folder (import package al_dic_3d, PyPI dist al-dic-3d, session extension .aldic3d). The two reference repos are SIBLING directories under the same MATLABCodes/ parent, and BOTH are READ-ONLY from your sessions: "../pyALDIC" is the 2D platform (import package al_dic), consumed as a PINNED LIBRARY (al-dic==0.6.*) — do NOT modify it (decision D11; the deferred 2D-platform backlog in 01 §C.1 is NOT your task and would be done in a separate 2D-repo session if ever); "../3D-Stereo-ALDIC" is the MATLAB algorithm reference. You may READ both freely; the settings.json denies writes to both. Absolute paths on the author's machine (2026-07-02, orientation only): C:\Users\13014\OneDrive - The University of Texas at Austin\Documents\MATLABCodes\{pyALDIC,3D-Stereo-ALDIC} . The user has more than one machine and the "13014" username may differ, so trust the SIBLING RELATIONSHIP over the absolute prefix: run `ls ..` from your workspace and confirm both siblings are present before relying on them. Ultimate fallback if a sibling is absent: clone https://github.com/zachtong/pyALDIC.git and https://github.com/zachtong/3D-Stereo-ALDIC.git into the sibling location; do NOT proceed without the references.

MATLAB USAGE. Trust ONLY gui/runPipelineCore.m and the functions it calls (StereoMatch_STAQ, TemporalMatch_quadtree_ST1, organizeMatchedPairds_*, stereoReconstruction_quadtree, PlaneFit3_Quadtree, computeStrain3D, cameraParamsFormatConvertFrom*). Everything else (TemporalMatch_inc*, StereoMatch2, *_ST2, epipolar_ICGN1, *_task2*) is experimental dead code — never port it. NEVER translate MATLAB literally: extract the math, write idiomatic Python. The MATLAB RD/ResultDisp bookkeeping and its mode branching are explicitly banned; pyALDIC-2D's FrameSchedule + cumulative transform replace them (see 01 §D.3 for the formal acc/inc contract).

VERIFIED ENGINE FACTS (do not re-derive; file:line in 01 Appendix). al_dic.core.pipeline.run_aldic accepts external mesh/U0 (skips FFT when both are given) and compute_strain=False; DICPara.admm_max_iter controls ADMM (0 = local-only). PipelineResult.result_disp holds CUMULATIVE displacements on the frame-1 mesh for any FrameSchedule. Incremental composition ground truth: U^k(X) = U^{k-1}(X) + u^k(X + U^{k-1}(X)) — increments interpolated at DEFORMED positions. Meshes are built once per reference frame and cached — never rebuild per frame (MATLAB's per-frame rebuild is a known hazard, 01 §D.3 rule 2).

ARCHITECTURE INVARIANTS. Correspondence strategies are pluggable components implementing the CorrespondenceStrategy protocol (02 §5); downstream modules (reconstruct/strain3d/viz3d/export) consume ONLY CorrespondenceSet and must not import concrete strategies — enforce with an architecture test. The 3D layer is mode- and strategy-agnostic: Displacement = P^k − P^1. Compute modules (calibration/sequence/matching/reconstruct/strain3d/export) are Qt-free; never import al_dic.utils.locale_format there. Frozen dataclasses; NaN = invalid, propagated end-to-end; float64 arrays. World frame = left camera (R=I, T=0); match on RAW images (no rectification); undistort point coordinates only before triangulation; epipolar geometry only for search seeding and QC.

ENGINEERING RULES. Talk to the user in Chinese; write all code/comments/commits/docs-in-code in English. Conventional commits; single author zachtong@utexas.edu; no Co-Authored-By trailers. Tests first (pytest), 80%+ coverage on new modules; files <= 800 lines. Every phase ends with a matplotlib PdfPages visual report under reports/ showing effect, performance, boundary conditions, and limitations (reports/ holds only PDFs, is gitignored, and is never referenced from README). The i18n contract applies from Phase 4 (GUI): 8 locales, tr() everywhere, pseudo-locale scan clean. At the phase gate: STOP, report metrics, update docs/architecture/00_INDEX.md changelog. Do not start the next phase.
```

---

## Phase 0 — 3D repo scaffold (does NOT touch the 2D repo)

> 2D 仓保持只读锁定，Phase 0 只在本仓工作区做，不需要任何跨仓写权限。
> （曾经的"Phase 0A 改 2D 5 条缝"已撤销——见决策 D11 与 01 §C.1；那些平台化项是
> 延迟的可选 backlog，只在将来真被绊到时于单独的 2D 会话里按需做。）

```text
Work in the pyALDIC-3D repository (this workspace). Do NOT modify ../pyALDIC or ../3D-Stereo-ALDIC (read-only references). Goal: scaffold the project; no stereo algorithms yet. Create a src-layout package (src/al_dic_3d/) with empty module skeletons per 01 §B.1 (project, calibration, sequence, matching, reconstruct, strain3d, export, viz3d, gui, i18n). Write pyproject.toml: distribution name "al-dic-3d", import package "al_dic_3d", console script "al-dic-3d"; dependencies numpy, scipy, opencv-python-headless, and al-dic pinned to the current released 2D version (al-dic==0.6.*), consumed read-only — during development use a local editable install of ../pyALDIC at that version. Optional extra [viz3d]: pyvista, pyvistaqt. Create docs/DEPENDS_ON_2D.md (initially empty table: "2D symbol | why we import it | public/internal") — every time later phases import something from al_dic, add a row; this is the coupling ledger the user checks before refactoring 2D. Set up pytest, CI, and pre-commit mirroring the 2D repo's configuration. `git init` and make the first commit. Verify and extend the already-present bootstrap CLAUDE.md if anything is missing (it should already carry the invariants, repo locations, and rules). Gate: CI green on the skeleton (import al_dic_3d works, `al-dic-3d --help` runs, empty test suite passes); brief reports/phase0_scaffold.pdf.
```

---

## Phase 1 — Headless stereo MVP: strategy interface + track_both (acc only)

```text
Goal: an end-to-end headless pipeline with the default strategy, validated against the MATLAB baseline. No GUI. Accumulative mode only. Build in dependency order.

1. al_dic_3d.calibration — CameraIntrinsics/StereoRig frozen dataclasses (N-camera-ready dict layout per 01 §E) plus importers for MatlabCV, MatchID, MMC, DICe, and OpenCorr (port the parsing math from the five cameraParamsFormatConvertFrom*.m), plus OpenCV YAML as the sixth format. Undistortion via cv2.undistortPoints; cross-check one dataset against MATLAB funUndistortPoints output.

2. docs/COORDINATES.md — THE single pixel-coordinate convention (MATLAB row-first vs numpy vs intrinsics (u,v)), plus a round-trip test: synthetic 3D points -> project through both cameras -> undistort -> triangulate -> recover within 1e-9. This lands BEFORE any matching code.

3. al_dic_3d.sequence — dual FrameProvider wrapper, dual mask streams, pairing validation (count / size / name-pattern).

4. al_dic_3d.matching — the CorrespondenceStrategy protocol + STRATEGY_REGISTRY + CorrespondenceConfig + CorrespondenceSet (02 §5.1-5.2, verbatim), the pure-primitive layer, and TrackBothStrategy. The primitive layer is match_points (a thin 3D-SIDE wrapper over al_dic's per-node/scattered local IC-GN, e.g. al_dic.solver.local_icgn — this keeps the 2D repo untouched; record the imported symbol in docs/DEPENDS_ON_2D.md), stereo_match_pair, temporal_track, and resample_to_points. Frame-1 cross-camera match: al_dic FFT integer search for the integer init, then sub-pixel local-only IC-GN via match_points at the quadtree mesh nodes on the [L1, R1] pair (no ADMM; tol=1e-3), mirroring StereoMatch_STAQ.m; support cfg.disparity_offset and cfg.epipolar_seed for large baselines; output a DisparityField. Temporal: run_aldic per camera (accumulative FrameSchedule; full pipeline, unchanged); resample the right camera's cumulative field onto the corr points (NaN-aware) -> CorrespondenceSet with quality/source filled.

5. al_dic_3d.reconstruct — batched DLT triangulation + per-frame reprojection errors (mirror stereoReconstruction_quadtree.m; left camera = world; NaN-safe). Reconstruction3D with D = P - P[0].

6. CLI: `al-dic-3d run config.toml` (console script; equivalent to `python -m al_dic_3d`) -> results .npz + .mat.

Gate: unit tests green; parity vs the MATLAB baseline .mat on the user's dataset (2D displacement fields within 1e-6 px where inputs are identical; 3D coordinates at micron scale; report any residual WITH analysis — never hide it); reports/phase1_report.pdf (disparity QC, reprojection error maps, 3D surface, parity tables).
```

## Phase 2 — Incremental mode + strategies S2/S3 + comparison harness

```text
Goal: complete the correspondence layer — incremental tracking, two more strategies, robustness, and the tri-strategy comparative study (02 §6).

1. Incremental mode for track_both via FrameSchedule.from_mode("incremental") per camera — the engine's cumulative transform does the composition; your work is the right-camera resampling path plus tests against the formal contract in 01 §D.3 (increments evaluated at deformed positions).

2. StereoEachFrameStrategy ("stereo_each_frame"): temporal left only; per-frame stereo match evaluated at tracked scattered points via the al_dic_3d.matching.match_points primitive (built in Phase 1), warm-started from the previous disparity; zero resampling. Fill source=STEREO_REFRESH rows.

3. RefDirectStrategy ("ref_direct"): temporal left (acc); direct L1->R_k matches chain-seeded from m^{k-1} (seed failure degrades convergence, never accuracy).

4. Robustness: 3D outlier removal (port the IDEA of funRemoveOutliers3D, not its code); QualityGate enforcement (znssd / reproj gates -> INVALID).

5. Synthetic stereo ground-truth generator: a known 3D surface + displacement field rendered through both camera models; deformed-texture warping MUST use fixed-point-iteration Lagrangian warp (established 2D practice); projectively consistent across views.

6. Comparison harness: run S1/S2/S3 on (a) MATLAB baseline data, (b) a Challenge sample, (c) synthetic truth. Metrics per 02 §6: RMSE, drift slope, noise floor, survival rate, reproj-vs-frame, runtime.

Gate: acc-vs-inc self-consistency on a small-deformation dataset (difference below the noise floor — quantify it); parity vs the MATLAB incremental baseline; reports/phase2_strategies.pdf with the tri-strategy comparison. Per decision D9 this PDF doubles as validation material for the SoftwareX Part-2 paper — keep the figures publication-grade.
```

## Phase 3 — 3D surface strain

```text
Goal: strain on the reconstructed surface, validated analytically. First write docs/strain3d_math.md deriving the method from PlaneFit3_Quadtree.m + computeStrain3D.m (local neighborhood plane fit -> tangent-frame displacement gradients -> exx, eyy, exy, e1, e2, max shear, von Mises, dwdx, dwdy), then implement al_dic_3d.strain3d against that document (reuse al_dic MLS/KDTree utilities; 3D smoothing analogous to funSmoothDisp_3D). Optional specimen-frame transform (GetRTMatrix equivalent) as a post-step on Reconstruction3D. Gate: analytic-field tests (rigid rotation -> zero strain; uniaxial stretch on plane/cylinder/sphere -> known strain within tolerance); parity vs MATLAB strainPerFrame on the baseline dataset; reports/phase3_strain.pdf including a VSG-size sensitivity study.
```

## Phase 4 — GUI alpha

```text
Goal: the application shell. Build your own MainWindow / AppState3D / controllers in al_dic_3d.gui, REUSING al_dic.gui widgets (image_list, frame_navigator, console_log, ROI toolbar, param panels) and the 2D canvas for per-camera fields. Workflow per 01 §F: a dual import page with pairing validation; a calibration import wizard with an epipolar sanity preview (errors die here); ROI on left frame 1 (reuse 2D ROI tools); correspondence settings with a strategy dropdown (default track_both) + per-strategy parameter sub-panels + a frame-1 stereo-match preview tab (disparity + ZNSSD QC before committing to a full run); staged progress + cancel via the 2D worker pattern; results as per-camera 2D tabs, a pyvista 3D tab (surface + scalar coloring + camera frusta + timeline) behind a lazy [viz3d] import, strain tabs, and a QC page (per-point quality/source maps, reproj-vs-frame drift monitor); and .aldic3d session save/resume (versioned schema, deduped npz envelope). Honor the i18n contract from day one (tr() everywhere, all 8 locales filled, pseudo-locale scan clean). Gate: full-workflow smoke test on the reference dataset; session round-trip test; pseudo-locale scan clean; reports/phase4_gui.pdf (annotated walkthrough).
```

## Phase 5 — Productization

```text
Goal: ship. Export suite (PLY/VTU, CSV/MAT, screenshots/animations reusing the 2D streaming-export pattern with resolution presets); i18n stats 100% across 8 locales; user manual (adapt the 2D LaTeX manual structure; compile to PDF); PyPI packaging (dist al-dic-3d) + Windows file association for .aldic3d; a validation sweep on Stereo-DIC Challenge 2.0 with published-envelope comparison; README + screenshots. Scholarly identity is INDEPENDENT of the 2D project (decision D9): mint pyALDIC-3D's OWN Zenodo record (its own concept DOI, distinct from the 2D DOI) at release, and assemble a skeleton for its OWN standalone SoftwareX article ("Part 2" — its own paper DOI, citing the 2D paper only as prior work; highlights, metadata table, illustrative examples drawn from the phase reports). Add the CITATION.cff and the Zenodo/DOI badge for the 3D record. Gate: release checklist mirroring pyALDIC-2D v0.6.0's; all CI green; manual compiled; Challenge report archived in reports/.
```
