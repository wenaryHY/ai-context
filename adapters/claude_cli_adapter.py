#!/usr/bin/env python3
"""
Claude CLI Adapter - Integration with Anthropic's Claude CLI.

This adapter interfaces with Claude through command-line tools.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Iterator, Callable, Dict, Any

from .base_adapter import (
    BaseAdapter,
    AdapterCapability,
    TaskType,
    TaskResult,
    AgentConfig,
)


class ClaudeCliAdapter(BaseAdapter):
    """
    Adapter for Claude CLI / Claude Code.
    
    Supports Claude models through the Anthropic API via CLI.
    
    Usage:
        adapter = ClaudeCliAdapter(project_root="/path/to/project")
        result = adapter.execute("Refactor this function for better readability")
    """
    
    AGENT_NAME = "Claude CLI"
    CLI_COMMAND = "claude"
    API_KEY_ENV_VAR = "ANTHROPIC_API_KEY"
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
        AdapterCapability.CONTEXT_AWARE
    )
    
    # Available Claude models
    MODELS = {
        "claude-3-opus": "claude-3-opus-20240229",
        "claude-3-sonnet": "claude-3-sonnet-20240229",
        "claude-3-haiku": "claude-3-haiku-20240307",
        "claude-3.5-sonnet": "claude-3-5-sonnet-20240620",
    }
    
    def __init__(
        self,
        project_root: Optional[Path] = None,
        config: Optional[AgentConfig] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
    ):
        """
        Initialize Claude CLI adapter.
        
        Args:
            project_root: Project root directory
            config: Optional configuration override
            model: Claude model to use
            max_tokens: Maximum tokens in response
        """
        super().__init__(project_root, config)
        self.model = model or "claude-3.5-sonnet"
        self.max_tokens = max_tokens
    
    def _build_prompt(
        self,
        task: str,
        context: Optional[str] = None,
        files: Optional[List[str]] = None,
    ) -> str:
        """Build a prompt for Claude."""
        parts = []
        
        # System context
        parts.append("You are an expert software developer assisting with a coding task.")
        parts.append("Provide clear, well-documented code following best practices.")
        parts.append("")
        
        # Add context if provided
        if context:
            parts.append("## Context")
            parts.append(context)
            parts.append("")
        
        # Add file contents if specified
        if files:
            parts.append("## Relevant Files")
            for file_path in files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    parts.append(f"\n### {file_path}")
                    parts.append("```")
                    parts.append(full_path.read_text(encoding="utf-8"))
                    parts.append("```")
            parts.append("")
        
        # Add task
        parts.append("## Task")
        parts.append(task)
        
        return "\n".join(parts)
    
    def _build_args(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> List[str]:
        """Build command line arguments for Claude CLI."""
        args = []
        
        # Model selection
        actual_model = model or self.model
        if actual_model in self.MODELS:
            actual_model = self.MODELS[actual_model]
        
        # Common arguments
        args.extend(["--model", actual_model])
        args.extend(["--max-tokens", str(max_tokens or self.max_tokens)])
        
        if stream:
            args.append("--stream")
        
        # The prompt is typically passed via stdin or as an argument
        args.extend(["--prompt", prompt])
        
        return args
    
    def execute(
        self,
        task: str,
        task_type: TaskType = TaskType.CUSTOM,
        context: Optional[str] = None,
        files: Optional[List[str]] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> TaskResult:
        """
        Execute a task using Claude.
        
        Args:
            task: Task description
            task_type: Type of task
            context: Additional context
            files: Files to include in context
            model: Override model for this task
            **kwargs: Additional arguments
        
        Returns:
            TaskResult with execution details
        """
        task_id = self._generate_task_id(task_type)
        started_at = datetime.now(timezone.utc)
        
        # Build prompt
        prompt = self._build_prompt(task, context, files)
        
        # Build arguments
        args = self._build_args(
            prompt=prompt,
            model=model,
        )
        
        try:
            result = self._run_command(args)
            
            completed_at = datetime.now(timezone.utc)
            duration = (completed_at - started_at).total_seconds()
            
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
                files_modified=files or [],
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
        prompt = self._build_prompt(task, context, files)
        
        args = self._build_args(
            prompt=prompt,
            model=kwargs.get("model"),
            stream=True,
        )
        
        yield from self._stream_command(args, on_output=on_output)
    
    def review_code(
        self,
        files: List[str],
        focus_areas: Optional[List[str]] = None
    ) -> TaskResult:
        """
        Perform code review on specified files.
        
        Args:
            files: Files to review
            focus_areas: Specific areas to focus on (e.g., "security", "performance")
        
        Returns:
            TaskResult with review feedback
        """
        focus = ""
        if focus_areas:
            focus = f"Focus particularly on: {', '.join(focus_areas)}. "
        
        task = f"""Please review the following code. {focus}
Provide:
1. Summary of what the code does
2. Potential issues or bugs
3. Suggestions for improvement
4. Security considerations
5. Performance considerations"""
        
        return self.execute(
            task=task,
            task_type=TaskType.REVIEW,
            files=files,
        )
    
    def explain_code(self, files: List[str]) -> TaskResult:
        """
        Get an explanation of the code in specified files.
        
        Args:
            files: Files to explain
        
        Returns:
            TaskResult with code explanation
        """
        task = """Please explain this code:
1. What is the overall purpose?
2. How does it work (high-level)?
3. What are the key functions/classes?
4. What are the inputs and outputs?"""
        
        return self.execute(
            task=task,
            task_type=TaskType.DOCUMENT,
            files=files,
        )
