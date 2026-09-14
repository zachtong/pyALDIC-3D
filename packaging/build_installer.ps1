<#
.SYNOPSIS
    Reproducible build of the pyALDIC-3D standalone Windows installer.

.DESCRIPTION
    Pipeline -- every step is logged to packaging\build\logs\build-<timestamp>.log:

      1. venv        A clean venv (%LOCALAPPDATA%\pyALDIC-3D-build\venv by
                     default) is created from the interpreter given by -Python
                     and filled from the pinned packaging\requirements-build.txt,
                     then this repository is installed into it with --no-deps.
                     The venv is re-created whenever requirements-build.txt
                     changes (or with -Clean); the full `pip freeze` goes into
                     the log.
      2. freeze      PyInstaller runs packaging\pyaldic3d.spec (onedir), with
                     the build environment's own DLL directories first on PATH.
      3. self-test   The frozen pyaldic3d-cli.exe must report the source
                     version (--version) and pass `self-test` (exit code 0),
                     run from a working directory whose name contains spaces
                     and non-ASCII characters. Any failure stops the build.
      4. installer   Inno Setup compiles packaging\installer.iss. The compiler
                     is a pinned, SHA-256-verified Inno Setup release, installed
                     once in portable mode under packaging\tools\ (no admin
                     rights, no registry entries), unless -Iscc names one.

    Outputs in packaging\dist\:
        pyALDIC-3D\                                 onedir bundle
        pyALDIC-3D-<ver>-win64-setup.exe            installer
        pyALDIC-3D-<ver>-win64-setup.exe.sha256     its checksum

    CI runs this same script (.github/workflows/build-exe.yml). The version is
    read from src\al_dic_3d\__init__.py, the single source of truth.

.PARAMETER Python
    Base interpreter for the build venv. Must be Python 3.12+ (the pins in
    requirements-build.txt need it). Default: the `python` on PATH. A
    python.org / setup-python interpreter is the reference; conda works but
    is warned about.

.PARAMETER VenvDir
    Where the build venv lives. Default: %LOCALAPPDATA%\pyALDIC-3D-build\venv,
    deliberately outside the repository: site-packages nests deep enough to
    exceed Windows' 260-character path limit under a long checkout path (long
    paths are off by default), and ~1.5 GB of small files do not belong in a
    OneDrive-synced folder.

.PARAMETER Iscc
    Use this ISCC.exe instead of the pinned portable Inno Setup (for example
    offline or behind a proxy). Its version is not verified.

.PARAMETER SkipFreeze
    Reuse the existing packaging\dist\pyALDIC-3D\ (the self-test still runs).

.PARAMETER SkipInstaller
    Stop after the freeze and the self-test.

.PARAMETER Clean
    Re-create the build venv and pass --clean to PyInstaller (full rebuild).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File packaging\build_installer.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File packaging\build_installer.ps1 -Python C:\Python312\python.exe -Clean
