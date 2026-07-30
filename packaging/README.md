# packaging/ — standalone Windows installer pipeline

Turns the pyALDIC-3D source tree into a double-clickable Windows installer for
users **without any Python installation** (the typical MATLAB / commercial-DIC
audience). Two-stage pipeline:

1. **PyInstaller** freezes the app into a self-contained *onedir* bundle
   (`packaging/dist/pyALDIC-3D/`) with two executables:
   - `pyALDIC-3D.exe` — the desktop GUI (windowed, no console),
   - `pyaldic3d-cli.exe` — the console CLI for headless `run` / `calibrate`.
2. **Inno Setup 6** wraps that bundle into a per-user installer
   (`pyALDIC-3D-<version>-win64-setup.exe`) with Start-Menu entries, an
   optional desktop icon, an optional `.aldic3d` file association, the
   markdown user guide, and a clean uninstaller.

## Quick start

From a "x64 Native"-agnostic PowerShell (no admin needed):

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_installer.ps1
```

That is the whole build. The script:

1. picks the Python interpreter (`-Python <path>`, else `$env:PYALDIC3D_PYTHON`,
   else the `pyaldic3d` conda env, else `python`) and verifies it can import
   `al_dic_3d` and `PyInstaller`;
2. reads the version from `src/al_dic_3d/__init__.py` (single source of truth);
3. runs PyInstaller with `packaging/pyaldic3d.spec` (several minutes — Qt + VTK);
4. smoke-tests the frozen CLI (`pyaldic3d-cli.exe --help` must exit 0);
5. locates `ISCC.exe` (PATH, `%LOCALAPPDATA%\Programs\InnoSetup6`, Program
   Files, `packaging/tools/InnoSetup6`) — and if absent **bootstraps Inno Setup
   6 automatically**: downloads the pinned official release from
   `github.com/jrsoftware/issrc/releases` and silently installs it per-user
   under `%LOCALAPPDATA%\Programs\InnoSetup6` (no admin);
6. compiles `packaging/installer.iss` and prints the onedir + installer sizes.

Flags: `-SkipFreeze` (reuse existing onedir, only recompile the installer),
`-SkipInstaller` (freeze only), `-Clean` (full PyInstaller rebuild).

### One-time environment prerequisites

```powershell
# inside the pyaldic3d environment
pip install -e ".[dev]"           # the app itself (al-dic resolves per pyproject)
pip install pyinstaller pyinstaller-hooks-contrib
```

Known-good versions (what this pipeline was verified with): Python 3.12,
PyInstaller 6.21, pyinstaller-hooks-contrib 2026.6, PySide6 6.11, pyvista
0.48 / VTK 9.6, numba 0.66, Inno Setup 6.7.3.

## Files in this directory

| file | role |
| --- | --- |
| `pyaldic3d.spec` | PyInstaller spec: two Analyses (GUI + CLI) merged into one `COLLECT` onedir; Qt-module excludes; vtkmodules/numba handled by hooks; data collection for `al_dic` + `al_dic_3d` (i18n `.qm`, theme SVGs, icons). |
| `launch_gui.py` | frozen entry for `pyALDIC-3D.exe` (windowed; forwards `.aldic3d` argv). |
| `launch_cli.py` | frozen entry for `pyaldic3d-cli.exe` (console). |
| `rthook_numba.py` | runtime hook: `NUMBA_CACHE_DIR` → `%LOCALAPPDATA%\pyALDIC-3D\numba_cache` (the install dir is read-only; JIT caches must live somewhere writable). |
| `rthook_qt.py` | runtime hook: `QT_API=pyside6` so qtpy/pyvistaqt never probe for other bindings. |
| `installer.iss` | Inno Setup 6 script (per-user default, `.aldic3d` association task, user-guide links). |
| `build_installer.ps1` | the one-command driver described above. |
| `assets/pyaldic3d.ico` | multi-resolution app icon (16–256 px, currently the shared pyALDIC family icon; drop in a 3D-specific `.ico` here to rebrand). |

## What the frozen bundle contains (and why)

- **PySide6**: only the Qt modules actually imported (QtCore/QtGui/QtWidgets +
  QtSvg for the themed SVG spin arrows + QtOpenGL(Widgets) for the VTK
  interactor). WebEngine, Qml/Quick, Charts, Multimedia, PDF, 3D, sensors,
  etc. are excluded in the spec — re-adding any of them is a one-line change.
- **pyvista / VTK**: `pyinstaller-hooks-contrib` ships per-`vtkmodules.*`
  hooks that resolve VTK's inter-DLL dependencies. Two lazily imported helper
  modules (`vtkmodules.util.data_model`, `vtkmodules.util.execution_model`)
  are pinned as hidden imports.
- **numba** (strain kernel + 2D engine ICGN kernels, `@njit(cache=True)`):
  - the cache is redirected to `%LOCALAPPDATA%\pyALDIC-3D\numba_cache` at
    process start (see `rthook_numba.py`) — the install dir must be treated
    as read-only;
  - `al_dic` / `al_dic_3d` are collected as **plain source outside the PYZ**
    (`module_collection_mode='py'`). This matters: PYZ-imported modules carry
    a *relative* `co_filename`, numba's source-backed cache locators then fail
    their existence check, `NUMBA_CACHE_DIR` is silently ignored, and numba
    falls back to a frozen-app user-wide cache whose subpath depends on the
    launch CWD (one full recompile per new working directory). Source-on-disk
    collection gives absolute `co_filename`s and deterministic caching;
  - dev-machine `__pycache__/*.nbc|*.nbi` artifacts are **filtered out** of
    the bundle: `.nbc` holds object code compiled for the *build* CPU and can
    crash older machines (illegal instruction). First run on a user machine
    JIT-compiles once (adds ~40–60 s to the first analysis), then caches
    (verified: warm run ~5x faster, cache survives across CWDs).
- **OpenCV**: `opencv-python(-headless)` freezes cleanly via PyInstaller's
  built-in `cv2` hook; no special handling needed.
- **i18n**: compiled `.qm` catalogs for both `al_dic_3d` and the reused
  `al_dic` widgets are collected as package data (`.ts` sources excluded).
- **matplotlib**: Agg backend only (colorbar / calibration-printout
  rendering) via the hook's `backends` option.
- **Not shipped**: the example dataset (`examples/Images_Stereo_Sample3_images`,
  size) — the user guide points to the GitHub repo for it. The markdown user
  guide *is* installed (`{app}\docs\user-guide`) with Start-Menu links to the
  local copy and to the online copy.

## The installer

- **Per-user by default** (`PrivilegesRequired=lowest`): installs under
  `%LOCALAPPDATA%\Programs\pyALDIC-3D`, no UAC prompt — the common case on
  university lab machines. An all-users install can still be chosen thanks to
  `PrivilegesRequiredOverridesAllowed=dialog` (or forced with
  `/ALLUSERS` on the command line).
- **Silent install / uninstall** (for IT deployment or CI):

  ```powershell
  pyALDIC-3D-<ver>-win64-setup.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
  # optional: /DIR="D:\apps\pyALDIC-3D"  /TASKS="desktopicon,fileassoc"  /LOG="install.log"
  # uninstall:
  "%LOCALAPPDATA%\Programs\pyALDIC-3D\unins000.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
  ```

- **`.aldic3d` association** (optional task, default on): double-clicking a
  session file opens it in the GUI.
- **Uninstall** removes the app, the association, and the per-user numba
  cache (`%LOCALAPPDATA%\pyALDIC-3D\numba_cache`).
- `AppId` in `installer.iss` is the upgrade identity — **never change it**, or
  Windows will treat a new release as a different product.

## Code signing and SmartScreen — the honest reality

The build produces **unsigned** binaries. On current Windows this means:

- Browsers (Edge/Chrome) may flag the downloaded `-setup.exe` as
  "not commonly downloaded".
- **Microsoft Defender SmartScreen shows "Windows protected your PC"** on
  first run; users must click *More info → Run anyway*. Expect a fraction of
  non-technical users to stop there — document the two clicks in release
  notes (screenshot helps).
- Some institutional AV/application-allowlisting setups block unsigned
  executables outright; those users need IT to whitelist the file hash.

### Options, roughly by cost

| option | cost (order of magnitude) | SmartScreen effect |
| --- | --- | --- |
| ship unsigned | free | warning until enough download reputation accrues *per release file* (resets every release) |
| **OV code-signing certificate** (Sectigo, Certum, GlobalSign, SSL.com…) | ~$70–250 / yr (Certum "Open Source" ≈ €69/yr is the budget favourite for academic/OSS) | signed + publisher name shown, but reputation still builds per *certificate* — warnings typically fade days-to-weeks after enough installs |
| **EV code-signing certificate** | ~$250–500 / yr + hardware token / cloud HSM | historically immediate SmartScreen reputation; since 2023 Microsoft has weakened the "instant" guarantee, but EV still reaches quiet status far faster |
| **Azure Trusted Signing** (Microsoft's signing service) | ~$9.99 / month | Microsoft-managed cert + timestamping; good SmartScreen standing; requires an Azure tenant and (for individuals) identity validation; currently the best value if eligible |

Since June 2023 CA/B-Forum rules require OV/EV private keys in hardware
(token or HSM), so all options are effectively token- or cloud-based signing.

### Exact signing procedure (once you have a certificate)

Sign **both executables and the installer** (the installer alone is not
enough — users can launch the inner exes directly, and AVs inspect them):

```powershell
# Windows SDK signtool; /fd+/td SHA-256, RFC-3161 timestamp is MANDATORY
# (signature must outlive certificate expiry).
$ts = "http://timestamp.digicert.com"        # any RFC-3161 TSA works

# 1) sign the frozen exes BEFORE compiling the installer
signtool sign /sha1 <CERT-THUMBPRINT> /fd SHA256 /tr $ts /td SHA256 `
    packaging\dist\pyALDIC-3D\pyALDIC-3D.exe `
    packaging\dist\pyALDIC-3D\pyaldic3d-cli.exe

# 2) rebuild only the installer over the signed payload
powershell -File packaging\build_installer.ps1 -SkipFreeze

# 3) sign the installer itself
signtool sign /sha1 <CERT-THUMBPRINT> /fd SHA256 /tr $ts /td SHA256 `
    packaging\dist\pyALDIC-3D-<ver>-win64-setup.exe

# 4) verify
signtool verify /pa /all packaging\dist\pyALDIC-3D-<ver>-win64-setup.exe
```

With a token-based cert, `/sha1 <thumbprint>` selects the cert from the
token's store (the vendor's CSP prompts for the PIN). With Azure Trusted
Signing, replace `signtool sign` with the `Invoke-TrustedSigning` module or
`signtool` + the Trusted Signing dlib per Microsoft's docs. Steps 1–3 can
also be automated inside Inno Setup via `SignTool=` directives, but the
explicit sequence above is easier to debug.

## Verification gate (what "it works" means here)

`build_installer.ps1` enforces step 1; the rest is the release checklist:

1. PyInstaller build exits 0 and `packaging/dist/pyALDIC-3D/` exists.
2. `pyaldic3d-cli.exe --help` exits 0 (proves the frozen import graph).
3. `pyaldic3d-cli.exe run <config>` on a small dataset with `[strain] enabled`
   completes and writes `.npz`/`.mat` — this exercises OpenCV, the 2D engine,
   numba JIT (first run) **and** the numba cache (second run must log
   *"loading cached kernels"* faster startup; check
   `%LOCALAPPDATA%\pyALDIC-3D\numba_cache` is populated).
4. `pyALDIC-3D.exe` boots to the main window (on headless CI:
   `QT_QPA_PLATFORM=offscreen` + watchdog — alive after 10 s means the import
   graph and Qt plugin loading are sound).
5. Installer: silent install into a temp dir, run the installed CLI smoke,
   silent uninstall, confirm the dir is gone.

## Size expectations

The onedir bundle is dominated by VTK + Qt + numpy/scipy/OpenCV/numba/
matplotlib. Measured for v1.0.0 (Python 3.12, PySide6 6.11, VTK 9.6):
**824 MB unpacked**, **196 MB** LZMA2/max-compressed installer. Sizes for the
current build are printed at the end of `build_installer.ps1`; if the bundle
suddenly grows, diff `packaging/build/pyaldic3d/xref-pyaldic3d.html` against
the previous build to find the new import.

## Troubleshooting

- **`ModuleNotFoundError` in the frozen app only** → a lazy/dynamic import
  PyInstaller could not see; add it to `hiddenimports` in the spec.
- **Blank/black 3D view on old machines** → OpenGL <3.2 drivers; Qt falls
  back to `opengl32sw.dll` (bundled) for widgets, but VTK needs real GL 3.2+;
  advise updating GPU drivers.
- **numba warning "cannot cache function"** → the `.py` sources are missing
  (module_collection_mode) or the cache dir is not writable (rthook). Both
  are configured here; if it reappears after a dependency bump, re-check.
- **Qt "could not find or load the Qt platform plugin 'windows'"** → the
  `_internal/PySide6/plugins/platforms` folder was stripped by AV quarantine
  or a bad copy; reinstall.
- **Inno bootstrap fails** (proxy/offline) → install Inno Setup 6 manually
  from <https://jrsoftware.org/isdl.php> and re-run; any of the probed
  locations (see above) is accepted, or put it on `PATH`.
- **`PermissionError: Access is denied` while PyInstaller clears `dist\`** →
  OneDrive is syncing the previous build output and holds file locks. Delete
  `packaging\dist\pyALDIC-3D` manually (retry once OneDrive settles) and
  re-run, or pause OneDrive sync during builds. (`packaging/dist` and
  `packaging/build` are gitignored; marking them "Free up space"/excluded in
  OneDrive avoids this entirely.)
- **`DLL load failed while importing pyexpat` (or `_lzma`, `_bz2`, `_ctypes`)
  in the frozen app** → the build picked DLLs from a *different* conda
  installation via PATH. `build_installer.ps1` guards against this by
  prepending the build env's `Library\bin`; if you invoke PyInstaller by hand,
  activate the env first (`conda activate pyaldic3d`).
- **`DLL load failed while importing QtWidgets: The specified procedure could
  not be found`** → a third-party ICU (conda/vcpkg, version-suffixed exports
  like `ucnv_open_73`) got bundled next to Qt, shadowing the Windows System32
  ICU (unsuffixed exports) that PySide6's Qt6Core actually links against. The
  spec's `_BANNED_BINARIES` filter drops `icuuc.dll`/`icudt*.dll` for exactly
  this reason — keep it when upgrading PySide6.
