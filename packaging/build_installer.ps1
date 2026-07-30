<#
.SYNOPSIS
    One-command build of the pyALDIC-3D standalone Windows installer.

.DESCRIPTION
    Pipeline: PyInstaller onedir freeze -> frozen smoke test -> Inno Setup
    installer compile. Outputs land in packaging\dist\:

        packaging\dist\pyALDIC-3D\                       (onedir bundle)
        packaging\dist\pyALDIC-3D-<ver>-win64-setup.exe  (installer)

    The app version is read from src\al_dic_3d\__init__.py (single source of
    truth). If the Inno Setup compiler (ISCC.exe) is not found, it is
    bootstrapped automatically: the official installer is downloaded from
    jrsoftware.org and silently installed per-user under
    %LOCALAPPDATA%\Programs\InnoSetup6 (no admin needed).

.PARAMETER Python
    Python interpreter of the environment that has al-dic-3d + PyInstaller
    installed. Defaults to $env:PYALDIC3D_PYTHON, then the project conda env,
    then plain "python".

.PARAMETER SkipFreeze
    Reuse an existing packaging\dist\pyALDIC-3D\ (only recompile installer).

.PARAMETER SkipInstaller
    Stop after the PyInstaller freeze + smoke test.

.PARAMETER Clean
    Pass --clean to PyInstaller (full rebuild, slower).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File packaging\build_installer.ps1
