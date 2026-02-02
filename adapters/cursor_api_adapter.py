#!/usr/bin/env python3
"""
Cursor API Adapter - Integration with Cursor IDE's AI features.

This adapter interfaces with Cursor IDE, primarily for context generation
and integration with Cursor's built-in AI capabilities.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .base_adapter import (
    BaseAdapter,
    AdapterCapability,
    TaskType,
    TaskResult,
    AgentConfig,
)


class CursorApiAdapter(BaseAdapter):
    """
    Adapter for Cursor IDE integration.
    
    Cursor is an AI-first code editor. This adapter helps generate
    context files (.cursorrules) and integrates with Cursor's features.
    
    Usage:
        adapter = CursorApiAdapter(project_root="/path/to/project")
        adapter.generate_cursorrules()
    """
    
    AGENT_NAME = "Cursor"
    CLI_COMMAND = "cursor"
    API_KEY_ENV_VAR = None  # Cursor manages its own API keys
    DEFAULT_CAPABILITIES = (
        AdapterCapability.CODE_GENERATION |
        AdapterCapability.CODE_EDITING |
        AdapterCapability.CODE_REVIEW |
        AdapterCapability.REFACTORING |
        AdapterCapability.DEBUGGING |
        AdapterCapability.CHAT |
        AdapterCapability.FILE_OPERATIONS |
        AdapterCapability.MULTI_FILE |
        AdapterCapability.CONTEXT_AWARE
    )
    
    def __init__(
        self,
        project_root: Optional[Path] = None,
        config: Optional[AgentConfig] = None,
    ):
        """Initialize Cursor adapter."""
        super().__init__(project_root, config)
    
    def generate_cursorrules(
        self,
        rules: Optional[List[str]] = None,
        include_context: bool = True
    ) -> str:
        """
        Generate .cursorrules file for the project.
        
        Args:
            rules: Custom rules to include
            include_context: Include ai-context rules
        
        Returns:
            Generated rules content
        """
        parts = ["# Project Rules for Cursor AI\n"]
        
        if include_context:
            # Try to load from ai-context
            core_rules = self.project_root / "ai-context" / "core" / "core.md"
            if core_rules.exists():
                parts.append("## Core Development Rules\n")
                parts.append(core_rules.read_text(encoding="utf-8"))
                parts.append("\n")
        
        if rules:
            parts.append("## Custom Rules\n")
            for rule in rules:
                parts.append(f"- {rule}\n")
        
        content = "\n".join(parts)
        
        # Write to .cursorrules
        cursorrules_path = self.project_root / ".cursorrules"
        cursorrules_path.write_text(content, encoding="utf-8")
        
        return content
    
    def execute(
        self,
        task: str,
        task_type: TaskType = TaskType.CUSTOM,
        context: Optional[str] = None,
        files: Optional[List[str]] = None,
        **kwargs
    ) -> TaskResult:
        """
        Execute a task - primarily for context generation.
        
        For actual AI tasks, use Cursor IDE directly.
        """
        task_id = self._generate_task_id(task_type)
        started_at = datetime.now(timezone.utc)
        
        try:
            # Generate context for Cursor
            output = f"Task prepared for Cursor IDE: {task}\n"
            
            if files:
                output += f"\nFiles to work with:\n"
                for f in files:
                    output += f"  - {f}\n"
            
            # Update .cursorrules if needed
            if kwargs.get("update_rules"):
                self.generate_cursorrules()
                output += "\nUpdated .cursorrules file.\n"
            
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
                metadata={"mode": "context_preparation"},
            )
            
        except Exception as e:
            completed_at = datetime.now(timezone.utc)
            duration = (completed_at - started_at).total_seconds()
            
            return TaskResult(
                success=False,
                task_id=task_id,
                task_type=task_type.value,
                agent=self.AGENT_NAME,
                started_at=started_at.isoformat(),
                completed_at=completed_at.isoformat(),
                duration_seconds=duration,
                error=str(e),
            )
    
    def open_in_cursor(self, files: Optional[List[str]] = None) -> bool:
        """
        Open project or files in Cursor IDE.
        
        Args:
            files: Specific files to open
        
        Returns:
            True if successful
        """
        import subprocess
        
        cli_path = self._get_cli_path()
        
        if files:
            args = [cli_path] + [str(self.project_root / f) for f in files]
        else:
            args = [cli_path, str(self.project_root)]
        
        try:
            subprocess.Popen(args)
            return True
        except Exception:
            return False
