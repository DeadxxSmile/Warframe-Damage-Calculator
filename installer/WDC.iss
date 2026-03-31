; Warframe Damage Calculator by TenZeroGG installer script
; Build the EXE first so dist\\WDC\\WDC.exe exists, then compile this file with Inno Setup 6.

#define MyAppName "Warframe Damage Calculator by TenZeroGG"
#define MyAppShortName "WDC"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "TenZeroGG"
#define MyAppExeName "WDC.exe"
#define MyAppSourceDir "..\\dist\\WDC"
#define MyOutputDir "..\\installer_output"

#define MySetupIcon "..\wdc.ico"

[Setup]
AppId={{8A7430B5-6BFE-42D5-9C47-2D225C2E8E77}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppShortName}
DefaultGroupName={#MyAppShortName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
OutputDir={#MyOutputDir}
OutputBaseFilename=WDC-Setup-v{#MyAppVersion}
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
SetupIconFile={#MySetupIcon}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "{#MyAppSourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppShortName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppShortName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppShortName}"; Flags: nowait postinstall skipifsilent
