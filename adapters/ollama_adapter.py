#!/usr/bin/env python3
"""
Ollama Adapter - Integration with Ollama for local LLM inference.

Ollama allows running LLMs locally without API keys.
https://ollama.ai
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


class OllamaAdapter(BaseAdapter):
    """
    Adapter for Ollama local LLM inference.
    
    Ollama supports running various open-source models locally:
    - Llama 2/3
    - Mistral
    - CodeLlama
    - DeepSeek Coder
    
    Usage:
        adapter = OllamaAdapter(project_root="/path/to/project")
        result = adapter.execute("Write a Python function to sort a list")
    """
    
    AGENT_NAME = "Ollama"
    CLI_COMMAND = "ollama"
    API_KEY_ENV_VAR = None  # Local model, no API key needed
    DEFAULT_CAPABILITIES = (
        AdapterCapability.CODE_GENERATION |
        AdapterCapability.CODE_REVIEW |
        AdapterCapability.DOCUMENTATION |
        AdapterCapability.CHAT |
        AdapterCapability.STREAMING
    )
    
    # Common coding models
    MODELS = {
        "codellama": "codellama",
        "deepseek-coder": "deepseek-coder",
        "llama3": "llama3",
        "llama2": "llama2",
        "mistral": "mistral",
        "mixtral": "mixtral",
        "phi": "phi",
        "qwen": "qwen",
    }
    
    def __init__(
        self,
        project_root: Optional[Path] = None,
        config: Optional[AgentConfig] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize Ollama adapter.
        
        Args:
            project_root: Project root directory
            config: Optional configuration
            model: Model to use (default: codellama)
        """
        super().__init__(project_root, config)
        self.model = model or "codellama"
    
    def list_models(self) -> List[str]:
        """
        List available models in Ollama.
        
        Returns:
            List of model names
        """
        try:
            result = self._run_command(["list"])
            if result.returncode != 0:
                return []
            
            models = []
            for line in result.stdout.splitlines()[1:]:  # Skip header
                if line.strip():
                    model_name = line.split()[0]
                    models.append(model_name)
            return models
        except Exception:
            return []
    
    def pull_model(self, model: str) -> bool:
        """
        Pull a model from Ollama registry.
        
        Args:
            model: Model name to pull
        
        Returns:
            True if successful
        """
        try:
            result = self._run_command(["pull", model], timeout=600)
            return result.returncode == 0
        except Exception:
            return False
    
    def is_model_available(self, model: str) -> bool:
        """Check if a model is available locally."""
        models = self.list_models()
        return any(model in m for m in models)
    
    def _build_prompt(
        self,
        task: str,
        context: Optional[str] = None,
        files: Optional[List[str]] = None,
    ) -> str:
        """Build prompt for the model."""
        parts = []
        
        if context:
            parts.append(f"Context:\n{context}\n")
        
        if files:
            parts.append("Files:\n")
            for file_path in files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    content = full_path.read_text(encoding="utf-8")
                    # Truncate large files
                    if len(content) > 10000:
                        content = content[:10000] + "\n... (truncated)"
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
        """Execute a task using Ollama."""
        task_id = self._generate_task_id(task_type)
        started_at = datetime.now(timezone.utc)
        
        actual_model = model or self.model
        
        # Check if model is available
        if not self.is_model_available(actual_model):
            return TaskResult(
                success=False,
                task_id=task_id,
                task_type=task_type.value,
                agent=self.AGENT_NAME,
                started_at=started_at.isoformat(),
                completed_at=datetime.now(timezone.utc).isoformat(),
                duration_seconds=0,
                error=f"Model '{actual_model}' not found. Run: ollama pull {actual_model}",
            )
        
        prompt = self._build_prompt(task, context, files)
        
        try:
            # Use ollama run command
            args = ["run", actual_model, prompt]
            result = self._run_command(args, timeout=300)
            
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
                    "model": actual_model,
                    "local": True,
                },
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
        args = ["run", self.model, prompt]
        yield from self._stream_command(args, on_output=on_output)
    
    def chat(
        self,
        initial_message: Optional[str] = None,
        files: Optional[List[str]] = None,
    ) -> None:
        """
        Start an interactive chat session.
        
        Args:
            initial_message: Optional initial message
            files: Files to include in context
        """
        import subprocess
        
        cli_path = self._get_cli_path()
        args = [cli_path, "run", self.model]
        
        subprocess.run(args, cwd=self.project_root)
