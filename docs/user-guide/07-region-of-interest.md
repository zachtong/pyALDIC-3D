# 7. Region of interest

The Region of Interest (ROI) is the area of the specimen the DIC actually
solves. You draw it **on the LEFT camera, frame 1** — all later frames and the
right camera follow from it. The section hint says exactly that:
*Draw on the LEFT camera, frame 1 — all later frames and the right camera follow
from it.*

## The ROI toolbox

The **REGION OF INTEREST** section holds a compact toolbar. The first row has
three drop-down buttons whose menus pop up above the button:

### Add ▴ and Cut ▴

Both open the same shape menu; **+ Add** paints the shape into the ROI, **✂ Cut**
removes it:

- **⬟ Polygon** — click vertices, close the loop.
- **□ Rectangle** — drag a box.
- **○ Circle** — drag from centre.
- **◌ Circle (3-point)** — click three points on the rim.

The shape tools are one-shot: after you finish one shape the tool reverts to
select, so you can immediately pan/zoom.

### + Refine ▴ (refinement brush)

The refine menu paints a "refine-here" brush that densifies the mesh where you
paint (used together with the mesh-refinement checkboxes in
[Parameters](08-parameters.md)):

- **Radius** — brush size spinbox, range **2–500 px**, default **16 px**.
- **✎ Paint** / **✖ Erase** — add or remove refine-here area.
- **Clear Brush** — remove all brushed area.

### Import / Save / Invert / Clear

- **Import** — load a mask image as the ROI (filter
  `*.png *.bmp *.tif *.tiff *.jpg *.jpeg`).
- **Save** — write the current mask to a PNG (*Save Mask*, default
  `roi_mask.png`).
- **Invert** — swap inside/outside.
- **Clear** — remove the ROI.

A **bbox readout** below the toolbar shows the ROI bounding box:
*bbox: not set*, or *bbox: xmin–xmax, ymin–ymax px* once drawn.

You can also right-click the canvas for **Clear ROI** and **Clear seed points**.

## Mesh preview and subset hover

The canvas toolbar has two view toggles that make the ROI concrete:

- **Show Grid** (on by default) — overlays the computational mesh on the
  reference view (LEFT camera, frame 1). It is rebuilt live from the current
  Subset Step and refinement settings by the *same* `build_reference_mesh` the
  run uses — **what you preview is the run's mesh**. The preview is debounced so
  it does not stutter while you edit parameters.
- **Show Subset** (off by default; needs Show Grid) — hovering a mesh node draws
  its correlation subset window (the Subset Size box), so you can judge whether a
  subset spans enough speckle texture. The hover snaps to the nearest node.

You can also set the mesh overlay's line **color** and **width** (1–8 px) from
the toolbar's appearance control — cosmetic only.

## Thin barriers = cracks (crack-aware runs)

There is **no separate "crack tool."** Instead, a **thin unmasked barrier** you
leave in the ROI *is* the crack. If your drawn LEFT mask contains a thin gap
(barrier) that separates two regions, the run detects it and becomes
**crack-aware** automatically:

- The frame-1 reference mesh is **cut** at the barrier, so FEM / global-step
  elements never bridge the crack.
- Surface and field-overlay cells that would span the crack are dropped, so the
  two faces render independently instead of being smeared into a smooth ramp.
- Strain becomes crack-aware too: the plane-fit neighbour search excludes points
  whose line of sight crosses the barrier, and the crack faces are folded into
  the edge trim (see [Strain post-processing](11-strain-processing.md)).

When a run is crack-aware, the strain window shows a read-only indicator
*Crack-aware: ROI barrier honored (mesh, strain, render)*, and the result's
metadata records `crack_aware = true`. A crack-free run is byte-identical to one
computed without any of this machinery — the crack path only activates when a
thin barrier is actually present.

To make a run crack-aware, simply **draw (or cut) your ROI so a thin unmasked
line follows the crack**, leaving material on both sides. The barrier lives on
the LEFT camera reference mask only.

Next: [Parameters →](08-parameters.md)
