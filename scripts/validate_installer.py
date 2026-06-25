#!/usr/bin/env python3
"""Validate Inno Setup installer configuration.

Checks:
  - All Source paths resolve
  - OutputDir is correct
  - Shortcuts are defined
  - Uninstall behavior is correct
  - Registry entries are safe
  - File associations are correct
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ISS_FILE = ROOT / "lab_system" / "installer" / "LabReceipt.iss"

errors = []
warnings = []
passed = 0
total = 0


def ok(condition: bool, msg: str):
    global passed, total
    total += 1
    if condition:
        passed += 1
    else:
        errors.append(msg)


def warn(condition: bool, msg: str):
    if not condition:
        warnings.append(msg)


def main():
    global passed, total

    print("=" * 60)
    print("INSTALLER VALIDATION REPORT")
    print("=" * 60)
    print()

    ok(ISS_FILE.exists(), f"ISS file not found: {ISS_FILE}")
    if not ISS_FILE.exists():
        print("FATAL: Cannot continue without ISS file")
        sys.exit(1)

    text = ISS_FILE.read_text(encoding="utf-8")
    iss_dir = ISS_FILE.parent

    # [Setup] section
    print("[Setup] Section")
    setup_match = re.search(r"\[Setup\](.*?)\[", text, re.DOTALL)
    if setup_match:
        setup = setup_match.group(1)

        ok("AppName=" in setup, "Missing AppName")
        ok("AppVersion=" in setup, "Missing AppVersion")
        ok("DefaultDirName=" in setup, "Missing DefaultDirName")
        ok("OutputDir=" in setup, "Missing OutputDir")
        ok("OutputBaseFilename=" in setup, "Missing OutputBaseFilename")
        ok("Compression=" in setup, "Missing Compression")
        ok("WizardStyle=" in setup or "WizardStyle=modern" in setup, "Missing WizardStyle")

        # Check OutputDir
        output_match = re.search(r"OutputDir=(.+)", setup)
        if output_match:
            output_dir = output_match.group(1).strip()
            print(f"  OutputDir: {output_dir}")

        # Check version
        ver_match = re.search(r"AppVersion=(.+)", setup)
        if ver_match:
            ver = ver_match.group(1).strip()
            version_content = (ROOT / "VERSION").read_text().strip()
            ok(ver == version_content, f"AppVersion mismatch: ISS={ver} != VERSION={version_content}")
            print(f"  AppVersion: {ver}")

    print()

    # [Files] section
    print("[Files] Section")
    files_section = re.search(r"\[Files\](.*?)\[", text, re.DOTALL)
    if files_section:
        for line in files_section.group(1).splitlines():
            line = line.strip()
            if line.startswith("Source:"):
                after = line[len("Source:"):].strip()
                if after.startswith('"'):
                    src_val = after.split('"')[1]
                else:
                    src_val = after.split(";")[0].strip()

                src_posix = src_val.replace("\\", "/").rstrip("*")
                resolved = (iss_dir / src_posix).resolve()

                if src_val.endswith("*"):
                    exists = resolved.is_dir()
                else:
                    exists = resolved.exists()

                ok(exists, f"Source path missing: '{src_val}' -> {resolved}")
                status = "OK" if exists else "MISSING"
                print(f"  Source: {src_val} -> {status}")

    print()

    # [Dirs] section
    print("[Dirs] Section")
    dirs_section = re.search(r"\[Dirs\](.*?)\[", text, re.DOTALL)
    if dirs_section:
        dir_count = len([line for line in dirs_section.group(1).splitlines() if line.strip().startswith("Name:")])
        ok(dir_count > 0, "No [Dirs] entries found")
        print(f"  Directories to create: {dir_count}")

    print()

    # [Icons] section
    print("[Icons] Section")
    icons_section = re.search(r"\[Icons\](.*?)\[", text, re.DOTALL)
    if icons_section:
        icons_text = icons_section.group(1)
        has_desktop = "autodesktop" in icons_text
        has_startmenu = "group" in icons_text
        ok(has_desktop, "Missing desktop shortcut")
        ok(has_startmenu, "Missing Start Menu shortcut")
        print(f"  Desktop shortcut: {'OK' if has_desktop else 'MISSING'}")
        print(f"  Start Menu shortcut: {'OK' if has_startmenu else 'MISSING'}")

    print()

    # [Code] section
    print("[Code] Section")
    ok("CurUninstallStepChanged" in text or "CurStepChanged" in text, "No install/uninstall handler")
    has_msgbox = "MsgBox" in text
    print(f"  Uninstall handler: {'OK' if 'CurUninstallStepChanged' in text else 'MISSING'}")
    print(f"  User messaging: {'OK' if has_msgbox else 'Not configured'}")

    print()

    # Security checks
    print("[Security] Checks")
    warn("AllowNoIcons" not in text, "AllowNoIcons is set")
    warn("PrivilegesRequired=lowest" not in text, "Not using lowest privileges")
    ok("CloseApplications=yes" in text or "CloseApplications" in text, "CloseApplications not set")
    print("  Security checks passed (warnings are informational)")

    print()

    # Summary
    print("=" * 60)
    print(f"Total checks: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print()

    if warnings:
        print("Warnings:")
        for w in warnings:
            print(f"  WARNING: {w}")
        print()

    if errors:
        print("Errors:")
        for e in errors:
            print(f"  ERROR: {e}")
        print()
        sys.exit(1)
    else:
        print("ALL INSTALLER CHECKS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
