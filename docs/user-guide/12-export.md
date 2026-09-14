# 12. Exporting

Both the main window and the [Strain window](11-strain-processing.md) open the
**same** export dialog (title: *Export Results*, `assets/export_window.png`).
Which window you launch it from only seeds the initial visualization preset
(colormap, range, deformed toggle, display unit). The dialog always exports
the results currently on screen: after a new run, a strain recompute or a
project switch, reopening it builds a fresh dialog, and an idle dialog left
open on the old results closes by itself.

Images, animations, the preview and the 3D renders use the canvas's **display
unit** and its velocity rule (per frame until you set a frame rate, see
[Viewing results](10-viewing-results.md)), so a colorbar reads exactly as on
screen. The numeric data (NPZ / MAT / CSV / PLY / VTU) always stays in **mm**.

At the top of the dialog, above the tabs, is a shared **OUTPUT FOLDER** row: a
path field (placeholder *Select output folder…*), a **Browse…** button, and an
**Open Folder** button. Each export click mints a **fresh timestamp**, so
repeated exports never overwrite one another. The bottom bar has a single
**Close** button — every export action button keeps the dialog open so you can
export several formats in one sitting.

## The five tabs

The tabs, in order, are:

1. **Data**
2. **Images**
3. **Animation**
4. **Preview & Colorbar**
5. **3D View**

## Data tab

Check the numeric-data formats you want (the **Format** group):

| Checkbox | Default | Output |
|----------|---------|--------|
| **NumPy archive (.npz)** | on | `<prefix>_<ts>.npz` |
| **MATLAB (.mat)** | on | `<prefix>_<ts>.mat` |
| **CSV (one file per frame)** | off | `<prefix>_csv_<ts>/<prefix>_frame_1.csv`, `…_frame_2.csv`, … (own sub-folder, frames numbered from 1 like every other export) |
| **PLY point clouds (per frame)** | off | `<prefix>_ply_<ts>/…` |
| **VTU mesh series (ParaView)** | off | `<prefix>_vtu_<ts>/frame_XXX.vtu` + `<prefix>.pvd` |

A **parameters JSON is always written** (`<prefix>_parameters_<ts>.json`),
regardless of which formats you tick — the note *"✓ Parameters file (JSON)
always exported"* reminds you. It records the parameters of the run that
produced the results (subset size, step, strategy, thresholds, ROI), even if
you changed the sidebar afterwards.

A progress bar follows each format, and **Cancel** stops between frames. A
cancelled NPZ or MAT leaves no partial file behind, and the status line says
*cancelled* only when the export really stopped early. MAT files refuse any
variable larger than MATLAB's version-5 limit (2 GB) before writing, naming the
variable.

Below the formats are two **field pickers**, each with **All** / **None**
buttons:

- **Displacement** — `U`, `V`, `W`, `|D|` (`mag`). All checked by default.
- **Strain** — `εxx`, `εyy`, `εxy`, `ε₁`, `ε₂`, `γ max`, `von Mises`
  (`exx, eyy, exy, e1, e2, max_shear, von_mises`). Checked by default *only when
  the run has strain*; the whole group is disabled if no strain was computed.

> *3D points, reprojection error, and source flags are always exported* — you
> do not select these; they are core arrays (see the variable structure below).

Click **Export Data** to write the ticked formats. When strain is exported and a
trim/crack validity mask exists, a `strain_valid` array is appended.

### Exact exported variable structure

The `.npz` / `.mat` archive from the **Data tab** always carries these **core
arrays**, plus one `(T, N)` stack per selected field. Shapes: `N` = node count,
`T` = number of frames.

| Variable | Shape | Meaning |
|----------|-------|---------|
| `strategy` | scalar string | the correspondence strategy used |
| `ref_coords` | `(N, 2)` | reference (frame-1) LEFT-image node coordinates in **pixels** |
| `points3D` | `(T, N, 3)` | reconstructed world coordinates in **mm** (`NaN` = invalid) |
| `reproj_error` | `(T, N)` | normalized reprojection RMS per node |
| `source` | `(T, N)` | per-node source flag: TRACKED / STEREO_REFRESH / RESCUED / INVALID |

Then, for each **selected** field:

| Variable | Shape | Meaning |
|----------|-------|---------|
| `U`, `V`, `W` | `(T, N)` | displacement components in **mm** |
| `mag` | `(T, N)` | `sqrt(U² + V² + W²)` |
| `exx`, `eyy`, `exy` | `(T, N)` | tangent-frame Green-Lagrange strain (when strain computed) |
| `e1`, `e2` | `(T, N)` | major / minor principal strain |
| `max_shear`, `von_mises` | `(T, N)` | strain invariants |
| `strain_valid` | `(T, N)` bool | edge-trim ∪ crack-trim mask (`True` = show), appended when strain is trimmed |

> The headless `al-dic-3d run` archive is a **superset**: on top of the above it
> also writes every field stack unconditionally plus `displacement3D`
> (`points3D[k] − points3D[0]`), the out-of-plane slope diagnostics `dwdx` /
> `dwdy`, the matched pixel coordinates `xL` / `xR`, the correspondence
> `quality`, and scalar `n_frames` / `n_pts`. Readers that ignore unknown keys
> work with either archive.

**Strain values stay dense.** Trimming does not blank the strain arrays;
instead the boolean `strain_valid` marks which nodes to show. Display and image
exports apply this mask (frame-0 validity for the reference view, frame-*k* for
the deformed view); the raw `.npz`/`.mat` strain arrays keep every value, so you
can re-trim downstream.

