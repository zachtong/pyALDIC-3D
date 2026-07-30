# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for pyALDIC-3D — onedir bundle with two executables.

Build (from the repo root, inside the ``pyaldic3d`` environment)::

    python -m PyInstaller --noconfirm \
        --distpath packaging/dist --workpath packaging/build \
        packaging/pyaldic3d.spec

or simply run ``packaging/build_installer.ps1`` which drives this spec and
then compiles the Inno Setup installer.

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
  ``module_collection_mode='pyz+py'`` for ``al_dic`` / ``al_dic_3d``.
* **Do NOT ship prebuilt numba caches** — ``collect_data_files`` picks up
  ``__pycache__/*.nbc/*.nbi`` from the dev machine; ``.nbc`` object code is
  compiled for the *build* CPU and can crash older machines with illegal
  instructions. ``_keep_data`` filters them out.
* **matplotlib** — used Agg-only (colorbar/printout renderers); the hook is
  told to keep just the Agg backend instead of collecting every backend.
"""

import sys
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
]

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
    binaries=[],
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
# Binary filter: never bundle a third-party ICU next to Qt.
#
# PySide6's Qt6Core.dll statically imports UNSUFFIXED ICU symbols
# ("ucnv_open") and is designed to resolve them from the Windows-supplied
# %SystemRoot%\System32\icuuc.dll (present since Win10 1703; our installer
# requires Win10+). A conda/vcpkg ICU picked up from the build machine's PATH
# exports version-SUFFIXED symbols ("ucnv_open_73") instead — if bundled, it
# shadows the system DLL inside _internal and Qt dies at load time with
# "DLL load failed while importing QtWidgets: The specified procedure could
# not be found" (verified with pefile on this exact failure). Dropping the
# DLLs lets the loader fall through to System32.
# --------------------------------------------------------------------------
_BANNED_BINARIES = {"icuuc.dll", "icudt73.dll", "icuin.dll", "icudt.dll"}


def _drop_banned(binaries):
    return [b for b in binaries if b[0].lower() not in _BANNED_BINARIES]


a_gui.binaries = _drop_banned(a_gui.binaries)
a_cli.binaries = _drop_banned(a_cli.binaries)

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
