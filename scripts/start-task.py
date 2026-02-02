#!/usr/bin/env python3
"""
Start Task - Enhanced task management with rollback integration.

This script:
1. Creates a snapshot before starting (for rollback)
2. Updates/creates the task brief
3. Optionally launches the AI agent

Usage:
    python3 scripts/start-task.py "Implement user login"
    python3 scripts/start-task.py "Fix bug #123" --type fix
    python3 scripts/start-task.py "Refactor auth" --agent aider
    python3 scripts/start-task.py "Add tests" --no-snapshot
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

from core.rollback_manager import RollbackManager
from core.agent_registry import AgentRegistry
from core.env_detector import EnvDetector


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
TEMPLATE = ROOT / "examples" / "prompts" / "task-brief.md"


def run_git(args: List[str]) -> str:
    """Run a git command and return output."""
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def current_branch() -> str:
    """Get current git branch."""
    return run_git(["rev-parse", "--abbrev-ref", "HEAD"]) or "unknown"


def utc_now() -> str:
    """Get current UTC time as ISO string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def create_task_brief(
    title: str,
    description: str,
    task_type: str,
    agent: Optional[str] = None,
    files: Optional[List[str]] = None,
    force: bool = False
) -> bool:
    """
    Create or update the task brief.
    
    Args:
        title: Task title
        description: Task description
        task_type: Type of task (feature, fix, refactor, etc.)
        agent: AI agent being used
        files: Files involved in the task
        force: Overwrite existing brief
    
    Returns:
        True if successful
    """
    if LATEST_BRIEF.exists() and not force:
        print(colorize(f"⚠️  Task brief already exists: {LATEST_BRIEF}", Colors.YELLOW))
        print("Use --force to overwrite, or archive first with:")
        print(f"  python3 {ROOT}/scripts/archive-task-brief.py")
        return False
    
    # Ensure directory exists
    LATEST_BRIEF.parent.mkdir(parents=True, exist_ok=True)
    
    content = f"""# Task Brief (Latest)

## Meta
- UpdatedAt: {utc_now()}
- Branch: {current_branch()}
- Title: {title}
- Type: {task_type}
- Agent: {agent or 'auto'}

## Description
{description}

## Scope
### In-scope
- {title}

### Out-of-scope
- (Define what's not included)

## Files
{chr(10).join(f'- {f}' for f in (files or [])) or '- (To be determined)'}

## Acceptance Criteria
- [ ] Task completed as described
- [ ] Tests pass
- [ ] Documentation updated (if needed)

## Notes
- Created by start-task.py
- Snapshot created for rollback capability
"""
    
    LATEST_BRIEF.write_text(content, encoding="utf-8")
    return True


def print_summary(
    task_id: str,
    title: str,
    task_type: str,
    agent: Optional[str],
    snapshot_id: Optional[str],
    files: Optional[List[str]]
) -> None:
    """Print task summary."""
    print(colorize("\n" + "═" * 60, Colors.CYAN))
    print(colorize("  Task Started Successfully", Colors.BOLD + Colors.GREEN))
    print(colorize("═" * 60, Colors.CYAN))
    
    print(f"\n{colorize('Task:', Colors.CYAN)} {title}")
    print(f"{colorize('Type:', Colors.CYAN)} {task_type}")
    print(f"{colorize('Agent:', Colors.CYAN)} {agent or 'auto-selected'}")
    
    if snapshot_id:
        print(f"{colorize('Snapshot:', Colors.CYAN)} {snapshot_id}")
    
    if files:
        print(f"{colorize('Files:', Colors.CYAN)}")
        for f in files[:5]:
            print(f"  - {f}")
        if len(files) > 5:
            print(f"  ... and {len(files) - 5} more")
    
    print(colorize("\n" + "─" * 60, Colors.GRAY))
    print(f"{colorize('Task Brief:', Colors.CYAN)} {LATEST_BRIEF}")
    print(colorize("─" * 60, Colors.GRAY))


