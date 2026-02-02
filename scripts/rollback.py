#!/usr/bin/env python3
"""
Rollback CLI - Command-line interface for managing AI task snapshots and rollbacks.

Usage:
    python3 scripts/rollback.py --list              # List all snapshots
    python3 scripts/rollback.py --latest            # Rollback to latest snapshot
    python3 scripts/rollback.py --id <snapshot_id>  # Rollback to specific snapshot
    python3 scripts/rollback.py --diff <snapshot_id> # View diff for snapshot
    python3 scripts/rollback.py --delete <id>       # Delete a snapshot
    python3 scripts/rollback.py --cleanup [count]   # Cleanup old snapshots
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, List

# Add parent directory to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from core.rollback_manager import RollbackManager, Snapshot, DiffResult


class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"


def colorize(text: str, color: str) -> str:
    """Apply color to text if terminal supports it."""
    if sys.stdout.isatty():
        return f"{color}{text}{Colors.RESET}"
    return text


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(colorize(f"\n{'='*60}", Colors.CYAN))
    print(colorize(f"  {text}", Colors.BOLD))
    print(colorize(f"{'='*60}\n", Colors.CYAN))


def print_snapshot(snapshot: Snapshot, index: int = None) -> None:
    """Print snapshot information in a formatted way."""
    prefix = f"[{index}] " if index is not None else ""
    
    print(f"{colorize(prefix + snapshot.id, Colors.BOLD)}")
    print(f"  {colorize('Created:', Colors.GRAY)} {snapshot.created_at}")
    print(f"  {colorize('Task:', Colors.GRAY)} {snapshot.task_description}")
    print(f"  {colorize('Agent:', Colors.GRAY)} {snapshot.agent}")
    print(f"  {colorize('Mode:', Colors.GRAY)} {snapshot.mode}")
    print(f"  {colorize('Files:', Colors.GRAY)} {len(snapshot.files_modified)} modified")
    if snapshot.files_modified:
        for f in snapshot.files_modified[:5]:
            print(f"    - {f}")
        if len(snapshot.files_modified) > 5:
            print(f"    ... and {len(snapshot.files_modified) - 5} more")
    print()


def print_diff(diff: DiffResult) -> None:
    """Print diff information in a formatted way."""
    if diff.files_added:
        print(colorize("Added files:", Colors.GREEN))
        for f in diff.files_added:
            print(f"  + {f}")
    
    if diff.files_modified:
        print(colorize("Modified files:", Colors.YELLOW))
        for f in diff.files_modified:
            print(f"  ~ {f}")
    
    if diff.files_deleted:
        print(colorize("Deleted files:", Colors.RED))
        for f in diff.files_deleted:
            print(f"  - {f}")
    
    if not (diff.files_added or diff.files_modified or diff.files_deleted):
        print(colorize("No changes detected.", Colors.GRAY))
    
    if diff.diff_content:
        print(colorize("\nDiff content:", Colors.CYAN))
        print("-" * 40)
        # Colorize diff output
        for line in diff.diff_content.splitlines()[:50]:
            if line.startswith("+") and not line.startswith("+++"):
                print(colorize(line, Colors.GREEN))
            elif line.startswith("-") and not line.startswith("---"):
                print(colorize(line, Colors.RED))
            elif line.startswith("@@"):
                print(colorize(line, Colors.CYAN))
            else:
                print(line)
        
        lines = diff.diff_content.splitlines()
        if len(lines) > 50:
            print(colorize(f"\n... ({len(lines) - 50} more lines)", Colors.GRAY))


def cmd_list(manager: RollbackManager) -> int:
    """List all available snapshots."""
    snapshots = manager.list_snapshots()
    
    if not snapshots:
        print(colorize("No snapshots found.", Colors.YELLOW))
        print("Create a snapshot with: python3 scripts/start-task.py 'task description'")
        return 0
    
    print_header(f"Available Snapshots ({len(snapshots)})")
    
    for i, snapshot in enumerate(snapshots, 1):
        print_snapshot(snapshot, i)
    
    return 0


def cmd_latest(manager: RollbackManager, dry_run: bool = False) -> int:
    """Rollback to the latest snapshot."""
    snapshot = manager.get_latest_snapshot()
    
    if not snapshot:
        print(colorize("No snapshots available for rollback.", Colors.RED))
        return 1
    
    print_header("Rolling Back to Latest Snapshot")
    print_snapshot(snapshot)
    
    if dry_run:
        print(colorize("Dry run mode - no changes made.", Colors.YELLOW))
        return 0
    
    # Show diff first
    diff = manager.diff(snapshot.id)
    if diff:
        print(colorize("Changes that will be reverted:", Colors.CYAN))
        print_diff(diff)
        print()
    
    # Confirm rollback
    if sys.stdin.isatty():
        response = input(colorize("Proceed with rollback? [y/N] ", Colors.YELLOW))
        if response.lower() != "y":
            print(colorize("Rollback cancelled.", Colors.GRAY))
            return 0
    
    if manager.rollback(snapshot.id):
        print(colorize(f"✅ Successfully rolled back to: {snapshot.id}", Colors.GREEN))
        return 0
    else:
        print(colorize(f"❌ Failed to rollback to: {snapshot.id}", Colors.RED))
        return 1


def cmd_rollback_by_id(
    manager: RollbackManager,
    snapshot_id: str,
    files: Optional[List[str]] = None,
    dry_run: bool = False
) -> int:
    """Rollback to a specific snapshot."""
    snapshot = manager.get_snapshot(snapshot_id)
    
    if not snapshot:
        print(colorize(f"Snapshot not found: {snapshot_id}", Colors.RED))
        print("\nAvailable snapshots:")
        for s in manager.list_snapshots()[:5]:
            print(f"  - {s.id}")
        return 1
    
    print_header(f"Rolling Back to: {snapshot_id}")
    print_snapshot(snapshot)
    
    if files:
        print(colorize(f"Selective rollback for {len(files)} files:", Colors.CYAN))
        for f in files:
            print(f"  - {f}")
        print()
    
    if dry_run:
        print(colorize("Dry run mode - no changes made.", Colors.YELLOW))
        return 0
    
    # Confirm rollback
    if sys.stdin.isatty():
        response = input(colorize("Proceed with rollback? [y/N] ", Colors.YELLOW))
        if response.lower() != "y":
            print(colorize("Rollback cancelled.", Colors.GRAY))
            return 0
    
    if manager.rollback(snapshot_id, files):
        print(colorize(f"✅ Successfully rolled back to: {snapshot_id}", Colors.GREEN))
        return 0
    else:
        print(colorize(f"❌ Failed to rollback to: {snapshot_id}", Colors.RED))
        return 1


def cmd_diff(manager: RollbackManager, snapshot_id: str) -> int:
    """Show diff for a snapshot."""
    snapshot = manager.get_snapshot(snapshot_id)
    
    if not snapshot:
        print(colorize(f"Snapshot not found: {snapshot_id}", Colors.RED))
        return 1
    
    print_header(f"Diff for: {snapshot_id}")
    print_snapshot(snapshot)
    
    diff = manager.diff(snapshot_id)
    if diff:
        print_diff(diff)
    else:
        print(colorize("Unable to generate diff.", Colors.YELLOW))
    
    return 0


def cmd_delete(manager: RollbackManager, snapshot_id: str) -> int:
    """Delete a snapshot."""
    snapshot = manager.get_snapshot(snapshot_id)
    
    if not snapshot:
        print(colorize(f"Snapshot not found: {snapshot_id}", Colors.RED))
        return 1
    
    print_header(f"Deleting Snapshot: {snapshot_id}")
    print_snapshot(snapshot)
    
    # Confirm deletion
    if sys.stdin.isatty():
        response = input(colorize("Are you sure you want to delete this snapshot? [y/N] ", Colors.YELLOW))
        if response.lower() != "y":
            print(colorize("Deletion cancelled.", Colors.GRAY))
            return 0
    
    if manager.delete_snapshot(snapshot_id):
        print(colorize(f"✅ Snapshot deleted: {snapshot_id}", Colors.GREEN))
        return 0
    else:
        print(colorize(f"❌ Failed to delete: {snapshot_id}", Colors.RED))
        return 1


def cmd_cleanup(manager: RollbackManager, keep_count: int) -> int:
    """Cleanup old snapshots."""
    snapshots = manager.list_snapshots()
    
    if len(snapshots) <= keep_count:
        print(colorize(f"No cleanup needed. {len(snapshots)} snapshots (keeping {keep_count}).", Colors.GREEN))
        return 0
    
    to_delete = len(snapshots) - keep_count
    print_header(f"Cleanup: Removing {to_delete} Old Snapshots")
    
    print(f"Current snapshots: {len(snapshots)}")
    print(f"Keeping: {keep_count}")
    print(f"To delete: {to_delete}")
    print()
    
    print("Snapshots to be deleted:")
    for snapshot in snapshots[keep_count:]:
        print(f"  - {snapshot.id} ({snapshot.task_description})")
    print()
    
    # Confirm cleanup
    if sys.stdin.isatty():
        response = input(colorize(f"Delete {to_delete} snapshots? [y/N] ", Colors.YELLOW))
        if response.lower() != "y":
            print(colorize("Cleanup cancelled.", Colors.GRAY))
            return 0
    
    deleted = manager.cleanup_old_snapshots(keep_count)
    print(colorize(f"✅ Deleted {deleted} snapshots.", Colors.GREEN))
    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Manage AI task snapshots and rollbacks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list                    List all snapshots
  %(prog)s --latest                  Rollback to latest snapshot
  %(prog)s --id snap_20260203_143022 Rollback to specific snapshot
  %(prog)s --diff snap_20260203_143022  View diff for snapshot
  %(prog)s --id snap_xxx --files src/api.py  Selective rollback
  %(prog)s --delete snap_xxx         Delete a snapshot
  %(prog)s --cleanup 10              Keep only 10 most recent snapshots
        """
    )
    
    # Action arguments (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available snapshots"
    )
    action_group.add_argument(
        "--latest",
        action="store_true",
        help="Rollback to the most recent snapshot"
    )
    action_group.add_argument(
        "--id", "-i",
        metavar="SNAPSHOT_ID",
        help="Rollback to a specific snapshot by ID"
    )
    action_group.add_argument(
        "--diff", "-d",
        metavar="SNAPSHOT_ID",
        help="Show diff between current state and snapshot"
    )
    action_group.add_argument(
        "--delete",
        metavar="SNAPSHOT_ID",
        help="Delete a specific snapshot"
    )
    action_group.add_argument(
        "--cleanup",
        metavar="KEEP_COUNT",
        type=int,
        nargs="?",
        const=10,
        help="Remove old snapshots, keeping only the most recent (default: 10)"
    )
    
    # Optional arguments
    parser.add_argument(
        "--files", "-f",
        nargs="+",
        metavar="FILE",
        help="Specific files to rollback (for selective rollback)"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--project-root", "-p",
        metavar="PATH",
        help="Project root directory (default: current directory)"
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompts"
    )
    
    args = parser.parse_args()
    
    # Initialize manager
    project_root = Path(args.project_root) if args.project_root else None
    manager = RollbackManager(project_root)
    
    # Handle --yes flag by making stdin non-interactive
    if args.yes:
        # Redirect stdin to prevent prompts
        import io
        sys.stdin = io.StringIO("y\n")
    
    # Execute command
    if args.list:
        return cmd_list(manager)
    elif args.latest:
        return cmd_latest(manager, args.dry_run)
    elif args.id:
        return cmd_rollback_by_id(manager, args.id, args.files, args.dry_run)
    elif args.diff:
        return cmd_diff(manager, args.diff)
    elif args.delete:
        return cmd_delete(manager, args.delete)
    elif args.cleanup is not None:
        return cmd_cleanup(manager, args.cleanup)
    else:
        # Default: list snapshots
        return cmd_list(manager)


if __name__ == "__main__":
    sys.exit(main())
