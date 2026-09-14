# packaging/ — standalone Windows installer pipeline

Turns the pyALDIC-3D source tree into a double-clickable Windows installer for
users **without any Python installation** (the typical MATLAB / commercial-DIC
audience). Two stages:

1. **PyInstaller** freezes the app into a self-contained *onedir* bundle
   (`packaging/dist/pyALDIC-3D/`) with two executables:
   - `pyALDIC-3D.exe` — the desktop GUI (windowed, no console),
   - `pyaldic3d-cli.exe` — the console CLI (`run`, `calibrate`, `self-test`, ...).
2. **Inno Setup 6** wraps that bundle into a per-user installer
   (`pyALDIC-3D-<version>-win64-setup.exe`) with Start-menu entries, an
   optional desktop icon, an optional `.aldic3d` file association, and a clean
   uninstaller.

The build is reproducible: the same pinned environment, the same script and the
same checks run on a maintainer's machine and in CI.

## Quick start

From any PowerShell (no admin needed), with a Python 3.12+ on `PATH`:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_installer.ps1
```

That is the whole build. Useful options: `-Python <python.exe>` (base
interpreter, default: the `python` on `PATH`), `-Clean` (re-create the venv and
rebuild from scratch), `-SkipFreeze` (reuse the existing onedir, recompile only
the installer), `-SkipInstaller` (freeze and self-test only), `-VenvDir <dir>`,
`-Iscc <ISCC.exe>`. `Get-Help packaging\build_installer.ps1 -Detailed` lists
them all.

## What the script does

| Step | What happens | Fails the build when |
| --- | --- | --- |
| **venv** | Creates a clean venv (default `%LOCALAPPDATA%\pyALDIC-3D-build\venv`) from the base interpreter, installs the pinned `requirements-build.txt`, then this repository with `--no-deps`, and records the full `pip freeze` in the log. The venv is reused until `requirements-build.txt` changes. | the interpreter is missing or older than 3.12, or an install fails |
| **freeze** | Runs PyInstaller on `pyaldic3d.spec` with the build environment's own DLL directories first on `PATH`, and prints the missing-import / missing-library warnings PyInstaller would otherwise bury in several thousand log lines. | PyInstaller fails |
| **self-test** | Runs the frozen `pyaldic3d-cli.exe --version` (must equal the source version) and `pyaldic3d-cli.exe self-test` from a working directory whose name contains spaces and non-ASCII characters. | either command fails |
| **installer** | Compiles `installer.iss` with a pinned Inno Setup (downloaded once, SHA-256-verified, installed in portable mode under `packaging\tools\` — no admin rights, no registry entries) and writes a `.sha256` next to the installer. | the download does not match its checksum, or ISCC fails |

Every run writes a timestamped log to `packaging\build\logs\build-<timestamp>.log`
(gitignored) with every command, its full output, and the environment it built
from.

The venv lives outside the repository on purpose: site-packages nests deep
enough to exceed Windows' 260-character path limit under a long checkout path
(long-path support is off by default), and ~1.5 GB of small files do not
belong in a OneDrive-synced folder.

### The pinned environment

`requirements-build.txt` pins every library whose version decides what the
bundle contains, PyInstaller and its hooks included. Its header explains how to
refresh the pins; the rule is that a pin moves only together with a build whose
self-test passes. Build from a **python.org** interpreter (CI uses
`actions/setup-python`); a conda interpreter works but is warned about, because
conda's `Library\bin` DLLs can leak into the bundle.

### The frozen self-test

`pyaldic3d-cli.exe self-test` is the application's own end-to-end check of the
frozen bundle (implemented in `al_dic_3d`, not here): one line per check, exit
code 0 when every check passes and 1 when any fails, `--json` for a machine
report. A bundle can start and still have lost a feature silently (a missing
plugin, catalog or DLL), so "it launches" is not the gate — the self-test is.
Because the build runs it with its output piped and from a non-ASCII working
directory, the self-test must survive both. On CI runners, which have no
OpenGL 3.2 context, the workflow sets `ALDIC3D_SELFTEST_SKIP_GL=1`.

## CI: `.github/workflows/build-exe.yml`

Runs on every `v*` tag push, and on demand (`workflow_dispatch`):

- **tag push** — builds with `build_installer.ps1` on `windows-latest`
  (Python 3.12), then silently installs the installer into a temp folder, runs
  the installed CLI, uninstalls, and checks that the files are gone. The
  installer and its `.sha256` are kept as a workflow artifact and attached to
  the GitHub Release of the tag once `publish.yml` has created it (the attach
  job waits up to 30 minutes for that).
- **dispatch with a tag** — the same, e.g. to re-attach after a failed run.
- **dispatch without a tag** — build and test only; use it to check a pin bump
  before tagging.

The build log is uploaded as an artifact on every run, failed or not. The
installer workflow is separate from `publish.yml` so that an installer failure
never blocks the PyPI release.

## Files in this directory

| file | role |
| --- | --- |
| `build_installer.ps1` | the one-command build described above (local and CI). |
| `requirements-build.txt` | the pinned build environment. |
| `pyaldic3d.spec` | PyInstaller spec: two Analyses (GUI + CLI) merged into one `COLLECT` onedir; Qt-module excludes; stray-DLL rules; numba threading layer; data collection for `al_dic` + `al_dic_3d` (i18n `.qm`, theme SVGs, icons). |
| `launch_gui.py` | frozen entry for `pyALDIC-3D.exe` (windowed; forwards `.aldic3d` argv). |
| `launch_cli.py` | frozen entry for `pyaldic3d-cli.exe` (console). |
| `rthook_numba.py` | runtime hook: `NUMBA_CACHE_DIR` → `%LOCALAPPDATA%\pyALDIC-3D\numba_cache` (the install dir is read-only; JIT caches must live somewhere writable). |
| `rthook_qt.py` | runtime hook: `QT_API=pyside6` so qtpy/pyvistaqt never probe for other bindings. |
| `installer.iss` | Inno Setup 6 script (per-user default, `.aldic3d` association task, online user-guide shortcut). The version is injected with `/DMyAppVersion`. |
| `extract_changelog.py` | prints one version's `CHANGELOG.md` section; `publish.yml` uses it as the GitHub release body. |
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
    (`module_collection_mode='py'`). PYZ-imported modules carry a *relative*
    `co_filename`, numba's source-backed cache locators then fail their
    existence check, `NUMBA_CACHE_DIR` is silently ignored, and numba falls
    back to a frozen-app user-wide cache whose subpath depends on the launch
    CWD (one full recompile per new working directory);
  - dev-machine `__pycache__/*.nbc|*.nbi` artifacts are **filtered out**:
    `.nbc` holds object code compiled for the *build* CPU and can crash older
    machines (illegal instruction). The first analysis on a user machine
    JIT-compiles once, then loads from the cache;
  - the threading layer is **omp**, as in a pip install: numba's `tbbpool`
    extension is dropped (it would pull in whatever `tbb12.dll` sits on the
    build machine's `PATH`) and `vcomp140.dll` is bundled, so machines without
    the VC++ runtime do not fall back to `workqueue` — which aborts when two
    threads run parallel kernels at once (the parallel-camera option).
- **Stray runtime DLLs** (rules mirrored from the pyALDIC 2D spec): ICU
  (`icuuc`/`icuin`/`icudt`/`icuio`) and the Universal CRT (`ucrtbase`,
  `api-ms-win-*`) are never bundled — they must resolve from Windows. A
  third-party ICU shadows the System32 one PySide6 is built against and kills
  every Qt import; a bundled UCRT makes the build depend on which toolchain
  happened to be on the build machine's `PATH`.
- **OpenCV**: `opencv-python` freezes cleanly via PyInstaller's built-in `cv2`
  hook.
- **i18n**: compiled `.qm` catalogs for both `al_dic_3d` and the reused
  `al_dic` widgets are collected as package data (`.ts` sources excluded).
- **matplotlib**: Agg backend only (colorbar / calibration-printout
  rendering) via the hook's `backends` option.
- **Not shipped**: example datasets. The markdown user guide is installed as an
  offline copy under `{app}\docs\user-guide`; the Start-menu *User Guide*
  entry opens the online guide on GitHub.

## The installer

- **Per-user by default** (`PrivilegesRequired=lowest`): installs under
  `%LOCALAPPDATA%\Programs\pyALDIC-3D`, no UAC prompt — the common case on
  university lab machines. An all-users install can still be chosen thanks to
  `PrivilegesRequiredOverridesAllowed=dialog` (or forced with `/ALLUSERS` on
  the command line).
- **Silent install / uninstall** (for IT deployment; CI does exactly this):

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

The build produces **unsigned** binaries (buying a certificate was evaluated
and declined for now: the academic audience accepts the SmartScreen prompt, as
for other unsigned DIC tools). On current Windows this means:

- Browsers (Edge/Chrome) may flag the downloaded `-setup.exe` as
  "not commonly downloaded".
- **Microsoft Defender SmartScreen shows "Windows protected your PC"** on
  first run; users must click *More info → Run anyway*. Expect a fraction of
  non-technical users to stop there — document the two clicks in release
  notes (screenshot helps).
- Some institutional AV/application-allowlisting setups block unsigned
  executables outright; those users need IT to whitelist the file hash (the
  published `.sha256` helps).

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

# 3) sign the installer itself (then regenerate its .sha256)
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

Automated by `build_installer.ps1` (and therefore by CI):

1. PyInstaller exits 0 and `packaging/dist/pyALDIC-3D/` exists.
2. The frozen CLI reports the source version (`--version`).
3. The frozen `self-test` exits 0, run from a non-ASCII working directory.
4. The installer compiles with the pinned Inno Setup.

Automated by `build-exe.yml` only:

5. Silent install into a temp folder, the installed CLI runs, silent
   uninstall, the files are gone.

Still manual, before announcing a release:

6. `pyALDIC-3D.exe` boots to the main window on a real desktop, and a small
   dataset runs end to end (a second run must reuse the numba cache —
   `%LOCALAPPDATA%\pyALDIC-3D\numba_cache` is populated and startup is faster).

## Size expectations

The onedir bundle is dominated by VTK + Qt + numpy/scipy/OpenCV/numba/
matplotlib: about **824 MB unpacked** and a **~197 MB** LZMA2/max-compressed
installer as of 1.0.0–1.1.0. Sizes for the current build are printed at the
end of `build_installer.ps1`; if the bundle suddenly grows, diff
`packaging/build/pyinstaller/pyaldic3d/xref-pyaldic3d.html` against the
previous build to find the new import.

## Troubleshooting

- **The self-test fails** → the failing checks are printed above the error and
  in the build log; in CI, download the `build-log` artifact.
- **`ModuleNotFoundError` in the frozen app only** → a lazy/dynamic import
  PyInstaller could not see; add it to `hiddenimports` in the spec. The
  "Reported by PyInstaller" block at the end of the freeze step lists the
  hidden imports it could not find.
- **`[Errno 2] No such file or directory` deep inside site-packages while the
  venv is created** → Windows' 260-character path limit. Keep `-VenvDir`
  short (the default is), or enable long paths
  (`LongPathsEnabled` in the registry, admin).
- **Blank/black 3D view on old machines** → OpenGL <3.2 drivers; Qt falls
  back to `opengl32sw.dll` (bundled) for widgets, but VTK needs real GL 3.2+;
  advise updating GPU drivers.
- **numba warning "cannot cache function"** → the `.py` sources are missing
  (`module_collection_mode`) or the cache dir is not writable (rthook). Both
  are configured here; if it reappears after a dependency bump, re-check.
- **Qt "could not find or load the Qt platform plugin 'windows'"** → the
  `_internal/PySide6/plugins/platforms` folder was stripped by AV quarantine
  or a bad copy; reinstall.
- **Inno Setup download fails** (proxy/offline) → install Inno Setup 6
  manually from <https://jrsoftware.org/isdl.php> and pass
  `-Iscc "<install dir>\ISCC.exe"` (its version is then not verified).
- **SHA-256 mismatch for the Inno Setup download** → do not bypass it. The
  pinned checksum is the one GitHub publishes for that release asset; a
  mismatch means a corrupted or tampered download.
- **`PermissionError: Access is denied` while clearing `dist\`** → OneDrive is
  syncing the previous build output and holds file locks. The script retries;
  if it still fails, pause OneDrive sync (or mark `packaging\dist` and
  `packaging\build` as excluded / "Free up space") and re-run.
- **`DLL load failed while importing pyexpat` (or `_lzma`, `_bz2`, `_ctypes`)
  in the frozen app** → DLLs were picked up from a *different* Python
  installation via `PATH`. The script puts the build environment's own DLL
  directories first; if you invoke PyInstaller by hand, do it from an
  activated build venv.
- **`DLL load failed while importing QtWidgets: The specified procedure could
  not be found`** → a third-party ICU got bundled next to Qt, shadowing the
  Windows ICU that PySide6's Qt6Core links against. The spec's `AMBIENT_DENY`
  rule drops ICU for exactly this reason — keep it when upgrading PySide6.
