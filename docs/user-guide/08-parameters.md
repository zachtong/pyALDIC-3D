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

Half-width (in pixels) of the per-node search window of the frame-1 stereo
match (LEFT to RIGHT). Spinbox range **4–400**, default **48 px**. Config key:
`[matching].stereo_search = 48`.

It is **not** the largest disparity the match can find. The window is centred
where the disparity is expected: at the match of a placed Starting Point, or,
without one, at the disparity measured from probe patches over the whole right
image (see [Initial guess](06-initial-guess.md)). The window only has to cover
how much the disparity varies around that centre; widen it for strongly curved
or tilted specimens.

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
> is inert. *Starting Points* with no point placed does run the FFT, so the
> controls stay active then.

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

## Advanced: Result checks

Every run checks its results before it ships them. **ADVANCED > Result checks**
sets how strict the checks are (0 turns a check off; each spin box then reads
*off*):

- **Tracking check** (default **1.0**; config `[matching].temporal_gate_znssd`)
  — every tracked point must still correlate with its frame-1 subset, compared
  with the subset deformed by the local strain. The value is a correlation
  mismatch (ZNSSD: 0 = identical, 1.0 = correlation 0.5, 4 = worst). Points
  below 60 % of the value always pass; points up to the value pass only when
  their neighbours move consistently with them; the rest are dropped. Raise it
  (for example to 1.5) for specimens strained close to failure, where genuine
  points correlate poorly; lower it for stricter results.
- **Stereo check** (default **0.6**, correlation 0.7; config
  `[matching].stereo_znssd_max`) — the largest correlation mismatch a frame-1
  left/right match may have.
- **Epipolar limit** (default **2 px**; config
  `[matching].stereo_epipolar_max_px`) — how far a left/right match may lie from
  the line the calibration predicts. Raise it only for a poor calibration.

Every point a check removes is counted in the run log.

Next: [Running →](09-running.md)
