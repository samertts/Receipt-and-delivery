$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $Root

Write-Host '== Receipt and Delivery Windows build ==' -ForegroundColor Cyan
Write-Host "Root: $Root"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'Python 3.11+ was not found. Install Python and enable it on PATH.'
}

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Host 'Running desktop tests...' -ForegroundColor Cyan
python -m pytest tests -q

Write-Host 'Building portable EXE...' -ForegroundColor Cyan
python -m PyInstaller --noconfirm --clean lab_system.spec
$Exe = Join-Path $Root 'dist\LabReceiptSystem.exe'
if (-not (Test-Path $Exe)) {
    throw "PyInstaller did not create $Exe"
}

$InstallerScript = Join-Path $Root 'lab_system\installer\LabReceipt.iss'
$Iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if ($Iscc) {
    Write-Host 'Building Inno Setup installer...' -ForegroundColor Cyan
    & $Iscc.Source $InstallerScript
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup failed with exit code $LASTEXITCODE"
    }
} else {
    Write-Warning 'ISCC.exe was not found; portable EXE was built, installer step was skipped.'
}

$HashFile = Join-Path $Root 'dist\SHA256SUMS.txt'
$Hashes = @((Get-FileHash $Exe -Algorithm SHA256))
$Installer = Join-Path $Root 'installer\Output\LabReceiptSetup.exe'
if (Test-Path $Installer) {
    $Hashes += Get-FileHash $Installer -Algorithm SHA256
}
$Hashes | ForEach-Object { '{0}  {1}' -f $_.Hash.ToLowerInvariant(), $_.Path.Substring($Root.Path.Length + 1) } | Set-Content -Encoding ascii $HashFile

Write-Host "EXE: $Exe" -ForegroundColor Green
Write-Host "Checksums: $HashFile" -ForegroundColor Green
if (Test-Path $Installer) {
    Write-Host "Installer: $Installer" -ForegroundColor Green
}
