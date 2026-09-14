# 6. Initial guess & Starting Points

The **INITIAL GUESS** section controls how the correlation gets its starting
displacement for frame 1 (the seed that IC-GN then refines per node). Three
mutually-exclusive radio buttons:

- **Starting Points** (`seed`) — **GUI default**. You click one or more points
  on the LEFT camera, frame 1; each point's neighbourhood is template-matched to
  seed the stereo offset and the first-pair motion.
- **FFT (cross-correlation)** (`fft`) — the engine's own path: an FFT integer
  search on frame 1 and at every reference switch, with warm-starting in
  between. (This is the *headless* CLI default.)
- **Previous frame** (`previous`) — frame 1 starts from zero; every later frame
  warm-starts from the previous converged field. Fastest in accumulative mode.

Config key: `[matching].init_guess = "seed" | "fft" | "previous"`.

> **What the temporal-search knobs actually control.** Because the 3D pipeline
> always drives the engine with an *external mesh*, the engine's per-frame FFT
> forcing and periodic FFT reset are skipped. The FFT integer search therefore
> runs only on **frame 1** and at **incremental reference switches**. Outside
> those points, every frame warm-starts from its predecessor. This is why the
> **Temporal Search** and **Auto-expand** controls in the sidebar grey out when
> the current mode means no FFT will run (see [Parameters](08-parameters.md)).
> *Starting Points* with no point placed runs as FFT, so the controls stay
> active in that case.

## When to use each

- **Previous frame** — smooth, slow, monotonic motion. Cheapest.
- **FFT** — moderate, unpredictable motion where a coarse whole-frame cross-
  correlation reliably finds the peak.
- **Starting Points** — pick this when FFT struggles:
  - **Large inter-frame displacement** (tens of pixels or more), where a single
    template match is cheaper and more reliable than a large FFT search.
  - **Multi-region ROIs / discontinuous fields** (cracks, shear bands), where an
    FFT peak-picker can select the wrong side of a discontinuity. Seeds respect
    mesh connectivity.

## Placing Starting Points

When **Starting Points** is selected, a seed panel appears with:

- **Place points…** — a checkable button; while active its label becomes
  *Placing… (click to exit)*. In placement mode, **left-click** the LEFT camera,
  frame 1 to add a point (the tool stays armed, so you can place several);
  **right-click** removes the nearest; **Esc** exits.
- **Auto-place** — places one point for you, at the spot deepest inside the
  drawn ROI (the centre of a rectangle). Draw the ROI first. It does nothing
  when points are already placed; press **Clear** first to replace them.
- **Clear** — remove all Starting Points.
- A **readiness status** line, which reflects per-region coverage:
  - *No point placed: the run finds the stereo offset from probe patches and
    seeds frame 1 by FFT…* (shown in amber, see below)
  - *N point(s) placed*
  - *N point(s) · X/Y regions ready* (all connected ROI regions seeded)
  - *N point(s) · X/Y regions seeded — rest auto-seeded at run* (partial)

## Running without a Starting Point

A run without any point is not blocked, and it no longer degrades silently:

- **Stereo (left to right, frame 1).** Five probe patches spread over the
  ROI are matched over the *whole* right image, exactly as a placed point is.
  Matches that disagree with the calibration's epipolar geometry are dropped.
  The remaining probes then act as Starting Points for the stereo match: the
  disparity is propagated from them node to node. On a 12 Mpx convergent test
  rig this raised the frame-1 stereo coverage from 75 % to 100 %, the same as
  one clicked point. The run log's stereo line names the probes it used.
- **Temporal (frame 1 to frame 2).** The engine's FFT search seeds the first
  frame pair, as with the *FFT* mode. Place a point, or press **Auto-place**,
  when the first-frame motion is larger than the **Temporal Search** radius.

The canvas card then reads *FFT (no starting point)*, and the right sidebar
shows *Ready to run* with an amber note that says the same.

Seeds are placed on the **LEFT camera, frame 1** only — the reference view.
Clicking elsewhere is refused with a warning telling you to switch to the LEFT /
frame-1 view. Markers render only there.

## Multi-seed behaviour and honest auto-fill

You can place **several** seeds (the multi-seed *Starting Points*, batch S). They
act as redundant anchors: each is bootstrapped independently, and the field is
propagated from them along the mesh. Unlike a hard gate, the run is **never
blocked** by unseeded regions — any connected ROI region left without a seed is
**auto-seeded at run time** (the readiness line says so). If a placed seed's
template match falls below the minimum correlation, it falls back to an FFT seed
for that piece rather than failing.

Practical advice: when you expect large accumulative deformation, place several
seeds in each region so a late-frame degradation of one still leaves a working
anchor.

## Sessions and seeds

Starting Points **are saved** in the `.aldic3d` session (both the legacy single
`seed_point` and the multi-seed `seed_points` list) and restored on open — see
[Sessions](13-session.md).

Next: [Region of interest →](07-region-of-interest.md)
