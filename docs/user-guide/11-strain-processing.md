# 11. Strain post-processing

Strain is computed in a **separate top-level window**, *Strain Post-Processing*
(`assets/strain_window.png`), with its own parameter panel and its own
visualization state, independent of the main window. It opens **automatically
the first time** a run finishes; after that, open it on demand with the
**Open Strain Window** button in the right sidebar. Without results it refuses
and logs *run an analysis first — no results to post-process*.

Surface strain is fitted on the reconstructed 3D point cloud: a local
tangent-plane fit of the displacement gradients, reduced to a strain tensor and
its invariants. It is always **total-Lagrangian**, computed on the frame-0
reference surface.

## RIGID MOTION

A specimen often moves and tilts as a whole between frames — a heated sample
drifts in its chamber, a fixture settles. That rigid-body motion can be much
larger than the deformation you are after: on a package warpage test the
specimen moved ~260 µm and tilted 2.9 mrad while it warped by ~7 µm. The
**RIGID MOTION** section removes it.

- **Remove**: **Off** (default), **Translation only** (subtracts the mean
  displacement of the fitted points) or **Translation + rotation** (also the
  best-fit rotation, Kabsch least squares). Each frame is fitted against
  frame 1, in incremental and accumulative runs alike.
- **Fit region**: by default **all valid points**. Draw a region with
  **+ Rectangle** / **+ Polygon** and remove parts of it with **− Rectangle** /
  **− Polygon** — for example to fit only on a part that you know does not
  deform. The region is drawn on frame 1 and shown in **amber** (the analysis
  ROI stays blue); **Show fit region** hides it, **Use all valid points**
  clears it. Translation needs at least 1 point in the region, translation +
  rotation at least 3 not in a line; a region that cannot support the mode is
  refused with the reason, and nothing changes.
- **What changes**: the removal applies **everywhere** — the main window's
  field maps and 3D view, this window, the strain computed afterwards and every
  export. Every colorbar and exported figure says so with the suffix
  *· rigid motion removed (mode)*. Switching the mode keeps the frame, the
  camera and the 3-point specimen frame, so you can compare on and off. **Off**
  restores the measured data: it is never overwritten.
- **Per-frame table**: for every frame, the shift of the fitted points'
  centroid ΔX/ΔY/ΔZ (µm), the rotation θ (mrad), the RMS residual of the fit
  (µm) and the points used N. A frame that cannot be fitted shows dashes and is
  left out of the corrected result (it reads as invalid, never as uncorrected).
- **Strain**: Green-Lagrange strain does not change when rigid motion is
  removed, but the slopes ∂w/∂x, ∂w/∂y and the other strain types do. After a
  change, *⚠ Rigid-motion setting changed — click Compute Strain* appears until
  you recompute; the hint survives saving and reopening the project.
- **Saved with the project**: the mode and the drawn region are part of the
  project; the project file keeps the measured data and re-applies the removal
  when it opens. A new analysis run applies the current setting too.

The plain least-squares fit is pulled by points that are wrong (the RMS column
shows it) and by real deformation inside the region — when the whole surface
bends, fit on its stiffest part. Across a crack the two sides may move
differently: draw the region on one side.

From the command line, add `[rigid_motion]` to the config:

```toml
[rigid_motion]
mode = "rigid"                    # "off" | "translation" | "rigid" (translation + rotation)
region_mask = "fit_region.png"    # optional: fit only inside this mask (left frame 1)
```

## STRAIN PARAMETERS

### Strain window (VSG size)

The virtual strain gauge (VSG) is a square window over the mesh. The
**Strain window** spinbox is in pixels, **odd only** (even inputs snap up),
default **65 px**. That default corresponds to a gauge of `strain_size = 5` grid
steps at the default 16 px node spacing (`(5−1)·16 + 1 = 65`).

A live **Strain window ≈ N×N nodes** readout below the control translates the
pixel window into the number of mesh nodes the plane fit spans on each axis (and,
when physical spacing is known, an approximate mm size). Larger = more smoothing.
An inline warning appears if the radius drops below the node spacing (the fit
needs at least a 3×3 node gauge).

### Strain type

The **Strain type** combo picks the finite-strain measure. All three share the
same gradient fit and tangent frame — only the reduction differs:

