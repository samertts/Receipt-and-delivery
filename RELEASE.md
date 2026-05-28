# Release v1.0.0 — نظام إدارة الاستلام المختبري

**Iraqi Laboratory Receipt & Delivery Management System**

## Installation

### Option 1: Windows Installer (Recommended)

1. Download `LabReceiptSetup.exe` from the [Releases](https://github.com/samertts/Receipt-and-delivery/releases) page
2. Double-click the installer
3. Follow the wizard — default settings are recommended
4. Launch from Start Menu or Desktop shortcut
5. Login with default credentials:
   - **Username:** `admin`
   - **Password:** `Admin@123`

### Option 2: Portable EXE (No Install)

1. Download `LabReceiptSystem.exe` from the [Releases](https://github.com/samertts/Receipt-and-delivery/releases) page
2. Run directly — no installation required
3. First-run creates all data directories in `%LOCALAPPDATA%\LabReceiptSystem\`

### Option 3: Run from Source (Developers)

```batch
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## System Requirements

- **OS:** Windows 10 64-bit or later / Windows Server 2019+
- **RAM:** 512 MB minimum, 2 GB recommended
- **Disk:** 200 MB for application + data growth
- **Display:** 1280×720 minimum, 1920×1080 recommended
- **Dependencies:** None — all libraries bundled in the EXE

## Data Persistence

All user data is stored in `%LOCALAPPDATA%\LabReceiptSystem\`:

| Directory  | Contents                    |
|------------|-----------------------------|
| `database/` | SQLite database (lab_system.db) |
| `backups/`  | Database backup files       |
| `attachments/` | Uploaded file attachments |
| `receipts/` | Generated PDF receipts      |
| `logs/`     | Application audit logs      |
| `recovery/` | Recovery checkpoints        |
| `exports/`  | Exported reports (CSV, etc) |

**Data survives uninstall/reinstall.** Uninstalling the application removes only program files. User data in `%LOCALAPPDATA%\LabReceiptSystem\` is preserved.

## Build from Source (Windows)

### Prerequisites

- Python 3.10+ installed
- Windows 10+ (for EXE packaging)
- Inno Setup 6+ (for installer)

### Step 1: Build EXE

```batch
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --noconfirm --clean lab_system.spec
```

Output: `dist\LabReceiptSystem.exe`

### Step 2: Build Installer (requires Inno Setup)

```batch
ISCC installer\setup.iss
```

Output: `installer\Output\LabReceiptSetup.exe`

### CI/CD Build

Push a tag matching `v*` to trigger automatic build via GitHub Actions:

```bash
git tag v1.0.0
git push origin v1.0.0
```

The workflow builds both EXE and Setup.exe and publishes them as a GitHub Release.

## First Run

1. Launch the application
2. Login with default credentials: `admin` / `Admin@123`
3. **Change the default password immediately** via Settings → Users
4. The dashboard shows system health status
5. All required data directories are auto-created on first launch

## Project Structure

```
Receipt-and-delivery/
├── main.py                 # Entry point
├── lab_system/             # Application code
├── tests/                  # Test suite (36 tests)
├── installer/              # Inno Setup script
├── assets/                 # Icons and resources
├── .github/workflows/      # CI/CD pipeline
├── lab_system.spec         # PyInstaller configuration
├── VERSION                 # Version file (1.0.0)
└── requirements.txt        # Python dependencies
```

## Upgrade Path

To upgrade from a previous installation:
1. Run the new installer — it overwrites the application files
2. Your existing data in `%LOCALAPPDATA%\LabReceiptSystem\` is preserved
3. The app auto-detects schema version and migrates if needed

## Uninstall

- Via Windows Settings → Apps → "نظام إدارة الاستلام المختبري"
- Or run `unins000.exe` in the installation directory
- **User data is preserved** after uninstall

## Verification

| Check           | Status |
|-----------------|--------|
| Tests           | 36/36 passing |
| Startup (clean) | All tables, indexes, WAL, foreign keys verified |
| Offline mode    | Fully operational — no internet required |
| GUI smoke test  | All 8 pages instantiate correctly |
| Audit logging   | Immutable, write-only |
| Backup/restore  | Verified with integrity check |
| EXE build       | PyInstaller 6.14.0, UPX compressed |
| Installer       | Inno Setup, Arabic UI, data-preserving uninstall |
| CI/CD           | GitHub Actions, automated build on tag push |

## Default Credentials

| User   | Password   | Role  |
|--------|------------|-------|
| admin  | Admin@123  | Admin |

> **SECURITY:** Change the default password immediately after first login.

## License

Proprietary — Iraqi Health Laboratory Directorate.
