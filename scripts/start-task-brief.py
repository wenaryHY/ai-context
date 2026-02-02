#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LATEST = ROOT / "docs" / "task-briefs" / "latest.md"
TEMPLATE = ROOT / "examples" / "prompts" / "task-brief.md"


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


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_template(path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
    return "\n".join(lines).rstrip() + "\n"


def archive_current(by_branch: bool, by_title: bool) -> None:
    archive_script = ROOT / "scripts" / "archive-task-brief.py"
    args = ["python3", str(archive_script)]
    if by_branch:
        args.append("--by-branch")
    if by_title:
        args.append("--by-title")
    subprocess.run(
        args,
        cwd=ROOT,
        check=False,
    )


def write_latest(title: str, template: str, force: bool) -> None:
    if LATEST.exists() and not force:
        raise FileExistsError("latest.md exists. Use --force to overwrite.")
    header = "\n".join(
        [
            "# Task Brief (Latest)",
            "",
            "## Meta",
            f"- UpdatedAt: {utc_now()}",
            f"- Branch: {current_branch()}",
            f"- Title: {title}",
            "",
        ]
    )
    LATEST.write_text(header + template, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", default="TODO", help="brief title")
    parser.add_argument("--template", default=str(TEMPLATE), help="template path")
    parser.add_argument("--force", action="store_true", help="overwrite latest.md")
    parser.add_argument("--archive-current", action="store_true", help="archive current latest")
    parser.add_argument("--archive-by-branch", action="store_true", help="archive under branch name")
    parser.add_argument("--archive-by-title", action="store_true", help="archive under task title")
    args = parser.parse_args()

    template_path = Path(args.template)
    if not template_path.exists():
        print(f"Template not found: {template_path}")
        return 1

    if args.archive_current and LATEST.exists():
        archive_current(args.archive_by_branch, args.archive_by_title)

    template = load_template(template_path)
    try:
        write_latest(args.title, template, args.force)
    except FileExistsError as exc:
        print(exc)
        return 1

    print(f"Created task brief: {LATEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
