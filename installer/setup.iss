; Inno Setup Script for Lab Receipt System
; Iraqi Laboratory Receipt & Delivery Management System

#define MyAppName "نظام إدارة الاستلام المختبري"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Iraqi Health Laboratory Directorate"
#define MyAppURL "https://github.com/samertts/Receipt-and-delivery"
#define MyAppExeName "LabReceiptSystem.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\LabReceiptSystem
DefaultGroupName={#MyAppName}
OutputDir=Output
OutputBaseFilename=LabReceiptSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"

[Tasks]
Name: "desktopicon"; Description: "إنشاء اختصار على سطح المكتب"; GroupDescription: "اختصارات:"; Flags: checkedonce

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{localappdata}\LabReceiptSystem\database"
Name: "{localappdata}\LabReceiptSystem\attachments"
Name: "{localappdata}\LabReceiptSystem\backups"
Name: "{localappdata}\LabReceiptSystem\logs"
Name: "{localappdata}\LabReceiptSystem\exports"
Name: "{localappdata}\LabReceiptSystem\settings"
Name: "{localappdata}\LabReceiptSystem\templates"
Name: "{localappdata}\LabReceiptSystem\receipts"
Name: "{localappdata}\LabReceiptSystem\recovery"
Name: "{localappdata}\LabReceiptSystem\diagnostics"
Name: "{localappdata}\LabReceiptSystem\migrations"
Name: "{localappdata}\LabReceiptSystem\updates"

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "تشغيل النظام"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\LabReceiptSystem\temp"
Type: dirifempty; Name: "{localappdata}\LabReceiptSystem\temp"
Type: dirifempty; Name: "{localappdata}\LabReceiptSystem"

[UninstallRun]
Filename: "{cmd}"; Parameters: "/C echo Uninstall complete. User data preserved at: {localappdata}\LabReceiptSystem"; Flags: runhidden
