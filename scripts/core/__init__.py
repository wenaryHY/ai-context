"""
AI Context Toolkit - Core modules

This package contains the core functionality for the AI Context Toolkit:
- env_detector: Environment detection and configuration
- agent_registry: AI Agent registration and management
- task_executor: Task execution engine
- rollback_manager: Snapshot and rollback management
"""

from .rollback_manager import RollbackManager, Snapshot, SnapshotMode, DiffResult
from .env_detector import EnvDetector, EnvironmentInfo, ProjectType, Framework
from .agent_registry import AgentRegistry, AgentInfo

__all__ = [
    # Rollback
    "RollbackManager",
    "Snapshot",
    "SnapshotMode",
    "DiffResult",
    # Environment
    "EnvDetector",
    "EnvironmentInfo",
    "ProjectType",
    "Framework",
    # Registry
    "AgentRegistry",
    "AgentInfo",
]
