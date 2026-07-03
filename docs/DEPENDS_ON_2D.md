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

<!--
Row template (copy when adding a dependency):
| `al_dic.core.pipeline.run_aldic` | drive per-camera IC-GN+ADMM tracking | public |
| `al_dic.solver.local_icgn`       | scattered-point local IC-GN for strategy S2/S3 | internal |
-->