#>
[CmdletBinding()]
param(
    [string]$Python = "python",
    [string]$VenvDir = "",
    [string]$Iscc = "",
    [switch]$SkipFreeze,
    [switch]$SkipInstaller,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
# Invoke-WebRequest is an order of magnitude slower with the progress bar on
# Windows PowerShell 5.1.
$ProgressPreference = "SilentlyContinue"

# ----------------------------------------------------------------- layout ---
$PackagingDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $PackagingDir
$BuildDir = Join-Path $PackagingDir "build"
$LogDir = Join-Path $BuildDir "logs"
$WorkDir = Join-Path $BuildDir "pyinstaller"
$DistDir = Join-Path $PackagingDir "dist"
$OneDir = Join-Path $DistDir "pyALDIC-3D"
$SpecFile = Join-Path $PackagingDir "pyaldic3d.spec"
$IssFile = Join-Path $PackagingDir "installer.iss"
$ReqFile = Join-Path $PackagingDir "requirements-build.txt"
if (-not $VenvDir) {
    # Short and unsynced -- see the VenvDir help above.
    $venvRoot = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { $BuildDir }
    $VenvDir = Join-Path $venvRoot "pyALDIC-3D-build\venv"
}

# requirements-build.txt pins numpy 2.5 / scipy 1.18, which need Python 3.12.
$MinPython = [version]"3.12"

# Pinned Inno Setup. The checksum is the one GitHub publishes for this release
# asset (jrsoftware/issrc, tag is-6_7_3), verified independently on download.
# Bump the three values together, after reading the Inno Setup changelog.
$InnoVersion = "6.7.3"
$InnoUrl = "https://github.com/jrsoftware/issrc/releases/download/is-6_7_3/innosetup-6.7.3.exe"
$InnoSha256 = "9C73C3BAE7ED48D44112A0F48E66742C00090BDB5BEF71D9D3C056C66E97B732"
$InnoDir = Join-Path $PackagingDir "tools\InnoSetup-$InnoVersion"

# PyInstaller log lines worth reading back out of several thousand: a missing
# hidden import is only a WARNING, and the bundle it produces starts and then
# fails somewhere specific.
$PyInstallerFlags = [regex]'^\d+ WARNING: (Hidden import .* not found|Library not found|Cannot find |lib not found)|^\d+ ERROR:|^spec: '

# ---------------------------------------------------------------- logging ---
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir ("build-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".log")
$script:LogWriter = New-Object System.IO.StreamWriter($LogFile, $true, (New-Object System.Text.UTF8Encoding($false)))
$script:LogWriter.AutoFlush = $true
$script:Flagged = New-Object System.Collections.ArrayList
$script:LastOutput = New-Object System.Collections.ArrayList
$Started = Get-Date

function Write-Log([string]$Text) {
    if ($script:LogWriter) { $script:LogWriter.WriteLine($Text) }
}

function Close-Log {
    if ($script:LogWriter) {
        $script:LogWriter.Dispose()
        $script:LogWriter = $null
    }
}

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
    Write-Log ""
    Write-Log ("[{0:HH:mm:ss}] ==> {1}" -f (Get-Date), $Message)
}

function Write-Info([string]$Message) {
    Write-Host $Message
    Write-Log $Message
}

function Stop-Build([string]$Message) {
    Write-Host "ERROR: $Message" -ForegroundColor Red
    Write-Log "ERROR: $Message"
    Write-Host "build log: $LogFile"
    Close-Log
    exit 1
}

# Anything that escapes as a terminating error still lands in the log.
trap {
    Write-Log ("ERROR: " + $_.Exception.Message)
    Write-Log $_.ScriptStackTrace
    Write-Host ("ERROR: " + $_.Exception.Message) -ForegroundColor Red
    Write-Host "build log: $LogFile"
    Close-Log
    exit 1
}

function Invoke-Logged {
    <#
        Run a native command, stream its merged stdout/stderr to the console
        and the log, keep the lines in $script:LastOutput, and return the exit
        code. Lines matching -Flag are also collected in $script:Flagged.
    #>
    param(
        [Parameter(Mandatory = $true)] [string]$FilePath,
        [string[]]$ArgumentList = @(),
        [string]$WorkingDirectory = "",
        [regex]$Flag = $null
    )
    Write-Log ("> " + $FilePath + " " + ($ArgumentList -join " "))
    $script:LastOutput.Clear()
    # Native stderr (PyInstaller logs there) must not become a terminating
    # error under $ErrorActionPreference = Stop (Windows PowerShell 5.1).
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    if ($WorkingDirectory) { Push-Location -LiteralPath $WorkingDirectory }
    try {
        # Never cut this pipeline short (e.g. Select-Object -First): closing it
        # early hands the process a broken pipe and turns exit 0 into -1.
        & $FilePath @ArgumentList 2>&1 | ForEach-Object {
            $line = "$_"
            Write-Host $line
            Write-Log $line
            [void]$script:LastOutput.Add($line)
            if ($Flag -and $Flag.IsMatch($line)) { [void]$script:Flagged.Add($line) }
        }
        return $LASTEXITCODE
    }
    finally {
        if ($WorkingDirectory) { Pop-Location }
        $ErrorActionPreference = $previous
    }
}

function Remove-Tree([string]$Path) {
    # OneDrive-synced repos: the sync client holds locks on the previous build
    # output, and a plain delete then dies with PermissionError. Retry.
    if (-not (Test-Path -LiteralPath $Path)) { return }
    foreach ($i in 1..6) {
        try {
            Remove-Item -LiteralPath $Path -Recurse -Force -Confirm:$false -ErrorAction Stop
            return
        }
        catch {
            Write-Info "  $Path is locked (OneDrive?), retry $i/6 ..."
            Start-Sleep -Seconds 5
        }
    }
    Stop-Build "cannot delete $Path (file locks); pause OneDrive sync and retry"
}

function Get-DirectorySizeMB([string]$Path) {
    $sum = (Get-ChildItem -LiteralPath $Path -Recurse -File | Measure-Object -Sum Length).Sum
    return [math]::Round($sum / 1MB, 1)
}

# ------------------------------------------------------------ interpreter ---
function Resolve-BasePython {
    $cmd = Get-Command $Python -ErrorAction SilentlyContinue
    if (-not $cmd) {
        Stop-Build "Python interpreter '$Python' not found; pass -Python <path to python.exe> (3.12+)"
    }
    $exe = $cmd.Source
    $probe = "import os, sys; v = sys.version_info; " +
        "print('%d.%d.%d' % (v[0], v[1], v[2])); print(sys.base_prefix); " +
        "print(os.path.isdir(os.path.join(sys.base_prefix, 'conda-meta')))"
    $code = Invoke-Logged -FilePath $exe -ArgumentList @("-c", $probe)
    if ($code -ne 0 -or $script:LastOutput.Count -lt 3) {
        Stop-Build "'$exe' is not a working Python (exit $code). The Microsoft Store alias in WindowsApps is not; pass -Python <path to python.exe>."
    }
    $pyVersion = [version]$script:LastOutput[0]
    if ($pyVersion -lt $MinPython) {
        Stop-Build "Python $pyVersion at $exe is too old: requirements-build.txt needs $MinPython or newer."
    }
    if ($script:LastOutput[2] -eq "True") {
        Write-Info ("note: '$exe' is a conda Python. Conda DLLs can leak into the bundle; " +
            "a python.org interpreter (what CI uses) is the reference build environment.")
    }
    Write-Info "base interpreter: $exe (Python $pyVersion)"
    return $exe
}

# ------------------------------------------------------------------ venv ----
function Initialize-BuildVenv([string]$BasePython) {
    $venvPython = Join-Path $VenvDir "Scripts\python.exe"
    $stampFile = Join-Path $VenvDir "requirements-build.sha256"
    $reqHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $ReqFile).Hash
    $stale = $true
    if (-not $Clean -and (Test-Path -LiteralPath $venvPython) -and (Test-Path -LiteralPath $stampFile)) {
        $stale = ((Get-Content -LiteralPath $stampFile -Raw).Trim() -ne $reqHash)
    }

    if ($stale) {
        Write-Step "Creating the build venv from requirements-build.txt ($VenvDir)"
        # Only ever delete what is recognisably a venv (or nothing at all): a
        # mistyped -VenvDir must not wipe an unrelated folder.
        if (Test-Path -LiteralPath $VenvDir) {
            $isVenv = Test-Path -LiteralPath (Join-Path $VenvDir "pyvenv.cfg")
            $isEmpty = -not (Get-ChildItem -LiteralPath $VenvDir -Force | Select-Object -First 1)
            if (-not ($isVenv -or $isEmpty)) {
                Stop-Build "$VenvDir exists and is not a virtual environment; refusing to delete it. Pass another -VenvDir."
            }
        }
        Remove-Tree $VenvDir
        $code = Invoke-Logged -FilePath $BasePython -ArgumentList @("-m", "venv", $VenvDir)
        if ($code -ne 0) { Stop-Build "python -m venv failed (exit $code)" }
        $code = Invoke-Logged -FilePath $venvPython -ArgumentList @(
            "-m", "pip", "install", "--disable-pip-version-check", "--upgrade", "pip")
        if ($code -ne 0) { Stop-Build "upgrading pip in the build venv failed (exit $code)" }
        $code = Invoke-Logged -FilePath $venvPython -ArgumentList @(
            "-m", "pip", "install", "--disable-pip-version-check", "-r", $ReqFile)
        if ($code -ne 0) { Stop-Build "installing the pinned build environment failed (exit $code)" }
        Set-Content -LiteralPath $stampFile -Value $reqHash -Encoding Ascii
    }
    else {
        Write-Step "Reusing the build venv ($VenvDir): requirements-build.txt unchanged"
    }

    # The application itself, always reinstalled, never its dependencies: the
    # bundle must carry this tree on top of exactly the pinned environment.
    Write-Step "Installing this repository into the build venv (--no-deps)"
    $code = Invoke-Logged -FilePath $venvPython -ArgumentList @(
        "-m", "pip", "install", "--disable-pip-version-check", "--no-deps", "--force-reinstall", $RepoRoot)
    if ($code -ne 0) { Stop-Build "installing al-dic-3d into the build venv failed (exit $code)" }

    Write-Step "Build environment (pip freeze)"
    $code = Invoke-Logged -FilePath $venvPython -ArgumentList @("-m", "pip", "freeze", "--all")
    if ($code -ne 0) { Stop-Build "pip freeze failed (exit $code)" }
    return $venvPython
}

