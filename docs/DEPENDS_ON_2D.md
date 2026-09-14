# DEPENDS_ON_2D — pyALDIC-3D → pyALDIC-2D (`al_dic`) coupling ledger

This file is the **single source of truth for exactly which parts of the 2D
package (`al_dic`) the 3D code imports, and which of its behaviours the 3D code
relies on.** pyALDIC-3D consumes `al-dic` as a **bounded, read-only library**
(decision D11; the range lives in `pyproject.toml`, currently `>=0.7.2,<0.9`, and
CI tests both of its ends); we never modify the 2D repo. This ledger is what the
2D maintainer consults before a refactor: if a symbol is listed here, a 2D-side
rename/move is a breaking change for 3D — and so is a change to any behaviour
listed under [Behavioural contracts](#behavioural-contracts).

## Rules

- **Every time** 3D code adds `from al_dic... import X` (or `import al_dic...`),
  add a row below in the same change. No silent coupling.
- Mark each symbol **public** (exported from `al_dic.__init__` / documented public
  API — stable) or **internal** (imported from a submodule that carries no
  stability guarantee — fragile; the risky rows a 2D refactor can break).
- Prefer **public** entry points. When only an internal will do, say why in the
  "why" column so the 2D-platformization backlog (01 §C.1) can weigh promoting it.
- When a dependency is removed, delete its row (keep the ledger current, not a
  changelog — git history holds the past).

## Known-public 2D surface (safe to depend on)

For reference, `al_dic`'s documented public API (from `al_dic/__init__.py`,
v0.7.0 — unchanged from v0.6.0 and through v0.8.0): `run_aldic`, `dicpara_default`,
`validate_dicpara`, `DICPara`, `DICMesh`, `FrameSchedule`, `FrameResult`,
`StrainResult`, `PipelineResult`.
Anything imported from a deeper path (e.g. `al_dic.solver.local_icgn`,
`al_dic.io...`, `al_dic.gui...`) is **internal** and belongs in the table with a
justification.

0.7.2 → 0.8.0 (checked 2026-09-13 against the `v0.8.0` tag): of every module
this ledger imports from, only two changed. `solver/numba_kernels.py` now
decorates its kernels with `cache=JIT_CACHE` from the new `al_dic._numba_compat`
(the JIT-cache fallback), and `gui/icons.py` gained an `app_icon_file()` helper
without changing any icon function 3D calls. `core/pipeline.py`,
`core/data_structures.py`, `io/image_ops.py` and the solver, mesh and utils
modules listed below are byte-identical.

## Ledger

