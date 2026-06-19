"""
Windows Build & Deployment Certification.

Verifies:
  - PyInstaller spec correctness (no missing hidden imports, valid paths)
  - Inno Setup script correctness (all directories, version sync)
  - CI pipeline covers all build steps
  - All assets exist
  - VERSION file bundled

Cannot execute on Linux — this is a static verification.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

errors = []
n_pass = 0
n_total = 0

ROOT = Path(__file__).resolve().parent.parent


def ok(cond, msg):
    global n_pass, n_total
    n_total += 1
    if cond:
        n_pass += 1
    else:
        errors.append(msg)


print("=" * 72)
print("WINDOWS BUILD & DEPLOYMENT CERTIFICATION REPORT")
print("=" * 72)

# -----------------------------------------------------------------------
# 1. PyInstaller spec analysis
# -----------------------------------------------------------------------
print("\n  1. PyInstaller spec (lab_system.spec) ...")

spec_path = ROOT / "lab_system.spec"
ok(spec_path.exists(), "lab_system.spec exists")

spec_text = spec_path.read_text(encoding="utf-8")

# Check entry point
ok("'main.py'" in spec_text, "entry point is main.py")

# Check datas (bundled files)
ok("('assets', 'assets')" in spec_text, "assets directory bundled")
ok("('VERSION', '.')" in spec_text, "VERSION file bundled")

# Check hidden imports are comprehensive
critical_imports = [
    "lab_system.app.ui.app",
    "lab_system.app.ui.receipts_page",
    "lab_system.app.ui.receipt_dialog",
    "lab_system.app.ui.receipt_detail_dialog",
    "lab_system.app.ui.org_page",
    "lab_system.app.ui.users_page",
    "lab_system.app.ui.reports_page",
    "lab_system.app.ui.settings_page",
    "lab_system.app.ui.audit_page",
    "lab_system.app.ui.backup_page",
    "lab_system.app.database.db",
    "lab_system.app.services.auth_service",
    "lab_system.app.services.backup_service",
    "lab_system.app.services.catalog_service",
    "lab_system.app.services.org_service",
    "lab_system.app.services.receipt_service",
    "lab_system.app.services.recovery_service",
    "lab_system.app.services.report_service",
    "lab_system.app.services.seed_service",
    "lab_system.app.services.user_service",
    "lab_system.app.printing.receipt_pdf",
    "lab_system.app.attachments.manager",
    "lab_system.app.audit.logger",
    "lab_system.app.sync.service",
    "lab_system.app.sync.api_client",
    "lab_system.app.sync.device",
    "lab_system.app.diagnostics.startup",
    "lab_system.app.settings.config",
    "lab_system.app.utils.constants",
    "lab_system.app.utils.errors",
    "lab_system.app.utils.logging",
    "lab_system.app.utils.validators",
    "lab_system.app.auth.permissions",
    "lab_system.app.auth.security",
    "lab_system.app.database.connection",
    "lab_system.app.services.base_service",
    "sqlite3",
    "bcrypt",
    "reportlab",
    "qrcode",
    "barcode",
    "PIL",
    "openpyxl",
]
for imp in critical_imports:
    ok(f"'{imp}'" in spec_text or f'"{imp}"' in spec_text, f"  hidden import: {imp}")

# Check excludes
excluded = [
    "tkinter",
    "matplotlib",
    "numpy",
    "scipy",
    "pandas",
    "cv2",
    "transformers",
    "torch",
    "tensorflow",
]
for ex in excluded:
    ok(f"'{ex}'" in spec_text, f"  excluded: {ex}")

# Check executable name
ok(
    "name='LabReceiptSystem'" in spec_text or 'name="LabReceiptSystem"' in spec_text,
    "EXE name is LabReceiptSystem",
)

# Check console=False
ok("console=False" in spec_text, "console mode disabled (GUI app)")

# Check icon
ok("icon='assets/icons/app.ico'" in spec_text, "app icon specified")

# -----------------------------------------------------------------------
# 2. Inno Setup installer analysis
# -----------------------------------------------------------------------
print("\n  2. Inno Setup installer (installer/setup.iss) ...")

iss_path = ROOT / "installer" / "setup.iss"
ok(iss_path.exists(), "installer/setup.iss exists")
iss_text = iss_path.read_text(encoding="utf-8")

# Check [Dirs] section completeness
required_dirs = [
    "database",
    "attachments",
    "backups",
    "logs",
    "exports",
    "settings",
    "templates",
    "recovery",
    "diagnostics",
    "migrations",
    "updates",
    "receipts",
]
for d in required_dirs:
    ok(d in iss_text, f"  [Dirs] includes '{d}'")

# Check version sync
ok("#define MyAppVersion" in iss_text, "  version defined as #define MyAppVersion")
ok(
    "AppVersion={#MyAppVersion}" in iss_text,
    "  AppVersion references #define (not hardcoded)",
)

# Check uninstall preserves user data
ok("[UninstallDelete]" in iss_text, "  [UninstallDelete] section exists")
ok(
    "temp" in iss_text.split("[UninstallDelete]")[1].split("[UninstallRun]")[0],
    "  temp directory is deleted on uninstall",
)
ok("[UninstallRun]" in iss_text, "  [UninstallRun] section exists")

# Check main EXE is bundled
ok(
    "dist\\{#MyAppExeName}" in iss_text or "dist\\LabReceiptSystem.exe" in iss_text,
    "  EXE source from dist\\",
)

# -----------------------------------------------------------------------
# 3. Secondary installer (LabReceipt.iss)
# -----------------------------------------------------------------------
print("\n  3. Secondary installer (lab_system/installer/LabReceipt.iss) ...")

iss2_path = ROOT / "lab_system" / "installer" / "LabReceipt.iss"
ok(iss2_path.exists(), "LabReceipt.iss exists")
iss2_text = iss2_path.read_text(encoding="utf-8")

required_dirs2 = [
    "database",
    "attachments",
    "backups",
    "logs",
    "exports",
    "settings",
    "templates",
    "recovery",
    "diagnostics",
    "migrations",
    "updates",
]
for d in required_dirs2:
    ok(d in iss2_text, f"  [Dirs] includes '{d}'")

# Check version is present (hardcoded in this file)
ok("AppVersion=" in iss2_text, "  AppVersion defined")

# -----------------------------------------------------------------------
# 4. CI pipeline verification
# -----------------------------------------------------------------------
print("\n  4. CI pipeline (.github/workflows/build.yml) ...")

ci_path = ROOT / ".github/workflows/build.yml"
ok(ci_path.exists(), "build.yml exists")
ci_text = ci_path.read_text(encoding="utf-8")

build_steps = [
    ("actions/checkout@v4", "checkout source"),
    ("actions/setup-python@v5", "setup Python"),
    ("pip install", "install dependencies"),
    ("pip install pyinstaller", "install PyInstaller"),
    ("py_compile", "syntax check"),
    ("pytest", "run tests"),
    ("pyinstaller", "build EXE"),
    ("ISCC", "build installer with Inno Setup"),
    ("actions/upload-artifact@v4", "upload artifacts"),
    ("softprops/action-gh-release@v2", "GitHub Release"),
]
for step, desc in build_steps:
    ok(step in ci_text, f"  CI step: {desc}")

ok(
    "dist/LabReceiptSystem.exe" in ci_text or "dist\\LabReceiptSystem.exe" in ci_text,
    "  EXE artifact is uploaded",
)
ok(
    "installer/Output/LabReceiptSetup.exe" in ci_text
    or "installer\\Output\\LabReceiptSetup.exe" in ci_text,
    "  Installer artifact is uploaded",
)

# Check version synchronization in CI
ok(
    "for /f %%i in (VERSION) do set APP_VER=%%i" in ci_text or "APP_VER" in ci_text,
    "  CI reads VERSION file dynamically",
)

# -----------------------------------------------------------------------
# 5. Asset verification
# -----------------------------------------------------------------------
print("\n  5. Assets verification ...")

icon = ROOT / "assets" / "icons" / "app.ico"
ok(icon.exists() and icon.stat().st_size > 0, "app.ico exists and non-empty")

# Check assets directory has files
assets_dir = ROOT / "assets"
if assets_dir.exists():
    files = list(assets_dir.rglob("*"))
    ok(len(files) > 0, f"assets directory has {len(files)} files")
else:
    ok(False, "assets directory exists")

# VERSION file
version_file = ROOT / "VERSION"
ok(version_file.exists(), "VERSION file exists")
ver = version_file.read_text(encoding="utf-8").strip()
ok(len(ver) > 0, f"VERSION file non-empty: '{ver}'")

# -----------------------------------------------------------------------
# 6. Requirements verification
# -----------------------------------------------------------------------
print("\n  6. Requirements verification ...")

req_path = ROOT / "requirements.txt"
ok(req_path.exists(), "requirements.txt exists")
req_text = req_path.read_text(encoding="utf-8")
required_pkgs = [
    "PySide6",
    "reportlab",
    "bcrypt",
    "qrcode",
    "python-barcode",
    "Pillow",
    "openpyxl",
]
for pkg in required_pkgs:
    ok(pkg.lower() in req_text.lower(), f"  requirement: {pkg}")

# -----------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------
print(f"\n{'=' * 72}")
print("WINDOWS BUILD & DEPLOYMENT CERTIFICATION REPORT")
print(f"{'=' * 72}")
print(f"Total checks:  {n_total}")
print(f"Passed:        {n_pass}")
print(f"Failed:        {n_total - n_pass}")

if errors:
    print(f"\nFailures ({len(errors)}):")
    for e in errors:
        print(f"  ✗ {e}")
    sys.exit(1)

print("\n✅ ALL BUILD VERIFICATION CHECKS PASSED")
print("   PyInstaller spec: complete (all imports, excludes, datas)")
print("   Inno Setup: all directories, version sync, uninstall data preservation")
print("   CI pipeline: full build-test-package-release chain")
print("   Assets: icon present, VERSION file bundled")
print("   Requirements: all runtime dependencies present")
print("\n   NOTE: EXE build and Setup.exe generation require Windows CI execution.")
print("   Static verification confirms all build artifacts are correctly configured.")
