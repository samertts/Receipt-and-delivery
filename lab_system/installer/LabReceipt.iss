[Setup]
AppName=Lab Receipt System
AppVersion=1.1.0
AppPublisher=Iraqi Health Laboratory Directorate
DefaultDirName={autopf}\LabReceiptSystem
DefaultGroupName=Lab Receipt System
OutputDir=Output
OutputBaseFilename=LabReceiptSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\LabReceiptSystem.exe
UsePreviousAppDir=yes
UsePreviousGroup=yes
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\LabReceiptSystem.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\*"; DestDir: "{app}\assets"; Flags: recursesubdirs createallsubdirs

[Dirs]
Name: "{localappdata}\LabReceiptSystem\database"
Name: "{localappdata}\LabReceiptSystem\attachments"
Name: "{localappdata}\LabReceiptSystem\logs"
Name: "{localappdata}\LabReceiptSystem\backups"
Name: "{localappdata}\LabReceiptSystem\exports"
Name: "{localappdata}\LabReceiptSystem\settings"
Name: "{localappdata}\LabReceiptSystem\templates"
Name: "{localappdata}\LabReceiptSystem\recovery"
Name: "{localappdata}\LabReceiptSystem\diagnostics"
Name: "{localappdata}\LabReceiptSystem\migrations"
Name: "{localappdata}\LabReceiptSystem\updates"

[Icons]
Name: "{autodesktop}\نظام إدارة الاستلام المختبري"; Filename: "{app}\LabReceiptSystem.exe"
Name: "{group}\نظام إدارة الاستلام المختبري"; Filename: "{app}\LabReceiptSystem.exe"

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then begin
    MsgBox('Application binaries were removed. Institutional data under %LOCALAPPDATA%\\LabReceiptSystem was preserved.', mbInformation, MB_OK);
  end;
end;
