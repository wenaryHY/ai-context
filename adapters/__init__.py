"""
AI Context Toolkit - Agent Adapters

This package contains adapters for various AI coding assistants:
- Aider
- Claude CLI
- Cursor API
- GitHub Copilot CLI
- OpenAI CLI
- Google Gemini CLI
- Ollama
- Continue.dev
"""

from .base_adapter import BaseAdapter, AdapterCapability, TaskResult, TaskType

# Import all adapters
from .aider_adapter import AiderAdapter
from .claude_cli_adapter import ClaudeCliAdapter
from .cursor_api_adapter import CursorApiAdapter
from .copilot_cli_adapter import CopilotCliAdapter
from .openai_cli_adapter import OpenAICliAdapter
from .gemini_cli_adapter import GeminiCliAdapter
from .ollama_adapter import OllamaAdapter
from .continue_adapter import ContinueAdapter

__all__ = [
    # Base classes
    "BaseAdapter",
    "AdapterCapability",
    "TaskResult",
    "TaskType",
    # Adapters
    "AiderAdapter",
    "ClaudeCliAdapter",
    "CursorApiAdapter",
    "CopilotCliAdapter",
    "OpenAICliAdapter",
    "GeminiCliAdapter",
    "OllamaAdapter",
    "ContinueAdapter",
]
