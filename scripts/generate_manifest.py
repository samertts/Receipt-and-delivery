#!/usr/bin/env python3
"""Generate artifact checksums and manifest.

Usage:
    python scripts/generate_manifest.py dist/LabReceiptSystem.exe installer/Output/LabReceiptSetup.exe
"""

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha512(path: Path) -> str:
    h = hashlib.sha512()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=ROOT
        )
        return result.stdout.strip()[:40]
    except Exception:
        return "unknown"


def git_tag() -> str:
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--exact-match", "HEAD"],
            capture_output=True, text=True, cwd=ROOT
        )
        tag = result.stdout.strip()
        if tag:
            return tag
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=7", "HEAD"],
            capture_output=True, text=True, cwd=ROOT
        )
        return result.stdout.strip() or "untagged"
    except Exception:
        return "unknown"


def git_branch() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=ROOT
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def generate_checksums(files: list[Path]) -> str:
    lines = []
    for f in files:
        if f.exists():
            lines.append(f"{sha256(f)}  {f.name}")
    return "\n".join(lines)


def generate_manifest(files: list[Path]) -> dict:
    version = (ROOT / "VERSION").read_text().strip()
    artifacts = []
    for f in files:
        if f.exists():
            artifacts.append({
                "name": f.name,
                "size_bytes": f.stat().st_size,
                "sha256": sha256(f),
                "sha512": sha512(f),
            })

    return {
        "version": version,
        "commit": git_commit(),
        "tag": git_tag(),
        "branch": git_branch(),
        "build_date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "builder": os.environ.get("GITHUB_ACTOR", os.environ.get("USER", "unknown")),
        "artifacts": artifacts,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: generate_manifest.py <file1> [file2] ...")
        sys.exit(1)

    files = [Path(f) for f in sys.argv[1:]]
    existing = [f for f in files if f.exists()]
    missing = [f for f in files if not f.exists()]

    if missing:
        print("WARNING: Missing files:")
        for f in missing:
            print(f"  - {f}")

    if not existing:
        print("ERROR: No files to process")
        sys.exit(1)

    # Generate checksums file
    checksums = generate_checksums(existing)
    checksums_file = ROOT / "checksums.sha256"
    checksums_file.write_text(checksums + "\n", encoding="utf-8")
    print(f"Checksums written to {checksums_file}")

    # Generate manifest
    manifest = generate_manifest(existing)
    manifest_file = ROOT / "manifest.json"
    manifest_file.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Manifest written to {manifest_file}")

    # Print summary
    print()
    print("=== Artifact Summary ===")
    print(f"Version: {manifest['version']}")
    print(f"Commit: {manifest['commit'][:12]}")
    print(f"Tag: {manifest['tag']}")
    print(f"Branch: {manifest['branch']}")
    print(f"Date: {manifest['build_date']}")
    print()
    for a in manifest["artifacts"]:
        size_mb = a["size_bytes"] / 1024 / 1024
        print(f"  {a['name']}: {size_mb:.1f} MB")
        print(f"    SHA256: {a['sha256'][:32]}...")


if __name__ == "__main__":
    main()
