#!/usr/bin/env python3
"""
Continue.dev Adapter - Integration with Continue AI coding assistant.

Continue is an open-source AI coding assistant that works with
various LLM providers.
https://continue.dev
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any

from .base_adapter import (
    BaseAdapter,
    AdapterCapability,
    TaskType,
    TaskResult,
    AgentConfig,
)


class ContinueAdapter(BaseAdapter):
    """
    Adapter for Continue.dev AI coding assistant.
    
    Continue integrates with various LLM providers and IDEs.
    This adapter primarily manages Continue's configuration.
    
    Usage:
        adapter = ContinueAdapter(project_root="/path/to/project")
        adapter.generate_config()
    """
    
    AGENT_NAME = "Continue"
    CLI_COMMAND = "continue"
    API_KEY_ENV_VAR = None  # Depends on configured provider
    DEFAULT_CAPABILITIES = (
        AdapterCapability.CODE_GENERATION |
        AdapterCapability.CODE_EDITING |
        AdapterCapability.CODE_REVIEW |
        AdapterCapability.REFACTORING |
        AdapterCapability.CHAT |
        AdapterCapability.CONTEXT_AWARE
    )
    
    CONFIG_PATH = Path.home() / ".continue" / "config.json"
    
    def __init__(
        self,
        project_root: Optional[Path] = None,
        config: Optional[AgentConfig] = None,
    ):
        """Initialize Continue adapter."""
        super().__init__(project_root, config)
    
    @classmethod
    def detect(cls) -> bool:
        """Check if Continue is available."""
        import shutil
        
        # Check for CLI
        if shutil.which("continue"):
            return True
        
        # Check for config file (IDE extension)
        if cls.CONFIG_PATH.exists():
            return True
        
        return False
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get Continue configuration.
        
        Returns:
            Configuration dictionary
        """
        if not self.CONFIG_PATH.exists():
            return {}
        
        try:
            return json.loads(self.CONFIG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    
    def generate_config(
        self,
        provider: str = "openai",
        model: str = "gpt-4",
        api_key_env: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate Continue configuration.
        
        Args:
            provider: LLM provider (openai, anthropic, ollama, etc.)
            model: Model to use
            api_key_env: Environment variable for API key
        
        Returns:
            Generated configuration
        """
        config = {
            "models": [
                {
                    "title": model,
                    "provider": provider,
                    "model": model,
                }
            ],
            "customCommands": [
                {
                    "name": "review",
                    "description": "Review the selected code",
                    "prompt": "Please review this code for potential issues, bugs, and improvements:\n\n{{{ input }}}"
                },
                {
                    "name": "explain",
                    "description": "Explain the selected code",
                    "prompt": "Please explain what this code does:\n\n{{{ input }}}"
                },
                {
                    "name": "refactor",
                    "description": "Refactor the selected code",
                    "prompt": "Please refactor this code to improve readability and maintainability:\n\n{{{ input }}}"
                },
                {
                    "name": "tests",
                    "description": "Generate tests for the selected code",
                    "prompt": "Please generate comprehensive tests for this code:\n\n{{{ input }}}"
                },
            ],
            "tabAutocompleteModel": {
                "title": "Tab Autocomplete",
                "provider": provider,
                "model": model,
            },
            "contextProviders": [
                {"name": "code"},
                {"name": "docs"},
                {"name": "diff"},
                {"name": "terminal"},
                {"name": "problems"},
                {"name": "folder"},
            ],
            "slashCommands": [
                {
                    "name": "edit",
                    "description": "Edit selected code"
                },
                {
                    "name": "comment",
                    "description": "Add comments to code"
                },
                {
                    "name": "share",
                    "description": "Share code snippet"
                },
            ],
        }
        
        if api_key_env:
            config["models"][0]["apiKeyEnvVar"] = api_key_env
        
        return config
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        Save Continue configuration.
        
        Args:
            config: Configuration to save
        
        Returns:
            True if successful
        """
        try:
            self.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            self.CONFIG_PATH.write_text(
                json.dumps(config, indent=2),
                encoding="utf-8"
            )
            return True
        except OSError:
            return False
    
    def execute(
        self,
        task: str,
        task_type: TaskType = TaskType.CUSTOM,
        context: Optional[str] = None,
        files: Optional[List[str]] = None,
        **kwargs
    ) -> TaskResult:
        """
        Execute a task - primarily for configuration management.
        
        For actual AI tasks, use Continue in your IDE.
        """
        task_id = self._generate_task_id(task_type)
        started_at = datetime.now(timezone.utc)
        
        try:
            output = f"Task prepared for Continue: {task}\n"
            
            if files:
                output += f"\nFiles to work with:\n"
                for f in files:
                    output += f"  - {f}\n"
            
            # Generate/update config if requested
            if kwargs.get("update_config"):
                config = self.generate_config(
                    provider=kwargs.get("provider", "openai"),
                    model=kwargs.get("model", "gpt-4"),
                )
                if self.save_config(config):
                    output += "\nUpdated Continue configuration.\n"
            
            completed_at = datetime.now(timezone.utc)
            duration = (completed_at - started_at).total_seconds()
            
            return TaskResult(
                success=True,
                task_id=task_id,
                task_type=task_type.value,
                agent=self.AGENT_NAME,
                started_at=started_at.isoformat(),
                completed_at=completed_at.isoformat(),
                duration_seconds=duration,
                output=output,
                files_modified=files or [],
                metadata={"mode": "configuration"},
            )
            
        except Exception as e:
            completed_at = datetime.now(timezone.utc)
            return TaskResult(
                success=False,
                task_id=task_id,
                task_type=task_type.value,
                agent=self.AGENT_NAME,
                started_at=started_at.isoformat(),
                completed_at=completed_at.isoformat(),
                duration_seconds=(completed_at - started_at).total_seconds(),
                error=str(e),
            )
    
    def add_context_file(self, file_path: str) -> bool:
        """
        Add a file to Continue's context.
        
        Note: This updates the config to include the file.
        """
        config = self.get_config()
        
        if "contextFiles" not in config:
            config["contextFiles"] = []
        
        if file_path not in config["contextFiles"]:
            config["contextFiles"].append(file_path)
        
        return self.save_config(config)
