#!/usr/bin/env python3
"""
AI Context Toolkit - One-Click Initialization Script

Initialize a project for AI-assisted development with:
- Environment detection
- AI agent selection
- Configuration generation
- Project setup

Usage:
    python3 scripts/init.py                     # Auto-detect and initialize
    python3 scripts/init.py --interactive       # Interactive mode
    python3 scripts/init.py --agent aider       # Use specific agent
    python3 scripts/init.py --config            # Use config file preferences
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, List

# Add script directory to path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from core.env_detector import EnvDetector, EnvironmentInfo
from core.agent_registry import AgentRegistry, AgentInfo


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


def print_banner() -> None:
    """Print welcome banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════╗
    ║       AI Context Toolkit - Project Initialization     ║
    ║                                                       ║
    ║   One-click setup for AI-assisted development         ║
    ╚═══════════════════════════════════════════════════════╝
    """
    print(colorize(banner, Colors.CYAN))


def print_section(title: str) -> None:
    """Print a section header."""
    print(colorize(f"\n{'─'*60}", Colors.GRAY))
    print(colorize(f"  {title}", Colors.BOLD))
    print(colorize(f"{'─'*60}", Colors.GRAY))


def print_env_summary(env: EnvironmentInfo) -> None:
    """Print environment detection summary."""
    print_section("Environment Detection")
    
    print(f"\n{colorize('System:', Colors.CYAN)}")
    print(f"  OS: {env.os_type} ({env.architecture})")
    print(f"  Shell: {env.shell}")
    
    print(f"\n{colorize('Languages:', Colors.CYAN)}")
    for lang in [env.python, env.node, env.java, env.go, env.rust]:
        if lang and lang.available:
            print(f"  ✅ {lang.name}: {lang.version or 'unknown'}")
        elif lang:
            print(f"  ❌ {lang.name}: not installed")
    
    print(f"\n{colorize('Project:', Colors.CYAN)}")
    print(f"  Type: {env.project_type}")
    if env.frameworks:
        print(f"  Frameworks: {', '.join(env.frameworks)}")
    
    if env.git and env.git.available:
        git_info = env.git.details
        print(f"\n{colorize('Git:', Colors.CYAN)}")
        if git_info.get("is_repo"):
            print(f"  Repository: ✅")
            print(f"  Branch: {git_info.get('branch', 'unknown')}")
            if git_info.get("has_uncommitted_changes"):
                print(f"  {colorize('⚠️  Uncommitted changes detected', Colors.YELLOW)}")
        else:
            print(f"  Repository: ❌ (not a git repo)")


def print_agents_summary(agents: List[AgentInfo]) -> None:
    """Print AI agents summary."""
    print_section("AI Agents Detection")
    
    available = [a for a in agents if a.available and a.api_key_configured]
    
    print(f"\n{colorize('Available and configured:', Colors.GREEN)}")
    if available:
        for agent in available:
            print(f"  ✅ {agent.name} (v{agent.version or 'unknown'})")
    else:
        print(f"  {colorize('No agents available', Colors.YELLOW)}")
    
    print(f"\n{colorize('Installed but not configured:', Colors.YELLOW)}")
    needs_config = [a for a in agents if a.available and not a.api_key_configured]
    if needs_config:
        for agent in needs_config:
            print(f"  ⚠️  {agent.name} - needs API key")
    else:
        print(f"  None")
    
    print(f"\n{colorize('Not installed:', Colors.GRAY)}")
    not_installed = [a for a in agents if not a.available]
    if not_installed:
        for agent in not_installed[:5]:
            print(f"  ❌ {agent.name}")
        if len(not_installed) > 5:
            print(f"  ... and {len(not_installed) - 5} more")


def interactive_agent_selection(registry: AgentRegistry) -> Optional[str]:
    """Interactive agent selection."""
    available = registry.get_available_agents()
    
    if not available:
        print(colorize("\n❌ No AI agents available.", Colors.RED))
        print("Please install and configure at least one AI agent.")
        print("\nRecommended options:")
        print("  1. Aider: pip install aider-chat")
        print("  2. Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable")
        return None
    
    print(colorize("\n📋 Select an AI agent:", Colors.CYAN))
    for i, agent in enumerate(available, 1):
        print(f"  [{i}] {agent.name} (v{agent.version or 'unknown'})")
    print(f"  [0] Auto-select (recommended)")
    
    while True:
        try:
            choice = input(colorize("\nEnter choice [0]: ", Colors.YELLOW)).strip()
            if not choice or choice == "0":
                return None  # Auto-select
            
            idx = int(choice) - 1
            if 0 <= idx < len(available):
                return available[idx].name.lower().replace(" ", "-")
            else:
                print(colorize("Invalid choice. Please try again.", Colors.RED))
        except ValueError:
            print(colorize("Please enter a number.", Colors.RED))


def generate_cursorrules(project_root: Path, env: EnvironmentInfo) -> None:
    """Generate .cursorrules file for Cursor IDE."""
    rules = ["# AI Context Rules (Auto-generated)", ""]
    
    rules.append("## Core Principles")
    rules.append("- Follow naming conventions: self-descriptive, no ambiguous names")
    rules.append("- Maintain clear DTO/VO/Request/Response boundaries")
    rules.append("- Update contracts (OpenAPI/Proto) before implementation")
    rules.append("")
    
    if env.project_type in ("frontend", "fullstack"):
        rules.append("## Frontend Rules")
        rules.append("- Global styles in SCSS entry point")
        rules.append("- Component styles: scoped only for local adjustments")
        rules.append("- Data management in Store/Composables, not components")
        rules.append("")
    
    if env.project_type in ("backend", "fullstack"):
        rules.append("## Backend Rules")
        rules.append("- Controllers only orchestrate; business logic in Services")
        rules.append("- Unified exception mapping, no leaking internal errors")
        rules.append("- Clear transaction boundaries")
        rules.append("")
    
    rules.append("## Workflow")
    rules.append("- Update task brief before making changes: docs/task-briefs/latest.md")
    rules.append("- Create snapshot before major changes: python3 scripts/rollback.py")
    rules.append("- Run validation after changes: python3 scripts/validate-context.py")
    
    cursorrules_path = project_root / ".cursorrules"
    cursorrules_path.write_text("\n".join(rules), encoding="utf-8")
    print(f"  ✅ Generated: .cursorrules")


def generate_claude_context(project_root: Path, env: EnvironmentInfo, agent: Optional[str]) -> None:
    """Generate CLAUDE.md for Claude Code / Project context."""
    content = f"""# Project Context for AI Assistants

