# pyALDIC-3D User Guide

pyALDIC-3D is a desktop and command-line application for **stereo (3D) Digital
Image Correlation**. From two synchronized camera views of a deforming
specimen and a stereo calibration, it computes millimetre-native **3D
displacement** (`U`, `V`, `W`) and **surface strain** on the reconstructed
point cloud.

This guide walks through the graphical workflow from left to right, chapter by
chapter, and documents every control against the shipping code. It is written
for pyALDIC-3D `0.1.0.dev0` (built on the pinned 2D engine `al-dic==0.7.*`).

> **New to 3D-DIC?** Read [Overview](01-overview.md) first, then
> [Installation & launching](02-installation-launching.md), then
> [Calibration](04-calibration.md) — a calibrated stereo rig is a prerequisite
> for every run.

## Contents

| # | Chapter | What it covers |
|---|---------|----------------|
| 1 | [Overview](01-overview.md) | What stereo-DIC computes here, the three-column GUI, a typical session. |
| 2 | [Installation & launching](02-installation-launching.md) | Extras (`[gui]`, `[viz3d]`, `[dev]`), the `al-dic==0.7.*` pin, `al-dic-3d gui`, `python -m al_dic_3d`, opening a `.aldic3d`. |
| 3 | [Loading stereo images](03-loading-images.md) | LEFT / RIGHT drop zones, pairing, natural sort, the pair list. |
| 4 | [Calibration](04-calibration.md) | The built-in stereo calibrator, the six import formats, manual parameters, the QC readout — a headline 3D feature. |
| 5 | [Workflow type](05-workflow-type.md) | Accumulative vs incremental, reference-update policy, solver, quality gates. |
| 6 | [Initial guess & Starting Points](06-initial-guess.md) | Seed propagation, FFT, Previous — and when to use each. |
| 7 | [Region of interest](07-region-of-interest.md) | The ROI toolbox, mesh preview, and thin-barrier crack awareness. |
| 8 | [Parameters](08-parameters.md) | Subset size, step, stereo/temporal search, mesh refinement. |
| 9 | [Running](09-running.md) | Run, progress/ETA, cancel-keeps-partial, failure accounting. |
| 10 | [Viewing results](10-viewing-results.md) | Field selector, display units, deformed/reference, camera view, the 3D View. |
| 11 | [Strain post-processing](11-strain-processing.md) | VSG, strain types, coordinate systems, edge-trim, crack-aware strain. |
| 12 | [Exporting](12-export.md) | The tabbed dialog, every format, and the exact exported variable structure. |
| 13 | [Sessions](13-session.md) | `.aldic3d` contents, what is / isn't saved, image relocation. |
| 14 | [Troubleshooting](14-troubleshooting.md) | Blank strain, moved images, calibration sanity, no valid 3D points, viz3d/OpenGL. |

## Screenshots

The `assets/` folder at the repository root holds reference screenshots of the
three main windows:

- `assets/main_page.png` — the three-column main window.
- `assets/strain_window.png` — the strain post-processing window.
- `assets/export_window.png` — the tabbed export dialog.

## Conventions used in this guide

- **Metric-native.** Every displacement and velocity value is millimetres (mm)
  on the wire — in the data arrays, the session file, and the exports (CSV
  headers say `_mm`). The units selector converts values at the **display**
  layer only. Strain is dimensionless and is never converted.
- **World frame = the LEFT camera** (rotation `R = I`, translation `T = 0`).
  Correlation runs on the RAW images; point coordinates are undistorted only
  just before triangulation.
- **`NaN` means invalid** and is propagated end to end. A node that could not
  be tracked or reconstructed is `NaN`, never zero.
- **Frames are 1-based in the GUI** (frame 1 = the reference) and 0-based in
  the file formats / TOML config.
