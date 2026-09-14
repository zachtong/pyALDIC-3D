# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for pyALDIC-3D — onedir bundle with two executables.

Build with ``packaging/build_installer.ps1``: it creates a clean venv from the
pinned ``packaging/requirements-build.txt``, drives this spec, runs the frozen
self-test and compiles the Inno Setup installer (CI runs the same script, see
``.github/workflows/build-exe.yml``). By hand, from the repo root and inside
such a venv::

    python -m PyInstaller --noconfirm \
        --distpath packaging/dist --workpath packaging/build/pyinstaller \
        packaging/pyaldic3d.spec

Produces ``packaging/dist/pyALDIC-3D/`` containing:

* ``pyALDIC-3D.exe``    — windowed GUI (no console window),
* ``pyaldic3d-cli.exe`` — console CLI (``run`` / ``calibrate`` / ``gui``),
* ``_internal/``        — shared Python runtime, Qt, VTK, numba, OpenCV, data.

Design notes (the hard parts, spelled out):

* **Two Analyses, one COLLECT** — the documented PyInstaller pattern for
  multiple executables sharing a single onedir tree. COLLECT de-duplicates
  binaries/data by destination name, so the ~1 GB VTK/Qt payload is shipped
  once.
* **PySide6 trimming** — the app uses QtWidgets/QtGui/QtCore (+ QtSvg for the
  theme's SVG spin arrows, + QtOpenGL(Widgets) for the VTK interactor). All
  other Qt Addons (WebEngine, Qml/Quick, Charts, Multimedia, ...) are
  explicitly excluded; WebEngine alone would add >150 MB.
* **pyvista / VTK** — handled by pyinstaller-hooks-contrib's per-module
  ``vtkmodules`` hooks (binary inter-DLL dependencies). pyvista's lazy
  ``vtkmodules.util.data_model`` / ``execution_model`` imports are pinned as
  hiddenimports (they are try/except-guarded upstream and easy to miss).
* **numba** — ``@njit(cache=True)`` kernels need (a) a writable cache dir in
  the frozen app -> ``rthook_numba.py`` sets ``NUMBA_CACHE_DIR`` to
  ``%LOCALAPPDATA%\\pyALDIC-3D\\numba_cache``; (b) the kernels' ``.py``
  sources on disk for numba's source-backed cache locator ->
  ``module_collection_mode='py'`` (source only, outside the PYZ) for
  ``al_dic`` / ``al_dic_3d`` -- the comment above ``module_collection_mode``
  below explains why ``'pyz+py'`` is not enough.
* **numba threading layer** -- ``tbbpool`` is dropped (see ``DEAD_EXTENSIONS``)
  and ``vcomp140.dll`` is bundled, so the frozen app runs on the ``omp`` layer,
  with ``workqueue`` behind it, exactly like a pip install.
* **Stray runtime DLLs** -- ICU and the Universal CRT must resolve from
  Windows, never from the bundle (``AMBIENT_DENY``; rules mirrored from the
  pyALDIC 2D spec).
* **Do NOT ship prebuilt numba caches** — ``collect_data_files`` picks up
  ``__pycache__/*.nbc/*.nbi`` from the dev machine; ``.nbc`` object code is
  compiled for the *build* CPU and can crash older machines with illegal
  instructions. ``_keep_data`` filters them out.
* **matplotlib** — used Agg-only (colorbar/printout renderers); the hook is
  told to keep just the Agg backend instead of collecting every backend.
"""

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, copy_metadata

SPEC_DIR = Path(SPECPATH).resolve()  # noqa: F821 - SPECPATH injected by PyInstaller
REPO_ROOT = SPEC_DIR.parent

APP_NAME = "pyALDIC-3D"
CLI_NAME = "pyaldic3d-cli"
ICON = str(SPEC_DIR / "assets" / "pyaldic3d.ico")


# --------------------------------------------------------------------------
# Data files
# --------------------------------------------------------------------------
def _keep_data(entry):
    """Filter one (source, dest_dir) data tuple.

    * ``__pycache__`` — dev-machine numba ``.nbc``/``.nbi`` caches are
      CPU-specific object code; shipping them risks SIGILL on older CPUs and
      they are useless once NUMBA_CACHE_DIR is redirected.
    * ``.ts`` — Qt Linguist *sources*; runtime only loads compiled ``.qm``.
    * ``pyvista/examples`` — sample datasets, not needed by the app.
    """
    src = str(entry[0]).replace("\\", "/")
    if "__pycache__" in src:
        return False
    if src.endswith(".ts"):
        return False
    if "/pyvista/examples/" in src:
        return False
    return True


datas = []
datas += collect_data_files("al_dic_3d")  # i18n compiled *.qm, py.typed
datas += collect_data_files("al_dic")  # theme SVG arrows, app icon, i18n *.qm
datas += collect_data_files("pyvista")  # themes/colormaps package data
datas = [d for d in datas if _keep_data(d)]

# pyvistaqt resolves its own version via importlib.metadata at import time.
datas += copy_metadata("pyvistaqt")

# --------------------------------------------------------------------------
# Hidden imports
# --------------------------------------------------------------------------
hiddenimports = [
    # Qt SVG: the dark theme styles QSpinBox arrows with .svg files via QSS and
    # icons render from SVG — needs the qsvg imageformat plugin, which the
    # PySide6 hook only collects when the QtSvg module is bundled.
    "PySide6.QtSvg",
    # VTK's Qt interactor (pyvistaqt QtInteractor) can require QOpenGLWidget.
    "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets",
    # pyvista >= 0.44 imports these behind try/except for VTK >= 9.4 wheels;
    # a miss degrades (or breaks) DataSet wrapping in the frozen app.
    "vtkmodules.util.data_model",
    "vtkmodules.util.execution_model",
    # Numba picks a threading backend by trying these in order, with
    # function-level imports the module graph cannot see. tbbpool is
    # deliberately absent: TBB is not a dependency of this project, the
    # environment does not provide tbb12.dll, and listing it made PyInstaller
    # satisfy the dependency from Anaconda's base environment -- which then won
    # the layer selection, so the bundle ran on a thread pool the developers
    # never tested and no user could have. omp (vcomp140.dll, bundled below) is
    # the intended layer; workqueue is the fallback. (Rule and rationale from
    # the pyALDIC 2D spec.)
    "numba.np.ufunc.omppool",
    "numba.np.ufunc.workqueue",
    "numba.np.ufunc._internal",
    "numba.np.ufunc._num_threads",
]

# --------------------------------------------------------------------------
# Binaries sourced on purpose
# --------------------------------------------------------------------------
binaries = []

# The OpenMP runtime backing numba's 'omp' threading layer. It resolves from
# System32 (the VC++ redistributable), which PyInstaller excludes from
# collection by design -- so on a machine without the redistributable,
# omppool fails to import and numba drops to 'workqueue' without saying so.
# That matters more here than in 2D: 'workqueue' aborts the process when two
# threads run parallel kernels at once, which is what the parallel-camera
# option does (the reason it is disabled on macOS). App-local deployment of
# this DLL is permitted by the redistributable licence.
_VCOMP = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "vcomp140.dll")
if os.path.isfile(_VCOMP):
    binaries.append((_VCOMP, "."))
else:  # pragma: no cover - build-machine dependent
    print(f"spec: WARNING {_VCOMP} not found; the bundle falls back to numba's workqueue layer")

# --------------------------------------------------------------------------
# Excludes — keep the bundle lean and deterministic
# --------------------------------------------------------------------------
excludes = [
    # Qt Addons the app never touches (biggest single lever on size).
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtWebChannel",
    "PySide6.QtWebSockets",
    "PySide6.QtWebView",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuickWidgets",
    "PySide6.QtQuickControls2",
    "PySide6.QtQuick3D",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DRender",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DExtras",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtGraphs",
    "PySide6.QtGraphsWidgets",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtSpatialAudio",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtPositioning",
    "PySide6.QtLocation",
    "PySide6.QtBluetooth",
    "PySide6.QtNfc",
    "PySide6.QtSensors",
    "PySide6.QtSerialPort",
    "PySide6.QtSerialBus",
    "PySide6.QtRemoteObjects",
    "PySide6.QtScxml",
    "PySide6.QtStateMachine",
    "PySide6.QtTextToSpeech",
    "PySide6.QtHelp",
    "PySide6.QtDesigner",
    "PySide6.QtUiTools",
    "PySide6.QtTest",
    "PySide6.QtSql",
    "PySide6.QtNetworkAuth",
    "PySide6.QtHttpServer",
    # Other Qt bindings qtpy would otherwise probe for.
    "PyQt5",
    "PyQt6",
    "PySide2",
    # Dev / test / notebook stacks that sneak in via optional imports.
    "tkinter",
    "pytest",
    "IPython",
    "jupyter",
    "notebook",
    "trame",
    "trame_vtk",
]

runtime_hooks = [
    str(SPEC_DIR / "rthook_numba.py"),
    str(SPEC_DIR / "rthook_qt.py"),
]

# Ship al_dic / al_dic_3d as SOURCE OUTSIDE the PYZ ('py', not 'pyz+py').
# Rationale (verified empirically on the frozen app): modules imported from
# the PYZ get a RELATIVE co_filename ("al_dic\\solver\\numba_kernels.py"), so
# numba's source-backed cache locators fail their os.path.exists(py_file)
# check (it resolves against the process CWD) and NUMBA_CACHE_DIR is silently
# ignored — numba then falls back to its frozen-app user-wide cache with a
# CWD-DEPENDENT subpath (one recompile per launch directory). Collecting these
# two packages as plain source makes Python import them from _internal with an
# absolute co_filename, so numba's UserProvidedCacheLocator engages and the
# rthook_numba.py NUMBA_CACHE_DIR redirect works deterministically.
module_collection_mode = {
    "al_dic": "py",
    "al_dic_3d": "py",
}

# matplotlib is Agg-only in this app (offscreen colorbar / calibration
# printout rendering) — do not collect the Qt/Tk/wx backends.
hooksconfig = {
    "matplotlib": {
        "backends": ["Agg"],
    },
}

common = dict(
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig=hooksconfig,
    runtime_hooks=runtime_hooks,
    excludes=excludes,
    noarchive=False,
    module_collection_mode=module_collection_mode,
)

a_gui = Analysis([str(SPEC_DIR / "launch_gui.py")], **common)
a_cli = Analysis([str(SPEC_DIR / "launch_cli.py")], **common)


# --------------------------------------------------------------------------
# Stray runtime DLLs -- rules and rationale mirrored from the pyALDIC 2D spec
# (packaging/pyaldic.spec there).
# --------------------------------------------------------------------------
# PyInstaller resolves a binary dependency by searching PATH, so any DLL the
# build machine happens to have can end up in the bundle and shadow the one
# the target machine would have used. That is not hypothetical: it broke the
# first build of this spec outright.
#
# PySide6's Qt6Core.dll is built against the ICU that ships in Windows'
# System32, which exports UNVERSIONED symbols (ucnv_open). A standard ICU
# build -- Anaconda's, for one -- exports VERSIONED symbols (ucnv_open_73) and
# nothing else. Collecting the latter into the bundle shadowed System32's
# copy, so Qt6Core could not resolve ucnv_open and every PySide6 import died
# with "DLL load failed while importing QtWidgets: The specified procedure
# could not be found" (verified with pefile on this exact failure). The
# application never got a window; nothing was logged; nothing named ICU.
#
# Windows 10 1703 and later always provide System32's ICU (the installer
# requires Windows 10+), so dropping these is safe as well as necessary.
# Must resolve from Windows, never from the bundle.
#
# The Universal CRT (ucrtbase.dll plus the api-ms-win-* forwarders) is an
# operating-system component from Windows 10 onward, kept current by Windows
# Update. Shipping it is only necessary for Windows 7 and 8.1.
#
# Leaving it collectible makes the bundle's contents depend on which unrelated
# toolchain happens to sit on the build machine's PATH: a conda environment
# supplies one copy, and a GitHub Windows runner supplies a different one from
# the bundled Temurin JDK. Neither belongs to pyALDIC-3D, and the difference is
# invisible until it is not. Dropping them makes the build reproducible across
# machines.
AMBIENT_DENY = (
    "icuuc", "icuin", "icudt", "icuio",
    "ucrtbase", "api-ms-win",
)

# Dead weight that decides behaviour if it is allowed to load. numba ships
# tbbpool.pyd inside its package, so PyInstaller collects it as an ordinary
# binary whatever hiddenimports says, and tbbpool.pyd imports tbb12.dll. The
# pinned build venv has no tbb12.dll -- `from numba.np.ufunc import tbbpool`
# raises ImportError there -- so PyInstaller satisfies it from whatever is on
# PATH (Anaconda's base installation, in 2D's case). The bundle would then
# select 'tbb' as its threading layer: a thread pool nobody has tested, that no
# user of the wheel would ever get. Dropping the extension leaves 'omp'
# (vcomp140.dll, bundled above) with 'workqueue' behind it, which is what the
# source install uses.
DEAD_EXTENSIONS = ("tbbpool", "tbb12")

# Not mirrored from 2D (yet): its DEAD_QT_LIBS list (Qt6Network, Qt6Pdf,
# Qt6Qml, Qt6Quick, ...) was verified against the PE import tables of 2D's Qt
# set; the 3D bundle adds Qt6OpenGL(Widgets) and VTK, which have not been
# audited. Likewise 2D's refusal to build when any other binary resolves from
# outside the build environment -- port it once a 3D build has been audited.


def _drop_unwanted(binaries):
    """Remove DLLs that must resolve from the OS or must not load at all."""
    kept, dropped = [], []
    for entry in binaries:
        name = os.path.basename(entry[0]).lower()
        unwanted = name.startswith(AMBIENT_DENY) or name.startswith(DEAD_EXTENSIONS)
        (dropped if unwanted else kept).append(entry)
    for entry in dropped:
        print(f"spec: dropping {entry[0]} <- {entry[1]}")
    return kept


a_gui.binaries = _drop_unwanted(a_gui.binaries)
a_cli.binaries = _drop_unwanted(a_cli.binaries)

pyz_gui = PYZ(a_gui.pure)
pyz_cli = PYZ(a_cli.pure)

exe_gui = EXE(
    pyz_gui,
    a_gui.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    icon=ICON,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX-packed Qt/VTK DLLs are a known crash + AV-flag source
    console=False,  # windowed: no console flash for GUI users
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

exe_cli = EXE(
    pyz_cli,
    a_cli.scripts,
    [],
    exclude_binaries=True,
    name=CLI_NAME,
    icon=ICON,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # headless batch users need stdout/stderr + exit codes
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe_gui,
    a_gui.binaries,
    a_gui.datas,
    exe_cli,
    a_cli.binaries,
    a_cli.datas,
    strip=False,
    upx=False,
    name=APP_NAME,
)
