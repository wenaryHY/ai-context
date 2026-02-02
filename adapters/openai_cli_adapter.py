#!/usr/bin/env python3
"""
OpenAI CLI Adapter - Integration with OpenAI's command line interface.

This adapter interfaces with OpenAI's API through CLI tools.
"""

from __future__ import annotations

import json
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


class OpenAICliAdapter(BaseAdapter):
    """
    Adapter for OpenAI CLI.
    
    Provides integration with OpenAI's GPT models through CLI.
    
    Usage:
        adapter = OpenAICliAdapter(project_root="/path/to/project")
        result = adapter.execute("Write a function to parse JSON")
    """
    
    AGENT_NAME = "OpenAI CLI"
    CLI_COMMAND = "openai"
    API_KEY_ENV_VAR = "OPENAI_API_KEY"
    DEFAULT_CAPABILITIES = (
        AdapterCapability.CODE_GENERATION |
        AdapterCapability.CODE_REVIEW |
        AdapterCapability.DOCUMENTATION |
        AdapterCapability.CHAT |
        AdapterCapability.STREAMING
    )
    
    MODELS = {
        "gpt-4": "gpt-4",
        "gpt-4-turbo": "gpt-4-turbo-preview",
        "gpt-3.5": "gpt-3.5-turbo",
        "gpt-4o": "gpt-4o",
    }
    
    def __init__(
        self,
        project_root: Optional[Path] = None,
        config: Optional[AgentConfig] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
    ):
        """
        Initialize OpenAI CLI adapter.
        
        Args:
            project_root: Project root directory
            config: Optional configuration
            model: Model to use
            max_tokens: Maximum tokens in response
        """
        super().__init__(project_root, config)
        self.model = model or "gpt-4"
        self.max_tokens = max_tokens
    
    def _build_messages(
        self,
        task: str,
        context: Optional[str] = None,
        files: Optional[List[str]] = None,
    ) -> List[dict]:
        """Build message array for chat completion."""
        messages = [
            {
                "role": "system",
                "content": "You are an expert software developer. Provide clear, well-documented code."
            }
        ]
        
        # Build user message
        user_content = []
        
        if context:
            user_content.append(f"Context:\n{context}\n")
        
        if files:
            user_content.append("Relevant files:\n")
            for file_path in files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    content = full_path.read_text(encoding="utf-8")
                    user_content.append(f"\n{file_path}:\n```\n{content}\n```\n")
        
        user_content.append(f"\nTask: {task}")
        
        messages.append({
            "role": "user",
            "content": "\n".join(user_content)
        })
        
        return messages
    
    def execute(
        self,
        task: str,
        task_type: TaskType = TaskType.CUSTOM,
        context: Optional[str] = None,
        files: Optional[List[str]] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> TaskResult:
        """Execute a task using OpenAI API."""
        task_id = self._generate_task_id(task_type)
        started_at = datetime.now(timezone.utc)
        
        actual_model = model or self.model
        if actual_model in self.MODELS:
            actual_model = self.MODELS[actual_model]
        
        messages = self._build_messages(task, context, files)
        
        try:
            # Build CLI args for chat completion
            args = [
                "api", "chat.completions.create",
                "-m", actual_model,
                "-M", str(self.max_tokens),
            ]
            
            # Add messages as JSON
            for msg in messages:
                args.extend(["-g", msg["role"], msg["content"]])
            
            result = self._run_command(args)
            
            completed_at = datetime.now(timezone.utc)
            duration = (completed_at - started_at).total_seconds()
            
            # Parse output
            output = result.stdout
            try:
                response = json.loads(output)
                if "choices" in response:
                    output = response["choices"][0]["message"]["content"]
            except json.JSONDecodeError:
                pass
            
            return TaskResult(
                success=result.returncode == 0,
                task_id=task_id,
                task_type=task_type.value,
                agent=self.AGENT_NAME,
                started_at=started_at.isoformat(),
                completed_at=completed_at.isoformat(),
                duration_seconds=duration,
                output=output,
                error=result.stderr if result.returncode != 0 else None,
                files_modified=files or [],
                metadata={"model": actual_model},
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
        actual_model = kwargs.get("model") or self.model
        if actual_model in self.MODELS:
            actual_model = self.MODELS[actual_model]
        
        messages = self._build_messages(task, context, files)
        
        args = [
            "api", "chat.completions.create",
            "-m", actual_model,
            "-M", str(self.max_tokens),
            "--stream",
        ]
        
        for msg in messages:
            args.extend(["-g", msg["role"], msg["content"]])
        
        yield from self._stream_command(args, on_output=on_output)
