# 13. Sessions

pyALDIC-3D saves an entire project — image references, calibration, parameters,
ROI, seeds, view state, and (optionally) the computed results — into a single
`.aldic3d` file. Reopening it lands you back where you left off, with no
recompute.

## File format

A `.aldic3d` file is a **versioned ZIP bundle** containing:

- **`session.json`** — always present; a human-readable JSON configuration.
- **`results.npz`** — present only when a run completed **and** you chose to
  include results (stored uncompressed inside the zip because the `.npz` is
  already per-array compressed).

The bundle is versioned: `session.json` carries `schema_version` (currently
**1**). Opening a file with an unknown schema, or a file that is not a zip,
raises an error rather than misinterpreting it.

`session.json` top-level keys: `schema_version`, `config` (the reproducible
`RunConfig`, or null), `draft` (the GUI project draft), `view_state`,
`workflow_step`, `strategy`, `meta` (human-readable run metadata), and
`has_results`.

## What is saved

- **All run parameters** — the full `RunConfig`: strategy, tracking / reference
  mode and update policy, subset size / step, stereo & temporal search,
  refinement, quality gates, calibration file path and format, etc. (path fields
  are stored as strings).
- **The project draft** — the ROI, disparity offset, output directory, and the
  calibration file reference.
- **The ROI** — the drawn shapes / bounding box are saved. The pixel mask array
  is *not* embedded in the bundle: it is dropped from `session.json` and rebuilt
  on load. (Only when a run has executed does `build()` materialize a mask PNG,
  and that PNG lives in the run's output folder and is referenced from the config
  by path — never stored inside the `.aldic3d` bundle.)
- **Seeds / Starting Points** — both the legacy single `seed_point` and the
  multi-seed `seed_points` list are saved and restored (a pre-multi-seed session
  migrates the single seed into the list on open).
- **View state** — the display state (see below).
- **Computed results** (optional) — when included, `results.npz` holds
  `ref_coords`, `points3D`, `displacement3D`, `reproj_error`, source flags, the
  correspondence (`xL`, `xR`, `quality`), and every strain field plus
  `strain_valid`.

### View state keys

The persisted `view_state` restores: `display_field`, `colormap`, `color_auto`,
`color_min`, `color_max`, `overlay_alpha`, `show_deformed`, `camera` (L/R),
`current_frame`, `display_unit`, `frame_rate`, and the mesh overlay
`mesh_line_color` / `mesh_line_width`.

> The interactive **3D View** camera pose / turntable state is **not** among the
> persisted keys — only the 2D display state above plus the L/R camera choice.

## What is *not* saved

- **The images themselves** — the bundle stores folder paths and file names,
  never pixel data. Keep the image folders (or relocate them on open, below).
- **The canvas-painted mask ndarrays in raw form** — they are rebuildable from
  the canvas and are written out as PNGs at save time, not embedded as arrays in
  the JSON.
- With **include-results = No**, the `results.npz` member is skipped entirely and
  the file reopens with no results (a small, shareable, config-only project).

Separately, GUI preferences — window geometry, the recent-projects list (up to
8), and last-used directories — live in the OS settings store
(`QSettings("pyALDIC", "pyALDIC-3D")`), **not** inside the `.aldic3d` file.

## The include-results prompt

If results exist when you save, a modal **Include Results?** dialog appears
first: *Include the analysis results in this project file?* with an estimate of
their uncompressed size. Buttons **Yes** (default) / **No** / **Cancel**:

- **Yes** — write the full results; reopening restores every field without
  recomputing (the point of saving a long run).
- **No** — write a small configuration-only file for sharing a setup.
- **Cancel** — abort the save.

## Opening a project whose images moved

The 3D app tries hard not to fail when image folders have moved. On open it
**auto-relocates** moved image sequences (e.g. by looking near the `.aldic3d`
file's own location and rewriting the draft's paths). Each successful relocation
is logged (*relocated N camera-L images: old → new*) and marks the project dirty
so the next save persists the corrected paths.

Only when auto-relocation cannot find a camera's frames does a **Locate Images**
dialog prompt you to pick the folder that now holds that camera's frames (file
names must match). Cancelling the prompt aborts the open; the app keeps its prior
state.

Next: [Troubleshooting →](14-troubleshooting.md)
