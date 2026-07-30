# 2. Installation & launching

pyALDIC-3D requires **Python 3.10 or newer**. It is distributed as the PyPI
package `al-dic-3d` (import name `al_dic_3d`, console script `al-dic-3d`).

## Runtime dependencies and the 2D-engine pin

The core compute layer depends only on `numpy`, `scipy`,
`opencv-python-headless`, and the pinned 2D engine:

```
al-dic == 0.7.*
```

pyALDIC-3D consumes pyALDIC-2D as a **pinned, read-only library**. It is not a
"3D mode" inside the 2D app — it is a separate application that calls the 2D
correlation engine. In CI and for end users the pin resolves from PyPI; during
development you satisfy the same `==0.7.*` constraint with an editable install of
the sibling 2D repo (see below).

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
`pre-commit`, `matplotlib`) is for running the test suite and report tooling.

## Development install (from source)

pyALDIC-3D is developed alongside the sibling 2D repo. Satisfy the `al-dic`
pin from the sibling source, then install this package editable:

```bash
pip install -e ../pyALDIC          # 2D engine, editable (reports 0.7.x)
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

prints, for the tree this guide documents:

```
al-dic-3d 1.0.0
```

## The command-line interface at a glance

`al-dic-3d` exposes three sub-commands. The GUI is only one of them; the whole
pipeline is scriptable headless.

```
al-dic-3d <command> ...

commands:
  run        run a headless correspondence + 3D-reconstruction pipeline from a TOML config
  gui        launch the graphical workflow (requires PySide6)
  calibrate  built-in stereo calibration from board image pairs
```

- **`al-dic-3d run config.toml`** — the headless pipeline: load calibration +
  image sequences per a TOML config, run the correspondence strategy and DLT
  reconstruction, and write the selected `--formats` (plus a parameters JSON)
  under the config's output directory. Flags: `-o/--output DIR` (override the
  output directory), `-q/--quiet` (suppress per-frame progress), and
  `--formats LIST` (comma list of `npz,mat,csv,ply,vtu`; default `npz,mat`).
  Every GUI parameter has a `config.toml` key — see the tables in
  [Workflow type](05-workflow-type.md), [Parameters](08-parameters.md), and
  [Initial guess](06-initial-guess.md).
- **`al-dic-3d calibrate ...`** — the built-in stereo calibrator, documented in
  [Calibration](04-calibration.md).
- **`al-dic-3d gui`** — the desktop application, the subject of the rest of this
  guide.

Next: [Loading stereo images →](03-loading-images.md)
