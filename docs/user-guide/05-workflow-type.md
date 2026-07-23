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
  Required for large rotations or large cumulative strain. Slightly slower.

Config key: `[matching].reference_mode = "accumulative" | "incremental"`.

> The 3D displacement is `P^k − P^1` regardless of tracking mode — the choice
> affects only *how the correspondence is found*, not how displacement is
> defined. The 3D layer is mode-agnostic.

## Reference Update (incremental only)

A **Reference Update** sub-section appears **only when Tracking Mode =
Incremental**. It controls when the rolling reference refreshes:

- **Every Frame** (default) — the reference resets every frame; most robust for
  large deformation. Only frame 1 needs an ROI — it is warped forward.
- **Every N Frames** — the reference resets every *N* frames. An **Update every**
  spinbox appears (range **2–100**, default **2**, suffix *frames*).
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

## Quality gates

A **Quality gates (ZNSSD / outliers)** checkbox (off by default) enables the
robustness gates: a ZNSSD gate on the correspondence, plus reprojection and
3D-outlier filters on the reconstruction. Every point a gate removes is
*counted* and reported in the run log (see [Running](09-running.md)) — a gate
never eats points silently. Leave it off to keep every tracked point.

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
| Small, monotonic deformation | Accumulative | — |
| Large cumulative strain | Incremental | Every Frame |
| Large rigid rotation | Incremental | Every Frame |
| Dynamic event / impact | Incremental | Every Frame |
| Quasi-static with known load steps | Incremental | Every N / Custom |

When in doubt, **Incremental + Every Frame** handles any deformation magnitude
and needs an ROI only on frame 1.

Next: [Initial guess & Starting Points →](06-initial-guess.md)
