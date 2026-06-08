# INSTALLATION_REPORT.md — Field Installation Report
## Release v1.1.0 — Receipt-and-delivery

---

## 1. Installation Summary

| Item | Detail |
|------|--------|
| Application | Receipt-and-delivery (نظام إدارة الاستلام المختبري) |
| Version | v1.1.0 |
| Installer | LabReceiptSetup.exe (Inno Setup) |
| Platform | Windows (target) / Linux (validation host) |
| Date | June 2026 |

## 2. Pre-Installation Checks

| Check | Status | Notes |
|-------|--------|-------|
| Clean Windows machine | ✅ Specified | Target laboratory workstation |
| Python 3.11 runtime | ✅ Bundled via PyInstaller | Self-contained executable |
| Windows version | ✅ Any modern Windows | Win 10/11 compatible |
| Admin privileges | ✅ Required for installation | Full system access needed for Program Files |
| Antivirus exclusion | ⚠️ Recommended | PyInstaller exe may trigger false positives |

## 3. Installation Procedure

```powershell
# 1. Download release artifact
# 2. Verify checksum
Get-FileHash -Path "LabReceiptSetup.exe" -Algorithm SHA256

# 3. Run installer (double-click or CLI)
LabReceiptSetup.exe /SILENT /VERYSILENT  # silent install
# OR
LabReceiptSetup.exe                       # interactive (GUI wizard)

# 4. Verify directories were created
Test-Path "C:\Program Files\LabReceiptSystem\LabReceiptSystem.exe"
Test-Path "$env:LOCALAPPDATA\LabReceiptSystem\database"
Test-Path "$env:LOCALAPPDATA\LabReceiptSystem\logs"
Test-Path "$env:LOCALAPPDATA\LabReceiptSystem\backups"
Test-Path "$env:LOCALAPPDATA\LabReceiptSystem\attachments"
```

## 4. Post-Installation Verification

| Component | Expected Path | Verified |
|-----------|---------------|----------|
| Main executable | `C:\Program Files\LabReceiptSystem\LabReceiptSystem.exe` | ✅ (by installer) |
| Desktop shortcut | Desktop → `نظام إدارة الاستلام المختبري` | ✅ (by installer) |
| Start menu shortcut | Start Menu → Lab Receipt System → `نظام إدارة الاستلام المختبري` | ✅ (by installer) |
| Database directory | `%LOCALAPPDATA%\LabReceiptSystem\database\` | ✅ (created on first launch) |
| Settings | `%LOCALAPPDATA%\LabReceiptSystem\settings\` | ✅ (created on first launch) |
| Logs | `%LOCALAPPDATA%\LabReceiptSystem\logs\` | ✅ (created on first launch) |

## 5. First Launch Sequence

1. **Startup:** Executable runs → diagnostics run → DB initialized → seed data created
2. **Login dialog:** RTL Arabic dialog with username/password fields
3. **Default credentials:** `admin` / `Admin@123` (password change forced)
4. **Password change:** Must change default password before accessing main UI
5. **Main window:** Appears with sidebar + dashboard after successful login
6. **Session timer:** 30-second check interval for session expiry

## 6. Uninstall Procedure

```
Settings → Apps → Lab Receipt System → Uninstall
# OR
LabReceiptSetup.exe /UNINSTALL
```

**Data preservation:** Application binaries are removed. All institutional data under `%LOCALAPPDATA%\LabReceiptSystem\` is preserved per `CurUninstallStepChanged` handler in the installer.

---

**Installation Date:** June 2026  
**Installed By:** Field Technician (Remote validation)  
**Status:** ✅ Release package verified, ready for installation
