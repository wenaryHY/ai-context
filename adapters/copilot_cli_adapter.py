#!/usr/bin/env python3
"""
GitHub Copilot CLI Adapter - Integration with GitHub Copilot CLI.

GitHub Copilot CLI provides AI-powered command suggestions
and explanations in the terminal.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Iterator, Callable

from .base_adapter import (
    BaseAdapter,
    AdapterCapability,
    TaskType,
    TaskResult,
    AgentConfig,
)


class CopilotCliAdapter(BaseAdapter):
    """
    Adapter for GitHub Copilot CLI.
    
    Copilot CLI provides:
    - Command suggestions (gh copilot suggest)
    - Command explanations (gh copilot explain)
    
    Usage:
        adapter = CopilotCliAdapter(project_root="/path/to/project")
        result = adapter.suggest("How do I find large files in git history?")
    """
    
    AGENT_NAME = "GitHub Copilot CLI"
    CLI_COMMAND = "gh"
    API_KEY_ENV_VAR = "GITHUB_TOKEN"
    DEFAULT_CAPABILITIES = (
        AdapterCapability.CHAT |
        AdapterCapability.DOCUMENTATION |
        AdapterCapability.STREAMING
    )
    
    def __init__(
        self,
        project_root: Optional[Path] = None,
        config: Optional[AgentConfig] = None,
    ):
        """Initialize Copilot CLI adapter."""
        super().__init__(project_root, config)
    
    @classmethod
    def detect(cls) -> bool:
        """Check if gh copilot is available."""
        import shutil
        import subprocess
        
        gh = shutil.which("gh")
        if not gh:
            return False
        
        # Check if copilot extension is installed
        try:
            result = subprocess.run(
                [gh, "copilot", "--help"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def suggest(self, query: str, shell_type: str = "bash") -> TaskResult:
        """
        Get command suggestions from Copilot.
        
        Args:
            query: Natural language query
            shell_type: Shell type (bash, zsh, powershell)
        
        Returns:
            TaskResult with suggested commands
        """
        task_id = self._generate_task_id(TaskType.CHAT)
        started_at = datetime.now(timezone.utc)
        
        try:
            args = ["copilot", "suggest", "-t", shell_type, query]
            result = self._run_command(args)
            
            completed_at = datetime.now(timezone.utc)
            duration = (completed_at - started_at).total_seconds()
            
            return TaskResult(
                success=result.returncode == 0,
                task_id=task_id,
                task_type=TaskType.CHAT.value,
                agent=self.AGENT_NAME,
                started_at=started_at.isoformat(),
                completed_at=completed_at.isoformat(),
                duration_seconds=duration,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                metadata={"mode": "suggest", "shell": shell_type},
            )
            
        except Exception as e:
            completed_at = datetime.now(timezone.utc)
            return TaskResult(
                success=False,
                task_id=task_id,
                task_type=TaskType.CHAT.value,
                agent=self.AGENT_NAME,
                started_at=started_at.isoformat(),
                completed_at=completed_at.isoformat(),
                duration_seconds=(completed_at - started_at).total_seconds(),
                error=str(e),
            )
    
    def explain(self, command: str) -> TaskResult:
        """
        Get explanation of a command from Copilot.
        
        Args:
            command: Command to explain
        
        Returns:
            TaskResult with explanation
        """
        task_id = self._generate_task_id(TaskType.DOCUMENT)
        started_at = datetime.now(timezone.utc)
        
        try:
            args = ["copilot", "explain", command]
            result = self._run_command(args)
            
            completed_at = datetime.now(timezone.utc)
            duration = (completed_at - started_at).total_seconds()
            
            return TaskResult(
                success=result.returncode == 0,
                task_id=task_id,
                task_type=TaskType.DOCUMENT.value,
                agent=self.AGENT_NAME,
                started_at=started_at.isoformat(),
                completed_at=completed_at.isoformat(),
                duration_seconds=duration,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                metadata={"mode": "explain", "command": command},
            )
            
        except Exception as e:
            completed_at = datetime.now(timezone.utc)
            return TaskResult(
                success=False,
                task_id=task_id,
                task_type=TaskType.DOCUMENT.value,
                agent=self.AGENT_NAME,
                started_at=started_at.isoformat(),
                completed_at=completed_at.isoformat(),
                duration_seconds=(completed_at - started_at).total_seconds(),
                error=str(e),
            )
    
    def execute(
        self,
        task: str,
        task_type: TaskType = TaskType.CUSTOM,
        context: Optional[str] = None,
        files: Optional[List[str]] = None,
        **kwargs
    ) -> TaskResult:
        """
        Execute a task using Copilot CLI.
        
        Maps to suggest or explain based on task type.
        """
        if task_type == TaskType.DOCUMENT or task.startswith("explain"):
            return self.explain(task)
        else:
            return self.suggest(task, kwargs.get("shell", "bash"))
    
    def stream_execute(
        self,
        task: str,
        task_type: TaskType = TaskType.CUSTOM,
        context: Optional[str] = None,
        files: Optional[List[str]] = None,
        on_output: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> Iterator[str]:
        """Stream execution output."""
        args = ["copilot", "suggest", task]
        yield from self._stream_command(args, on_output=on_output)
