#define MyAppName "LinkCue Manager"
#define MyAppVersion "0.5.0"
#define MyAppPublisher "LinkCue"
#define MyAppExeName "LinkCueManager.exe"

[Setup]
AppId={{6A9D99EB-634F-4AAF-84F4-54D50921A94B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\LinkCue\LinkCue Manager
DefaultGroupName=LinkCue\LinkCue Manager

DisableProgramGroupPage=yes
PrivilegesRequired=admin

OutputDir=C:\Projects\LinkCue Suite\LinkCue Manager\release\v0.5.0
OutputBaseFilename=LinkCue Manager Setup 0.5.0

SetupIconFile=C:\Projects\LinkCue Suite\LinkCue Manager\assets\linkcue_manager.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} {#MyAppVersion}
Uninstallable=yes

Compression=lzma2
SolidCompression=yes
WizardStyle=modern

ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

VersionInfoVersion=0.5.0
VersionInfoCompany=LinkCue
VersionInfoDescription=LinkCue Manager Installer
VersionInfoProductName=LinkCue Manager
VersionInfoProductVersion=0.5.0

[Files]
Source: "C:\Projects\LinkCue Suite\LinkCue Manager\dist\LinkCueManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\LinkCue Manager"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall LinkCue Manager"; Filename: "{uninstallexe}"
Name: "{autodesktop}\LinkCue Manager"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch LinkCue Manager"; Flags: nowait postinstall skipifsilent
