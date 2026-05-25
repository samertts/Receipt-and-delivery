[Setup]
AppName=Lab Receipt System
AppVersion=1.0.0
AppPublisher=Iraqi Health Laboratory Directorate
DefaultDirName={autopf}\LabReceiptSystem
DefaultGroupName=Lab Receipt System
OutputDir=Output
OutputBaseFilename=LabReceiptSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\LabReceiptSystem.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\LabReceiptSystem.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\*"; DestDir: "{app}\assets"; Flags: recursesubdirs createallsubdirs

[Dirs]
Name: "{app}\storage\receipts"
Name: "{app}\storage\attachments"
Name: "{app}\storage\exports"
Name: "{app}\storage\backups"
Name: "{app}\storage\temp"

[Icons]
Name: "{autodesktop}\نظام إدارة الاستلام المختبري"; Filename: "{app}\LabReceiptSystem.exe"
Name: "{group}\نظام إدارة الاستلام المختبري"; Filename: "{app}\LabReceiptSystem.exe"