#>
[CmdletBinding()]
param(
    [string]$Python = "",
    [switch]$SkipFreeze,
    [switch]$SkipInstaller,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$PackagingDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $PackagingDir

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Fail($msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }

# ---------------------------------------------------------------- python ---
if (-not $Python) {
    if ($env:PYALDIC3D_PYTHON) {
        $Python = $env:PYALDIC3D_PYTHON
    } elseif (Test-Path "$env:USERPROFILE\anaconda3\envs\pyaldic3d\python.exe") {
        $Python = "$env:USERPROFILE\anaconda3\envs\pyaldic3d\python.exe"
    } else {
        $Python = "python"
    }
}
Write-Step "Python: $Python"
& $Python -c "import al_dic_3d, PyInstaller; print('al-dic-3d', al_dic_3d.__version__, '| PyInstaller', PyInstaller.__version__)"
if ($LASTEXITCODE -ne 0) {
    Fail "This Python cannot import al_dic_3d + PyInstaller. Run: pip install -e `".[gui,viz3d]`" pyinstaller pyinstaller-hooks-contrib"
}

# ---------------------------------------------------------------- version ---
$initPy = Join-Path $RepoRoot "src\al_dic_3d\__init__.py"
$m = Select-String -Path $initPy -Pattern '__version__\s*=\s*"([^"]+)"'
if (-not $m) { Fail "cannot read __version__ from $initPy" }
$Version = $m.Matches[0].Groups[1].Value
Write-Step "Building pyALDIC-3D $Version"

$DistDir = Join-Path $PackagingDir "dist"
$OneDir = Join-Path $DistDir "pyALDIC-3D"

# ----------------------------------------------------------------- freeze ---
if (-not $SkipFreeze) {
    Write-Step "PyInstaller onedir freeze (this takes several minutes: VTK + Qt)"
    # CRITICAL (conda environments): PyInstaller resolves DLL dependencies of
    # compiled extensions through PATH. If a *base* Anaconda's Library\bin is
    # on PATH ahead of this env's, mismatched DLLs (libexpat, liblzma, ffi,
    # icu*, tbb12, ...) get bundled and the frozen app dies at import time
    # ("DLL load failed while importing pyexpat"). Prepend this interpreter's
    # own env directories so its DLLs always win, exactly like `conda activate`.
    $pyExe = (Get-Command $Python).Source
    $pyHome = Split-Path -Parent $pyExe
    $env:PATH = "$pyHome;$pyHome\Library\bin;$pyHome\Scripts;$pyHome\DLLs;" + $env:PATH
    # OneDrive-synced repos: the sync client holds locks on the previous dist
    # output and PyInstaller's own cleanup then dies with PermissionError.
    # Pre-delete with retries so the freeze starts from a clean slate.
    if (Test-Path $OneDir) {
        foreach ($i in 1..6) {
            try { Remove-Item -Recurse -Force -Confirm:$false $OneDir -ErrorAction Stop; break }
            catch { Write-Host "  dist locked (OneDrive?), retry $i/6 ..."; Start-Sleep -Seconds 5 }
        }
        if (Test-Path $OneDir) { Fail "cannot delete $OneDir (file locks); pause OneDrive sync and retry" }
    }
    $piArgs = @(
        "-m", "PyInstaller", "--noconfirm",
        "--distpath", $DistDir,
        "--workpath", (Join-Path $PackagingDir "build")
    )
    if ($Clean) { $piArgs += "--clean" }
    $piArgs += (Join-Path $PackagingDir "pyaldic3d.spec")
    & $Python @piArgs
    if ($LASTEXITCODE -ne 0) { Fail "PyInstaller build failed" }
} elseif (-not (Test-Path $OneDir)) {
    Fail "-SkipFreeze given but $OneDir does not exist"
}

# ------------------------------------------------------------- smoke test ---
Write-Step "Frozen smoke test: pyaldic3d-cli.exe --help"
# NOTE: do NOT pipe the exe into Select-Object -First — closing the pipeline
# early sends the exe a broken pipe and turns exit 0 into -1 (false negative).
$helpOut = & (Join-Path $OneDir "pyaldic3d-cli.exe") --help
if ($LASTEXITCODE -ne 0) { Fail "frozen CLI --help failed (exit $LASTEXITCODE)" }
$helpOut | Select-Object -First 3

$oneDirMB = [math]::Round((Get-ChildItem $OneDir -Recurse -File | Measure-Object -Sum Length).Sum / 1MB, 1)
Write-Host "onedir size: $oneDirMB MB"

if ($SkipInstaller) { Write-Step "Done (freeze only)."; exit 0 }

# ------------------------------------------------------------- find ISCC ----
Write-Step "Locating Inno Setup 6 compiler (ISCC.exe)"
$iscc = $null
$cmd = Get-Command "iscc.exe" -ErrorAction SilentlyContinue
if ($cmd) { $iscc = $cmd.Source }
if (-not $iscc) {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\InnoSetup6\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        (Join-Path $PackagingDir "tools\InnoSetup6\ISCC.exe")
    )
    foreach ($c in $candidates) { if ($c -and (Test-Path $c)) { $iscc = $c; break } }
}
if (-not $iscc) {
    Write-Step "ISCC not found - bootstrapping Inno Setup 6 (per-user, no admin)"
    # Official binaries are published on the jrsoftware GitHub releases page
    # (jrsoftware.org/download.php serves an HTML page, not the exe). Pinned
    # version; bump deliberately after checking the Inno Setup changelog.
    $innoVer = "6.7.3"
    $innoUrl = "https://github.com/jrsoftware/issrc/releases/download/is-$($innoVer -replace '\.', '_')/innosetup-$innoVer.exe"
    $isDl = Join-Path $env:TEMP "innosetup-$innoVer.exe"
    Invoke-WebRequest -Uri $innoUrl -OutFile $isDl -UseBasicParsing
    $isDir = "$env:LOCALAPPDATA\Programs\InnoSetup6"
    Start-Process -FilePath $isDl -ArgumentList "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CURRENTUSER", "/DIR=`"$isDir`"" -Wait
    $iscc = Join-Path $isDir "ISCC.exe"
    if (-not (Test-Path $iscc)) { Fail "Inno Setup bootstrap failed; install manually from https://jrsoftware.org/isdl.php" }
}
Write-Host "ISCC: $iscc"

# -------------------------------------------------------- compile installer -
Write-Step "Compiling installer"
& $iscc "/DMyAppVersion=$Version" "/O$DistDir" (Join-Path $PackagingDir "installer.iss")
if ($LASTEXITCODE -ne 0) { Fail "ISCC compile failed" }

$setupExe = Join-Path $DistDir "pyALDIC-3D-$Version-win64-setup.exe"
$setupMB = [math]::Round((Get-Item $setupExe).Length / 1MB, 1)

Write-Step "Done."
Write-Host "  onedir:    $OneDir ($oneDirMB MB)"
Write-Host "  installer: $setupExe ($setupMB MB)"
Write-Host ""
Write-Host "NOTE: the installer is UNSIGNED - Windows SmartScreen will warn on"
Write-Host "first download/run. See packaging\README.md for signing options."
