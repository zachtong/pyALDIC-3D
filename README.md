<p align="center">
  <img src="https://raw.githubusercontent.com/zachtong/pyALDIC-3D/main/assets/banner_3d.png" alt="pyALDIC-3D Banner" width="100%"/>
</p>

<p align="center">
  Stereo (two-camera) Digital Image Correlation: 3D shape, displacement and<br/>
  Green–Lagrange surface strain in millimetres — calibration to export, in one desktop app.
</p>

<p align="center">
  <a href="https://github.com/zachtong/pyALDIC-3D/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/zachtong/pyALDIC-3D/ci.yml?style=flat-square&label=CI" alt="CI"/></a>
  <img src="https://img.shields.io/badge/tests-687-22c55e?style=flat-square" alt="Tests"/>
  <img src="https://img.shields.io/badge/Python-3.10+-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/GUI-PySide6-41cd52?style=flat-square" alt="PySide6"/>
  <img src="https://img.shields.io/badge/3D-PyVista%2FVTK-blue?style=flat-square" alt="PyVista"/>
  <img src="https://img.shields.io/badge/License-BSD--3--Clause-22c55e?style=flat-square" alt="License"/>
  <a href="https://doi.org/10.5281/zenodo.21696564"><img src="https://img.shields.io/badge/DOI-10.5281%2Fzenodo.21696564-blue?style=flat-square" alt="DOI"/></a>
  <a href="https://pypi.org/project/al-dic-3d/"><img src="https://img.shields.io/pypi/v/al-dic-3d?style=flat-square&label=PyPI" alt="PyPI"/></a>
</p>

<p align="center">
  <strong>🌍 Available in 8 languages</strong><br/>
  <img src="https://img.shields.io/badge/English-✓-22c55e?style=flat-square" alt="English"/>
  <img src="https://img.shields.io/badge/简体中文-✓-22c55e?style=flat-square" alt="Simplified Chinese"/>
  <img src="https://img.shields.io/badge/繁體中文-✓-22c55e?style=flat-square" alt="Traditional Chinese"/>
  <img src="https://img.shields.io/badge/日本語-✓-22c55e?style=flat-square" alt="Japanese"/>
  <img src="https://img.shields.io/badge/한국어-✓-22c55e?style=flat-square" alt="Korean"/>
  <img src="https://img.shields.io/badge/Deutsch-✓-22c55e?style=flat-square" alt="German"/>
  <img src="https://img.shields.io/badge/Français-✓-22c55e?style=flat-square" alt="French"/>
  <img src="https://img.shields.io/badge/Español-✓-22c55e?style=flat-square" alt="Spanish"/>
</p>

---

## Why pyALDIC-3D?

Stereo-DIC solves two problems at once: *where is this material point in the other
camera* (shape) and *where did it go* (motion). Almost every tool answers both with
independent subset correlations, which is accurate for small, smooth deformation but
degrades exactly where experiments get interesting — steep gradients, discontinuities,
decorrelating patterns. pyALDIC-3D runs temporal tracking through an **Augmented
Lagrangian (AL-DIC)** solver that couples the local IC-GN subproblems to a global FEM
regularizer, on an **adaptive quadtree mesh** you can refine where the field needs it,
and then triangulates to a **metric, millimetre-native** 3D surface. Calibration,
crack handling, quality gating, 3D visualization and export are all in the box — there
is no second application in the workflow.

<p align="center">
  <img src="https://raw.githubusercontent.com/zachtong/pyALDIC-3D/main/assets/stereo_principle.png" alt="Stereo-DIC principle — two calibrated camera frusta, rays converging on a surface point, and the resulting disparity field in the left and right images" width="92%"/>
</p>

> **Scope, honestly:** v1 supports a **two-camera stereo rig**. The data model is
> N-camera-ready, but **N-camera (> 2) support is post-v1** — if you need 6 or 12
> cameras today, use MultiDIC or a commercial system.

---

## Key Features

### Built-in stereo calibration — including a coded-target detector

