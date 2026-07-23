# DEPENDS_ON_2D — pyALDIC-3D → pyALDIC-2D (`al_dic`) coupling ledger

This file is the **single source of truth for exactly which parts of the 2D
package (`al_dic`) the 3D code imports.** pyALDIC-3D consumes `al-dic==0.7.*` as a
**pinned, read-only library** (decision D11); we never modify the 2D repo. This
ledger is what the 2D maintainer consults before a refactor: if a symbol is
listed here, a 2D-side rename/move is a breaking change for 3D.

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
v0.7.0 — unchanged from v0.6.0): `run_aldic`, `dicpara_default`,
`validate_dicpara`, `DICPara`, `DICMesh`, `FrameSchedule`, `FrameResult`,
`StrainResult`, `PipelineResult`.
Anything imported from a deeper path (e.g. `al_dic.solver.local_icgn`,
`al_dic.io...`, `al_dic.gui...`) is **internal** and belongs in the table with a
justification.

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
| `al_dic.solver.seed_propagation.Seed` / `.SeedSet` | seed + tuning record types passed to `propagate_from_seeds` (Batch S) | public (import via full path) |
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
| `al_dic.gui.widgets.double_spin.LocaleSafeDoubleSpinBox` | locale-safe Min/Max color-range spin boxes (right sidebar + strain window, G2.2) — dot-decimal input on comma-decimal OS locales | internal (GUI widget; import via full path) |

<!--
Row template (copy when adding a dependency):
| `al_dic.core.pipeline.run_aldic` | drive per-camera IC-GN+ADMM tracking | public |
| `al_dic.solver.local_icgn`       | scattered-point local IC-GN for strategy S2/S3 | internal |
-->
| `al_dic.mesh.refinement.build_refinement_policy` | runner quadtree mesh levers (inner/outer/brush + level), 2D-app parity |
| `al_dic.mesh.refinement.refine_mesh` | one-shot static frame-1 mesh refinement in `_build_reference_mesh` |
| `al_dic.mesh.refinement.RefinementContext` | context for the refinement criteria (mesh + frame-1 mask) |
| `al_dic.utils.interpolation.FieldInterpolator` | cached Delaunay scattered-field interpolator for the dense overlay renderer (`viz3d.fieldmap`, shared by the GUI canvas and the image exporter) | public (module-level; import via full path) |
| `al_dic.utils.interpolation.scatter_to_grid` | scattered node values -> regular pixel grid (smart output-step sizing) for the dense field overlay (`viz3d.fieldmap`) | public (module-level; import via full path) |
| `al_dic.utils.interpolation.FieldInterpolator.cross_crack_grid` | Batch C item 4: crack-aware dense-render cell blank (value-reduced cross-crack cell mask over the SAME Delaunay `scatter_to_grid` uses) in `viz3d.fieldmap.render_field_rgba`; `None` (bit-exact) when no triangle crosses | public (method of the already-imported FieldInterpolator) |
| `al_dic.utils.crack_barrier.segment_crosses_barrier` | Batch C item 4: per-cell crack-crossing edge test for the 3D surface (`viz3d.surface.filter_cells_cross_barrier`) — blank quads/tris bridging a crack | public (module-level, no underscore; import via full path) |
| `al_dic.mesh.mark_bridging.mark_bridging` | Batch C item 1: cut the EXTERNAL frame-1 mesh at thin crack barriers (`matching.crack_mesh`), so FEM/global-step elements never bridge a crack — the same test the engine applies to its internal mesh | public (module-level, no underscore; NOT re-exported from `al_dic.mesh.__init__`, import via full path) |

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
