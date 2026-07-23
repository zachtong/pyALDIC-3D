# 8. Parameters

The **PARAMETERS** section holds the subset- and mesh-related choices. Change any
of these and the pipeline recomputes on the next Run. The mesh preview
(Show Grid) updates live so you can see the effect before running.

## Subset Size

The IC-GN correlation window in pixels. Displayed as an **odd** number
(spinbox range **5–201**, step 2, default **33**); typing an even value snaps up
to the next odd. Internally the engine uses the even half-width (`winsize` =
display − 1, so 33 → 32). Config key: `[matching].winsize = 32`.

Larger subsets average over more pixels — better signal-to-noise but smoother,
lower spatial resolution. Rule of thumb: each subset should contain roughly 5–10
speckle particles.

| Value | When to use |
|-------|-------------|
| 21–31 | Fine, dense speckle; small strain; best spatial resolution. |
| 33 (default) | General speckle with ~3–5 px particles. |
| 51–81 | Noisy images, coarse speckle, low-contrast regions. |

## Subset Step

Node spacing in pixels, restricted to powers of two. The **Subset Step** combo
offers `2, 4, 8, 16, 32, 64, 128`, default **16**. Smaller step = more mesh
nodes = a denser field, but runtime grows quadratically. Config key:
`[matching].winstepsize = 16`.

> Total mesh nodes grow as `ROI_area / step²`. Halving the step roughly
> quadruples the node count and the runtime. Start coarse, settle the ROI and
> other parameters, then reduce the step for the final run.

## Stereo Search

Maximum stereo disparity (in pixels) the stereo match searches for between the
LEFT and RIGHT cameras. Spinbox range **4–400**, default **48 px**. Set it to
comfortably exceed the real disparity of your rig; too small and the stereo
match clips. Config key: `[matching].stereo_search = 48`.

## Temporal Search

Half-width (in pixels) of the FFT integer search for frame-to-frame motion.
Spinbox range **8–400**, default **20 px**. Config key:
`[matching].fft_search = 20`.

> **Honest scope of the temporal-search controls.** Because the 3D pipeline
> drives the engine with an external mesh, the FFT temporal search runs **only
> in the frame-1 FFT initialization and at incremental reference switches** —
> not on every frame. The sidebar reflects this: the Temporal Search spinbox
> (and the Auto-expand checkbox below) are **greyed out** whenever the current
> Initial Guess / Tracking Mode means no FFT will run. In *Previous frame* mode
> in an accumulative run, for example, no temporal FFT runs at all, so the knob
> is inert.

The spinbox tooltip also shows image-derived caps: the effective start is
clamped to about `min(H,W)/4 − subset`, and Auto-expand grows the region up to
about `min(H,W)/2`.

## Mesh refinement

Quadtree refinement subdivides mesh elements where you need higher resolution.
Two independent checkboxes (both off by default):

- **Refine at mask boundaries (holes)** — subdivide near holes inside the ROI
  (`refine_inner`). Config key `[matching].refine_inner`.
- **Refine at ROI edges** — subdivide near the outer ROI edge, where boundary
  effects matter (`refine_outer`). Config key `[matching].refine_outer`.

A **Refinement Level** spinbox (range **1–3**, default **1**) sets how deep the
subdivision goes: the minimum element size is `step / 2^level` (floored at 2 px).
Config key `[matching].refinement_level = 1`. The refine **brush** painted in the
[ROI toolbox](07-region-of-interest.md) also triggers refinement where you
painted, at the same level.

The refined reference mesh is built **once** (not per frame) and handed to the
correlation as the external mesh, so the preview and the run agree.

## Advanced: Auto-expand FFT search

In the collapsed **ADVANCED** section, **Auto-expand FFT search on clipped
peaks** (checked by default) retries the FFT with a larger search region when
the integer peak lands on the search boundary (a sign the real motion is
larger). Config key `[matching].fft_auto_expand = true`. Leave it on unless you
are debugging FFT behaviour. Like the Temporal Search knob, it is inert when no
FFT runs.

Next: [Running →](09-running.md)