## Project Overview
- **Type**: {env.project_type}
- **Frameworks**: {', '.join(env.frameworks) if env.frameworks else 'None detected'}
- **Root**: {project_root}

## Development Rules
Follow the rules in `ai-context/`:
- `core/core.md` - Core development principles
- `frontend.md` - Frontend conventions
- `backend.md` - Backend conventions

## AI Agent
- **Preferred**: {agent or 'Auto-selected'}

## Quick Commands

```bash
# Initialize environment
python3 ai-context/scripts/init.py

# Start a new task
python3 ai-context/scripts/start-task.py "task description"

# Create snapshot (for rollback)
python3 ai-context/scripts/rollback.py --list

# Finish task
python3 ai-context/scripts/finish-task.py
```

## Task Brief Workflow
1. Before changes: Update `docs/task-briefs/latest.md`
2. Make changes with AI assistance
3. Verify: `python3 scripts/validate-context.py`
4. Archive: `python3 scripts/archive-task-brief.py`
"""
    
    claude_path = project_root / "CLAUDE.md"
    claude_path.write_text(content, encoding="utf-8")
    print(f"  ✅ Generated: CLAUDE.md")


def generate_config_files(project_root: Path, agent: Optional[str]) -> None:
    """Generate configuration files."""
    config_dir = project_root / "ai-context" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Try to import yaml, fall back to json
    try:
        import yaml
        HAS_YAML = True
    except ImportError:
        HAS_YAML = False
    
    # agents config
    agents_config = {
        "preferences": {
            "preferred_agent": agent,
            "auto_snapshot": True,
            "auto_commit": False,
        },
        "agents": {
            "aider": {
                "enabled": True,
                "model": "gpt-4",
                "auto_commits": False,
            },
            "claude-cli": {
                "enabled": True,
                "model": "claude-3.5-sonnet",
                "max_tokens": 4096,
            },
        },
    }
    
    if HAS_YAML:
        agents_path = config_dir / "agents.yaml"
        agents_path.write_text(
            yaml.dump(agents_config, default_flow_style=False, allow_unicode=True),
            encoding="utf-8"
        )
        print(f"  ✅ Generated: config/agents.yaml")
    else:
        agents_path = config_dir / "agents.json"
        agents_path.write_text(
            json.dumps(agents_config, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"  ✅ Generated: config/agents.json")
    
    # environments config
    env_config = {
        "snapshot": {
            "mode": "auto",
            "keep_count": 10,
        },
        "validation": {
            "require_task_brief": True,
            "require_archive": True,
        },
    }
    
    if HAS_YAML:
        env_path = config_dir / "environments.yaml"
        env_path.write_text(
            yaml.dump(env_config, default_flow_style=False, allow_unicode=True),
            encoding="utf-8"
        )
        print(f"  ✅ Generated: config/environments.yaml")
    else:
        env_path = config_dir / "environments.json"
        env_path.write_text(
            json.dumps(env_config, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"  ✅ Generated: config/environments.json")


def setup_project(
    project_root: Path,
    env: EnvironmentInfo,
    agent: Optional[str],
    skip_generation: bool = False
) -> bool:
    """Set up the project for AI-assisted development."""
    print_section("Project Setup")
    
    if skip_generation:
        print(colorize("  Skipping file generation (--no-generate)", Colors.YELLOW))
        return True
    
    try:
        # Ensure ai-context directory exists
        ai_context_dir = project_root / "ai-context"
        if not ai_context_dir.exists():
            print(colorize(f"  ⚠️  ai-context directory not found at {project_root}", Colors.YELLOW))
            print("  This script should be run from the ai-context project root")
            print("  or the ai-context toolkit should be copied to your project.")
            return False
        
        # Generate configuration files
        generate_config_files(project_root, agent)
        
        # Generate IDE integration files
        generate_cursorrules(project_root, env)
        generate_claude_context(project_root, env, agent)
        
        print(colorize("\n✅ Project setup complete!", Colors.GREEN))
        return True
        
    except Exception as e:
        print(colorize(f"\n❌ Setup failed: {e}", Colors.RED))
        return False


def print_next_steps(agent: Optional[str]) -> None:
    """Print next steps for the user."""
    print_section("Next Steps")
    
    print(f"""
{colorize('1. Start a new task:', Colors.CYAN)}
   python3 ai-context/scripts/start-task.py "Your task description"