Calibration is where stereo-DIC accuracy is won or lost, so it is a first-class step
rather than a prerequisite you satisfy elsewhere. Point the app at synchronized board
image pairs and it solves per-camera intrinsics and stereo extrinsics with OpenCV, from
**chessboards, ChArUco boards, circle grids, or a self-developed coded circular
target** (three concentric-ring fiducials, so partial and clipped views still key
correctly). What surrounds the solve matters as much as the solve: per-image
reprojection bars, threshold-based worst-pair rejection with an automatic re-solve,
epipolar validation, coverage and pose diagnostics, optional joint bundle adjustment
with board-morphology refinement, a leave-*p*-out stability jackknife, a 1:1 printable
board PDF, and an independent **known-distance verification** that catches a wrong
scale a reprojection RMS never will (the MATLAB predecessor has none of this — it
imports a calibration and prints one frame's error).
Already calibrated? Import from **six external formats** (MATLAB/OpenCV, MatchID, MMC,
DICe, OpenCorr, OpenCV-YAML) or type parameters in by hand.

<p align="center">
  <img src="https://raw.githubusercontent.com/zachtong/pyALDIC-3D/main/assets/calibration.png" alt="Calibration workflow — the printable coded target, the detector recovering all 108 dots on an oblique view with the fiducial triangle, and per-pair reprojection QC bars from a real stereo solve" width="92%"/>
</p>

### Metric 3D surface, displacement and surface strain

Every node is triangulated into world coordinates (**millimetres**, left camera at the
origin), so displacement is `P^k − P^1` with no pixel-size calibration step and no
scale ambiguity. Surface strain is a post-process on that 3D cloud: a local tangent
plane is fitted over a virtual strain gauge window, the in-plane displacement gradient
is differentiated on it, and the tensor is reported in your choice of **three strain
types** (Green–Lagrange, infinitesimal, Euler–Almansi) and **three coordinate systems**
(fitted surface plane, left-camera frame, or a custom 3-point specimen frame you pick
on the canvas) — with edge trimming for low-confidence boundary nodes and a
Numba-accelerated kernel.

<p align="center">
  <img src="https://raw.githubusercontent.com/zachtong/pyALDIC-3D/main/assets/surface_3d.png" alt="3D surface rendered by the application: out-of-plane displacement on the reconstructed shape next to the Green-Lagrange surface strain on the same mesh" width="92%"/>
</p>

### Crack-aware stereo DIC

Draw the crack into the ROI as a thin barrier and the whole chain respects it: the mesh
is **cut** so the AL-DIC global step never bridges the two lips, strain neighbours whose
line of sight would cross the barrier are excluded, the crack is warped through the
frame-1 correspondence into the right camera, and rendering blanks any cell that spans
it — on the canvas, in the strain window, in exported images, animations and the 3D
view alike. Without it, the interpolation smears the two sides into one continuous
field and the discontinuity you came to measure disappears.

<p align="center">
  <img src="https://raw.githubusercontent.com/zachtong/pyALDIC-3D/main/assets/crack_aware.png" alt="Same displacement field rendered twice: without a declared crack barrier the field smears across the crack; with the barrier the discontinuity is sharp and the bridging cells are blanked" width="85%"/>
</p>

### The honesty gate — every shipped displacement is re-verified

A DIC solver can converge on garbage. Warm-started IC-GN on a decorrelated pattern
"converges" with a zero update and returns the previous frame's field verbatim;
incremental composition then carries that lie forward, and the field stays smooth,
finite and completely wrong. pyALDIC-3D therefore re-derives, for every node of every
frame, the **ZNSSD between the frame-0 subset at X and frame k at X + Uᵏ** — an
independent check of the shipped number, not a reading of the solver's own convergence
flag — and NaNs out whatever fails. Gate kills are counted per frame and reported in
the run log rather than vanishing as anonymous holes, and frames the gate never got to
verify are **dropped rather than shipped unverified**.

<p align="center">
  <img src="https://raw.githubusercontent.com/zachtong/pyALDIC-3D/main/assets/honesty_gate.png" alt="Honesty gate demonstration: a plausible-looking raw solver field, the independently re-derived ZNSSD that exposes the decorrelated region, and the gated result with those nodes NaN-ed out" width="92%"/>
</p>

### Pluggable correspondence strategies

How stereo and temporal matching are interleaved changes what a sequence can survive,
so the choice is yours — all three feed the identical downstream 3D layer:

| Strategy | What it does | Where it wins |
|---|---|---|
| `track_both` *(default)* | tracks both cameras temporally from their own frame 1 | the MATLAB-reference baseline; robust general case |
| `stereo_each_frame` | one left temporal chain + a fresh scattered stereo match per frame | long sequences — no stereo drift accumulates |
| `ref_direct` | left temporal chain + direct L₁ → R\_k cross-matching | small deformation; the cleanest fields, zero drift |

On top of that: **accumulative** or **incremental** reference mode (with Every-Frame /
Every-N / Custom reference update), AL-DIC or plain local IC-GN, three initial-guess
modes (multi-seed Starting-Points propagation, FFT cross-correlation, previous frame),
quadtree refinement at mask boundaries / ROI edges / a painted brush region, and
optional ZNSSD + reprojection + 3D-outlier quality gates.

### Desktop GUI, and sessions you can come back to

A single three-column window: dual-camera import with pairing checks, calibration,
the full ROI toolbox (rectangle / polygon / circle / 3-point circle, add and cut,
brush, import, invert) and parameters on the left; a zoom-and-pan canvas with the mesh
preview, dense continuous field rendering and a WYSIWYG colorbar in the middle; run
controls, field selection, camera switch, live progress and the log on the right. Save
the whole project — images, calibration, ROI **masks**, parameters, view state **and
the computed results** — into one `.aldic3d` file, double-click it later (after a
one-click Windows file association) and land exactly where you left off.

<p align="center">
  <img src="https://raw.githubusercontent.com/zachtong/pyALDIC-3D/main/assets/main_page.png" alt="pyALDIC-3D main window — dual-camera import, calibration, ROI and parameters on the left, the field overlay on the canvas, run controls and log on the right" width="92%"/>
</p>

### 3D view, strain window, and an export matrix

An interactive PyVista/VTK 3D view (with the camera frusta drawn in) sits on the same
canvas toggle as the 2D overlay. Strain is a post-process in its own window with its
own parameters, colorbar and frame navigation. Export covers **NPZ, MATLAB `.mat`, CSV,
PLY point clouds, VTU+PVD time series for ParaView**, per-frame field images, MP4/GIF
animations, **offscreen 3D-view sequences**, and a parameters JSON that is always
written — all through the same renderer the canvas uses, so what you see is what you
export.

<p align="center">
  <img src="https://raw.githubusercontent.com/zachtong/pyALDIC-3D/main/assets/strain_window.png" alt="Strain post-processing window — strain parameters, coordinate system and strain type selectors, field buttons and frame navigation" width="47%"/>
  &nbsp;
  <img src="https://raw.githubusercontent.com/zachtong/pyALDIC-3D/main/assets/export_window.png" alt="Export dialog — data, images, animation, 3D view and preview tabs with field and format selection" width="47%"/>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/zachtong/pyALDIC-3D/main/assets/surface_orbit.gif" alt="The reconstructed 3D surface, coloured by out-of-plane displacement, rendered offscreen from thirty viewpoints around it" width="46%"/>
</p>

<p align="center">
  <i>Thirty offscreen renders of the same reconstructed surface — the export path needs
  no display, no external renderer, and no GPU.</i>
</p>

### Eight languages, and a headless CLI

The entire interface is translated into **English, 简体中文, 繁體中文, 日本語, 한국어,
Deutsch, Français and Español** (647 strings × 7 locales, 100% filled, pseudo-locale
scan clean). And when you don't want an interface at all, `al-dic-3d run config.toml`
drives the same pipeline from a TOML file on a headless server — Qt and OpenGL imports
are lazy, so the compute path never needs a display.

<p align="center">
  <img src="https://raw.githubusercontent.com/zachtong/pyALDIC-3D/main/assets/i18n_zh.png" alt="The same main window rendered under the Simplified Chinese translation" width="80%"/>
</p>

---

## Comparison with Stereo-DIC Tools

|  | **pyALDIC-3D** | **3D-Stereo-ALDIC** | **MultiDIC** | **DICe** | **VIC-3D** | **MatchID Stereo** | **Ncorr** |
|---|---|---|---|---|---|---|---|
| **Formulation** | <mark>**Hybrid local + global in one AL solve**</mark> | Hybrid local + global (AL) | Local subset (via Ncorr) | Local subset, **or** a separate global FE solver³ | Local subset⁴ | Vendor: "combines principles of local and global DIC"⁵ | Local subset — **2D only** |
| **Adaptive mesh** | <mark>**Adaptive quadtree**</mark> | Adaptive quadtree | Uniform grid | Uniform grid (local) | Uniform grid⁴ | Uniform grid | Uniform grid |
| **Built-in stereo calibration** | <mark>**Yes — 4 board types incl. coded targets, with per-image QC**</mark> | No — import only | Yes (DLT; needs a non-planar target) | Yes (OpenCV; checkerboard / dots) | Yes — the most capable of the set⁶ | Yes (incl. multi-camera) | n/a (2D) |
| **Crack-aware correlation** | <mark>**Yes — mesh cut, strain + rendering**</mark> | No | No | No⁷ | Not documented | Fracture-mechanics module (crack detection, COD, SIF)⁸ | No |
| **GUI** | <mark>**Built-in desktop**</mark> | Built-in (MATLAB)¹ | Script-driven¹ | Built-in desktop (basic cases)³ | Built-in desktop | Built-in desktop | Built-in (MATLAB)¹ |
| **Platform** | <mark>**Windows, macOS, Linux**</mark> | MATLAB R2024a+¹ | Windows (only OS tested)¹ | Windows, macOS, Linux | Windows only | Windows only | MATLAB¹ |
| **Cost / licence** | <mark>**Free · BSD-3 · no MATLAB**</mark> | Free · MIT¹ | Free · Apache-2.0¹ | Free · BSD-3 | Commercial | Commercial | Free · BSD-3¹ |
| **Latest release**² | <mark>**v1.1.0 (2026)**</mark> | No tagged release | v1.1.0 (2021) | v3.0-beta.8 (2023) | VIC-3D 11 | MatchID 2026.2 | v1.2.2 (2017) |
| **UI languages** | <mark>**8**</mark> | Not documented | Not documented | Not documented | Not documented | Not documented | Not documented |
| **Cameras** | 2 (N-camera post-v1) | 2 | **Up to 12+** | ≤ 10 in code, no documented workflow³ | **Up to 16** | **Vendor: no limit** | n/a |

<sub>¹ Requires a MATLAB licence (MultiDIC and Ncorr additionally require several toolboxes).</sub><br/>
<sub>² Compiled from public sources; commercial vendors publish no dated changelogs, so those cells give the version, not a date.</sub><br/>
<sub>³ DICe ships both a local and a global (FE/Exodus) formulation as separate solvers; the global path is a build option and is documented as command-line-only. Its `CameraSystem` allows up to 10 cameras in code, but no >2-camera user workflow is published.</sub><br/>
<sub>⁴ Subset-based operation is uncontested in the literature and implied by the subset-size / step-size controls, but Correlated Solutions publishes no verbatim algorithmic statement.</sub><br/>
<sub>⁵ MatchID's own wording for its 2D and Stereo modules; quoted rather than paraphrased.</sub><br/>
<sub>⁶ VIC-3D's calibration stack (coded targets with automatic spacing detection, Variable Ray Origin calibration, speckle-based refinement, non-parametric distortion fields for stereo microscopes) is materially ahead of every open-source entry here, including this one.</sub><br/>
<sub>⁷ DICe documents robust strain calculation for discontinuities and high gradients — that is strain post-processing, not crack-aware correlation.</sub><br/>
<sub>⁸ MatchID is the only tool in this set with a first-class fracture module (crack detection, crack opening displacement, Williams' series and J-integrals for crack-tip location and stress intensity factors). It answers a different question than the crack-aware *correlation* above, and it answers it well.</sub><br/>
<sub>Sources: project repositories, vendor documentation and release pages. **Last verified: 2026-07-31.** Corrections are welcome — <a href="https://github.com/zachtong/pyALDIC-3D/issues/new/choose">open an issue</a>.</sub>

---

## Accuracy

The method is peer-reviewed; this application is the Python implementation of it.

- **Tong, Z. & Yang, J.** *3D Stereo Adaptive Mesh Augmented Lagrangian Digital Image Correlation.* **Experimental Mechanics** (2025). [doi:10.1007/s11340-025-01225-7](https://doi.org/10.1007/s11340-025-01225-7)  _— the stereo AL-DIC method this application implements._
- **Yang, J. & Bhattacharya, K.** *Augmented Lagrangian Digital Image Correlation.* **Experimental Mechanics** 59, 187–205 (2019). [doi:10.1007/s11340-018-00457-0](https://doi.org/10.1007/s11340-018-00457-0)  _— the original AL-DIC formulation._
- **Tong, Z. & Yang, J.** *pyALDIC: A Python Implementation of Augmented Lagrangian Digital Image Correlation…* **arXiv:2607.22755** (2026)  _— the 2D platform whose correlation engine this application consumes; preprint, under review._

**What has been measured here**, against independent references rather than against
itself (full protocols and reports live in [`docs/architecture/00_INDEX.md`](docs/architecture/00_INDEX.md)):

| Benchmark | Reference | Result |
|---|---|---|
| MATLAB parity, real stereo pair (Challenge 1.0 S3) | the MATLAB 3D-Stereo-ALDIC baseline | median difference **U 1.2 µm · V 1.0 µm · W 5.8 µm**; static-surface Z 30 µm |
| Incremental tracking, real data | per-point template-matching truth | **0.38 / 0.43 px** median |
| Rigid translation, ±10/20 mm steps (Challenge 1.0 S2) | exact analytic truth | median error **0.3 µm / 0.1 µm** on the two lens setups; noise floor (0.37, 0.43, 0.98) µm |
| D-specimen tension (Challenge 1.0 S4) | MatchID Stereo export | tension axis **0.5 µm** median at 4 mm (0.012%) |
| Stereo-DIC Challenge 2.0, Task 1 (elastic frames)ᵃ | DICe export + the official strain anchor | pixel displacement **0.003–0.015 px** median over 11,300 points/frame; **ε_yy = 0.269% vs the 0.26% anchor** |
| Built-in calibration on a real 66-pair coded-target set | DICe's calibration of the same images | baseline 123.672 mm vs 123.602 mm (**+0.06%**); triangulated dot pitch **7.0005 ± 0.0010 mm** against a 7 mm target |
| Real tension to fracture | load cell | 10.9% strain at 2070 lb with 98% node validity; strain noise floor **12 µε** |

<sub>ᵃ The elastic series with the provided calibration, against the shipped DICe solution and the protocol's two anchors. The full official protocol (five VSG sizes, per-pixel export, the standard coordinate system) has not been run yet.</sub>

---

## Performance

Measured end to end (tracking + honesty gate + reconstruction) on a desktop CPU:

| Sequence | Nodes | Wall clock | Per-frame tracking |
|---|---|---|---|
| 400 frames × 5 Mpx, two cameras | 11,466 | 48.4 min<sup>†</sup> | **1.02 s** median |
| 150 frames × 12 Mpx, two cameras | 27,170 | 58.9 min<sup>†</sup> | — |
| 3 frames × 2.3 Mpx (shipped sample) | 1,309 | seconds | — |

Both long runs held **100% node validity end to end**, and the final frame matched the
synthetic truth to **0.010–0.011 px** in the image plane and **0.002–0.004 mm** in 3D —
no drift over hundreds of frames. Recent work paid off where it was measured to hurt:
the honesty gate got **3.29× faster** in v1.1.0 (2.97 → 0.90 s/frame, bit-identical
results), the strain kernel is **6.5–19×** faster under Numba, and the plane-fit solve
is **5.2×** faster via batched SVD.

<sub><sup>†</sup> Measured before the v1.1.0 gate speedup; it takes roughly 27 min off the two-camera 400-frame run. The table is not re-timed, so treat these wall clocks as upper bounds.</sub>

**Memory.** Peak RSS was **5.68 GB** on the 12 Mpx / 150-frame run and 3.06 GB on the
400-frame run. Frames stream from disk behind bounded LRU caches instead of being
pre-loaded, the ZNSSD verification is evaluated in point chunks (1.4 GB → 143 MB
instantaneous), and the 3D visualization caches are capped (~15 GB unbounded → ~0.5 GB).
A **pre-run RAM check** projects the requirement and refuses to start rather than
dying at frame 300; it currently under-projects by ~20%, which stays inside its own
70%-of-RAM budget.

---

## Quick Start

### Installation

Requires Python ≥ 3.10. A bare install is **full-featured** — the desktop GUI (PySide6)
and the interactive 3D view (PyVista/VTK) ship alongside the headless compute stack.

**From PyPI** (recommended):

```bash
conda create -n pyaldic3d python=3.12 && conda activate pyaldic3d   # or a venv
pip install al-dic-3d
```

**Windows, no Python:** a self-contained installer
(`pyALDIC-3D-1.1.0-win64-setup.exe`, ~197 MB — Python, Qt, VTK and all
dependencies bundled) is attached to the
[latest release](https://github.com/zachtong/pyALDIC-3D/releases/latest).
It installs per-user (no admin prompt) and registers `.aldic3d` files.
The installer is unsigned, so Windows SmartScreen shows a warning on first
run — choose *More info → Run anyway*.

**From source** (editable, with test dependencies):

```bash
git clone https://github.com/zachtong/pyALDIC-3D.git
cd pyALDIC-3D
pip install -e ".[dev]"
```

### Launch

```bash
al-dic-3d gui              # desktop application
al-dic-3d gui my.aldic3d   # …opening straight into a saved session
al-dic-3d run config.toml  # headless pipeline
al-dic-3d calibrate --help # built-in stereo calibration
```

### Try it on the shipped sample

The repo ships three synchronized stereo pairs of a speckled D-specimen (Stereo-DIC
Challenge 1.0 "Sample 3") plus a DICe-format calibration under
[`examples/Images_Stereo_Sample3_images/`](examples/Images_Stereo_Sample3_images):

```bash
al-dic-3d run examples/quickstart/config.toml -o examples/quickstart/out
```

That reconstructs the surface and computes surface strain for all three frames in
seconds, writing `quickstart.npz` / `.mat` (3D points, U/V/W/|D|, the full strain
stack, and the raw correspondence with quality and reprojection error) plus a
parameters JSON. The GUI walkthrough for the same data is in
[`examples/quickstart/README.md`](examples/quickstart/README.md).

<details>
<summary><b>Programmatic API</b></summary>

```python
from pathlib import Path

import numpy as np
from al_dic_3d.runner import RunConfig, run_pipeline, write_results

cfg = RunConfig(
    calibration_file=Path("examples/Images_Stereo_Sample3_images/cal.xml"),
    calibration_format="dice",           # or matlabcv / matchid / mmc / opencorr / opencv_yaml
    left="examples/Images_Stereo_Sample3_images/L/*_0.tif",
    right="examples/Images_Stereo_Sample3_images/R/*_1.tif",
    roi=(340, 1560, 430, 690),           # (xmin, xmax, ymin, ymax) on the LEFT frame 1
    output_dir=Path("out"),
    output_prefix="demo",
    strategy="track_both",               # or stereo_each_frame / ref_direct
    reference_mode="incremental",        # or accumulative
    winsize=32,                          # subset size, px (even)
    winstepsize=16,                      # node spacing, px (power of 2)
    stereo_search=60,
    fft_search=60,
    compute_strain=True,
    strain_size=5,                       # virtual strain gauge, in nodes
)

result = run_pipeline(cfg)

rec = result.reconstruction
print(f"{rec.n_frames} frames, {rec.points.shape[1]} nodes")
for k in range(rec.n_frames):
    mag = np.linalg.norm(rec.displacement[k], axis=1)
    print(f"frame {k}: max |D| = {np.nanmax(mag):.4f} mm, "
          f"valid {100 * np.isfinite(mag).mean():.1f}%")

# points3D (n_frames, n_pts, 3) in mm, displacement, strain, correspondence
paths = write_results(result, cfg, formats=("npz", "mat", "csv", "ply", "vtu"))
print(paths)
```

</details>

---

<details>
<summary><b>Project Structure</b></summary>

```
src/al_dic_3d/
├── calibration/    Board specs, detectors (incl. coded targets), solve, QC, bundle adjustment
├── sequence/       Lazy stereo image/mask streams with bounded caches
├── matching/       Correspondence strategies, temporal tracking, honesty gate, crack mesh
├── reconstruct/    DLT triangulation, 3D outlier rejection, Reconstruction3D
├── strain3d/       Plane fit → Green–Lagrange, coordinate frames, edge trim, crack exclusion
├── viz3d/          Qt-free dense field rendering, surface construction, mask warping
├── export/         NPZ/MAT/CSV/PLY/VTU, field images, animations, 3D renders
├── project/        AppState3D and the .aldic3d session format
├── gui/            PySide6 desktop application (panels, controllers, dialogs, widgets)
├── i18n/           8-locale translation sources and compiled catalogues
├── runner.py       RunConfig / run_pipeline / write_results — the headless entry point
└── cli.py          `al-dic-3d` console script (run · gui · calibrate)

tests/              67 test files, 687 tests
tools/marketing/    Generators for every figure in this README (headless, reproducible)
```

The compute modules (`calibration`, `sequence`, `matching`, `reconstruct`, `strain3d`,
`export`) are **Qt-free** and enforced so by an architecture test; only `viz3d`, `gui`
and `i18n` may touch Qt or OpenGL.

</details>

<details>
<summary><b>Testing</b></summary>

```bash
pytest                                   # everything (687 tests)
pytest -n auto                           # parallel
pytest tests/test_parity_gate.py         # the MATLAB-parity gates
ruff check . && ruff format .
```

CI runs the full suite on **Windows, macOS and Linux** against **Python 3.10 and 3.12**
(six jobs), with Qt in offscreen mode.

</details>

---

## About the Authors

pyALDIC-3D is developed in [Dr. Jin Yang's group](https://sites.utexas.edu/jyang/) at
**The University of Texas at Austin**.

Beyond the software itself, the authors have contributed to community-wide DIC standards:

- **Jin Yang** — co-editor of *A Good Practices Guide for Digital Image Correlation*,
  **1st edition** (2018) and **2nd edition** (2025), published by the International
  Digital Image Correlation Society (iDICs).
- **Zixiang Tong** — co-editor of *A Good Practices Guide for Digital Image
  Correlation*, **2nd edition** (2025).

---

## Community

pyALDIC-3D and pyALDIC-2D come from the same lab and share their real-time channels;
issues and discussions are per-project.

### 💬 Async forum (English + 中文)

[**GitHub Discussions**](https://github.com/zachtong/pyALDIC-3D/discussions) — the
long-form, searchable home for stereo-DIC questions.

- [Q&A](https://github.com/zachtong/pyALDIC-3D/discussions/categories/q-a) — how do I use pyALDIC-3D for X?
- [Ideas](https://github.com/zachtong/pyALDIC-3D/discussions/categories/ideas) — feature proposals and design talk
- [Show and tell](https://github.com/zachtong/pyALDIC-3D/discussions/categories/show-and-tell) — share your experiments and figures
- [Announcements](https://github.com/zachtong/pyALDIC-3D/discussions/categories/announcements) — release notes and news

Both **English** and **中文** posts are welcome; please tag Chinese posts with `[中文]`
in the title.

### ⚡ Real-time chat (shared with pyALDIC-2D)

| Audience | Platform | Join |
|---|---|---|
| 🌍 International | Discord | [**discord.gg/Uh9RXvZt6n**](https://discord.gg/Uh9RXvZt6n) |
| 🇨🇳 中文用户 | QQ 群 | 群号 `1061177356` |

### 🐛 Bug reports

[**GitHub Issues**](https://github.com/zachtong/pyALDIC-3D/issues/new/choose) — the
template asks for the version, your OS, and the LOG panel's saved output. Usage
questions belong in Discussions.

This is young software meeting real-world setups for the first time; reports of
*"it broke on my machine/data"* are exactly what make it robust, and a small shareable
dataset that reproduces the problem is the fastest path to a fix.

### 📧 Private consulting

For research collaboration, confidential data, or one-on-one consulting:
**zachtong@utexas.edu**.

---

## Documentation

- **User guide** — [`docs/user-guide/`](docs/user-guide/index.md): overview, installation,
  calibration, ROI, running, strain, export, sessions, troubleshooting.
- **Architecture & decision baseline** — [`docs/architecture/00_INDEX.md`](docs/architecture/00_INDEX.md):
  technical baseline, correspondence-strategy study, decision log, full changelog.
- **Reference notes** — [`docs/COORDINATES.md`](docs/COORDINATES.md),
  [`docs/strain3d_math.md`](docs/strain3d_math.md),
  [`docs/DEPENDS_ON_2D.md`](docs/DEPENDS_ON_2D.md),
  [`docs/RELEASING.md`](docs/RELEASING.md).

---

## Citation

pyALDIC-3D has its **own scholarly identity**, independent of the 2D project. Citation
metadata ships in [`CITATION.cff`](CITATION.cff) (GitHub renders a *"Cite this
repository"* button from it), every version is archived on Zenodo under the concept DOI
[**10.5281/zenodo.21696564**](https://doi.org/10.5281/zenodo.21696564), and a standalone
*SoftwareX* article is forthcoming.

```bibtex
@software{tong2026pyaldic3dsoftware,
  author  = {Tong, Zixiang},
  title   = {pyALDIC-3D: stereo / 3D Digital Image Correlation built on the
             pyALDIC platform},
  year    = {2026},
  url     = {https://github.com/zachtong/pyALDIC-3D},
  version = {1.1.0},
  doi     = {10.5281/zenodo.21696564}
}
```

Please also cite the method, the MATLAB reference it ports, and the 2D engine it builds on:

```bibtex
@article{tong2025stereoaldic,
  author  = {Tong, Zixiang and Yang, Jin},
  title   = {3D Stereo Adaptive Mesh Augmented Lagrangian Digital Image Correlation},
  journal = {Experimental Mechanics},
  year    = {2025},
  doi     = {10.1007/s11340-025-01225-7}
}

@article{yang2019aldic,
  author  = {Yang, Jin and Bhattacharya, Kaushik},
  title   = {Augmented Lagrangian Digital Image Correlation},
  journal = {Experimental Mechanics},
  volume  = {59},
  pages   = {187--205},
  year    = {2019},
  doi     = {10.1007/s11340-018-00457-0}
}

@article{tong2026pyaldic,
  author  = {Tong, Zixiang and Yang, Jin},
  title   = {pyALDIC: A Python Implementation of Augmented Lagrangian Digital
             Image Correlation with a GUI, Adaptive Meshing, and Mask-Aware
             Subset Splitting},
  journal = {arXiv preprint arXiv:2607.22755},
  year    = {2026},
  doi     = {10.48550/arXiv.2607.22755},
  url     = {https://arxiv.org/abs/2607.22755}
}
```

The last entry is a **preprint under review**, not peer-reviewed yet.
*The SoftwareX article citation will be added here when available.*

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Every figure in
this README is generated by a script under `tools/marketing/`, so it can be
reproduced (and corrected) from the shipping code.

## Acknowledgments

pyALDIC-3D follows the MATLAB
**[3D-Stereo-ALDIC](https://github.com/zachtong/3D-Stereo-ALDIC)** reference and builds
on the **[pyALDIC](https://github.com/zachtong/pyALDIC)** 2D platform (the `al-dic`
package, likewise BSD-3-Clause), which it consumes as a pinned, read-only library for
the underlying correlation engine. Developed at **The University of Texas at Austin**.

## License

BSD 3-Clause. See [LICENSE](LICENSE).