The per-frame **CSV** files (`<prefix>_frame_1.csv`, … in the
`<prefix>_csv_<ts>/` sub-folder) have one row per node with columns
`x_px, y_px, X_mm, Y_mm, Z_mm`, then the selected fields.

The headless `al-dic-3d run` records the archive layout as `archive_schema = 3`
in its parameters JSON (the export dialog's parameters JSON does not carry this
key). Both paths put CSV files in a `<prefix>_csv_<ts>/` sub-folder; the
headless runner names the archives `<prefix>.npz` / `<prefix>.mat`, whereas the
export dialog adds the timestamp to every name.

## Images tab

Render each field to a per-frame image. Controls:

- **Fields** — one row per field (`U, V, W, mag, exx … von_mises`). Each row has
  an enable checkbox, a colormap combo, an **Auto** range checkbox (on by
  default) with **Min**/**Max** spinboxes, and an **Opacity** spinbox
  (0.0–1.0, step 0.05, default 0.85). By default only `U`, `V`, `W` are enabled.
- **Camera** — *Left*, *Right*, or *Left + Right* (default *Left*).
- **Format** — **PNG** (default), **JPEG**, or **TIFF**.
- **JPEG quality** — 10–100, default **92** (shown only for JPEG).
- **Resolution (long edge)** — 512 / 768 / 1024 (default) / 1536 / 2048 px, or
  **Full resolution** (native). Aspect ratio is kept.
- **Include colorbar** — on by default. Leave it on for quantitative figures.
- **Background** — *Original (frame 1 background)* or *Deformed (current frame
  background)*. The background uses the canvas's brightness stretch, so 12-bit
  images stored in 16-bit files are no longer nearly black.
- **Frame range** — *All frames* (default), or a *From frame* / *to* range
  (1-based).

Click **Export Images** to write one file per frame per enabled field.
Right-camera images use the same region as the canvas (the left ROI mapped
into the right camera). A frame with nothing to draw is skipped and named in
the status line, and an export that writes nothing is shown as a failure.

## Animation tab

Render an MP4 or GIF sweeping through frames, for each enabled field. Frames are
encoded one at a time (streaming), so even long 4K sequences export without a
memory spike. Controls mirror the Images tab (Fields / Camera / Background /
Frame range / Include colorbar) plus:

- **Format** — **MP4** (default) or **GIF**.
- **Frames per second** — 1–120, default **10**.
- **Frame step** — export every *N*th frame (1–*n_frames*, default 1). Higher is
  faster and smaller but choppier; the playback fps scales down by the same
  factor so real duration is preserved.
- **Resolution (long edge)** — same presets as Images.

> MP4 uses the encoder bundled with OpenCV (mp4v, with XVID as a fallback);
> odd frame sizes are padded to even. If no encoder opens, the export fails
> with an error instead of reporting success. GIFs are written frame by frame,
> so memory stays small even for long sequences, and they play at the chosen
> rate (GIF timing allows at most 50 fps). GIF files are still large at native
> resolution — cap the resolution for GIFs. A cancelled animation's unfinished
> file is deleted.

## Preview & Colorbar tab (WYSIWYG)

A live preview of one exported frame, rendered through the **exact export code
path** — what you see here is what Images and Animation will write. The
colorbar and margin settings on this tab are the style **all** image and
animation exports use.

- **Field / Frame / Camera** pickers on the left drive the preview.
- **FIELD APPEARANCE** — Colormap, an **Auto** range checkbox (on) with
  **Min**/**Max**, and **Opacity**. These are **two-way synced** with the
  matching row on the Images tab. **Apply to all fields** copies the colormap,
  opacity, and auto-range mode to every enabled field (each keeps its own
  Min/Max).
- **COLORBAR STYLE** — with defaults:
  - **Position** — Right (default) / Left / Top / Bottom.
  - **Font size** — 6–32 pt, default **9**.
  - **Font family** — sans-serif (default) / serif / monospace.
  - **Bar thickness** — 0.02–0.25 (fraction of the image), default **0.05**.
  - **Background** — Black (default) / White.
  - **Margin** — 0.0–0.30 (fraction of the long edge), default **0.0** (none).
  - **Margin color** — White (default) / Black.

When physical units are enabled, the colorbar label and ticks use them (e.g.
`|D| (mm)`) in both the preview and the exported files.

## 3D View tab (offscreen render)

Render the interactive 3D surface offscreen:

- **Field** / **Colormap** / **Resolution** — resolution is one of
  `1024 × 768` (default), `1280 × 960`, `1920 × 1080`, `800 × 600`.
- **Auto** range (on: each frame's 2nd–98th percentile inside the ROI, the
  interactive view's rule) or fixed **Min** / **Max**.
- The surface is limited to the ROI, and the camera is the one of the
  interactive 3D view when it is open (otherwise an isometric view).
- **Frame sequence** group:
  - **Per-frame image sequence (PNG)** — on by default.
  - **Animation** — on by default; **MP4** (default) / **GIF**, **Frames per
    second** (1–120, default 10), **Frame step** (default 1).
  - Frame range (All frames by default).
- **Turntable** group:
  - **Turntable (360° orbit at frame N)** — off by default.
  - **Orbit frames** — 4–360, default **36**.

Click **Export 3D View**. At least one of the sequence / animation / turntable
options must be selected.

## Colormaps

The colormap combos everywhere offer: `turbo` (default), `viridis`, `jet`,
`coolwarm`, `plasma`, `inferno`, `RdBu_r`. Diverging maps (`coolwarm`,
`RdBu_r`) are best for signed fields that cross zero.

Next: [Sessions →](13-session.md)