{colorize('2. Or start interactive AI session:', Colors.CYAN)}
   {"aider" if agent == "aider" else "your-ai-agent"} 

{colorize('3. After making changes:', Colors.CYAN)}
   python3 ai-context/scripts/finish-task.py

{colorize('4. If you need to rollback:', Colors.CYAN)}
   python3 ai-context/scripts/rollback.py --list
   python3 ai-context/scripts/rollback.py --latest

{colorize('For more information:', Colors.GRAY)}
   See ai-context/docs/usage.md
""")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AI Context Toolkit - Project Initialization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive mode for agent selection"
    )
    parser.add_argument(
        "--agent", "-a",
        metavar="NAME",
        help="Specify AI agent to use (aider, claude-cli, etc.)"
    )
    parser.add_argument(
        "--config", "-c",
        action="store_true",
        help="Use preferences from config file"
    )
    parser.add_argument(
        "--project-root", "-p",
        metavar="PATH",
        help="Project root directory (default: parent of ai-context)"
    )
    parser.add_argument(
        "--no-generate",
        action="store_true",
        help="Skip generating configuration files"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output environment info as JSON"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimal output"
    )
    
    args = parser.parse_args()
    
    # Determine project root
    if args.project_root:
        project_root = Path(args.project_root).resolve()
    else:
        # Default to parent of ai-context directory
        project_root = SCRIPT_DIR.parent
        if project_root.name == "ai-context":
            project_root = project_root.parent
    
    if not args.quiet:
        print_banner()
    
    # Detect environment
    detector = EnvDetector(project_root)
    env = detector.detect_all()
    
    if args.json:
        print(json.dumps(env.to_dict(), indent=2))
        return 0
    
    if not args.quiet:
        print_env_summary(env)
    
    # Initialize agent registry
    registry = AgentRegistry(project_root)
    agents = registry.get_all_agents()
    
    if not args.quiet:
        print_agents_summary(agents)
    
    # Determine which agent to use
    selected_agent = None
    
    if args.agent:
        selected_agent = args.agent
    elif args.config:
        selected_agent = registry.get_user_preferred_agent()
    elif args.interactive:
        selected_agent = interactive_agent_selection(registry)
    else:
        # Auto-select best available
        recommended = registry.get_recommended_agent()
        if recommended:
            selected_agent = recommended.name.lower().replace(" ", "-")
    
    if selected_agent and not args.quiet:
        print(colorize(f"\n🤖 Selected agent: {selected_agent}", Colors.GREEN))
    
    # Setup project
    if not setup_project(project_root, env, selected_agent, args.no_generate):
        return 1
    
    if not args.quiet:
        print_next_steps(selected_agent)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
