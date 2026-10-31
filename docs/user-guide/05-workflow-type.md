# 5. Workflow type

The **WORKFLOW TYPE** section sets how each frame is compared against a
reference and which solver runs. As in the 2D app, make these choices early:
the tracking mode and reference-update policy determine which frames need a
Region of Interest.

## Tracking Mode

The **Tracking Mode** combo:

- **Accumulative** (default) — every frame is correlated directly against
  frame 1. Accurate for small, monotonic deformation. Fast, but the reference
  and current subsets drift apart under large cumulative motion.
- **Incremental** — each frame is correlated against a rolling reference frame,
  and the per-segment displacements are composed into cumulative output.
  Needed when accumulative tracking loses the points (large rotations, strain
  too large to correlate against frame 1). Slightly slower.

Config key: `[matching].reference_mode = "accumulative" | "incremental"`.

> The 3D displacement is `P^k − P^1` regardless of tracking mode — the choice
> affects only *how the correspondence is found*, not how displacement is
> defined. The 3D layer is mode-agnostic.

## Reference Update (incremental only)

A **Reference Update** sub-section appears **only when Tracking Mode =
Incremental**. It controls when the rolling reference refreshes:

- **Every Frame** (default) — the reference resets every frame, so each match
  only has to follow one frame's motion. Each reset, though, adds a small
  tracking error, and over a long sequence these errors add up (see *Which
  combination to pick?* below). Only frame 1 needs an ROI; each later reference
  frame reuses that outline unchanged, so if the specimen moves far beyond it,
  import per-frame masks (see [Region of interest](07-region-of-interest.md)).
- **Every N Frames** — the reference resets every *N* frames: fewer resets, so
  less accumulated error, as long as the images still correlate across *N*
  frames of motion. An **Update every** spinbox appears (range **2–100**,
  default **2**, suffix *frames*).
- **Custom Frames** — type a comma-separated list of 0-based reference-frame
  indices (placeholder *e.g. 5, 10, 20 (0-based frame indices)*). Frame 0 is
  always a reference.

Config keys: `[matching].ref_update_mode = "every_frame" | "every_n" | "custom"`,
`ref_update_n = 2`, `ref_update_frames = [5, 10, 20]`.

## Solver

The **Solver** combo:

- **AL-DIC** (default) — Augmented-Lagrangian DIC couples local IC-GN with a
  global FEM regularizer. Smoother fields, better strain accuracy, more robust
  in noisy/high-gradient regions. Roughly 3× slower than Local DIC.
- **Local DIC** — each subset is solved independently with IC-GN. Fast,
  preserves sharp local features, more sensitive to noise. Good for previews and
  high-quality images with small deformation.

Config key: `[matching].use_global_step = true` (AL-DIC) `| false` (Local DIC).

When AL-DIC is selected, the **ADVANCED** section's **AL-DIC Iterations** spinbox
applies (range **1–10**, default **3**): 1 is a single global pass (fastest), 3
is the default, 5+ gives diminishing returns. Config key
`[matching].admm_max_iter = 3`. (It is ignored by Local DIC.)

## Extra filters

An **Extra filters (correlation, outliers)** checkbox (off by default) enables
the robustness gates: a correlation (ZNSSD) gate on the correspondence, plus
reprojection and 3D-outlier filters on the reconstruction. Every point a gate
removes is *counted* and reported in the run log (see [Running](09-running.md))
— a gate never eats points silently. Leave it off to keep every tracked point.

These filters come on top of the checks every run makes. Those are set in the
**ADVANCED** section under **Result checks** (see below).

Config keys: `[quality].enabled = true`, `znssd_max = 0.5`,
`reproj_max_px = 2.0`, `outlier_threshold = 3.0`.

## Advanced: correspondence strategy

The **ADVANCED** section (collapsed by default) exposes the **Strategy** combo —
the pluggable rule for finding stereo + temporal correspondence:

- **Track Both** (`track_both`, default) — track both cameras through time and
  match stereo per frame. The general-purpose choice.
- **Stereo Each Frame** (`stereo_each_frame`) — an independent stereo match on
  every frame.
- **Reference Direct** (`ref_direct`) — match each frame directly against the
  reference.

Config key: `[matching].strategy = "track_both"`.

A **Parallel camera tracking** checkbox (off by default; `track_both` only)
tracks the two cameras concurrently — a modest speedup (the solver already uses
all cores, so the measured gain is only ~1.1×), at roughly double the peak
memory. Results are identical either way. Config key
`[matching].parallel_cameras = false`.

## Which combination to pick?

| Experiment | Tracking | Reference Update |
|------------|----------|------------------|
| Small or moderate, smoothly loaded deformation | Accumulative | — |
| Large cumulative strain | Accumulative first; Incremental if it loses points | Every N Frames |
| Large rigid rotation | Incremental | Every N Frames |
| Dynamic event / impact (large jumps between frames) | Incremental | Every Frame |
| Quasi-static with known load steps | Incremental | Custom |

**Start with Accumulative.** Each reference update adds a small tracking error
(about a hundredth of a pixel), and the errors add up over a sequence.
One example is a 136-frame tension test pulled to failure, with per-frame masks.
Incremental + Every Frame lost most points by the end. Every 10 Frames did
better. Accumulative kept 82 % of the points up to the fracture, and needed no
Starting Point for it.

Switch to Incremental when accumulative validity collapses (the log says so).
For long sequences, prefer **Every N Frames**. Keep **Every Frame** for short
sequences, or for motion too large to correlate across several frames.

Incremental needs an ROI only on frame 1. Each later reference frame reuses
that outline, so when the specimen moves far beyond it, add per-frame masks.
The analysis grid then covers every reference frame's mask, so material that
moves past the frame-1 outline keeps being tracked.

Next: [Initial guess & Starting Points →](06-initial-guess.md)
