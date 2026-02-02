#!/usr/bin/env python3
"""
Agent Registry - Central registry for AI agent adapters.

Manages registration, discovery, and selection of AI agents.
"""

from __future__ import annotations

import importlib
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
import sys

# Try to import yaml, fall back to json-only mode
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# Add adapters to path
SCRIPT_DIR = Path(__file__).resolve().parent.parent
ADAPTERS_DIR = SCRIPT_DIR.parent / "adapters"
sys.path.insert(0, str(ADAPTERS_DIR.parent))

from adapters.base_adapter import BaseAdapter, AdapterCapability, TaskType


@dataclass
class AgentInfo:
    """Information about a registered AI agent."""
    name: str
    adapter_class: str
    cli_command: str
    available: bool = False
    version: Optional[str] = None
    api_key_configured: bool = False
    capabilities: List[str] = field(default_factory=list)
    priority: int = 0  # Higher = more preferred
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AgentRegistry:
    """
    Central registry for AI agent adapters.
    
    Usage:
        registry = AgentRegistry()
        
        # Get all available agents
        agents = registry.get_available_agents()
        
        # Get recommended agent for a task
        agent = registry.get_recommended_agent(TaskType.FEATURE)
        
        # Get specific agent
        adapter = registry.get_adapter("aider")
    """
    
    # Built-in agent definitions with priority (higher = more preferred)
    BUILTIN_AGENTS = {
        "aider": {
            "module": "adapters.aider_adapter",
            "class": "AiderAdapter",
            "priority": 100,
        },
        "claude-cli": {
            "module": "adapters.claude_cli_adapter",
            "class": "ClaudeCliAdapter",
            "priority": 95,
        },
        "cursor": {
            "module": "adapters.cursor_api_adapter",
            "class": "CursorApiAdapter",
            "priority": 90,
        },
        "copilot-cli": {
            "module": "adapters.copilot_cli_adapter",
            "class": "CopilotCliAdapter",
            "priority": 85,
        },
        "openai-cli": {
            "module": "adapters.openai_cli_adapter",
            "class": "OpenAICliAdapter",
            "priority": 80,
        },
        "gemini-cli": {
            "module": "adapters.gemini_cli_adapter",
            "class": "GeminiCliAdapter",
            "priority": 75,
        },
        "ollama": {
            "module": "adapters.ollama_adapter",
            "class": "OllamaAdapter",
            "priority": 70,
        },
        "continue": {
            "module": "adapters.continue_adapter",
            "class": "ContinueAdapter",
            "priority": 65,
        },
    }
    
    def __init__(
        self,
        project_root: Optional[Path] = None,
        config_file: Optional[Path] = None
    ):
        """
        Initialize the agent registry.
        
        Args:
            project_root: Root directory of the project
            config_file: Path to agents configuration file
        """
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.config_file = config_file or self.project_root / "ai-context" / "config" / "agents.yaml"
        
        self._adapters: Dict[str, Type[BaseAdapter]] = {}
        self._agent_info: Dict[str, AgentInfo] = {}
        self._config: Dict[str, Any] = {}
        
        self._load_config()
        self._register_builtin_agents()
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                content = self.config_file.read_text(encoding="utf-8")
                if HAS_YAML:
                    self._config = yaml.safe_load(content) or {}
                else:
                    # Fall back to JSON config
                    json_config = self.config_file.with_suffix('.json')
                    if json_config.exists():
                        self._config = json.loads(json_config.read_text(encoding="utf-8"))
                    else:
                        self._config = {}
            except (OSError, json.JSONDecodeError) as e:
                self._config = {}
            except Exception:
                self._config = {}
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        if HAS_YAML:
            self.config_file.write_text(
                yaml.dump(self._config, default_flow_style=False, allow_unicode=True),
                encoding="utf-8"
            )
        else:
            # Fall back to JSON
            json_config = self.config_file.with_suffix('.json')
            json_config.write_text(
                json.dumps(self._config, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
    
    def _register_builtin_agents(self) -> None:
        """Register all built-in agents."""
        for agent_id, agent_def in self.BUILTIN_AGENTS.items():
            self._register_agent(agent_id, agent_def)
    
    def _register_agent(self, agent_id: str, agent_def: Dict[str, Any]) -> None:
        """
        Register an agent adapter.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_def: Agent definition with module, class, and priority
        """
        try:
            # Try to import the adapter module
            module = importlib.import_module(agent_def["module"])
            adapter_class = getattr(module, agent_def["class"])
            
            # Store the adapter class
            self._adapters[agent_id] = adapter_class
            
            # Detect availability and build info
            available = adapter_class.detect()
            version = adapter_class.get_version() if available else None
            
            # Check API key configuration
            api_key_configured = True
            if hasattr(adapter_class, 'API_KEY_ENV_VAR') and adapter_class.API_KEY_ENV_VAR:
                import os
                api_key_configured = bool(os.environ.get(adapter_class.API_KEY_ENV_VAR))
            
            # Get capabilities
            capabilities = []
            if hasattr(adapter_class, 'DEFAULT_CAPABILITIES'):
                caps = adapter_class.DEFAULT_CAPABILITIES
                for cap in AdapterCapability:
                    if cap != AdapterCapability.NONE and (caps & cap):
                        capabilities.append(cap.name)
            
            self._agent_info[agent_id] = AgentInfo(
                name=adapter_class.AGENT_NAME if hasattr(adapter_class, 'AGENT_NAME') else agent_id,
                adapter_class=f"{agent_def['module']}.{agent_def['class']}",
                cli_command=adapter_class.CLI_COMMAND if hasattr(adapter_class, 'CLI_COMMAND') else "",
                available=available,
                version=version,
                api_key_configured=api_key_configured,
                capabilities=capabilities,
                priority=agent_def.get("priority", 0),
            )
            
        except (ImportError, AttributeError) as e:
            # Agent not available - create placeholder info
            self._agent_info[agent_id] = AgentInfo(
                name=agent_id,
                adapter_class=f"{agent_def['module']}.{agent_def['class']}",
                cli_command="",
                available=False,
                priority=agent_def.get("priority", 0),
            )
    
    def register_custom_agent(
        self,
        agent_id: str,
        adapter_class: Type[BaseAdapter],
        priority: int = 50
    ) -> None:
        """
        Register a custom agent adapter.
        
        Args:
            agent_id: Unique identifier for the agent
            adapter_class: The adapter class
            priority: Priority level (higher = more preferred)
        """
        self._adapters[agent_id] = adapter_class
        
        available = adapter_class.detect()
        version = adapter_class.get_version() if available else None
        
        self._agent_info[agent_id] = AgentInfo(
            name=adapter_class.AGENT_NAME if hasattr(adapter_class, 'AGENT_NAME') else agent_id,
            adapter_class=f"{adapter_class.__module__}.{adapter_class.__name__}",
            cli_command=adapter_class.CLI_COMMAND if hasattr(adapter_class, 'CLI_COMMAND') else "",
            available=available,
            version=version,
            priority=priority,
        )
    
    def get_agent_info(self, agent_id: str) -> Optional[AgentInfo]:
        """
        Get information about a specific agent.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            AgentInfo or None if not found
        """
        return self._agent_info.get(agent_id)
    
    def get_all_agents(self) -> List[AgentInfo]:
        """
        Get information about all registered agents.
        
        Returns:
            List of AgentInfo objects
        """
        return list(self._agent_info.values())
    
    def get_available_agents(self) -> List[AgentInfo]:
        """
        Get all agents that are available and properly configured.
        
        Returns:
            List of available AgentInfo objects, sorted by priority
        """
        available = [
            info for info in self._agent_info.values()
            if info.available and info.api_key_configured
        ]
        return sorted(available, key=lambda x: x.priority, reverse=True)
    
    def get_adapter(
        self,
        agent_id: str,
        project_root: Optional[Path] = None
    ) -> Optional[BaseAdapter]:
        """
        Get an instantiated adapter for a specific agent.
        
        Args:
            agent_id: Agent identifier
            project_root: Project root to use (defaults to registry's project_root)
        
        Returns:
            Instantiated adapter or None if not available
        """
        adapter_class = self._adapters.get(agent_id)
        if not adapter_class:
            return None
        
        return adapter_class(project_root=project_root or self.project_root)
    
    def get_recommended_agent(
        self,
        task_type: Optional[TaskType] = None,
        required_capabilities: Optional[AdapterCapability] = None
    ) -> Optional[AgentInfo]:
        """
        Get the recommended agent for a task.
        
        Args:
            task_type: Type of task to perform
            required_capabilities: Required capabilities
        
        Returns:
            Recommended AgentInfo or None if no suitable agent
        """
        available = self.get_available_agents()
        
        if not available:
            return None
        
        # Filter by capabilities if specified
        if required_capabilities:
            available = [
                info for info in available
                if all(cap.name in info.capabilities for cap in AdapterCapability
                       if cap != AdapterCapability.NONE and (required_capabilities & cap))
            ]
        
        if not available:
            return None
        
        # Return highest priority
        return available[0]
    
    def refresh(self) -> None:
        """Refresh agent availability and versions."""
        self._adapters.clear()
        self._agent_info.clear()
        self._register_builtin_agents()
    
    def set_user_preference(self, agent_id: str, priority_boost: int = 50) -> None:
        """
        Set user preference for an agent.
        
        Args:
            agent_id: Agent to boost
            priority_boost: Amount to boost priority
        """
        if agent_id in self._agent_info:
            self._agent_info[agent_id].priority += priority_boost
            
            # Save preference to config
            if "preferences" not in self._config:
                self._config["preferences"] = {}
            self._config["preferences"]["preferred_agent"] = agent_id
            self._save_config()
    
    def get_user_preferred_agent(self) -> Optional[str]:
        """Get the user's preferred agent from config."""
        return self._config.get("preferences", {}).get("preferred_agent")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert registry to dictionary."""
        return {
            "agents": {
                agent_id: info.to_dict()
                for agent_id, info in self._agent_info.items()
            },
            "available_count": len(self.get_available_agents()),
            "total_count": len(self._agent_info),
        }


def main():
    """CLI entry point for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent Registry")
    parser.add_argument("--list", "-l", action="store_true", help="List all agents")
    parser.add_argument("--available", "-a", action="store_true", help="List available agents")
    parser.add_argument("--recommend", "-r", action="store_true", help="Get recommended agent")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--refresh", action="store_true", help="Refresh agent detection")
    args = parser.parse_args()
    
    registry = AgentRegistry()
    
    if args.refresh:
        registry.refresh()
        print("Agent registry refreshed.")
    
    if args.json:
        print(json.dumps(registry.to_dict(), indent=2))
    elif args.available:
        agents = registry.get_available_agents()
        print(f"Available AI Agents ({len(agents)}):")
        print("-" * 50)
        for agent in agents:
            print(f"  {agent.name}")
            print(f"    CLI: {agent.cli_command}")
            print(f"    Version: {agent.version or 'unknown'}")
            print(f"    Priority: {agent.priority}")
            print()
    elif args.recommend:
        agent = registry.get_recommended_agent()
        if agent:
            print(f"Recommended Agent: {agent.name}")
            print(f"  CLI: {agent.cli_command}")
            print(f"  Version: {agent.version or 'unknown'}")
        else:
            print("No suitable agent found.")
    else:
        agents = registry.get_all_agents()
        print(f"All Registered AI Agents ({len(agents)}):")
        print("-" * 50)
        for agent in agents:
            status = "✅" if agent.available else "❌"
            key_status = ""
            if not agent.api_key_configured:
                key_status = " ⚠️ (no API key)"
            print(f"{status} {agent.name}{key_status}")
            if agent.version:
                print(f"   Version: {agent.version}")


if __name__ == "__main__":
    main()
