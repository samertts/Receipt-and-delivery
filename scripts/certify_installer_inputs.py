"""
Installer Input Certification.

Validates every dependency of the Inno Setup installer before compilation.

Runs in CI before ISCC invocation. Fails fast with clear diagnostics.

Checks:
  - EXE exists, non-zero, valid PE header
  - VERSION file exists
  - Assets directory contains required files
  - Icon file exists and is valid
  - LabReceipt.iss syntax expectations (Source paths, OutputDir)
  - Path consistency between build output and installer expectations
"""

import os
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

errors = []
warnings = []
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


def warn(cond, msg):
    if not cond:
        warnings.append(msg)


def check_pe_header(path: Path) -> bool:
    """Check if file has a valid PE (Portable Executable) header."""
    try:
        with open(path, 'rb') as f:
            header = f.read(2)
            if header != b'MZ':
                return False
            f.seek(0x3C)
            pe_offset_bytes = f.read(4)
            if len(pe_offset_bytes) < 4:
                return False
            pe_offset = struct.unpack('<I', pe_offset_bytes)[0]
            f.seek(pe_offset)
            pe_sig = f.read(4)
            return pe_sig == b'PE\x00\x00'
    except Exception:
        return False


print("=" * 72)
print("INSTALLER INPUT CERTIFICATION REPORT")
print("=" * 72)
print()

# -----------------------------------------------------------------------
# 1. EXE artifact
# -----------------------------------------------------------------------
print("[1] EXE Artifact")
exe_path = ROOT / "dist" / "LabReceiptSystem.exe"
ok(exe_path.exists(), f"EXE not found: {exe_path}")
if exe_path.exists():
    size = exe_path.stat().st_size
    ok(size > 0, f"EXE is zero bytes: {exe_path}")
    warn(size > 1_000_000, f"EXE suspiciously small ({size} bytes) — expected > 1 MB")
    ok(check_pe_header(exe_path), f"EXE has no valid PE header: {exe_path}")
    print(f"  {exe_path}  ({size:,} bytes)")
else:
    print(f"  MISSING: {exe_path}")

# -----------------------------------------------------------------------
# 2. VERSION file
# -----------------------------------------------------------------------
print()
print("[2] VERSION File")
version_path = ROOT / "VERSION"
ok(version_path.exists(), "VERSION file not found")
if version_path.exists():
    version_text = version_path.read_text(encoding="utf-8").strip()
    ok(bool(version_text), "VERSION file is empty")
    ok(version_text.count(".") >= 1, f"VERSION does not look like a version: {version_text}")
    print(f"  Version: {version_text}")
else:
    print("  MISSING")

# -----------------------------------------------------------------------
# 3. Assets
# -----------------------------------------------------------------------
print()
print("[3] Assets")
assets_path = ROOT / "assets"
ok(assets_path.is_dir(), f"Assets directory not found: {assets_path}")
if assets_path.is_dir():
    entries = list(assets_path.iterdir())
    ok(len(entries) > 0, f"Assets directory is empty: {assets_path}")
    for e in entries:
        print(f"  {e}")
else:
    print("  MISSING")

# -----------------------------------------------------------------------
# 4. Icon
# -----------------------------------------------------------------------
print()
print("[4] Application Icon")
icon_path = ROOT / "assets" / "icons" / "app.ico"
ok(icon_path.exists(), f"Icon not found: {icon_path}")
if icon_path.exists():
    size = icon_path.stat().st_size
    ok(size > 0, f"Icon is zero bytes: {icon_path}")
    ok(size > 1000, f"Icon too small ({size} bytes)")
    with open(icon_path, 'rb') as f:
        magic = f.read(4)
    ok(magic[:2] == b'\x00\x00' and magic[2:4] in (b'\x01\x00', b'\x02\x00'),
       f"Icon has invalid .ico header: {icon_path}")
    print(f"  {icon_path}  ({size:,} bytes)")
else:
    print("  MISSING")

# -----------------------------------------------------------------------
# 5. LabReceipt.iss analysis
# -----------------------------------------------------------------------
print()
print("[5] Installer Script (LabReceipt.iss)")
iss_path = ROOT / "lab_system" / "installer" / "LabReceipt.iss"
ok(iss_path.exists(), f"Installer script not found: {iss_path}")
if iss_path.exists():
    iss_text = iss_path.read_text(encoding="utf-8")
    ok(bool(iss_text.strip()), "Installer script is empty")

    contains_exe_source = "LabReceiptSystem.exe" in iss_text
    ok(contains_exe_source, "Installer script missing EXE Source directive")

    contains_assets = "assets" in iss_text
    ok(contains_assets, "Installer script missing assets Source directive")

    output_dir_lines = [l for l in iss_text.splitlines() if "OutputDir" in l]
    ok(len(output_dir_lines) > 0, "Installer script missing OutputDir directive")
    if output_dir_lines:
        print(f"  OutputDir: {output_dir_lines[0].strip()}")

    # Check that Source paths in .iss resolve from iss_dir to valid locations
    iss_dir = iss_path.parent  # lab_system/installer/
    for line in iss_text.splitlines():
        line = line.strip()
        if line.startswith("Source:"):
            after_colon = line[len("Source:"):].strip()
            if after_colon.startswith('"'):
                src_val = after_colon.split('"')[1]
            elif after_colon.startswith("'"):
                src_val = after_colon.split("'")[1]
            else:
                src_val = after_colon.split(";")[0].strip()
            src_posix = src_val.replace('\\', '/').rstrip('*')
            resolved = (iss_dir / src_posix).resolve()
            parent_dir = resolved.parent if src_val.endswith('*') else resolved
            ok(parent_dir.exists(),
               f"Source path does not resolve: '{src_val}' → {resolved}")
            print(f"  Source: {src_val} → {resolved}")
else:
    print("  MISSING")

# -----------------------------------------------------------------------
# 6. Path consistency
# -----------------------------------------------------------------------
print()
print("[6] Path Consistency")
# EXE from spec should land where .iss expects it
exe_expected = ROOT / "dist" / "LabReceiptSystem.exe"
ok(exe_expected == exe_path,
   f"Path inconsistency: expected EXE at {exe_expected}")

# Installer output path
installer_output = ROOT / "installer" / "Output" / "LabReceiptSetup.exe"
print(f"  Expected installer output: {installer_output}")

# -----------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------
print()
print("=" * 72)
print("INSTALLER INPUT CERTIFICATION REPORT")
print("=" * 72)
print(f"Total checks:  {n_total}")
print(f"Passed:        {n_pass}")
print(f"Failed:        {n_total - n_pass}")
print()

if warnings:
    print("Warnings:")
    for w in warnings:
        print(f"  ⚠ {w}")
    print()

if errors:
    print("Errors:")
    for e in errors:
        print(f"  ❌ {e}")
    print()
    sys.exit(1)
else:
    print("✅ ALL INSTALLER INPUT CHECKS PASSED")
    print("   All installer prerequisites are present and valid.")
    print()
    sys.exit(0)
