#!/usr/bin/env python3
"""
Gemini CLI Adapter - Integration with Google's Gemini AI.

This adapter interfaces with Google's Gemini models through
Google Cloud CLI or dedicated Gemini tools.
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


class GeminiCliAdapter(BaseAdapter):
    """
    Adapter for Google Gemini CLI.
    
    Provides integration with Google's Gemini models.
    
    Usage:
        adapter = GeminiCliAdapter(project_root="/path/to/project")
        result = adapter.execute("Explain this code")
    """
    
    AGENT_NAME = "Google Gemini CLI"
    CLI_COMMAND = "gemini"  # or gcloud with Gemini API
    API_KEY_ENV_VAR = "GOOGLE_API_KEY"
    DEFAULT_CAPABILITIES = (
        AdapterCapability.CODE_GENERATION |
        AdapterCapability.CODE_REVIEW |
        AdapterCapability.DOCUMENTATION |
        AdapterCapability.CHAT |
        AdapterCapability.STREAMING |
        AdapterCapability.CONTEXT_AWARE
    )
    
    MODELS = {
        "gemini-pro": "gemini-pro",
        "gemini-pro-vision": "gemini-pro-vision",
        "gemini-1.5-pro": "gemini-1.5-pro",
        "gemini-1.5-flash": "gemini-1.5-flash",
    }
    
    def __init__(
        self,
        project_root: Optional[Path] = None,
        config: Optional[AgentConfig] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize Gemini CLI adapter.
        
        Args:
            project_root: Project root directory
            config: Optional configuration
            model: Model to use
        """
        super().__init__(project_root, config)
        self.model = model or "gemini-1.5-pro"
    
    @classmethod
    def detect(cls) -> bool:
        """Check if Gemini CLI or gcloud is available."""
        import shutil
        
        # Check for dedicated gemini CLI
        if shutil.which("gemini"):
            return True
        
        # Check for gcloud with Gemini access
        if shutil.which("gcloud"):
            return True
        
        return False
    
    def _build_prompt(
        self,
        task: str,
        context: Optional[str] = None,
        files: Optional[List[str]] = None,
    ) -> str:
        """Build prompt for Gemini."""
        parts = []
        
        parts.append("You are an expert software developer. Help with the following task.")
        parts.append("")
        
        if context:
            parts.append(f"Context:\n{context}\n")
        
        if files:
            parts.append("Relevant files:\n")
            for file_path in files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    content = full_path.read_text(encoding="utf-8")
                    parts.append(f"\n{file_path}:\n```\n{content}\n```\n")
        
        parts.append(f"Task: {task}")
        
        return "\n".join(parts)
    
    def execute(
        self,
        task: str,
        task_type: TaskType = TaskType.CUSTOM,
        context: Optional[str] = None,
        files: Optional[List[str]] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> TaskResult:
        """Execute a task using Gemini."""
        task_id = self._generate_task_id(task_type)
        started_at = datetime.now(timezone.utc)
        
        actual_model = model or self.model
        if actual_model in self.MODELS:
            actual_model = self.MODELS[actual_model]
        
        prompt = self._build_prompt(task, context, files)
        
        try:
            # Try dedicated gemini CLI first
            import shutil
            if shutil.which("gemini"):
                args = ["--model", actual_model, "--prompt", prompt]
            else:
                # Fall back to gcloud
                args = [
                    "ai", "generate-content",
                    "--model", actual_model,
                    "--prompt", prompt,
                ]
            
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
        prompt = self._build_prompt(task, context, files)
        
        import shutil
        if shutil.which("gemini"):
            args = ["--model", self.model, "--stream", "--prompt", prompt]
        else:
            args = [
                "ai", "generate-content",
                "--model", self.model,
                "--stream",
                "--prompt", prompt,
            ]
        
        yield from self._stream_command(args, on_output=on_output)
