; Inno Setup script for Print Recovery MVP
; Requires Inno Setup 6+ (https://jrsoftware.org/isinfo.php)
;
; How to use:
;   1. First run build-exe.ps1 so that dist\PrintRecovery exists
;   2. Open this file in Inno Setup Compiler and click Compile
;   3. The finished installer will appear in dist\installer\
;
; The resulting Setup.exe is what you put on a flash drive.

#define MyAppName "Print Recovery"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Print Recovery Project"
#define MyAppURL "https://github.com/akameredon/print-recovery-mvp"
#define MyAppExeName "PrintRecovery.exe"

[Setup]
AppId={{A8F3C2E1-9B47-4D6A-8F21-PrintRecoveryMVP}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\PrintRecovery
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=
OutputDir=..\..\dist\installer
OutputBaseFilename=PrintRecovery-Setup-{#MyAppVersion}
SetupIconFile=
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

; Keep user data safe on uninstall
[UninstallDelete]
Type=filesandordirs; Name={app}\data
Type=filesandordirs; Name={app}\outputs

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Everything produced by PyInstaller
Source: "..\..\dist\PrintRecovery\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
