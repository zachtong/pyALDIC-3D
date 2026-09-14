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
- **`roi_mask.png`** — present only when you drew an arbitrary-shape ROI; the
  ROI mask as an 8-bit grayscale PNG (255 = inside the ROI, 0 = outside).
- **`refinement_mask.png`** — present only when you painted refinement zones
  with the brush; same encoding.
- **`calibration/<file name>`** — a copy of the calibration file (up to 50 MB),
  so the project still has its calibration on another computer or after the
  file moved.

The bundle is versioned: `session.json` carries `schema_version` (currently
**1**). Opening a file with an unknown schema, or a file that is not a zip,
raises an error rather than misinterpreting it. The two mask members are
**optional**, so a session written before they existed still opens normally (it
simply comes back with no drawn mask).

`session.json` top-level keys: `schema_version`, `config` (the reproducible
`RunConfig`, or null), `draft` (the GUI project draft), `view_state`,
`workflow_step`, `strategy`, `meta` (human-readable run metadata, including
`run_params`, the parameters that produced the results), `has_results`, and
`calibration_member` (the name of the embedded calibration copy).

## What is saved

- **All run parameters** — the full `RunConfig`: strategy, tracking / reference
  mode and update policy, subset size / step, stereo & temporal search,
  refinement, quality gates, calibration file path and format, etc. (path fields
  are stored as strings).
- **The project draft** — the ROI, disparity offset, output directory, the
  calibration file path, and per-frame mask files if you imported them.
- **The calibration itself** — a copy travels inside the file. When the
  original path does not exist on opening, pyALDIC-3D first looks for a file
  of the same name next to the project and next to the image folders, and
  otherwise restores the embedded copy to a folder of your user profile; the
  log says which one it used.
- **The ROI, exactly as drawn** — the bounding box lives in `session.json` and
  the pixel mask itself is embedded as `roi_mask.png`. Polygons, circles, cut
  shapes, brush strokes and imported PNG masks therefore all come back
  pixel-for-pixel: reopening a project correlates the same region it did before,
  cut-out holes included, and a crack barrier keeps its crack-aware behaviour.
- **The refinement brush** — embedded as `refinement_mask.png`. It feeds the
  quadtree refinement, so keeping it is what makes a re-run of a reopened
  session build the *same* mesh as the run it was saved with.
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
`current_frame`, `display_unit`, `frame_rate` (and whether you set one:
without it velocity is shown per frame), the mesh overlay
`mesh_line_color` / `mesh_line_width`, and the canvas toolbar toggles
`show_grid` / `show_subset` / `view_3d` — so a project reopens on the view you
left it on, 3D page included.

> Whether the **3D View** page was showing is persisted (`view_3d`), but its
> camera pose / turntable state is **not**: the reopened 3D view is framed from
> the default viewpoint.

## What is *not* saved

- **The images themselves** — the bundle stores folder paths and file names,
  never pixel data. Keep the image folders (or relocate them on open, below).
- **The undo history of your ROI edits** — the mask is saved as pixels, so the
  shapes you drew to get there are not individually recoverable.
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
names must match). If you cancel it, a second question offers **Open anyway**:
the project opens with its results viewable and exportable, the log lists the
images that were not found, and the **Run** button stays disabled until the
images are back (readiness reports the unreadable images). Choosing **Cancel**
there aborts the open, and the app keeps its prior state.

Next: [Troubleshooting →](14-troubleshooting.md)