# ---------------------------------------------------------------- freeze ----
function Invoke-Freeze([string]$VenvPython) {
    Write-Step "PyInstaller onedir freeze (several minutes: VTK + Qt)"
    # PyInstaller resolves the DLL dependencies of compiled extensions through
    # PATH, so the build machine's PATH decides what lands in the bundle. Put
    # the build environment's own directories first (including the base
    # interpreter's, since a venv's stdlib DLLs live there), exactly like an
    # activated environment; the spec drops the known strays (ICU, UCRT, TBB).
    $code = Invoke-Logged -FilePath $VenvPython -ArgumentList @("-c", "import sys; print(sys.base_prefix)")
    if ($code -ne 0) { Stop-Build "cannot query the build venv (exit $code)" }
    $basePrefix = $script:LastOutput[0].Trim()
    # @() keeps a single surviving entry an array (not a string) for the join.
    $front = @(@(
            (Join-Path $VenvDir "Scripts"),
            $basePrefix,
            (Join-Path $basePrefix "DLLs"),
            (Join-Path $basePrefix "Library\bin"),
            (Join-Path $basePrefix "Library\mingw-w64\bin"),
            (Join-Path $basePrefix "Library\usr\bin")
        ) | Where-Object { Test-Path -LiteralPath $_ })

    Remove-Tree $OneDir
    $piArgs = @("-m", "PyInstaller", "--noconfirm", "--distpath", $DistDir, "--workpath", $WorkDir)
    if ($Clean) { $piArgs += "--clean" }
    $piArgs += $SpecFile

    $savedPath = $env:PATH
    $env:PATH = (($front + @($savedPath)) -join ";")
    try {
        $code = Invoke-Logged -FilePath $VenvPython -ArgumentList $piArgs -Flag $PyInstallerFlags
    }
    finally {
        $env:PATH = $savedPath
    }
    if ($script:Flagged.Count -gt 0) {
        Write-Step "Reported by PyInstaller / the spec (review after a dependency bump)"
        foreach ($line in $script:Flagged) { Write-Info "  $line" }
    }
    if ($code -ne 0) { Stop-Build "PyInstaller failed (exit $code)" }
}

