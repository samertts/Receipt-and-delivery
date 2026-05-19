[Setup]
AppName=Lab Receipt System
AppVersion=1.0.0
DefaultDirName={autopf}\LabReceipt
DefaultGroupName=Lab Receipt System
OutputBaseFilename=LabReceiptSetup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\LabReceiptSystem.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "lab_system\assets\*"; DestDir: "{app}\assets"; Flags: recursesubdirs createallsubdirs

[Dirs]
Name: "{app}\storage\receipts"
Name: "{app}\storage\attachments"
Name: "{app}\storage\exports"
Name: "{app}\storage\backups"
Name: "{app}\storage\temp"

[Icons]
Name: "{commondesktop}\نظام إدارة الاستلام المختبري"; Filename: "{app}\LabReceiptSystem.exe"
Name: "{group}\نظام إدارة الاستلام المختبري"; Filename: "{app}\LabReceiptSystem.exe"
