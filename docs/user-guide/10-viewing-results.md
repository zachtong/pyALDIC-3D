# 10. Viewing results

After a run the right sidebar's viewing controls come alive and the canvas shows
a colour-mapped overlay of the selected field. The 3D pipeline reports **3D**
displacement, so the field menu carries `W` (out-of-plane) alongside `U` and `V`.

## FIELD section

Under **DISPLACEMENT**, a 2-column grid of exclusive toggle buttons selects the
field:

| Button | Field | Meaning |
|--------|-------|---------|
| **U** | `U` | world-frame displacement along X, in mm |
| **V** | `V` | world-frame displacement along Y, in mm |
| **W** | `W` | world-frame displacement along Z (out-of-plane), in mm |
| **\|D\|** | `mag` | magnitude `sqrt(U² + V² + W²)`, in mm |
| **Vel** | `velocity` | inter-frame speed `\|D(k) − D(k−1)\| × frame rate` |

**Vel** is disabled until results exist. (The strain fields — εxx, εyy, εxy, ε₁,
ε₂, γ max, von Mises — live in the separate
[Strain window](11-strain-processing.md), not here.)

Below the toggles:

- **Show on deformed frame** (checked by default) — plot the field at the
  displaced node positions on each frame's own image; uncheck to plot on the
  undeformed reference geometry.
- **Camera** — **Left** (default) or **Right**. *Left* is the reference view
  (ROI, seeds, and mesh live here). *Right* warps the field onto the right
  camera's images as a cross-check that the stereo match is sound.

The overlay is a **dense, continuous field** interpolated across the mesh — not
just coloured nodes.

## VISUALIZATION section

- **Colormap** — `turbo` (default), `viridis`, `jet`, `coolwarm`, `plasma`,
  `inferno`, `RdBu_r`. Diverging maps (`coolwarm`, `RdBu_r`) suit signed fields
  that cross zero.
- **Auto range** (checked by default) — rescales the colour range to each
  frame's data using the 2–98 percentile of visible values (excludes extreme
  outliers). Uncheck to type fixed **Min** / **Max** bounds (kept for every
  frame — useful for reporting a common scale). The Min/Max spinboxes are
  disabled while Auto range is on and seed from the live percentile range when
  you turn it off.
- **Opacity** — slider 0–100, blends the field overlay against the background
  image.

## UNITS section (collapsible)

- **Display unit** — `µm`, `mm` (default), `cm`, `m`. This converts the
  displacement / velocity **display** values (colorbar, 3D scalar bar, and the
  bounds auto-range writes back). The underlying data, session, and exports stay
  **mm** on the wire. Strain is dimensionless and never converted.
- **Frame rate** — feeds only the *Vel* (velocity) field, converting mm/frame to
  mm/s.

## The 3D View

The canvas toolbar has a **3D View** checkbox (requires the `[viz3d]` extra and
existing results). Checking it switches the canvas from the 2D image view to the
**reconstructed 3D surface**, coloured by the selected field and shown with the
two **camera frusta** so you can see the rig geometry. Uncheck it to return to
the 2D view. Without results it shows *3D view — run an analysis to see the
reconstructed surface.*

## Frame navigator

The bottom bar navigates frames: previous / play-pause / next buttons, a
**speed** combo (`1, 2, 5, 10, 30 fps`, default **2 fps**), a bold
**FRAME k/N** label (1-based), and a timeline slider. Playback loops and needs at
least two frames.

## Console log

The **LOG** section (see [Running](09-running.md)) stays available for reviewing
warnings after the run. If a field looks wrong, check the log — per-frame
validity and gate counts are recorded there.

Next: [Strain post-processing →](11-strain-processing.md)
