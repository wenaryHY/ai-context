# AI Agent Adapters

本目录包含用于不同 AI 编码助手的适配器。

## 文档适配器 (*.md)

这些 Markdown 文件为不同 AI 平台提供上下文加载策略指南：

| 文件 | 平台 | 说明 |
|------|------|------|
| `cursor.md` | Cursor IDE | 通过 `.cursorrules` 加载 |
| `claude.md` | Claude (Anthropic) | 通过 `CLAUDE.md` 加载 |
| `chatgpt.md` | ChatGPT (OpenAI) | 附加最小规则 |
| `copilot.md` | GitHub Copilot | 通过 `copilot-instructions.md` |
| `gemini.md` | Google Gemini | 简洁提示策略 |
| `plain.md` | 通用/其他 | 纯文本模式 |

## Python 适配器 (*_adapter.py)

这些 Python 模块提供与 AI CLI 工具的编程集成：

| 文件 | Agent | CLI 命令 | API Key |
|------|-------|----------|---------|
| `aider_adapter.py` | Aider | `aider` | `OPENAI_API_KEY` |
| `claude_cli_adapter.py` | Claude CLI | `claude` | `ANTHROPIC_API_KEY` |
| `cursor_api_adapter.py` | Cursor | `cursor` | - |
| `copilot_cli_adapter.py` | GitHub Copilot | `gh copilot` | `GITHUB_TOKEN` |
| `openai_cli_adapter.py` | OpenAI CLI | `openai` | `OPENAI_API_KEY` |
| `gemini_cli_adapter.py` | Gemini CLI | `gemini` / `gcloud` | `GOOGLE_API_KEY` |
| `ollama_adapter.py` | Ollama | `ollama` | - (本地模型) |
| `continue_adapter.py` | Continue.dev | `continue` | - |

## 使用示例

### 使用 Agent 注册表（推荐）

```python
import sys
sys.path.insert(0, "scripts")

from core.agent_registry import AgentRegistry

# 初始化注册表
registry = AgentRegistry(project_root="/path/to/project")

# 获取推荐的 Agent
recommended = registry.get_recommended_agent()
print(f"Recommended: {recommended.name}")

# 获取可用的 Agent 列表
available = registry.get_available_agents()
for agent in available:
    print(f"- {agent.name}: {agent.version}")

# 获取特定 Agent 的适配器实例
adapter = registry.get_adapter("aider")
```

### 直接使用适配器

```python
from adapters import AiderAdapter, TaskType

# 创建适配器
adapter = AiderAdapter(
    project_root="/path/to/project",
    model="gpt-4"
)

# 检查是否可用
if adapter.detect() and adapter.is_api_key_configured():
    # 执行任务
    result = adapter.execute(
        task="Add error handling to the login function",
        task_type=TaskType.FEATURE,
        files=["src/auth.py"]
    )
    
    if result.success:
        print(f"Task completed in {result.duration_seconds}s")
        print(f"Modified files: {result.files_modified}")
    else:
        print(f"Error: {result.error}")
```

### 流式输出

```python
from adapters import AiderAdapter

adapter = AiderAdapter()

# 流式执行
for line in adapter.stream_execute("Refactor this code"):
    print(line, end="")
```

## 基类接口

所有适配器继承自 `BaseAdapter`，提供统一接口：

```python
class BaseAdapter:
    # 类属性
    AGENT_NAME: str           # Agent 名称
    CLI_COMMAND: str          # CLI 命令
    API_KEY_ENV_VAR: str      # API Key 环境变量
    DEFAULT_CAPABILITIES: AdapterCapability  # 支持的能力
    
    # 类方法
    @classmethod
    def detect(cls) -> bool                    # 检测是否安装
    @classmethod
    def get_version(cls) -> Optional[str]      # 获取版本
    
    # 实例方法
    def execute(task, task_type, context, files, **kwargs) -> TaskResult
    def stream_execute(task, ...) -> Iterator[str]
    def get_capabilities() -> AdapterCapability
    def is_api_key_configured() -> bool
```

## 能力标志

```python
class AdapterCapability(Flag):
    CODE_GENERATION    # 代码生成
    CODE_EDITING       # 代码编辑
    CODE_REVIEW        # 代码审查
    REFACTORING        # 重构
    DEBUGGING          # 调试
    DOCUMENTATION      # 文档生成
    TESTING            # 测试生成
    CHAT               # 交互聊天
    STREAMING          # 流式输出
    FILE_OPERATIONS    # 文件操作
    GIT_OPERATIONS     # Git 操作
    MULTI_FILE         # 多文件支持
    CONTEXT_AWARE      # 上下文感知
```

## 配置

Agent 配置存储在 `config/agents.yaml`：

```yaml
preferences:
  preferred_agent: aider
  auto_snapshot: true
  auto_commit: false

agents:
  aider:
    enabled: true
    model: gpt-4
    auto_commits: false
  claude-cli:
    enabled: true
    model: claude-3.5-sonnet
    max_tokens: 4096
```

## 环境检测

使用环境检测器查看可用的 Agent：

```bash
python3 scripts/core/env_detector.py --agents-only
```

输出示例：
```
Available AI Agents:
----------------------------------------
✅ Aider (aider)
   Version: 0.50.0
❌ Claude CLI (claude) ⚠️ (no API key)
✅ Cursor (cursor)
   Version: 0.40.0
```