| Option | Formula | Notes |
|--------|---------|-------|
| **Green-Lagrange (default)** | `E = ½(FᵀF − I)` | Reference configuration. **Exactly zero under rigid rotation** — use it whenever rotation exceeds ~2°. |
| **Infinitesimal** | `e = ½(G + Gᵀ)` | Small deformation only; reports `cos θ − 1` as false strain under rotation. |
| **Almansi (Eulerian, true tensor)** | `e = ½(I − F⁻ᵀF⁻¹)` | Current (deformed) configuration; the *exact* tensor (a singular `F` yields `NaN`). |

Codes: `green_lagrange`, `infinitesimal`, `almansi`.

### Coordinate system

The **Coordinate system** combo sets the frame the strain tensor is reported in:

- **Surface tangent plane** (`local`, default) — a per-node fitted tangent plane;
  the natural surface frame.
- **Left camera frame** (`camera0`) — the fixed world/left-camera frame.
- **Custom (3 points)** (`specific`) — a fixed specimen frame you define with the
  **Pick 3 points…** button (enabled only in this mode). Picking jumps to the
  reference frame and prompts *Click Origin, then +X, then +Y on the image*; each
  click **snaps to the nearest valid reference-mesh node**. The three picks build
  the specimen frame (markers **O** / **+X** / **+Y**), after which Compute is
  enabled.

### Trim low-confidence edges

Near the ROI boundary (or a hole / crack edge) the VSG window crosses the
boundary and the one-sided plane fit becomes biased. The **Trim low-confidence
edges** control (range 0.00–1.00, default **0.70**) hides those edge nodes: a
node is flagged when its distance to the boundary is below `alpha × VSG-radius`.
`0.00` keeps every node; `1.00` is strictest. A live **Trimmed: N nodes (M%)**
readout shows the effect.

Trimming does **not** blank the strain arrays. Values stay dense; a per-frame
boolean `strain_valid` (edge-trim ∪ crack-trim) marks what to show — the
reference view applies frame-0 validity, the deformed view frame-*k* validity.
Exports honour the same mask (see [Exporting](12-export.md)).

### Strain field smoothing

An optional Gaussian smoothing of the displacement field before the plane fit
(so every strain component is computed from the same smoothed field):
**Off** (default), **Light (σ = 0.5 × step)**, **Medium (σ = 1 × step)**, or
**Strong (σ = 2 × step) ⚠**.

### Crack-aware strain

When the run's ROI carried a thin crack barrier, strain is crack-aware
automatically: the VSG neighbour search **excludes** any point whose reference
line of sight crosses the barrier, so the two crack faces never mix in one plane
fit, and the crack faces are folded into the edge trim. A read-only indicator
*Crack-aware: ROI barrier honored (mesh, strain, render)* confirms it. See
[Region of interest](07-region-of-interest.md).

## Compute and view

Click the green **Compute Strain** button to (re)compute with the current
settings; it runs in the background with a *Computing strain… {pct}%* progress
label and a **Cancel** button. If you change a parameter after computing, a
*⚠ Params changed — click Compute Strain* hint appears.

### FIELD

Exclusive toggle buttons in three groups select what is shown (default **εxx**):

- **Displacement** — `U`, `V`, `W` (world / left-camera axes) and `|D|`, in the
  display unit chosen in the main window. These are available as soon as a run
  exists, before any strain is computed, so the effect of rigid-motion removal
  can be checked first.
- **Slope** — `∂w/∂x`, `∂w/∂y` (`dwdx, dwdy`): the out-of-plane slopes of the
  strain fit, shown in **mrad** (= µm/mm). They tilt with the specimen, so they
  are meaningful once rigid motion is removed.
- **Strain** — `εxx`, `εyy`, `εxy` (`exx, eyy, exy`); the principal strains
  `ε₁`, `ε₂` (`e1, e2`); `γ max` (`max_shear`); and `von Mises` (`von_mises`),
  the plane equivalent strain `sqrt(εxx² + εyy² − εxx·εyy + 3·εxy²)` used by
  pyALDIC (2D) as well.

Slope and strain buttons are disabled until strain is computed.

### VISUALIZATION

Independent of the main window: **Show on deformed frame** (checked by default),
**Colormap** (`turbo` default, same seven maps), **Auto range** (checked;
2–98 percentile), **Min** / **Max**, and **Opacity** (default 85). The strain
window has its own frame navigator and its own private frame index.

The **Export Results** button here opens the same export dialog as the main
window ([Exporting](12-export.md)).

Next: [Sessions →](13-session.md)