| 2D symbol | why we import it | public/internal |
|---|---|---|
| `al_dic.DICMesh` | reference-mesh type in `CorrespondenceStrategy.compute` / `matching` (type-only, `TYPE_CHECKING`) | public |
| `al_dic.FrameSchedule` | acc/inc schedule fields on `CorrespondenceConfig` (type-only, `TYPE_CHECKING`) | public |
| `al_dic.core.data_structures.FrameSchedule` | RUNTIME import in `matching.temporal.build_frame_schedule` (Q5): `from_every_n` / `from_custom` build the incremental reference-update schedule handed to `DICPara.frame_schedule` (validated by `run_aldic` against `n_frames - 1`) | public |
| `al_dic.core.data_structures.DICPara.fft_auto_expand_search` / `.frame_schedule` | FIELDS set through `dicpara_default(**overrides)` in `matching.primitives.make_dicpara` (Q8 clipped-peak FFT expansion knob; Q5 explicit schedule) — a 2D rename breaks us | public (fields; no extra import) |
| `al_dic.core.config.dicpara_default` | build + validate a local-only `DICPara` in `matching.primitives.make_local_dicpara` | public |
| `al_dic.core.data_structures.DICPara` | parameter container consumed by the IC-GN primitive | public |
| `al_dic.core.data_structures.GridxyROIRange` | ROI (pixel bounds) for the `DICPara` / mesh build | public |
| `al_dic.io.image_ops.compute_image_gradient` | reference-image gradients (7-pt central diff) for IC-GN | public |
| `al_dic.io.image_ops.normalize_one` | byte-identical per-frame ROI normalization in `matching.temporal._EngineFrames` (streaming provider handed to `run_aldic`, replaces the engine's eager full-stack `ListFrameProvider` copy — perf P1.2) | public (module-level; import via full path) |
| `al_dic.io.image_ops.compute_clamped_roi` | clamp the normalization ROI exactly as the engine's `ListFrameProvider` does (`_EngineFrames.clamped_roi`, read back by `run_aldic` at `core/pipeline.py:784`, v0.7.0) | public (module-level; import via full path) |
| `al_dic.core.data_structures.FrameProvider` | STRUCTURAL protocol (`__len__`/`shape`/`clamped_roi`/`get_normalized`) that `matching.temporal._EngineFrames` implements for `run_aldic`'s `images` argument (duck-typed at `core/pipeline.py:770`, v0.7.0 — nothing imported; a 2D protocol change still breaks us) | public (protocol; not imported) |
| `al_dic.solver.local_icgn.local_icgn_precompute` | build the IC-GN reference context at scattered points (`match_points`) | public (import via full path; not in `solver.__all__`) |
| `al_dic.solver.local_icgn.local_icgn_solve_subset` | run 6-DOF local IC-GN at scattered points, returns `(U, F, conv_iter)` | public (import via full path; not in `solver.__all__`) |
| `al_dic.core.pipeline.run_aldic` | drive per-camera accumulative IC-GN tracking in `matching.temporal.temporal_track` (external mesh, `compute_strain=False`; `progress_fn` forwarded for the P3.6 parallel-track progress, `stop_fn` for cooperative cancel) | public |
| `al_dic.core.data_structures.DICMesh` | reference mesh type built by / passed to `temporal_track` and `build_grid_mesh` (runtime import) | public |
| `al_dic.core.data_structures.split_uv` | split interleaved `FrameResult.U_accum` into `(u, v)` node arrays | public (module-level; not in `al_dic.__all__`, import via `al_dic.core.data_structures`) |
| `al_dic.core.data_structures.PipelineResult` | `run_aldic` return; `temporal_track` reads `.dic_mesh` + `.result_disp` (attribute access, not imported) | public |
| `al_dic.core.data_structures.PipelineResult.stopped_early` / `.stopped_at_frame` / `.stop_reason` | partial-results-on-cancel bookkeeping (new in 0.7): `temporal_track` keeps the tracked prefix and surfaces these on `TemporalField` -> `CorrespondenceSet` -> run meta -> GUI log (R2). A user cancel now RETURNS a partial result (`core/pipeline.py:937-954,1886-1890`) instead of raising | public (attribute access, not imported) |
| `al_dic.core.data_structures.FrameResult` | per-frame element of `result_disp`; `temporal_track` reads `.U_accum` (cumulative) / `.U` (attribute access, not imported) | public |
| `al_dic.mesh.mesh_setup.mesh_setup` | build the uniform Q8 reference mesh from grid coords in `build_grid_mesh` | public (re-exported in `al_dic.mesh.__init__`) |
| `al_dic.solver.seed_prop_pipeline.build_grid_for_roi` | FFT-path `(x0, y0)` grid for the reference mesh (matches `run_aldic`'s internal grid) | public (module-level, no underscore) |
| `al_dic.solver.seed_propagation.propagate_from_seeds` | Batch S: F-aware BFS seed propagation reused verbatim to build a per-node `U0` field from sparse seeds (`matching.seed_propagation.build_seed_u0`) — the engine's own seed-prop path is skipped under an external mesh, so we drive this routine ourselves | public (import via full path; not in `solver.__all__`) |
| `al_dic.solver.seed_propagation.build_node_adjacency` | Q8 node adjacency graph for the propagation BFS (Batch S) | public (import via full path) |
| `al_dic.solver.seed_propagation.covered_region_ids` | which regions already have a seed, so auto-fill only touches unseeded regions (Batch S) | public (import via full path) |
| `al_dic.solver.seed_propagation.Seed` / `.SeedSet` | seed + tuning record types passed to `propagate_from_seeds` (Batch S); fix batch V also sets `Seed.user_hint_uv` (the centre of a seed's bootstrap NCC search) for the automatic stereo disparity prior (`matching.disparity_prior`, via `build_seed_u0(seed_hints=...)`) | public (import via full path) |
| `al_dic.solver.seed_propagation.SeedPropagationError` | typed failure -> `build_seed_u0` returns None -> FFT fallback (Batch S) | public (import via full path) |
| `al_dic.solver.seed_auto_place.auto_place_seeds_on_mesh` / `.AutoPlaceConfig` | 3-tier auto-place (quality/edge/topology) for regions the user left unseeded (Batch S auto-fill + rescue) | public (import via full path; not in `solver.__all__`) |
| `al_dic.utils.region_analysis.precompute_node_regions` | connected-component region map of the ROI mask (per-region seed validation + GUI readiness) (Batch S) | public (import via full path) |
| `al_dic.gui.widgets.console_log.ConsoleLog` | base class of `ConsoleLog3D` (right sidebar + strain window log): 3D subclasses it for the context menu / replayable entries (G3.1c/G3.5) — relies on its QTextEdit styling and `append_log` | internal (GUI widget; import via full path) |
| `al_dic.gui.theme.build_stylesheet` | shared pyALDIC dark-navy QSS applied in `create_app` (visual consistency with 2D) | internal (GUI theme; import via full path) |
| `al_dic.gui.theme.COLORS` | shared palette tokens used across the 3D GUI panels/widgets (incl. the ported ROI toolbar) | internal (GUI theme; import via full path) |
| `al_dic.gui.widgets.colorbar_overlay.ColorbarOverlay` | reused 2D colorbar overlay on the main canvas AND the strain window (`update_params`) | internal (GUI widget; import via full path) |
| `al_dic.gui.widgets.collapsible_section.CollapsibleSection` | reused 2D collapsible sections in the left sidebar and the strain window's right column | internal (GUI widget; import via full path) |
| `al_dic.gui.icons` | shared icon set (`icon_maximize`, `icon_zoom_in/out`, `icon_chevron_*`, `icon_play/pause`, `icon_download`, `icon_stop`) across toolbars/navigators incl. the strain window | internal (GUI icons; import via full path) |
| `al_dic.gui.window_chrome.enable_dark_title_bar` | dark OS title bar on `MainWindow3D`, `StrainWindow3D` and the About / Shortcuts / detection-zoom dialogs (one visual frame with the 2D app) | internal (GUI chrome; import via full path) |
| `al_dic.gui.widgets.double_spin.LocaleSafeDoubleSpinBox` | locale-safe spin boxes: base class of the export dialog's `RangeSpinBox` (`gui/dialogs/export_tabs/common.py`), which the right sidebar, the strain window and the export tabs use for Min/Max color ranges (fix batch V), plus the ADVANCED result-check thresholds and the frame-rate box — dot-decimal input on comma-decimal OS locales | internal (GUI widget; import via full path) |
| `al_dic.mesh.refinement.build_refinement_policy` | runner quadtree mesh levers (inner/outer/brush + level), 2D-app parity | public (re-exported in `al_dic.mesh.__init__`) |
| `al_dic.mesh.refinement.refine_mesh` | one-shot static frame-1 mesh refinement in `_build_reference_mesh` | public (re-exported in `al_dic.mesh.__init__`) |
| `al_dic.mesh.refinement.RefinementContext` | context for the refinement criteria (mesh + frame-1 mask) | public (re-exported in `al_dic.mesh.__init__`) |
| `al_dic.utils.interpolation.scatter_to_grid` | TEST-ONLY since fix batch V: the dense overlay renders through its own `viz3d.raster` (one Delaunay per camera, reused across frames), and `tests/test_view_perf_raster.py` pins its grid (`GridSpec`) against this function. `FieldInterpolator` and its `cross_crack_grid`, used before, are no longer imported | public (module-level; import via full path) |
| `al_dic.utils.crack_barrier.segment_crosses_barrier` | TEST-ONLY since fix batch V: `tests/test_view_perf_raster.py` and `tests/test_view_perf_surface.py` pin the vectorised crack test (`viz3d.raster.edges_cross_barrier`, used by the dense overlay and the 3D surface) against it | public (module-level, no underscore; import via full path) |
| `al_dic.strain.compute_strain._compute_derived_strains` | TEST-ONLY (fix batch V): `tests/test_batch_v_von_mises.py` pins the 3D derived strains to the 2D ones (von Mises bit-identical, e1 / e2 / max_shear to 1e-13). Note its argument order is `(exx, exy, eyy)` | internal (private) |
| `al_dic.mesh.mark_bridging.mark_bridging` | Batch C item 1: cut the EXTERNAL frame-1 mesh at thin crack barriers (`matching.crack_mesh`), so FEM/global-step elements never bridge a crack — the same test the engine applies to its internal mesh | public (module-level, no underscore; NOT re-exported from `al_dic.mesh.__init__`, import via full path) |

| `al_dic/i18n/compiled/al_dic_<locale>.qm` (file layout, located with `importlib.util.find_spec("al_dic.i18n")`) | fix batch V: `al_dic_3d.i18n.install_translators` installs the 2D catalog before the 3D one, so the reused 2D widgets (console log, collapsible sections) are translated | internal (package data layout) |
| `al_dic.gui.icons._HAS_SVG`, `.icon_app` + the `al_dic/gui/assets/icon/*` files | fix batch V `al-dic-3d self-test`: a frozen bundle that lost QtSvg or the icons still starts, so the self-test checks both | internal (`_HAS_SVG` is private) |
| `al_dic.gui.theme` package location (`arrows/*.svg` beside it) | fix batch V self-test: the spin-box arrow images the theme stylesheet points at must be bundled | internal (package data layout) |
| `al_dic.solver.numba_kernels.icgn_6dof_parallel` (its type) | fix batch V self-test: a numba `Dispatcher` proves the kernels are compiled, not the pure-Python fallback | internal |

<!--
Row template (copy when adding a dependency; keep new rows ABOVE this comment,
an HTML comment inside a Markdown table ends the table):
| `al_dic.core.pipeline.run_aldic` | drive per-camera IC-GN+ADMM tracking | public |
| `al_dic.solver.local_icgn`       | scattered-point local IC-GN for strategy S2/S3 | internal |
-->

## Behavioural contracts

Behaviours of the engine that 3D code relies on although no signature states
them. A 2D change to any of these breaks 3D as surely as a rename, without a
single import failing. Engine locations are al-dic **0.7.2** (identical in
0.8.0); 3D locations are named by function because line numbers move.

| Contract | Engine side | 3D side (what depends on it) |
|---|---|---|
| **Masks passed to the engine are binary `{0, 1}` `float64`.** The engine multiplies the reference image by the mask and then the image gradients by it again, so a `0/255` mask scales the IC-GN system by 255 and a fractional mask weights pixels — neither raises. | `core/pipeline.py:986-989` (`f_img_raw * f_mask`), `io/image_ops.py:168-170` (`df_dx *= img_ref_mask`) | every mask goes through `sequence.lazy.as_binary_mask` / `binary_mask_sequence` before `run_aldic` (`matching.temporal.temporal_track`) |
| **The warning text `All nodes are NaN` means "this field is zeros, not a result".** When no node survives, the IDW refill returns an all-zero field with only a `UserWarning` — which would reach 3D as a perfectly valid frozen camera. | `utils/outlier_detection.py:155` (`"All nodes are NaN, cannot interpolate. Returning zeros."`) | `temporal_track` records warnings around `run_aldic`, pins each one to the engine frame then in flight (from the `Frame k/N` progress text) and invalidates that frame; only when no deformed frame survives does it raise `ZERO_FILL_ERROR` (fix batch V). The parallel path's shared recorder hands the warning to the emitting thread's track (`matching.temporal.note_zero_fill`). Matching is by substring on both texts: rewording either silently disables the guard. |
| **`progress_fn` is not monotonic.** The frame loop ends at 0.99 and "Assembling results..." then reports 0.95. | `core/pipeline.py:933` (`_loop_end = 0.99`), `core/pipeline.py:1832` | `matching.temporal._Ratchet` clamps the fraction so the bar never moves backwards; messages pass through unchanged. |
| **`run_aldic` keeps a copy of the mesh for every completed frame.** `result_fe_mesh[frame]` holds fresh copies of `coordinates_fem`, `elements_fem` and `mark_coord_hole_edge` — about 78 B per node on a uniform mesh (16 B coordinates + ~62 B Q8 connectivity). With the per-frame `U`, `F` and cumulative `U_accum` it retains about **144 B per node per frame**, all resident until `run_aldic` returns. | `core/pipeline.py:1679-1684` | the memory pre-check (`memcheck.estimate_peak_bytes`, per-(frame, node) term) must budget it — for each camera tracked. |
| **Frames handed to the engine are copied before use.** A raw list is wrapped in `ListFrameProvider`, which materialises a normalised `float64` copy of the whole stack; a `FrameProvider` is used as is, and every frame it returns is `.copy()`-ed before the engine touches it. | `core/pipeline.py:770-773` (provider selection), `core/pipeline.py:987,1002` (`.copy()`) | 3D passes the streaming `matching.temporal._EngineFrames` provider (no full-stack copy), whose `get_normalized` returns arrays straight from an LRU cache without a defensive copy — safe only because of the `.copy()`. |
| **The FFT search half-width is clamped to `max(10, min(H, W) // 4 - winsize)`, with a `UserWarning`, even when a `U0` is passed.** | `core/pipeline.py` (search-region auto-scale notice) | the GUI forwards the warning to the log (`gui.run_worker`); the JIT warm-up (`gui.kernel_warmup`) sets an explicit search width so a warm-up raises no warning. |
| **The batch subset precompute (the largest single JIT compile) runs only from 50 nodes per frame.** | `solver/icgn_batch.py` (dispatch threshold) | the background JIT warm-up correlates a 192 px pair (100 nodes) so the first real run compiles nothing new (`gui.kernel_warmup`; a test checks the node count). |
| **`Seed.user_hint_uv` centres a seed's bootstrap NCC search.** | `solver/seed_propagation.py` (`Seed`, `_bootstrap_seed_fft`) | the automatic stereo disparity prior passes each probe's whole-image match as the hint (`matching.disparity_prior`, `matching.seed_propagation.build_seed_u0(seed_hints=...)`), so a disparity far outside the search box is still found. |

## 2D fixes to mirror

User-facing fixes in pyALDIC 0.7.x–0.8.0 (`../pyALDIC/CHANGELOG.md`) that concern
behaviour 3D shares — the same code path reused, or the same pattern
re-implemented — and so need a 3D counterpart. The 2D 0.7.1 / 0.7.2 fixes were
triaged in July (batch Z, 3D 1.0.0): the export-dialog close crash did not apply,
and the mask-persistence family was fixed.

| 2D version | Fix | 3D status |
|---|---|---|
| 0.8.0 | Export failures were reported as success: an error handler that itself raised, and a failed animation export shown as "Exported 0 animation(s)" in green. A failed export must raise and be shown as an error. | done (fix batch V: `StreamingAnimWriter` raises, zero files is shown as a failure, `ExportOutcome` reports partial problems) |
| 0.8.0 | `cv2.imwrite` / `cv2.imread` silently fail on non-ASCII paths (Windows): route image I/O through `cv2.imencode` / `cv2.imdecode`. | done (1.0.0, July: `pathsafe.py`, batch G3) |
| 0.8.0 | Frozen builds get a log file (`%LOCALAPPDATA%\<app>\logs\`) and a dialog that reports an unhandled error and names it — a windowed build has no console. | done (fix batch V: `gui/app.py`; plus a faulthandler crash log for native VTK crashes) |
| 0.8.0 | JIT compile of the solver kernels runs in the background at startup instead of freezing the first Run click (32.1 s → 0.1 s measured in 2D). | done (fix batch V: `gui/kernel_warmup.py`, through the 3D external-mesh path plus the strain kernels; first run 0.3 s after a 23 s cold warm-up) |
| 0.8.0 | The file association registered from a frozen build pointed at `-m al_dic`, which only an interpreter can run, and a stale association was reported as valid. | done (fix batch V: `gui/file_association.py`) |
| 0.8.0 | Save dialogs proposed a bare relative file name, which resolves against the working directory — for an app started from a shortcut, not the project folder. | done (fix batch V: `gui.persistence.suggested_save_path` for Save Mask, Save log and the manual calibration; the calibration dialog starts in the board images' folder) |
| 0.8.0 | `@njit(cache=True)` raises at import when no JIT-cache location is writable (a frozen build on a locked-down profile); probe once and fall back to `cache=False` (`al_dic._numba_compat`). The 2D kernels have it from 0.8.0; the 3D strain kernels need their own. | done (fix batch V: `al_dic_3d._numba_compat`) |

## Known engine caveats (read-only observations; re-audited 2026-07-22 for 0.7.0)

These al_dic behaviors shape how the 3D layer must defend itself; none can be
fixed here (D11). File:line refer to al-dic **0.7.0** (every row re-verified
against the v0.7.0 source during the R2 pin bump).

| Behavior | Where (0.7.0) | 3D-layer defense |
|---|---|---|
| Per-node failures are laundered into finite values: IC-GN bad points are IDW-refilled, subpb2's FEM field is finite everywhere, composition nearest-fills dropped nodes — `isfinite` validity is structurally all-True. (0.7's crack-aware composition NaNs only near-MASK-GAP points; away from mask gaps — and always with all-ones masks — the laundering is unchanged) | `local_icgn.py:239-252`, `subpb1_solver.py:152-163`, `interpolation.py:59-73,151-155` | `temporal_track` honesty gate: frame-0 -> k ZNSSD re-verification invalidates fake tracks |
| FFT auto-expand fires only on boundary-CLIPPED peaks; a decorrelated jump beyond the radius yields an in-bounds noise peak and never expands | `pipeline.py:1105-1151`, `integer_search.py:257-276` | `fft_search` knob (RunConfig/GUI) must cover the largest per-frame motion |
| Accumulative sibling warm-start seeds frame k from frame k-1's solution and skips FFT; on decorrelation IC-GN "converges" at the seed (frozen field) | `pipeline.py:1297-1372` (skip via `need_fft`, `pipeline.py:1058`) | honesty gate flags the frozen frame; use incremental mode for decorrelating sequences |
| With an external mesh, `base_mesh` is never captured (only when the mesh is FFT-built), so per-ref mask re-trims erode elements monotonically | `pipeline.py:1157-1207` | static frame-1 mesh + mesh-drift hard error in `track_both` |
| Deformed-frame mask `g_mask` is loaded but never used; ref mask applies at fixed pixel coords (no material warping) | `pipeline.py:995` (load), `pipeline.py:986,1004` (ref mask) | masks are per-frame and indexed by the moving reference (correct for inc); gate catches residual contamination |
| Mid-chain composition break assigns a PARTIAL cumulative field; `U_accum=None` only when composing was skipped | `pipeline.py:573-576` (break), `pipeline.py:670-676` (partial assign), `pipeline.py:551-552` (skip) | `temporal_track` hard-errors on `U_accum is None` in incremental mode |
| NEW in 0.7 — composition is ALWAYS crack-aware in `run_aldic` (`masks` + `crack_radius = 2*winstepsize` are always passed): within 2 winsteps of a masked-OUT pixel, composed increments are re-evaluated inside crack-cut elements, majority-masked points become permanently NaN, and frame-0-masked nodes near a gap are born dead. All-ones masks (the 3D default) keep the byte-identical legacy path; user ROI masks can now yield honest NaN near the mask boundary where 0.6 laundered finite values | `pipeline.py:1719-1728` (call), `pipeline.py:487-676` (override) | aligned with the 3D `NaN` = invalid contract; MATLAB-parity gates P1/P2 re-run on 0.7 to bound drift |
| NEW in 0.7 — `DICPara.init_guess_mode` default flipped `"auto"` -> `"fft"`; `"auto"` now maps to `"previous"`. A no-op for the 3D layer: the per-frame FFT force is gated on `not mesh_is_external` and every `temporal_track` run passes an external mesh | `data_structures.py:305-307` (default), `pipeline.py:833-840` (mapping), `pipeline.py:1026-1035` (external-mesh skip) | none needed (verified no-op); `matching/seed.py` docstring documents the external-mesh mapping |
| NEW in 0.7 — a user cancel (`stop_fn` True) RETURNS a partial `PipelineResult` (`stopped_early` / `stopped_at_frame` / `stop_reason` set, `result_disp` = contiguous prefix of completed frames) instead of raising. NOTE: `run_aldic`'s docstring (`pipeline.py:745-748`) still stale-claims it raises on `stop_fn` — trust the implementation | `pipeline.py:937-954` (cancel), `pipeline.py:1834-1890` (assembly/return) | `temporal_track` keeps the tracked prefix (frames after it NaN) and surfaces the stop through `CorrespondenceSet` -> run meta -> GUI/CLI log (R2) |
