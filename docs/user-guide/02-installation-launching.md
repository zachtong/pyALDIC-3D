# 2. Installation & launching

pyALDIC-3D requires **Python 3.10 or newer**. It is distributed as the PyPI
package `al-dic-3d` (import name `al_dic_3d`, console script `al-dic-3d`).

## What it is built on

pyALDIC-3D is a **separate application**, not a "3D mode" inside the 2D app: it
calls the pyALDIC 2D correlation engine (distributed as the `al-dic` package) as
a library. That engine, and everything else it needs, installs automatically —
the exact version pin lives in `pyproject.toml`, so nothing here needs to be
installed by hand.

## What a bare install includes

Since v1.0.0 a plain `pip install al-dic-3d` is **full-featured**: the desktop
GUI (PySide6), the interactive **3D View** (pyvista/VTK), and the headless
compute stack all ship together — there is nothing extra to install for the
normal desktop workflow:

```bash
pip install al-dic-3d
```

GUI and 3D imports are lazy, so the same install still works headless (CI,
servers, `al-dic-3d run` / `calibrate`) even where Qt or OpenGL cannot
initialize — the 3D View degrades to an explanatory placeholder instead of
crashing.

The historical `[gui]` / `[viz3d]` extras remain as no-op compatibility
aliases for older instructions. `[dev]` (`pytest`, `pytest-xdist`, `ruff`,
`pre-commit`, `psutil`, `h5py`) is for running the test suite and the report tooling.

Only one OpenCV package may be installed: `opencv-python` (a dependency) or
`opencv-python-headless`, not both — they overwrite each other's `cv2`.
OpenCV 4.7 and later work, as does 5.x.

### Windows installer

The Windows installer bundles everything, Python included. Windows SmartScreen
may warn that the publisher is unknown the first time: choose *More info* >
*Run anyway*. The installed application writes a log file (see
[Troubleshooting](14-troubleshooting.md)); to watch the output live, start
`pyaldic3d-cli.exe gui` from a terminal instead of the Start-menu entry.

## Development install (from source)

pyALDIC-3D is developed alongside the sibling 2D repo. Satisfy the `al-dic`
pin from the sibling source, then install this package editable:

```bash
pip install -e ../pyALDIC          # 2D engine, editable (0.7.2 up to 0.8.x)
pip install -e ".[dev]"            # this package + pytest/ruff/pre-commit
pre-commit install                 # optional: enable hooks
```

## Launching the GUI

```bash
al-dic-3d gui
# or equivalently
python -m al_dic_3d gui
```

Both open the pyALDIC-3D desktop application. `al-dic-3d gui` accepts an
optional session path to open at startup:

```bash
al-dic-3d gui path/to/project.aldic3d
```

If PySide6 is somehow missing (a stripped custom install), the command prints
`the GUI requires PySide6: ...` and exits with a non-zero code — PySide6 ships
with every normal install of the package.

## Opening a `.aldic3d` project

There are three ways to open a saved project (see [Sessions](13-session.md) for
the file format):

1. **From the GUI** — *File → Open Project*.
2. **From the command line** — `al-dic-3d gui path/to/project.aldic3d`.
3. **By double-clicking** in the file manager — the Windows file association
   launches `python -m al_dic_3d "<file>"`. A bare `*.aldic3d` first argument is
   automatically rewritten to the `gui` sub-command, so double-click opens the
   project directly.

## Checking the version

```bash
al-dic-3d --version
```

prints the name and the installed version, for example:

```
al-dic-3d 1.1.0
```

To check that an installation works end to end — images and videos in
folders with non-ASCII names, the translations, the compiled kernels, a small
stereo run, an offscreen 3D render — run:

```bash
al-dic-3d self-test            # one line per check; exit code 0 = all passed
al-dic-3d self-test --json report.json
```

## The command-line interface at a glance

`al-dic-3d` exposes five sub-commands. The GUI is only one of them; the whole
pipeline is scriptable headless.

```
al-dic-3d <command> ...

commands:
  run        run a headless correspondence + 3D-reconstruction pipeline from a TOML config
  gui        launch the graphical workflow (requires PySide6)
  calibrate  built-in stereo calibration from board image pairs
  demo       write a small synthetic stereo dataset (images, calibration, config.toml)
  self-test  check that this installation works end to end
```

- **`al-dic-3d run config.toml`** — the headless pipeline: load calibration +
  image sequences per a TOML config, run the correspondence strategy and DLT
  reconstruction, and write the selected `--formats` (plus a parameters JSON)
  under the config's output directory. Flags: `-o/--output DIR` (override the
  output directory), `-q/--quiet` (suppress per-frame progress), and
  `--formats LIST` (comma list of `npz,mat,csv,ply,vtu`; default `npz,mat`).
  Every GUI parameter has a `config.toml` key — see the tables in
  [Workflow type](05-workflow-type.md), [Parameters](08-parameters.md), and
  [Initial guess](06-initial-guess.md). The first **Ctrl+C** finishes the frame
  in flight and writes the frames computed so far (exit code 130); a second
  Ctrl+C aborts. If one output format fails (for example a MAT variable over
  MATLAB's 2 GB limit), the other formats are still written and the command
  exits with code 1.
- **`al-dic-3d demo OUT`** — writes a synthetic stereo dataset with analytic
  ground truth into `OUT` (a distorted convergent camera pair, its calibration
  and a ready `config.toml`) and prints the command to run it; `--run` also
  runs it and reports the accuracy. `--frames N` and `--size PX` set the size.
- **`al-dic-3d self-test`** — the installation check above.
- **`al-dic-3d calibrate ...`** — the built-in stereo calibrator, documented in
  [Calibration](04-calibration.md).
- **`al-dic-3d gui`** — the desktop application, the subject of the rest of this
  guide.

Next: [Loading stereo images →](03-loading-images.md)
