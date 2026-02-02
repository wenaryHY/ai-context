#!/usr/bin/env python3
"""
Aider Adapter - Integration with Aider AI coding assistant.

Aider is a command-line tool that lets you pair program with AI.
https://github.com/paul-gauthier/aider
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


class AiderAdapter(BaseAdapter):
    """
    Adapter for Aider AI coding assistant.
    
    Aider supports:
    - Code generation and editing
    - Multi-file changes
    - Git integration
    - Interactive chat
    - Streaming output
    
    Usage:
        adapter = AiderAdapter(project_root="/path/to/project")
        result = adapter.execute("Add error handling to the login function")
    """
    
    AGENT_NAME = "Aider"
    CLI_COMMAND = "aider"
    API_KEY_ENV_VAR = "OPENAI_API_KEY"  # Default, can use others
    DEFAULT_CAPABILITIES = (
        AdapterCapability.CODE_GENERATION |
        AdapterCapability.CODE_EDITING |
        AdapterCapability.CODE_REVIEW |
        AdapterCapability.REFACTORING |
        AdapterCapability.DEBUGGING |
        AdapterCapability.DOCUMENTATION |
        AdapterCapability.TESTING |
        AdapterCapability.CHAT |
        AdapterCapability.STREAMING |
        AdapterCapability.FILE_OPERATIONS |
        AdapterCapability.GIT_OPERATIONS |
        AdapterCapability.MULTI_FILE |
        AdapterCapability.CONTEXT_AWARE
    )
    
    # Model mappings
    MODELS = {
        "gpt-4": "gpt-4",
        "gpt-4-turbo": "gpt-4-turbo-preview",
        "gpt-3.5": "gpt-3.5-turbo",
        "claude-3": "claude-3-opus-20240229",
        "claude-3-sonnet": "claude-3-sonnet-20240229",
        "deepseek": "deepseek-coder",
    }
    
    def __init__(
        self,
        project_root: Optional[Path] = None,
        config: Optional[AgentConfig] = None,
        model: Optional[str] = None,
        auto_commits: bool = False,
    ):
        """
        Initialize Aider adapter.
        
        Args:
            project_root: Project root directory
            config: Optional configuration override
            model: AI model to use (default: gpt-4)
            auto_commits: Whether to auto-commit changes
        """
        super().__init__(project_root, config)
        self.model = model or "gpt-4"
        self.auto_commits = auto_commits
    
    def _build_args(
        self,
        message: str,
        files: Optional[List[str]] = None,
        yes_always: bool = True,
        no_git: bool = False,
        no_auto_commits: bool = True,
        model: Optional[str] = None,
    ) -> List[str]:
        """Build command line arguments for Aider."""
        args = []
        
        # Model selection
        actual_model = model or self.model
        if actual_model in self.MODELS:
            actual_model = self.MODELS[actual_model]
        args.extend(["--model", actual_model])
        
        # Auto-confirm
        if yes_always:
            args.append("--yes-always")
        
        # Git options
        if no_git:
            args.append("--no-git")
        elif no_auto_commits and not self.auto_commits:
            args.append("--no-auto-commits")
        
        # Add message
        args.extend(["--message", message])
        
        # Add files
        if files:
            for f in files:
                args.append(str(self.project_root / f))
        
        return args
    
    def execute(
        self,
        task: str,
        task_type: TaskType = TaskType.CUSTOM,
        context: Optional[str] = None,
        files: Optional[List[str]] = None,
        model: Optional[str] = None,
        auto_commits: Optional[bool] = None,
        **kwargs
    ) -> TaskResult:
        """
        Execute a task using Aider.
        
        Args:
            task: Task description
            task_type: Type of task
            context: Additional context (prepended to task)
            files: Files to work with
            model: Override model for this task
            auto_commits: Override auto-commit setting
            **kwargs: Additional arguments
        
        Returns:
            TaskResult with execution details
        """
        task_id = self._generate_task_id(task_type)
        started_at = datetime.now(timezone.utc)
        
        # Build full message
        message = task
        if context:
            message = f"{context}\n\n{task}"
        
        # Build arguments
        args = self._build_args(
            message=message,
            files=files,
            no_auto_commits=not (auto_commits if auto_commits is not None else self.auto_commits),
            model=model,
        )
        
        try:
            result = self._run_command(args)
            
            completed_at = datetime.now(timezone.utc)
            duration = (completed_at - started_at).total_seconds()
            
            # Parse output for modified files
            files_modified = []
            files_created = []
            output_lines = result.stdout.splitlines()
            
            for line in output_lines:
                if "Applied edit to" in line or "Wrote" in line:
                    # Extract filename
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part in ("to", "Wrote") and i + 1 < len(parts):
                            filename = parts[i + 1].strip()
                            if filename not in files_modified:
                                files_modified.append(filename)
            
            return TaskResult(
                success=result.returncode == 0,
                task_id=task_id,
                task_type=task_type.value,
                agent=self.AGENT_NAME,
                started_at=started_at.isoformat(),
                completed_at=completed_at.isoformat(),
                duration_seconds=duration,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                files_modified=files_modified,
                files_created=files_created,
                metadata={
                    "model": model or self.model,
                    "return_code": result.returncode,
                },
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
    
    def stream_execute(
        self,
        task: str,
        task_type: TaskType = TaskType.CUSTOM,
        context: Optional[str] = None,
        files: Optional[List[str]] = None,
        on_output: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> Iterator[str]:
        """
        Execute with streaming output.
        
        Args:
            task: Task description
            task_type: Type of task
            context: Additional context
            files: Files to work with
            on_output: Callback for output
            **kwargs: Additional arguments
        
        Yields:
            Output lines as they are produced
        """
        # Build full message
        message = task
        if context:
            message = f"{context}\n\n{task}"
        
        args = self._build_args(
            message=message,
            files=files,
            model=kwargs.get("model"),
        )
        
        yield from self._stream_command(args, on_output=on_output)
    
    def chat(
        self,
        initial_message: Optional[str] = None,
        files: Optional[List[str]] = None,
    ) -> None:
        """
        Start an interactive chat session with Aider.
        
        Note: This launches Aider in interactive mode.
        
        Args:
            initial_message: Optional initial message
            files: Files to include in chat
        """
        import subprocess
        
        args = [self._get_cli_path()]
        
        if self.model:
            args.extend(["--model", self.MODELS.get(self.model, self.model)])
        
        if files:
            args.extend([str(self.project_root / f) for f in files])
        
        # Run interactively
        subprocess.run(args, cwd=self.project_root)
