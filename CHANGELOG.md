# Changelog

All notable changes to AI Context Toolkit are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **懒人化脚本系统** - 一键启动 AI 辅助开发
  - `scripts/init.py` - 一键初始化，环境检测 + Agent 选择 + 配置生成
  - `scripts/start-task.py` - 智能任务启动，自动创建快照和 task brief
  - `scripts/finish-task.py` - 任务完成，验证 + 归档 + 可选 git 提交
  - `scripts/rollback.py` - 快照回滚管理 CLI
- **核心模块** (`scripts/core/`)
  - `rollback_manager.py` - 快照和回滚管理器，支持 Git stash 和文件备份模式
  - `env_detector.py` - 全面的环境检测器（系统、语言、AI Agent、项目类型）
  - `agent_registry.py` - AI Agent 注册表，自动检测和优先级管理
- **8 个 AI Agent Python 适配器** (`adapters/`)
  - `aider_adapter.py` - Aider 终端 AI 编程助手
  - `claude_cli_adapter.py` - Anthropic Claude CLI
  - `cursor_api_adapter.py` - Cursor IDE 集成
  - `copilot_cli_adapter.py` - GitHub Copilot CLI
  - `openai_cli_adapter.py` - OpenAI CLI
  - `gemini_cli_adapter.py` - Google Gemini CLI
  - `ollama_adapter.py` - Ollama 本地模型
  - `continue_adapter.py` - Continue.dev
- **配置文件** (`config/`)
  - `agents.yaml` - Agent 配置和优先级
  - `environments.yaml` - 环境和验证设置

### Changed
- 更新 `adapters/__init__.py` 导出所有适配器类
- 更新 `scripts/core/__init__.py` 导出所有核心模块

### Fixed
- 修复 YAML 依赖问题，支持 JSON 回退模式

## [1.0.0] - 2026-02-03

### Added
- Core context tiers: `core-min.md`, `core.md`, `core-full.md` with automatic synchronization.
- Module documentation: `frontend.md` (Vue/Lit + SCSS + Rsbuild/Vite) and `backend.md` (Spring Boot + Go/Rust).
- Collaboration protocol for multi-AI workflows.
- Adapters for Cursor, Claude, and plain text environments.
- Task brief enforcement system with archive and validation.
- Module map generator with Chinese and English output.
- Contract templates for OpenAPI and Proto.
- GitHub Actions CI/CD pipelines for validation and release.
- Comprehensive documentation: usage guides, FAQ, versioning, and release docs.
- Chinese documentation: `usage-zh.md`, `release-zh.md`, `module-map-zh.md`.
- Example prompt templates for common workflows.
- Cross-platform scripts: Bash, PowerShell, and CMD support.

### Technical Highlights
- Layered context architecture for scalable AI assistance.
- Contract-first development principles embedded in rules.
- Architecture notes covering scalability, consistency, and performance patterns.
