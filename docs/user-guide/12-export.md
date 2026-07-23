# 12. Exporting

Both the main window and the [Strain window](11-strain-processing.md) open the
**same** export dialog (title: *Export Results*, `assets/export_window.png`).
Which window you launch it from only seeds the initial visualization preset
(colormap, range, deformed toggle).

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
| **CSV (one file per frame)** | off | `<prefix>_<ts>_frameNNN.csv` (flat, in the folder) |
| **PLY point clouds (per frame)** | off | `<prefix>_ply_<ts>/…` |
| **VTU mesh series (ParaView)** | off | `<prefix>_vtu_<ts>/frame_XXX.vtu` + `<prefix>.pvd` |

A **parameters JSON is always written** (`<prefix>_parameters_<ts>.json`),
regardless of which formats you tick — the note *"✓ Parameters file (JSON)
always exported"* reminds you.

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

The per-frame **CSV** files (`<prefix>_<ts>_frameNNN.csv`) have one row per node
with columns `x_px, y_px, X_mm, Y_mm, Z_mm`, then the selected fields.

The headless `al-dic-3d run` records the archive layout as `archive_schema = 3`
in its parameters JSON (the export dialog's parameters JSON does not carry this
key). The two paths also differ in file layout: the headless runner groups CSV
into a `<prefix>_csv_<ts>/` subfolder and names the archives `<prefix>.npz` /
`<prefix>.mat`, whereas the export dialog writes flat, timestamped files as
shown above.

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
  background)*.
- **Frame range** — *All frames* (default), or a *From frame* / *to* range
  (1-based).

Click **Export Images** to write one file per frame per enabled field.

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

> MP4 encoding requires `ffmpeg`. GIF is a dependency-free fallback but explodes
> in size at native resolution — cap the resolution for GIFs.

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

Render the interactive 3D surface offscreen (requires the `[viz3d]` extra):

- **Field** / **Colormap** / **Resolution** — resolution is one of
  `1024 × 768` (default), `1280 × 960`, `1920 × 1080`, `800 × 600`.
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
