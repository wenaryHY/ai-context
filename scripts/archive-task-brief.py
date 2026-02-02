#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LATEST = ROOT / "docs" / "task-briefs" / "latest.md"
ARCHIVE_DIR = ROOT / "docs" / "task-briefs" / "archive"


def read_latest() -> str:
    return LATEST.read_text(encoding="utf-8")


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def current_branch() -> str:
    return run_git(["rev-parse", "--abbrev-ref", "HEAD"]) or "unknown"


def extract_meta_value(content: str, key: str) -> str:
    prefix = f"- {key}:"
    for line in content.splitlines():
        if line.strip().startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""


def extract_title(content: str) -> str:
    value = extract_meta_value(content, "Title")
    return value or "untitled"


def extract_branch(content: str) -> str:
    value = extract_meta_value(content, "Branch")
    return value or current_branch()


def slugify(value: str, max_len: int = 64) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    if not cleaned:
        return "untitled"
    return cleaned[:max_len]


def find_matching_archive(content: str, archive_dir: Path) -> Path | None:
    if not archive_dir.exists():
        return None
    for path in archive_dir.rglob("*.md"):
        try:
            if path.read_text(encoding="utf-8") == content:
                return path
        except OSError:
            continue
    return None


def archive_latest(by_branch: bool, by_title: bool) -> Path | None:
    if not LATEST.exists():
        raise FileNotFoundError(f"Missing task brief: {LATEST}")
    content = read_latest()
    if not content.strip():
        raise ValueError("Task brief is empty.")
    archive_dir = ARCHIVE_DIR
    if by_branch:
        archive_dir = archive_dir / slugify(extract_branch(content))
    if by_title:
        archive_dir = archive_dir / slugify(extract_title(content))
    match = find_matching_archive(content, archive_dir)
    if match:
        return None
    archive_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d--%H%M%SZ")
    path = archive_dir / f"{stamp}.md"
    path.write_text(content, encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify latest is archived")
    parser.add_argument("--flat", action="store_true", help="archive in a flat folder")
    parser.add_argument("--no-branch", action="store_true", help="disable branch directory")
    parser.add_argument("--no-title", action="store_true", help="disable title directory")
    args = parser.parse_args()

    if args.check:
        content = read_latest()
        match = find_matching_archive(content, ARCHIVE_DIR)
        if not match:
            print("Task brief archive missing. Run scripts/archive-task-brief.py.")
            return 1
        return 0

    if args.flat:
        by_branch = False
        by_title = False
    else:
        by_branch = not args.no_branch
        by_title = not args.no_title

    archived = archive_latest(by_branch, by_title)
    if archived is None:
        print("Task brief already archived.")
        return 0
    print(f"Archived task brief to {archived}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
