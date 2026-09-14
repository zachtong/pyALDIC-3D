; Inno Setup 6 script for pyALDIC-3D (Windows x64, per-user by default).
;
; Normally compiled by packaging\build_installer.ps1 (locally and in CI), which
; reads the version from src\al_dic_3d\__init__.py, uses the pinned Inno Setup
; release and runs the frozen self-test first. By hand, once the PyInstaller
; onedir build exists under packaging\dist\:
;   ISCC.exe /DMyAppVersion=1.2.0 packaging\installer.iss
; The version must always be injected with /DMyAppVersion; the fallback below
; only marks a development compile.
;
; Design decisions:
; * PrivilegesRequired=lowest -> installs per-user under
;   %LOCALAPPDATA%\Programs\pyALDIC-3D with NO admin prompt (typical for lab
;   machines where users lack admin). "Overrides allowed" lets an admin pick
;   an all-users install from the wizard/command line if wanted.
; * The example dataset is NOT shipped (size). The Start-menu "User Guide"
;   entry opens the rendered online guide, kept current on GitHub; a raw .md
;   file opens in Notepad or not at all. The markdown sources are still
;   installed under {app}\docs\user-guide as an offline copy.
; * ChangesAssociations + the optional .aldic3d association task let users
;   double-click session files to open them in the GUI (the GUI entry point
;   already handles a session path in argv).

#define MyAppName "pyALDIC-3D"
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0-dev"
#endif
#define MyAppPublisher "Zixiang (Zach) Tong"
#define MyAppURL "https://github.com/zachtong/pyALDIC-3D"
#define MyUserGuideURL "https://github.com/zachtong/pyALDIC-3D/blob/main/docs/user-guide/index.md"
#define MyAppExeName "pyALDIC-3D.exe"
#define MyCliExeName "pyaldic3d-cli.exe"
#define MyDistDir "dist\pyALDIC-3D"

[Setup]
; NEVER change AppId between releases -- it is how Windows/Inno identify the
; app for upgrades and uninstall.
AppId={{2F5E80ED-4B57-40CD-A5CE-8D86D269F4E8}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputBaseFilename={#MyAppName}-{#MyAppVersion}-win64-setup
SetupIconFile=assets\pyaldic3d.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
ChangesAssociations=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "fileassoc"; Description: "Associate .aldic3d session files with {#MyAppName}"; GroupDescription: "File associations:"

[Files]
; The whole PyInstaller onedir tree (exes + _internal runtime).
Source: "{#MyDistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Markdown user guide, an offline copy (the example dataset is deliberately NOT
; shipped). The Start-menu entry points at the online guide instead.
Source: "..\docs\user-guide\*.md"; DestDir: "{app}\docs\user-guide"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[INI]
; Internet shortcut to the online user guide (rendered by GitHub, kept current).
Filename: "{app}\UserGuideOnline.url"; Section: "InternetShortcut"; Key: "URL"; String: "{#MyUserGuideURL}"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\User Guide"; Filename: "{app}\UserGuideOnline.url"; Comment: "pyALDIC-3D user guide (opens in your browser)"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Per-user (HKA -> HKCU under PrivilegesRequired=lowest) .aldic3d association.
Root: HKA; Subkey: "Software\Classes\.aldic3d"; ValueType: string; ValueName: ""; ValueData: "pyALDIC3D.Session"; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\pyALDIC3D.Session"; ValueType: string; ValueName: ""; ValueData: "pyALDIC-3D session"; Flags: uninsdeletekey; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\pyALDIC3D.Session\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\pyALDIC3D.Session\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: fileassoc

[InstallDelete]
; 1.0.0 - 1.1.0 created a second "User Guide (online)" entry next to one that
; opened the raw index.md. The single "User Guide" entry now opens the online
; guide, so remove the old duplicate when upgrading over those versions.
Type: files; Name: "{group}\User Guide (online).lnk"

[UninstallDelete]
Type: files; Name: "{app}\UserGuideOnline.url"
; numba JIT cache written at runtime (see rthook_numba.py).
Type: filesandordirs; Name: "{localappdata}\pyALDIC-3D\numba_cache"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
