# DEPENDS_ON_2D — pyALDIC-3D → pyALDIC-2D (`al_dic`) coupling ledger

This file is the **single source of truth for exactly which parts of the 2D
package (`al_dic`) the 3D code imports.** pyALDIC-3D consumes `al-dic==0.6.*` as a
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
v0.6.0): `run_aldic`, `dicpara_default`, `validate_dicpara`, `DICPara`,
`DICMesh`, `FrameSchedule`, `FrameResult`, `StrainResult`, `PipelineResult`.
Anything imported from a deeper path (e.g. `al_dic.solver.local_icgn`,
`al_dic.io...`, `al_dic.gui...`) is **internal** and belongs in the table with a
justification.

## Ledger

| 2D symbol | why we import it | public/internal |
|---|---|---|
| `al_dic.DICMesh` | reference-mesh type in `CorrespondenceStrategy.compute` / `matching` (type-only, `TYPE_CHECKING`) | public |
| `al_dic.FrameSchedule` | acc/inc schedule fields on `CorrespondenceConfig` (type-only, `TYPE_CHECKING`) | public |
| `al_dic.core.config.dicpara_default` | build + validate a local-only `DICPara` in `matching.primitives.make_local_dicpara` | public |
| `al_dic.core.data_structures.DICPara` | parameter container consumed by the IC-GN primitive | public |
| `al_dic.core.data_structures.GridxyROIRange` | ROI (pixel bounds) for the `DICPara` / mesh build | public |
| `al_dic.io.image_ops.compute_image_gradient` | reference-image gradients (7-pt central diff) for IC-GN | public |
| `al_dic.solver.local_icgn.local_icgn_precompute` | build the IC-GN reference context at scattered points (`match_points`) | public (import via full path; not in `solver.__all__`) |
| `al_dic.solver.local_icgn.local_icgn_solve_subset` | run 6-DOF local IC-GN at scattered points, returns `(U, F, conv_iter)` | public (import via full path; not in `solver.__all__`) |
| `al_dic.core.pipeline.run_aldic` | drive per-camera accumulative IC-GN tracking in `matching.temporal.temporal_track` (external mesh, `compute_strain=False`) | public |
| `al_dic.core.data_structures.DICMesh` | reference mesh type built by / passed to `temporal_track` and `build_grid_mesh` (runtime import) | public |
| `al_dic.core.data_structures.split_uv` | split interleaved `FrameResult.U_accum` into `(u, v)` node arrays | public (module-level; not in `al_dic.__all__`, import via `al_dic.core.data_structures`) |
| `al_dic.core.data_structures.PipelineResult` | `run_aldic` return; `temporal_track` reads `.dic_mesh` + `.result_disp` (attribute access, not imported) | public |
| `al_dic.core.data_structures.FrameResult` | per-frame element of `result_disp`; `temporal_track` reads `.U_accum` (cumulative) / `.U` (attribute access, not imported) | public |
| `al_dic.mesh.mesh_setup.mesh_setup` | build the uniform Q8 reference mesh from grid coords in `build_grid_mesh` | public (re-exported in `al_dic.mesh.__init__`) |
| `al_dic.solver.seed_prop_pipeline.build_grid_for_roi` | FFT-path `(x0, y0)` grid for the reference mesh (matches `run_aldic`'s internal grid) | public (module-level, no underscore) |

<!--
Row template (copy when adding a dependency):
| `al_dic.core.pipeline.run_aldic` | drive per-camera IC-GN+ADMM tracking | public |
| `al_dic.solver.local_icgn`       | scattered-point local IC-GN for strategy S2/S3 | internal |
-->
