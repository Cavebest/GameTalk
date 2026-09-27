; Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
; Inno Setup script for GameTalk Translator. Build with packaging\build_installer.bat.
; Asks: install for all users (Program Files, needs admin) or just me (no admin).
; English + Arabic installer UI.

#define AppName "GameTalk Translator"
#define AppVersion "1.0.0"
#define AppPublisher "Shkour Bashtawi"
#define AppURL "https://github.com/ShkourBashtawi"
#define AppExe "GameTalk.exe"

[Setup]
AppId={{6E0A7C58-9D1B-4B7E-8E35-3B2F6A1C9D40}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppCopyright=(c) 2026 {#AppPublisher}. MIT License.
; {autopf} = C:\Program Files for all users, %LOCALAPPDATA%\Programs for "just me"
DefaultDirName={autopf}\GameTalk
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog commandline
; Settings live in %APPDATA% and the startup entry in HKCU: per user, on purpose.
UsedUserAreasWarning=no
OutputDir=..\dist
OutputBaseFilename=GameTalk-Setup-{#AppVersion}
SetupIconFile=gametalk.ico
UninstallDisplayIcon={app}\{#AppExe}
LicenseFile=..\LICENSE
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"

[CustomMessages]
english.DesktopIcon=Create a desktop shortcut
arabic.DesktopIcon=إنشاء اختصار على سطح المكتب
english.StartupIcon=Start GameTalk when Windows starts
arabic.StartupIcon=تشغيل البرنامج مع بدء ويندوز
english.LaunchNow=Open GameTalk now
arabic.LaunchNow=فتح البرنامج الآن
english.Extra=Options:
arabic.Extra=خيارات:

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopIcon}"; GroupDescription: "{cm:Extra}"
Name: "startup"; Description: "{cm:StartupIcon}"; GroupDescription: "{cm:Extra}"; Flags: unchecked

[Files]
Source: "..\dist\GameTalk\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
; Same entry the app's own "Start with Windows" switch uses, so both stay in sync.
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; \
  ValueName: "{#AppName}"; ValueData: """{app}\{#AppExe}"" --app"; Tasks: startup; \
  Flags: uninsdeletevalue

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchNow}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM {#AppExe}"; Flags: runhidden; RunOnceId: "StopGameTalk"

[UninstallDelete]
; Settings and logs in %APPDATA%\GameTalk are kept on purpose (reinstall keeps your setup).
Type: filesandordirs; Name: "{app}"