# ------------------------------------------------------------- self-test ----
function Invoke-SelfTest([string]$Version) {
    $cli = Join-Path $OneDir "pyaldic3d-cli.exe"
    if (-not (Test-Path -LiteralPath $cli)) { Stop-Build "frozen CLI not found: $cli" }

    Write-Step "Frozen CLI: pyaldic3d-cli.exe --version"
    $code = Invoke-Logged -FilePath $cli -ArgumentList @("--version")
    $reported = ($script:LastOutput -join " ").Trim()
    if ($code -ne 0 -or $reported -ne "al-dic-3d $Version") {
        Stop-Build "frozen CLI reported '$reported' (exit $code); expected 'al-dic-3d $Version'"
    }

    # The working directory is whatever launched the exe (Explorer, a
    # shortcut's "Start in", a double-clicked session), not the install folder:
    # run from one with spaces and non-ASCII characters. Built from char codes
    # so this file stays ASCII (Windows PowerShell 5.1 reads BOM-less scripts
    # in the ANSI code page).
    $hostileName = "self-test " + [char]0x81EA + [char]0x68C0 + " " + [char]0x00E9 + "t" + [char]0x00E9
    $hostileDir = Join-Path $BuildDir $hostileName
    New-Item -ItemType Directory -Force -Path $hostileDir | Out-Null

    Write-Step "Frozen self-test: pyaldic3d-cli.exe self-test (cwd: $hostileDir)"
    $code = Invoke-Logged -FilePath $cli -ArgumentList @("self-test") -WorkingDirectory $hostileDir
    if ($code -ne 0) {
        Stop-Build "frozen self-test failed (exit $code); the failing checks are listed above"
    }
    Write-Info ("onedir: {0} ({1} MB)" -f $OneDir, (Get-DirectorySizeMB $OneDir))
}

