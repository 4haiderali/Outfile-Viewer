#define MyAppName "Outfile Viewer"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Haider"
#define MyAppExeName "OutfileViewer.exe"

[Setup]
AppId={{8B64F5D4-9B61-4D3E-9E99-OUTFILEVIEWER}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\OutfileViewer
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=OutfileViewerSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
AlwaysUsePersonalGroup=yes
UninstallDisplayName={#MyAppName}
SetupIconFile=out_viewer\Icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "dist\OutfileViewer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\{#MyAppName}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"; IconIndex: 0
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"; IconIndex: 0; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent