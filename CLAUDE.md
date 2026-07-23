# pyALDIC-3D — Project Instructions

> This file auto-loads every session in this repo. It carries the Master Preamble
> so phase sessions need only paste the Phase Prompt from
> `docs/architecture/03_opus_phase_prompts.md`. Full baseline: `docs/architecture/`
> (read `00_INDEX.md` first). On any conflict, the architecture docs win — amend
> them before deviating.

## Language policy
- **对话语言**：始终用中文（Chinese）与用户交流。
- **代码/注释/commit/文档内文本**：一律用英文（English）。

## What this project is
pyALDIC-3D is an **independent application** (own repo, own project schema
`.aldic3d`, own `AppState3D`, own workflow controllers, own 3D visualization
layer) built **on top of** the pyALDIC-2D platform, which it consumes as a
**pinned, read-only library** (`al-dic==0.7.*`). It is NOT a "3D mode" inside the 2D app.
- Import package: `al_dic_3d` — PyPI dist: `al-dic-3d` — CLI: `al-dic-3d` — session ext: `.aldic3d`.
- Scholarly identity is INDEPENDENT of the 2D project (decision D9): its own Zenodo concept DOI and its own standalone SoftwareX article ("Part 2"), not shared with or attached to the 2D record. N-camera support: post-v1 (D10).

## Repository locations — verify at session start
The reference repos are how you consult the 2D engine and the algorithm. **If you
cannot find them, STOP and ask the user** — do not guess or reinvent.
- Workspace = this folder (`pyALDIC-3D`).
- Reference repos are **SIBLING directories** (same `MATLABCodes/` parent), **both READ-ONLY**:
  - `../pyALDIC` — 2D platform (import `al_dic`), consumed as a **pinned library** (`al-dic==0.7.*`). **Do NOT modify it** (decision D11); the settings.json denies writes. The deferred 2D-platform backlog in `01 §C.1` is NOT your task.
  - `../3D-Stereo-ALDIC` — MATLAB algorithm reference.
- Absolute paths on the author's machine (2026-07-02, orientation only):
  `C:\Users\13014\OneDrive - The University of Texas at Austin\Documents\MATLABCodes\{pyALDIC,3D-Stereo-ALDIC}`.
  The user has multiple machines; the `13014` username may differ — **trust the
  sibling relationship over the absolute prefix**. Run `ls ..` and confirm both
  siblings exist before relying on them.
- Fallback if a sibling is absent: clone `github.com/zachtong/pyALDIC` and
  `github.com/zachtong/3D-Stereo-ALDIC` into the sibling location.

## MATLAB usage
- Trust ONLY `gui/runPipelineCore.m` and the functions it calls (StereoMatch_STAQ,
  TemporalMatch_quadtree_ST1, organizeMatchedPairds_*, stereoReconstruction_quadtree,
  PlaneFit3_Quadtree, computeStrain3D, cameraParamsFormatConvertFrom*).
- Everything else (TemporalMatch_inc*, StereoMatch2, *_ST2, epipolar_ICGN1,
  *_task2*) is experimental **dead code — never port it**.
- **Never translate MATLAB literally**: extract the math, write idiomatic Python.
  The MATLAB RD/ResultDisp bookkeeping and mode branching are banned; the 2D
  engine's `FrameSchedule` + cumulative transform replace them (formal acc/inc
  contract in `01 §D.3`).

## Verified engine facts (do not re-derive; file:line in `01` Appendix)
- `al_dic.core.pipeline.run_aldic` accepts external `mesh`/`U0` (skips FFT when
  both given) and `compute_strain=False`; `DICPara.admm_max_iter` controls ADMM
  (0 = local-only).
- `PipelineResult.result_disp` holds **cumulative** displacements on the frame-1
  mesh for any `FrameSchedule`.
- Incremental composition ground truth: `U^k(X) = U^{k-1}(X) + u^k(X + U^{k-1}(X))`
  — increments interpolated at **deformed** positions.
