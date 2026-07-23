# pyALDIC-3D quickstart

Run the full stereo-DIC pipeline end to end on the shipped sample dataset — either from
the desktop GUI or headless from the command line.

## The sample data

The dataset lives one level up, in
[`../Images_Stereo_Sample3_images/`](../Images_Stereo_Sample3_images):

```
Images_Stereo_Sample3_images/
├── cal.xml        # DICe-format OpenCV stereo calibration
├── L/             # left camera:  0000_0.tif, 0001_0.tif, 0002_0.tif  (1920x1200)
└── R/             # right camera: 0000_1.tif, 0001_1.tif, 0002_1.tif
```

It is three synchronized stereo pairs of a speckled **D-specimen** (Stereo-DIC
Challenge 1.0, "Sample 3"). Three frames is a deliberately small quickstart — enough to
exercise calibration → correspondence → 3D reconstruction → surface strain, not a full
experiment. The config below tracks in **incremental** mode, which handles this sequence's
frame-to-frame motion well (all three frames track at ~100 % validity).

---

## Option A — CLI (headless, ~seconds)

From the repository root:

```bash
al-dic-3d run examples/quickstart/config.toml -o examples/quickstart/out
# or:  python -m al_dic_3d run examples/quickstart/config.toml -o examples/quickstart/out
```

All paths in [`config.toml`](config.toml) are relative to the config file, so it runs from
any working directory.

### Expected output

Under `examples/quickstart/out/` you get:

| File | Contents |
|---|---|
| `quickstart.npz`, `quickstart.mat` | the unified result archive (below) |
| `quickstart_parameters_<timestamp>.json` | the full run configuration |

The archive holds, keyed by name:

- `points3D` — `(3, 1309, 3)` metric surface points (mm), one slice per frame;
- `U`, `V`, `W`, `mag` — `(3, 1309)` displacement components + magnitude (mm);
- `exx`, `eyy`, `exy`, `e1`, `e2`, `max_shear`, `von_mises` — `(3, 1309)` surface strain;
- `ref_coords`, `xL`, `xR`, `quality`, `reproj_error` — mesh + raw correspondence.

Load it in Python:

```python
import numpy as np
d = np.load("examples/quickstart/out/quickstart.npz")
print(d["points3D"].shape)            # (3, 1309, 3)
print(np.nanmax(np.abs(d["W"][-1])))  # peak out-of-plane displacement, mm
```

The reconstructed surface sits ~377–390 mm from the left camera (the world origin),
matching the calibration; the specimen undergoes a few-mm rigid motion across the three
frames.

### Try the other exporters

```bash
al-dic-3d run examples/quickstart/config.toml -o examples/quickstart/out --formats npz,csv,ply,vtu
```

`ply` gives per-frame point clouds (open in MeshLab/CloudCompare); `vtu` writes a
`.vtu` + `.pvd` time series for ParaView; `csv` writes per-frame tables.

---

## Option B — GUI

Launch the desktop app (needs the `[gui]` extra, and `[viz3d]` for the 3D view):

```bash
al-dic-3d gui
```

Then, in the three-column window:

1. **Import images.** Drag the `L/` folder onto the **left** camera drop zone and the
   `R/` folder onto the **right** one (or use the import buttons). The three pairs appear
   in the image list.
2. **Set the calibration.** In the calibration section, choose **Import** and select
   `../Images_Stereo_Sample3_images/cal.xml`, format **DICe**. The panel shows the loaded
   stereo rig and its QC summary.
3. **Choose the workflow.** Strategy **Track Both** (default), reference mode
   **Incremental**. Optionally open **Advanced** to confirm subset = 32, step = 16.
4. **Draw an ROI.** With the ROI toolbox (rectangle tool), draw a box over the speckled
   specimen face on the left, frame-1 image — roughly the central bright region. (You can
   also draw an arbitrary polygon/mask to follow the D-shape exactly.)
5. **Run.** Click **Run 3D Analysis** on the right. Progress ticks per frame; the log
   reports per-frame validity.
6. **Inspect.** Use the **FIELD** buttons (U / V / W / |D|) to color the field, switch to
   the **3D View** to see the reconstructed surface with camera frusta, and open the
   **Strain** window for surface strain (pick the strain type and coordinate system).
7. **Export / Save.** Use **Export** for images, animations, PLY/VTU, or data tables; or
   **Save** the whole project (including results) to a `.aldic3d` session to reopen later.

---

## Notes

- **ROI matters.** The config's rectangular ROI (`[roi]` in `config.toml`) is kept inside
  the coupon to avoid the dark background. Widen it and you will see more `NaN`
  (untracked) nodes where there is no speckle — that is honest behaviour, not an error.
- **Small dataset.** With only three frames this is a smoke-test-scale example. For a real
  study, point `[sequence].left/right` at your own image globs and calibrate with
  `al-dic-3d calibrate` (see the main [README](../../README.md#calibration)).