def print_next_steps(agent: Optional[str], task_id: str) -> None:
    """Print next steps."""
    print(f"""
{colorize('Next Steps:', Colors.BOLD)}

{colorize('1.', Colors.CYAN)} Edit the task brief if needed:
   {LATEST_BRIEF}

{colorize('2.', Colors.CYAN)} Start working with your AI agent:
   {f'{agent}' if agent else 'Use your preferred AI tool'}

{colorize('3.', Colors.CYAN)} When done, finish the task:
   python3 {ROOT}/scripts/finish-task.py

{colorize('4.', Colors.CYAN)} If you need to rollback:
   python3 {ROOT}/scripts/rollback.py --latest
   # or view all snapshots:
   python3 {ROOT}/scripts/rollback.py --list
""")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Start a new AI-assisted development task",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Implement user login feature"
  %(prog)s "Fix authentication bug" --type fix
  %(prog)s "Refactor database layer" --agent aider
  %(prog)s "Add unit tests" --files src/auth.py src/utils.py
        """
    )
    
    parser.add_argument(
        "description",
        nargs="?",
        help="Task description (required unless --interactive)"
    )
    parser.add_argument(
        "--title", "-t",
        help="Task title (default: derived from description)"
    )
    parser.add_argument(
        "--type",
        choices=["feature", "fix", "refactor", "test", "docs", "chore", "custom"],
        default="feature",
        help="Type of task (default: feature)"
    )
    parser.add_argument(
        "--agent", "-a",
        help="AI agent to use (aider, claude-cli, etc.)"
    )
    parser.add_argument(
        "--files", "-f",
        nargs="+",
        help="Files involved in the task"
    )
    parser.add_argument(
        "--no-snapshot",
        action="store_true",
        help="Skip creating a snapshot"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing task brief"
    )
    parser.add_argument(
        "--launch",
        action="store_true",
        help="Launch AI agent after setup"
    )
    parser.add_argument(
        "--project-root", "-p",
        help="Project root directory"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive mode"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimal output"
    )
    
    args = parser.parse_args()
    
    # Validate input
    if not args.description and not args.interactive:
        parser.error("Task description is required (or use --interactive)")
    
    # Interactive mode
    if args.interactive:
        print(colorize("\n📝 Interactive Task Setup", Colors.CYAN))
        
        if not args.description:
            args.description = input(colorize("Task description: ", Colors.YELLOW)).strip()
        
        if not args.title:
            default_title = args.description[:50]
            title_input = input(colorize(f"Task title [{default_title}]: ", Colors.YELLOW)).strip()
            args.title = title_input or default_title
        
        if not args.type:
            type_input = input(colorize("Task type [feature]: ", Colors.YELLOW)).strip()
            args.type = type_input or "feature"
    
    # Derive title from description if not provided
    title = args.title or args.description[:50]
    if len(args.description) > 50:
        title += "..."
    
    # Determine project root
    project_root = Path(args.project_root) if args.project_root else ROOT.parent
    
    if not args.quiet:
        print(colorize("\n🚀 Starting new task...\n", Colors.BOLD))
    
    # Create snapshot (unless disabled)
    snapshot_id = None
    if not args.no_snapshot:
        if not args.quiet:
            print(colorize("Creating snapshot for rollback...", Colors.GRAY))
        
        manager = RollbackManager(project_root)
        task_id = f"task_{args.type}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        
        snapshot = manager.create_snapshot(
            task_id=task_id,
            task_description=args.description,
            agent=args.agent or "auto"
        )
        snapshot_id = snapshot.id
        
        if not args.quiet:
            print(colorize(f"  ✅ Snapshot created: {snapshot_id}", Colors.GREEN))
    
    # Create task brief
    if not args.quiet:
        print(colorize("Creating task brief...", Colors.GRAY))
    
    if not create_task_brief(
        title=title,
        description=args.description,
        task_type=args.type,
        agent=args.agent,
        files=args.files,
        force=args.force
    ):
        return 1
    
    if not args.quiet:
        print(colorize(f"  ✅ Task brief created: {LATEST_BRIEF}", Colors.GREEN))
    
    # Determine agent
    selected_agent = args.agent
    if not selected_agent:
        registry = AgentRegistry(project_root)
        recommended = registry.get_recommended_agent()
        if recommended:
            selected_agent = recommended.name.lower().replace(" ", "-")
    
    # Print summary
    if not args.quiet:
        print_summary(
            task_id=task_id if snapshot_id else "none",
            title=title,
            task_type=args.type,
            agent=selected_agent,
            snapshot_id=snapshot_id,
            files=args.files
        )
        print_next_steps(selected_agent, task_id if snapshot_id else "none")
    
    # Launch agent if requested
    if args.launch and selected_agent:
        if not args.quiet:
            print(colorize(f"\n🤖 Launching {selected_agent}...", Colors.CYAN))
        
        # Get adapter and launch
        registry = AgentRegistry(project_root)
        adapter = registry.get_adapter(selected_agent.replace("-", "_"))
        
        if adapter and hasattr(adapter, 'chat'):
            adapter.chat(initial_message=args.description, files=args.files)
        else:
            # Fallback to direct CLI launch
            import shutil
            cli_cmd = selected_agent
            if shutil.which(cli_cmd):
                subprocess.run([cli_cmd], cwd=project_root)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
