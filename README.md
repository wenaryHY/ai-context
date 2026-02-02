# AI Context Toolkit

[![CI](https://github.com/YOUR_USERNAME/ai-context/actions/workflows/validate.yml/badge.svg)](https://github.com/YOUR_USERNAME/ai-context/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](CHANGELOG.md)

> 为 AI 辅助开发提供分层、可复用的上下文规则和模板。
>
> Layered, reusable context rules and templates for AI-assisted development.

## ✨ Features

- **分层上下文** - 三级核心规则（min/standard/full），按任务复杂度选择
- **模块化文档** - 前端（Vue/Lit + SCSS）和后端（Spring Boot + Go/Rust）独立规则
- **多 AI 适配** - 支持 Cursor、Claude 等多个 AI 平台
- **契约优先** - OpenAPI/Proto 模板，强制接口契约管理
- **任务简报** - 严格的变更追踪和归档机制
- **自动化工具** - 同步、验证、发布脚本全覆盖

## 🚀 Quick Start

### 1. 选择核心层级

| 层级 | 文件 | 适用场景 |
|------|------|----------|
| Minimal | `core/core-min.md` | 小任务、单文件修改 |
| Standard | `core/core.md` | 重构、多文件变更 |
| Full | `core/core-full.md` | 架构设计、策略制定 |

### 2. 加载模块文档

```text
核心规则 + 单一模块 = 最佳实践

示例：core/core.md + frontend.md
```

- `frontend.md` - 前端规则（Vue/Lit + SCSS + Rsbuild/Vite）
- `backend.md` - 后端规则（Spring Boot + Go/Rust）

### 3. 使用模板

```bash
# 查看 prompt 模板
ls examples/prompts/

# 可用模板
- task-brief.md           # 任务简报
- analyze-edit-verify.md  # 分阶段工作流
- feature-implementation.md
- api-change.md
- refactor.md
- code-review.md
```

## 📖 Documentation

### 用户指南

| 文档 | 语言 | 描述 |
|------|------|------|
| [docs/user-guide.md](docs/user-guide.md) | English | 人类用户指南 |
| [docs/usage.md](docs/usage.md) | English | 详细使用说明 |
| [docs/usage-zh.md](docs/usage-zh.md) | 中文 | 中文使用说明 |
| [docs/faq.md](docs/faq.md) | English | 常见问题 |

### 技术文档

| 文档 | 描述 |
|------|------|
| [docs/contracts/README.md](docs/contracts/README.md) | 契约优先指南 |
| [docs/verification.md](docs/verification.md) | 验证流程 |
| [docs/versioning.md](docs/versioning.md) | 版本策略 |
| [docs/release.md](docs/release.md) | 发布流程 |
| [collaboration-protocol.md](collaboration-protocol.md) | 多 AI 协作协议 |

## 🛠️ Scripts & Tools

### 懒人化工作流（推荐）

```bash
# 1. 一键初始化项目
python3 scripts/init.py

# 2. 启动新任务（自动创建快照）
python3 scripts/start-task.py "实现用户登录功能"

# 3. 完成任务
python3 scripts/finish-task.py --commit

# 4. 如需回滚
python3 scripts/rollback.py --list
python3 scripts/rollback.py --latest
```

### 环境检测

```bash
# 查看完整环境信息
python3 scripts/init.py --json

# 仅查看可用 AI Agent
python3 scripts/core/env_detector.py --agents-only

# 交互式选择 Agent
python3 scripts/init.py --interactive
```

### 验证

```bash
# 检查核心层级同步
python3 scripts/sync-core.py --check

# 验证所有必需文件
python3 scripts/validate-context.py
```

### 任务简报管理

```bash
# 归档当前简报
python3 scripts/archive-task-brief.py

# 创建新简报（自动归档旧简报）
python3 scripts/start-task-brief.py --archive-current

# 智能任务启动（推荐）
python3 scripts/start-task.py "任务描述" --type feature
```

### 回滚管理

```bash
# 列出所有快照
python3 scripts/rollback.py --list

# 回滚到最新快照
python3 scripts/rollback.py --latest

# 查看快照差异
python3 scripts/rollback.py --diff <snapshot_id>

# 选择性回滚特定文件
python3 scripts/rollback.py --id <snapshot_id> --files src/api.py
```

### 模块地图生成

```bash
# 为项目生成模块地图
python3 scripts/generate-module-map.py --project-root /path/to/project
```

### 发布

```bash
# Linux/macOS
./scripts/release.sh X.Y.Z

# Windows
scripts\release.cmd X.Y.Z
# or
scripts\release.ps1 X.Y.Z
```

## 📁 Project Structure

```text
ai-context/
├── core/                    # 核心上下文规则（分层）
│   ├── core-full.md         # 完整版（编辑源）
│   ├── core.md              # 标准版（自动生成）
│   └── core-min.md          # 最小版（自动生成）
├── frontend.md              # 前端模块规则
├── backend.md               # 后端模块规则
├── collaboration-protocol.md # 多 AI 协作协议
├── adapters/                # AI 平台适配器
│   ├── *.md                 # 文档适配器（Cursor/Claude/Copilot/Gemini）
│   ├── base_adapter.py      # Python 适配器基类
│   └── *_adapter.py         # Python 适配器（8 个 AI Agent）
├── config/                  # 配置文件
│   ├── agents.yaml          # Agent 配置和优先级
│   └── environments.yaml    # 环境和验证设置
├── docs/                    # 文档
│   ├── contracts/           # 契约指南
│   ├── task-briefs/         # 任务简报
│   └── ...
├── examples/                # 示例与模板
│   └── prompts/             # Prompt 模板
├── templates/               # 契约模板
│   └── contracts/
│       ├── openapi/
│       └── proto/
└── scripts/                 # 自动化脚本
    ├── core/                # 核心模块
    │   ├── rollback_manager.py  # 快照和回滚
    │   ├── env_detector.py      # 环境检测
    │   └── agent_registry.py    # Agent 注册表
    ├── init.py              # 一键初始化
    ├── start-task.py        # 智能任务启动
    ├── finish-task.py       # 任务完成
    ├── rollback.py          # 回滚管理 CLI
    └── ...                  # 其他工具脚本
```

## 🎯 Large Project Tips

### 上下文策略

1. **分层加载** - 核心规则 + 单一模块 + 任务简报
2. **检索优先** - 使用搜索/RAG，避免全量加载
3. **分阶段执行** - 分析 → 编辑 → 验证

### 严格规则

- 任何变更必须更新 `docs/task-briefs/latest.md`
- 契约变更必须更新 `templates/contracts/CHANGELOG.md`
- 验证通过后才能合并

### 推荐工具

- 代码检索：Sourcegraph/Cody, ctags+rg, SCIP/LSIF
- RAG 框架：LlamaIndex, LangChain, Haystack
- 任务 Agent：Aider, Cline, OpenHands/SWE-agent

### 支持的 AI Agent

| Agent | CLI 命令 | 说明 |
|-------|----------|------|
| Aider | `aider` | 终端 AI 编程助手 |
| Claude CLI | `claude` | Anthropic Claude |
| Cursor | `cursor` | AI-first 代码编辑器 |
| GitHub Copilot | `gh copilot` | GitHub AI 助手 |
| OpenAI CLI | `openai` | OpenAI API CLI |
| Gemini CLI | `gemini` / `gcloud` | Google AI |
| Ollama | `ollama` | 本地 LLM |
| Continue.dev | `continue` | 开源 AI 编码助手 |

## 🤝 Contributing

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 📄 License

本项目采用 [MIT License](LICENSE) 许可证。

## 📚 Related Links

- [CHANGELOG.md](CHANGELOG.md) - 版本变更记录
- [docs/module-map.md](docs/module-map.md) - 模块地图
- [docs/module-map-zh.md](docs/module-map-zh.md) - 模块地图（中文）