- Meshes are built **once per reference frame and cached** — never rebuild per
  frame (MATLAB's per-frame rebuild is a known hazard).

## Architecture invariants
- Correspondence strategies are **pluggable** (`CorrespondenceStrategy` protocol,
  `02 §5`). Downstream (`reconstruct`/`strain3d`/`viz3d`/`export`) consumes ONLY
  `CorrespondenceSet` and must not import concrete strategies — enforce with an
  architecture test.
- The 3D layer is **mode- and strategy-agnostic**: `Displacement = P^k − P^1`.
- Compute modules (`calibration`/`sequence`/`matching`/`reconstruct`/`strain3d`/
  `export`) are **Qt-free**; never import `al_dic.utils.locale_format` there.
- Frozen dataclasses; `NaN` = invalid, propagated end-to-end; `float64` arrays.
- World frame = left camera (R=I, T=0); match on **RAW** images (no rectification);
  undistort point coordinates only before triangulation; epipolar geometry only
  for search seeding and QC.

## Engineering rules
- Commit author: single `zachtong@utexas.edu`; **no `Co-Authored-By` trailers**;
  conventional commits.
- Tests first (pytest), 80%+ coverage on new modules; files ≤ 800 lines.
- Every phase ends with a matplotlib `PdfPages` visual report under `reports/`
  (effect, performance, boundary conditions, limitations). `reports/` holds
  **only PDFs**, is **gitignored**, and is **never referenced from README**.
- **i18n contract applies from Phase 4 (GUI)**: 8 locales (en, zh_CN, zh_TW, ja,
  ko, de, fr, es), every user-facing string wrapped in `tr()`, pseudo-locale
  scan clean. Port the full contract from the 2D repo's CLAUDE.md at Phase 4.
- **Phase gate discipline**: at each gate, STOP, report metrics, update
  `docs/architecture/00_INDEX.md` changelog. Do **not** start the next phase.

## Dev setup, layout & commands (from Phase 0)
- **Install (development)**: satisfy the `al-dic==0.7.*` pin from the sibling
  source, then install this package editable:
  ```
  pip install -e ../pyALDIC        # 2D engine, editable (reports 0.7.0)
  pip install -e ".[dev]"          # this package + pytest/ruff/pre-commit
  pre-commit install               # optional: enable hooks
  ```
  In CI / for users, `al-dic==0.7.*` resolves from PyPI instead — the 2D repo is
  never modified either way.
- **Run / test / lint**: `al-dic-3d --help` · `python -m al_dic_3d` ·
  `pytest` · `ruff check . && ruff format .`.
- **Package map** (`src/al_dic_3d/`, one dir per `01 §B.1` module): `project`,
  `calibration`, `sequence`, `matching`, `reconstruct`, `strain3d`, `export` are
  **Qt-free** compute; `viz3d`, `gui`, `i18n` are the GUI/viz layer. `cli.py` is
  the `al-dic-3d` console-script entry; version lives once in `__init__.py`
  (`pyproject` reads it via hatchling dynamic-version).
- **Phase reports**: `python tools/phase0_report.py` regenerates
  `reports/phase0_scaffold.pdf` (gitignored). The generator self-verifies the
  gate (import / `--help` / pytest) so the PDF cannot claim green falsely.
- **Committed vs ignored**: `CLAUDE.md` and `.claude/settings.json` ARE versioned
  (they are this repo's operating contract + cross-repo read-only boundary);
  `reports/`, `.venv/`, caches, and `*.aldic3d` are gitignored.

## Cross-repo boundary note (permissions)
All phases run in THIS workspace and never modify the reference repos. The two
siblings are read-only: `.claude/settings.json` grants `additionalDirectories`
access to both (so you can READ 2D source and the MATLAB reference) but DENIES
Write/Edit to both, and denies `rm -rf`. If you ever conclude a 2D change is
truly unavoidable (see `01 §C.1`), STOP and tell the user — it would be done in
a separate 2D-repo session, never from here. Maintain `docs/DEPENDS_ON_2D.md`:
add a row whenever you import something from `al_dic`, so 2D refactors can check
what 3D depends on.
