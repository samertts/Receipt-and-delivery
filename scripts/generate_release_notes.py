#!/usr/bin/env python3
"""Generate release notes from git history.

Usage:
    python scripts/generate_release_notes.py              # Current version
    python scripts/generate_release_notes.py --tag v1.2.0 # Specific tag
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return result.stdout.strip()


def get_version() -> str:
    return (ROOT / "VERSION").read_text().strip()


def get_last_tag() -> str:
    tag = run(["git", "describe", "--tags", "--abbrev=0", "HEAD^"])
    return tag if tag else ""


def get_commits_since(tag: str) -> list[dict]:
    range_spec = f"{tag}..HEAD" if tag else "HEAD"
    log = run([
        "git", "log", range_spec,
        "--pretty=format:%H|%s|%an|%ad",
        "--date=short",
    ])
    commits = []
    for line in log.splitlines():
        if "|" in line:
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append({
                    "hash": parts[0][:8],
                    "message": parts[1],
                    "author": parts[2],
                    "date": parts[3],
                })
    return commits


def categorize(commits: list[dict]) -> dict:
    categories = {
        "Added": [],
        "Changed": [],
        "Fixed": [],
        "Security": [],
        "Breaking": [],
        "Other": [],
    }
    for c in commits:
        msg = c["message"].lower()
        prefix = f"`{c['hash']}`"
        entry = f"- {c['message']} {prefix}"
        if msg.startswith("feat"):
            categories["Added"].append(entry)
        elif msg.startswith("fix"):
            categories["Fixed"].append(entry)
        elif msg.startswith("security") or "cve" in msg or "vuln" in msg:
            categories["Security"].append(entry)
        elif msg.startswith("breaking") or msg.startswith("refactor"):
            categories["Changed"].append(entry)
        elif msg.startswith("docs"):
            categories["Other"].append(entry)
        elif msg.startswith("chore") or msg.startswith("ci") or msg.startswith("build"):
            categories["Other"].append(entry)
        else:
            categories["Other"].append(entry)
    return categories


def generate(version: str, tag: str = "") -> str:
    last_tag = tag or get_last_tag()
    commits = get_commits_since(last_tag)
    categories = categorize(commits)

    lines = []
    lines.append(f"# Release Notes — v{version}")
    lines.append("")
    lines.append(f"**Release Date:** {run(['date', '+%Y-%m-%d'])}")
    if last_tag:
        lines.append(f"**Previous Release:** {last_tag}")
    lines.append(f"**Commits:** {len(commits)}")
    lines.append("")

    section_headers = {
        "Added": "Added",
        "Changed": "Changed",
        "Fixed": "Fixed",
        "Security": "Security",
        "Breaking": "Breaking Changes",
        "Other": "Other Changes",
    }

    for cat, header in section_headers.items():
        items = categories[cat]
        if items:
            lines.append(f"### {header}")
            lines.append("")
            for item in items:
                lines.append(item)
            lines.append("")

    if not any(categories.values()):
        lines.append("No changes recorded.")
        lines.append("")

    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    tag = ""
    if "--tag" in args:
        idx = args.index("--tag")
        if idx + 1 < len(args):
            tag = args[idx + 1]

    version = get_version()
    notes = generate(version, tag)

    output = ROOT / "release_notes.md"
    output.write_text(notes, encoding="utf-8")
    print(f"Release notes written to {output}")
    print()
    print(notes)


if __name__ == "__main__":
    main()
