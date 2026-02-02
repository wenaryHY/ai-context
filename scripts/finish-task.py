#!/usr/bin/env python3
"""
Finish Task - Complete a task and archive the task brief.

This script:
1. Validates that changes are complete
2. Runs any configured validations
3. Archives the task brief
4. Optionally generates a commit message

Usage:
    python3 scripts/finish-task.py
    python3 scripts/finish-task.py --commit
    python3 scripts/finish-task.py --no-archive
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

# Add script directory to path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))


class Colors:
    """ANSI color codes."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"


def colorize(text: str, color: str) -> str:
    """Apply color if terminal supports it."""
    if sys.stdout.isatty():
        return f"{color}{text}{Colors.RESET}"
    return text


# Root and paths
ROOT = SCRIPT_DIR.parent
LATEST_BRIEF = ROOT / "docs" / "task-briefs" / "latest.md"
ARCHIVE_DIR = ROOT / "docs" / "task-briefs" / "archive"


def run_git(args: List[str]) -> tuple[int, str, str]:
    """Run a git command and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT.parent,  # Project root
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def get_changed_files() -> List[str]:
    """Get list of changed files."""
    code, stdout, _ = run_git(["status", "--porcelain"])
    if code != 0:
        return []
    
    files = []
    for line in stdout.splitlines():
        if line.strip():
            # Format: "XY filename"
            filename = line[3:].strip()
            if " -> " in filename:
                filename = filename.split(" -> ")[-1]
            files.append(filename)
    return files


def parse_task_brief() -> dict:
    """Parse the task brief to extract metadata."""
    if not LATEST_BRIEF.exists():
        return {}
    
    content = LATEST_BRIEF.read_text(encoding="utf-8")
    metadata = {}
    
    for line in content.splitlines():
        if line.startswith("- Title:"):
            metadata["title"] = line.split(":", 1)[1].strip()
        elif line.startswith("- Type:"):
            metadata["type"] = line.split(":", 1)[1].strip()
        elif line.startswith("- Branch:"):
            metadata["branch"] = line.split(":", 1)[1].strip()
    
    # Extract description
    if "## Description" in content:
        desc_start = content.index("## Description") + len("## Description")
        desc_end = content.find("##", desc_start)
        if desc_end == -1:
            desc_end = len(content)
        metadata["description"] = content[desc_start:desc_end].strip()
    
    return metadata


def run_validation() -> bool:
    """Run validation script if available."""
    validate_script = ROOT / "scripts" / "validate-context.py"
    
    if not validate_script.exists():
        return True
    
    print(colorize("Running validation...", Colors.GRAY))
    result = subprocess.run(
        ["python3", str(validate_script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        print(colorize("❌ Validation failed:", Colors.RED))
        print(result.stdout)
        print(result.stderr)
        return False
    
    print(colorize("✅ Validation passed", Colors.GREEN))
    return True


def archive_task_brief(by_branch: bool = False, by_title: bool = False) -> bool:
    """Archive the current task brief."""
    archive_script = ROOT / "scripts" / "archive-task-brief.py"
    
    if not archive_script.exists():
        # Manual archive
        if not LATEST_BRIEF.exists():
            return True
        
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        archive_path = ARCHIVE_DIR / f"task_{timestamp}.md"
        
        import shutil
        shutil.copy(LATEST_BRIEF, archive_path)
        LATEST_BRIEF.unlink()
        print(colorize(f"✅ Archived to: {archive_path}", Colors.GREEN))
        return True
    
    args = ["python3", str(archive_script)]
    if by_branch:
        args.append("--by-branch")
    if by_title:
        args.append("--by-title")
    
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(colorize("✅ Task brief archived", Colors.GREEN))
        return True
    else:
        print(colorize(f"⚠️  Archive warning: {result.stderr or result.stdout}", Colors.YELLOW))
        return True  # Non-fatal


def generate_commit_message(metadata: dict, files: List[str]) -> str:
    """Generate a commit message based on task brief."""
    task_type = metadata.get("type", "chore")
    title = metadata.get("title", "Complete task")
    description = metadata.get("description", "")
    
    # Conventional commit format
    type_map = {
        "feature": "feat",
        "fix": "fix",
        "refactor": "refactor",
        "test": "test",
        "docs": "docs",
        "chore": "chore",
    }
    commit_type = type_map.get(task_type, "chore")
    
    message = f"{commit_type}: {title}"
    
    if description:
        # Truncate description if too long
        if len(description) > 200:
            description = description[:197] + "..."
        message += f"\n\n{description}"
    
    if files:
        message += f"\n\nFiles changed ({len(files)}):"
        for f in files[:10]:
            message += f"\n- {f}"
        if len(files) > 10:
            message += f"\n... and {len(files) - 10} more"
    
    return message


def create_commit(message: str) -> bool:
    """Create a git commit with the given message."""
    # Stage all changes
    code, _, stderr = run_git(["add", "-A"])
    if code != 0:
        print(colorize(f"❌ Failed to stage changes: {stderr}", Colors.RED))
        return False
    
    # Commit
    code, stdout, stderr = run_git(["commit", "-m", message])
    if code != 0:
        if "nothing to commit" in stdout or "nothing to commit" in stderr:
            print(colorize("ℹ️  Nothing to commit", Colors.YELLOW))
            return True
        print(colorize(f"❌ Commit failed: {stderr}", Colors.RED))
        return False
    
    print(colorize("✅ Changes committed", Colors.GREEN))
    return True


def print_summary(
    metadata: dict,
    files: List[str],
    archived: bool,
    committed: bool
) -> None:
    """Print task completion summary."""
    print(colorize("\n" + "═" * 60, Colors.CYAN))
    print(colorize("  Task Completed", Colors.BOLD + Colors.GREEN))
    print(colorize("═" * 60, Colors.CYAN))
    
    print(f"\n{colorize('Title:', Colors.CYAN)} {metadata.get('title', 'Unknown')}")
    print(f"{colorize('Type:', Colors.CYAN)} {metadata.get('type', 'Unknown')}")
    print(f"{colorize('Files changed:', Colors.CYAN)} {len(files)}")
    print(f"{colorize('Archived:', Colors.CYAN)} {'Yes' if archived else 'No'}")
    print(f"{colorize('Committed:', Colors.CYAN)} {'Yes' if committed else 'No'}")
    
    print(colorize("\n" + "─" * 60, Colors.GRAY))


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Complete a task and archive the task brief",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--commit", "-c",
        action="store_true",
        help="Create a git commit with generated message"
    )
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="Skip archiving the task brief"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validation"
    )
    parser.add_argument(
        "--by-branch",
        action="store_true",
        help="Archive using branch name in filename"
    )
    parser.add_argument(
        "--by-title",
        action="store_true",
        help="Archive using task title in filename"
    )
    parser.add_argument(
        "--message", "-m",
        help="Custom commit message (overrides generated)"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimal output"
    )
    
    args = parser.parse_args()
    
    if not args.quiet:
        print(colorize("\n📋 Finishing task...\n", Colors.BOLD))
    
    # Check if task brief exists
    if not LATEST_BRIEF.exists():
        print(colorize("❌ No active task brief found.", Colors.RED))
        print(f"Expected: {LATEST_BRIEF}")
        print("\nStart a new task with:")
        print(f"  python3 {ROOT}/scripts/start-task.py 'task description'")
        return 1
    
    # Parse task brief
    metadata = parse_task_brief()
    
    if not args.quiet:
        print(colorize(f"Task: {metadata.get('title', 'Unknown')}", Colors.CYAN))
    
    # Get changed files
    files = get_changed_files()
    
    if not args.quiet:
        print(colorize(f"Changed files: {len(files)}", Colors.GRAY))
    
    # Run validation
    if not args.no_validate:
        if not run_validation():
            if not args.quiet:
                print(colorize("\n⚠️  Fix validation issues before completing the task.", Colors.YELLOW))
            return 1
    
    if args.dry_run:
        print(colorize("\n[Dry run - no changes made]", Colors.YELLOW))
        
        # Show what would happen
        if not args.no_archive:
            print(f"Would archive: {LATEST_BRIEF}")
        
        if args.commit:
            message = args.message or generate_commit_message(metadata, files)
            print(f"Would commit with message:\n{message}")
        
        return 0
    
    # Archive task brief
    archived = False
    if not args.no_archive:
        archived = archive_task_brief(args.by_branch, args.by_title)
    
    # Create commit if requested
    committed = False
    if args.commit:
        message = args.message or generate_commit_message(metadata, files)
        
        if not args.quiet:
            print(colorize("\nCommit message:", Colors.CYAN))
            print(colorize("─" * 40, Colors.GRAY))
            print(message)
            print(colorize("─" * 40, Colors.GRAY))
        
        committed = create_commit(message)
    
    # Print summary
    if not args.quiet:
        print_summary(metadata, files, archived, committed)
    
    if not args.quiet:
        print(colorize("\n✅ Task completed successfully!", Colors.GREEN))
        
        if not args.commit:
            print(colorize("\nTo commit changes:", Colors.GRAY))
            print(f"  git add -A && git commit -m '{metadata.get('title', 'Complete task')}'")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
