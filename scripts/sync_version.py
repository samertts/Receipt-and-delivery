#!/usr/bin/env python3
"""Version synchronization utility.

Ensures VERSION file is the single source of truth.
Syncs version to all downstream files (ISS, pyproject.toml, etc.).

Usage:
    python scripts/sync_version.py          # Sync and validate
    python scripts/sync_version.py --check  # Check only (CI)
    python scripts/sync_version.py --set 1.3.0  # Set version
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT / "VERSION"
ISS_FILE = ROOT / "lab_system" / "installer" / "LabReceipt.iss"
CHANGELOG_FILE = ROOT / "CHANGELOG.md"


def read_version() -> str:
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def set_version(version: str) -> None:
    VERSION_FILE.write_text(version + "\n", encoding="utf-8")


def sync_iss(version: str) -> bool:
    """Sync AppVersion in .iss file. Returns True if changed."""
    if not ISS_FILE.exists():
        return False
    text = ISS_FILE.read_text(encoding="utf-8")
    new_text = re.sub(r"(AppVersion=)[\d\w.-]+", f"\\g<1>{version}", text)
    if new_text != text:
        ISS_FILE.write_text(new_text, encoding="utf-8")
        return True
    return False


def validate_version(version: str) -> bool:
    """Validate semantic versioning format."""
    pattern = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$"
    return bool(re.match(pattern, version))


def check_changelog(version: str) -> bool:
    """Check if version is mentioned in CHANGELOG."""
    if not CHANGELOG_FILE.exists():
        return False
    text = CHANGELOG_FILE.read_text(encoding="utf-8")
    return version in text


def main():
    args = sys.argv[1:]

    if "--set" in args:
        idx = args.index("--set")
        if idx + 1 >= len(args):
            print("ERROR: --set requires a version argument")
            sys.exit(1)
        new_version = args[idx + 1]
        if not validate_version(new_version):
            print(f"ERROR: Invalid version format: {new_version}")
            print("Expected: MAJOR.MINOR.PATCH[-prerelease][+build]")
            sys.exit(1)
        set_version(new_version)
        sync_iss(new_version)
        print(f"Version set to {new_version}")
        print("  Updated: VERSION")
        print("  Updated: LabReceipt.iss")
        sys.exit(0)

    version = read_version()
    print(f"Current version: {version}")

    errors = []

    if not validate_version(version):
        errors.append(f"VERSION format invalid: {version}")

    if ISS_FILE.exists():
        iss_text = ISS_FILE.read_text(encoding="utf-8")
        iss_match = re.search(r"AppVersion=([\d\w.-]+)", iss_text)
        if iss_match:
            iss_version = iss_match.group(1)
            if iss_version != version:
                print(f"  ISS AppVersion: {iss_version} (MISMATCH)")
                if "--check" not in args:
                    sync_iss(version)
                    print(f"  Fixed: ISS AppVersion -> {version}")
                else:
                    errors.append(f"ISS AppVersion={iss_version} != VERSION={version}")
            else:
                print(f"  ISS AppVersion: {iss_version} (OK)")

    if not check_changelog(version):
        print(f"  CHANGELOG: version {version} not mentioned (WARNING)")

    if errors:
        print(f"\nERRORS: {len(errors)}")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\nAll version checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