# ------------------------------------------------------------- installer ----
function Resolve-Iscc {
    if ($Iscc) {
        if (-not (Test-Path -LiteralPath $Iscc)) { Stop-Build "-Iscc $Iscc does not exist" }
        Write-Info "WARNING: using $Iscc as given; its version is not verified (pinned: Inno Setup $InnoVersion)"
        return (Resolve-Path -LiteralPath $Iscc).Path
    }
    $pinned = Join-Path $InnoDir "ISCC.exe"
    if (Test-Path -LiteralPath $pinned) { return $pinned }

    Write-Step "Bootstrapping Inno Setup $InnoVersion (portable mode: no admin, no registry)"
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    $download = Join-Path $BuildDir "innosetup-$InnoVersion.exe"
    try {
        Invoke-WebRequest -Uri $InnoUrl -OutFile $download -UseBasicParsing
    }
    catch {
        Stop-Build ("downloading $InnoUrl failed: " + $_.Exception.Message +
            ". Offline or behind a proxy: install Inno Setup $InnoVersion and pass -Iscc <path>\ISCC.exe")
    }
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $download).Hash
    if ($actual -ne $InnoSha256) {
        Remove-Item -LiteralPath $download -Force
        Stop-Build "SHA-256 mismatch for $InnoUrl (expected $InnoSha256, got $actual); refusing to run it"
    }
    Write-Info "SHA-256 verified: $actual"

    $innoArgs = @("/PORTABLE=1", "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CURRENTUSER", "/DIR=`"$InnoDir`"")
    $proc = Start-Process -FilePath $download -ArgumentList $innoArgs -Wait -PassThru
    Remove-Item -LiteralPath $download -Force
    if ($proc.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $pinned)) {
        Stop-Build "Inno Setup bootstrap failed (exit $($proc.ExitCode)); install Inno Setup $InnoVersion manually and pass -Iscc <path>\ISCC.exe"
    }
    return $pinned
}

function Invoke-Installer([string]$Version) {
    $isccPath = Resolve-Iscc
    Write-Step "Compiling the installer with $isccPath"
    $code = Invoke-Logged -FilePath $isccPath -ArgumentList @("/DMyAppVersion=$Version", "/O$DistDir", $IssFile)
    if ($code -ne 0) { Stop-Build "ISCC failed (exit $code)" }

    $setupExe = Join-Path $DistDir "pyALDIC-3D-$Version-win64-setup.exe"
    if (-not (Test-Path -LiteralPath $setupExe)) { Stop-Build "installer not produced: $setupExe" }
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $setupExe).Hash.ToLowerInvariant()
    $leaf = Split-Path -Leaf $setupExe
    # sha256sum format, so `sha256sum -c` verifies a download next to it.
    [System.IO.File]::WriteAllText("$setupExe.sha256", "$hash *$leaf`n", (New-Object System.Text.UTF8Encoding($false)))
    Write-Info ("installer: {0} ({1} MB)" -f $setupExe, [math]::Round((Get-Item -LiteralPath $setupExe).Length / 1MB, 1))
    Write-Info "sha256:    $hash"
}

# ------------------------------------------------------------------ main ----
Write-Info "pyALDIC-3D installer build -- log: $LogFile"

$initPy = Join-Path $RepoRoot "src\al_dic_3d\__init__.py"
$match = Select-String -LiteralPath $initPy -Pattern '__version__\s*=\s*"([^"]+)"'
if (-not $match) { Stop-Build "cannot read __version__ from $initPy" }
$Version = $match.Matches[0].Groups[1].Value
Write-Step "Building pyALDIC-3D $Version"

if (-not $SkipFreeze) {
    $basePython = Resolve-BasePython
    $venvPython = Initialize-BuildVenv $basePython
    Invoke-Freeze $venvPython
}
elseif (-not (Test-Path -LiteralPath $OneDir)) {
    Stop-Build "-SkipFreeze given but $OneDir does not exist"
}

Invoke-SelfTest $Version

if (-not $SkipInstaller) {
    Invoke-Installer $Version
}

$elapsed = (Get-Date) - $Started
Write-Step ("Done in {0:N1} min." -f $elapsed.TotalMinutes)
if (-not $SkipInstaller) {
    Write-Info "The installer is NOT code-signed: Windows SmartScreen warns on first run."
    Write-Info "See packaging\README.md for the signing procedure."
}
Write-Info "build log: $LogFile"
Close-Log
exit 0
