#!/usr/bin/env python3
"""
Base Adapter - Abstract base class for AI agent adapters.

All AI agent adapters must inherit from this class and implement
the required methods.
"""

from __future__ import annotations

import subprocess
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, Flag, auto
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterator, Callable
import os


class AdapterCapability(Flag):
    """Capabilities that an AI agent adapter can support."""
    NONE = 0
    CODE_GENERATION = auto()      # Can generate new code
    CODE_EDITING = auto()         # Can edit existing code
    CODE_REVIEW = auto()          # Can review code
    REFACTORING = auto()          # Can refactor code
    DEBUGGING = auto()            # Can help debug issues
    DOCUMENTATION = auto()        # Can generate documentation
    TESTING = auto()              # Can generate tests
    CHAT = auto()                 # Supports interactive chat
    STREAMING = auto()            # Supports streaming output
    FILE_OPERATIONS = auto()      # Can create/modify/delete files
    GIT_OPERATIONS = auto()       # Can perform git operations
    MULTI_FILE = auto()           # Can work with multiple files
    CONTEXT_AWARE = auto()        # Can understand project context
    
    # Common combinations
    FULL = (CODE_GENERATION | CODE_EDITING | CODE_REVIEW | REFACTORING |
            DEBUGGING | DOCUMENTATION | TESTING | CHAT | STREAMING |
            FILE_OPERATIONS | GIT_OPERATIONS | MULTI_FILE | CONTEXT_AWARE)
    
    BASIC = CODE_GENERATION | CODE_EDITING | CHAT


class TaskType(Enum):
    """Types of tasks that can be executed."""
    FEATURE = "feature"           # Implement new feature
    FIX = "fix"                   # Fix a bug
    REFACTOR = "refactor"         # Refactor code
    REVIEW = "review"             # Code review
    DOCUMENT = "document"         # Generate documentation
    TEST = "test"                 # Generate tests
    CHAT = "chat"                 # Interactive chat
    CUSTOM = "custom"             # Custom task


@dataclass
class TaskResult:
    """Result of executing a task."""
    success: bool
    task_id: str
    task_type: str
    agent: str
    started_at: str
    completed_at: str
    duration_seconds: float
    output: str = ""
    error: Optional[str] = None
    files_modified: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    files_deleted: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "task_id": self.task_id,
            "task_type": self.task_type,
            "agent": self.agent,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
            "output": self.output,
            "error": self.error,
            "files_modified": self.files_modified,
            "files_created": self.files_created,
            "files_deleted": self.files_deleted,
            "metadata": self.metadata,
        }


@dataclass
class AgentConfig:
    """Configuration for an AI agent."""
    name: str
    cli_command: str
    api_key_env_var: Optional[str] = None
    config_file: Optional[str] = None
    default_model: Optional[str] = None
    timeout: int = 300  # seconds
    extra_args: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)


class BaseAdapter(ABC):
    """
    Abstract base class for AI agent adapters.
    
    Subclasses must implement:
    - detect() -> bool
    - get_version() -> Optional[str]
    - execute(task, context, ...) -> TaskResult
    
    Optional overrides:
    - get_capabilities() -> AdapterCapability
    - stream_execute(...) -> Iterator[str]
    - validate_config() -> bool
    """
    
    # Class-level properties to be overridden by subclasses
    AGENT_NAME: str = "Unknown"
    CLI_COMMAND: str = ""
    API_KEY_ENV_VAR: Optional[str] = None
    DEFAULT_CAPABILITIES: AdapterCapability = AdapterCapability.BASIC
    
    def __init__(
        self,
        project_root: Optional[Path] = None,
        config: Optional[AgentConfig] = None
    ):
        """
        Initialize the adapter.
        
        Args:
            project_root: Root directory of the project
            config: Optional configuration override
        """
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.config = config or self._default_config()
        self._cli_path: Optional[str] = None
    
    def _default_config(self) -> AgentConfig:
        """Get default configuration for this agent."""
        return AgentConfig(
            name=self.AGENT_NAME,
            cli_command=self.CLI_COMMAND,
            api_key_env_var=self.API_KEY_ENV_VAR,
        )
    
    @classmethod
    def detect(cls) -> bool:
        """
        Check if this AI agent is available on the system.
        
        Returns:
            True if the agent is installed and accessible
        """
        return shutil.which(cls.CLI_COMMAND) is not None
    
    @classmethod
    def get_version(cls) -> Optional[str]:
        """
        Get the version of the installed AI agent.
        
        Returns:
            Version string or None if not available
        """
        cli_path = shutil.which(cls.CLI_COMMAND)
        if not cli_path:
            return None
        
        try:
            result = subprocess.run(
                [cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                # Extract version from output
                import re
                match = re.search(r"(\d+\.\d+\.\d+)", result.stdout + result.stderr)
                return match.group(1) if match else result.stdout.strip()
        except (subprocess.TimeoutExpired, OSError):
            pass
        
        return None
    
    def get_capabilities(self) -> AdapterCapability:
        """
        Get the capabilities of this AI agent.
        
        Returns:
            AdapterCapability flags indicating supported features
        """
        return self.DEFAULT_CAPABILITIES
    
    def has_capability(self, capability: AdapterCapability) -> bool:
        """Check if the agent has a specific capability."""
        return bool(self.get_capabilities() & capability)
    
    def is_api_key_configured(self) -> bool:
        """Check if the required API key is configured."""
        if not self.API_KEY_ENV_VAR:
            return True  # No API key required
        return bool(os.environ.get(self.API_KEY_ENV_VAR))
    
    def validate_config(self) -> bool:
        """
        Validate the adapter configuration.
        
        Returns:
            True if configuration is valid
        """
        if not self.detect():
            return False
        if not self.is_api_key_configured():
            return False
        return True
    
    def _get_cli_path(self) -> str:
        """Get the path to the CLI command."""
        if self._cli_path is None:
            self._cli_path = shutil.which(self.CLI_COMMAND)
        if not self._cli_path:
            raise RuntimeError(f"{self.AGENT_NAME} CLI not found: {self.CLI_COMMAND}")
        return self._cli_path
    
    def _run_command(
        self,
        args: List[str],
        timeout: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
        input_text: Optional[str] = None,
    ) -> subprocess.CompletedProcess:
        """
        Run a CLI command.
        
        Args:
            args: Command arguments (without the CLI command itself)
            timeout: Command timeout in seconds
            env: Additional environment variables
            input_text: Text to send to stdin
        
        Returns:
            CompletedProcess result
        """
        cli_path = self._get_cli_path()
        full_cmd = [cli_path] + args
        
        # Merge environment
        full_env = os.environ.copy()
        if self.config.environment:
            full_env.update(self.config.environment)
        if env:
            full_env.update(env)
        
        return subprocess.run(
            full_cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=timeout or self.config.timeout,
            env=full_env,
            input=input_text,
        )
    
    def _stream_command(
        self,
        args: List[str],
        timeout: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
        on_output: Optional[Callable[[str], None]] = None,
    ) -> Iterator[str]:
        """
        Run a CLI command with streaming output.
        
        Args:
            args: Command arguments
            timeout: Command timeout in seconds
            env: Additional environment variables
            on_output: Callback for each output line
        
        Yields:
            Output lines as they are produced
        """
        cli_path = self._get_cli_path()
        full_cmd = [cli_path] + args
        
        # Merge environment
        full_env = os.environ.copy()
        if self.config.environment:
            full_env.update(self.config.environment)
        if env:
            full_env.update(env)
        
        process = subprocess.Popen(
            full_cmd,
            cwd=self.project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=full_env,
        )
        
        try:
            for line in process.stdout:
                yield line
                if on_output:
                    on_output(line)
        finally:
            process.wait(timeout=timeout or self.config.timeout)
    
    def _generate_task_id(self, task_type: TaskType) -> str:
        """Generate a unique task ID."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"task_{task_type.value}_{timestamp}"
    
    @abstractmethod
    def execute(
        self,
        task: str,
        task_type: TaskType = TaskType.CUSTOM,
        context: Optional[str] = None,
        files: Optional[List[str]] = None,
        **kwargs
    ) -> TaskResult:
        """
        Execute a task using this AI agent.
        
        Args:
            task: Task description or prompt
            task_type: Type of task being executed
            context: Additional context to provide
            files: Specific files to work with
            **kwargs: Additional agent-specific arguments
        
        Returns:
            TaskResult with execution details
        """
        pass
    
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
        Execute a task with streaming output.
        
        Default implementation falls back to non-streaming execute.
        Subclasses should override if they support streaming.
        
        Args:
            task: Task description
            task_type: Type of task
            context: Additional context
            files: Files to work with
            on_output: Callback for output lines
            **kwargs: Additional arguments
        
        Yields:
            Output lines as they are produced
        """
        result = self.execute(task, task_type, context, files, **kwargs)
        for line in result.output.splitlines():
            yield line
            if on_output:
                on_output(line)
    
    def build_context(
        self,
        task: str,
        files: Optional[List[str]] = None,
        include_rules: bool = True
    ) -> str:
        """
        Build context string for the AI agent.
        
        Args:
            task: The task description
            files: Files to include in context
            include_rules: Whether to include AI context rules
        
        Returns:
            Formatted context string
        """
        parts = []
        
        # Add rules if requested and available
        if include_rules:
            rules_file = self.project_root / "ai-context" / "core" / "core.md"
            if rules_file.exists():
                parts.append("# Development Rules\n")
                parts.append(rules_file.read_text(encoding="utf-8"))
                parts.append("\n---\n")
        
        # Add task
        parts.append(f"# Task\n{task}\n")
        
        # Add file contents if specified
        if files:
            parts.append("\n# Relevant Files\n")
            for file_path in files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    parts.append(f"\n## {file_path}\n```\n")
                    parts.append(full_path.read_text(encoding="utf-8"))
                    parts.append("\n```\n")
        
        return "".join(parts)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.AGENT_NAME!r}, available={self.detect()})"


class MockAdapter(BaseAdapter):
    """
    Mock adapter for testing purposes.
    
    This adapter doesn't actually call any AI service,
    but simulates the behavior for testing.
    """
    
    AGENT_NAME = "Mock"
    CLI_COMMAND = "echo"  # Uses echo as a placeholder
    API_KEY_ENV_VAR = None
    DEFAULT_CAPABILITIES = AdapterCapability.FULL
    
    def execute(
        self,
        task: str,
        task_type: TaskType = TaskType.CUSTOM,
        context: Optional[str] = None,
        files: Optional[List[str]] = None,
        **kwargs
    ) -> TaskResult:
        """Execute a mock task."""
        task_id = self._generate_task_id(task_type)
        started_at = datetime.now(timezone.utc)
        
        # Simulate some work
        output = f"Mock execution of task: {task}\n"
        output += f"Task type: {task_type.value}\n"
        if files:
            output += f"Files: {', '.join(files)}\n"
        
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
            metadata={"mock": True},
        )
