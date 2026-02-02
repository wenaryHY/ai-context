# 中文使用说明

## 适用对象
本说明面向维护和使用本仓库的人类用户。

## 懒人化工作流（推荐）

### 一键初始化
```bash
# 自动检测环境并选择最优 AI Agent
python3 scripts/init.py

# 交互式选择 Agent
python3 scripts/init.py --interactive

# 指定 Agent
python3 scripts/init.py --agent aider
```

### 启动任务
```bash
# 基本用法（自动创建快照）
python3 scripts/start-task.py "实现用户登录功能"

# 指定任务类型
python3 scripts/start-task.py "修复登录 bug" --type fix

# 指定文件
python3 scripts/start-task.py "重构 API" --files src/api.py src/service.py
```

### 完成任务
```bash
# 验证并归档
python3 scripts/finish-task.py

# 带自动提交
python3 scripts/finish-task.py --commit
```

### 回滚（如需撤销 AI 修改）
```bash
# 列出所有快照
python3 scripts/rollback.py --list

# 回滚到最新快照
python3 scripts/rollback.py --latest

# 查看差异后决定
python3 scripts/rollback.py --diff <snapshot_id>

# 选择性回滚特定文件
python3 scripts/rollback.py --id <snapshot_id> --files src/api.py
```

## 日常使用流程
1. 选择最小可用的核心层级。
2. 只加载一个模块文档（`frontend.md` 或 `backend.md`）。
3. 只有在改接口时才加载契约文档。

## 安全修改规则
1. 只修改 `core/core-full.md`。
2. 重新生成分层：
   - `python3 scripts/sync-core.py`
3. 执行校验：
   - `python3 scripts/validate-context.py`

## 文件使用建议
- `core/core-min.md`：小改动、单文件任务。
- `core/core.md`：重构或多文件任务。
- `core/core-full.md`：架构与规则类改动。

## 大型项目上下文策略
### 典型表现
- AI 只改局部代码，容易忽略跨模块影响。
- 全局约束在多轮对话中被遗忘。

### 解决思路
- 分层上下文：核心规则 + 单一模块 + 任务简报（边界/禁止触碰）。
- 检索优先：用搜索/RAG 拉取相关代码片段。
- 分阶段流程：分析 -> 修改 -> 校验，强制检查点。
- 守门规则：契约/命名/一致性检查清单必过。
- 多 Agent 分工：分析/修改/审查角色隔离。

### 模板与索引
- 任务简报模板：`../examples/prompts/task-brief.md`
- 分阶段流程模板：`../examples/prompts/analyze-edit-verify.md`
- 模块地图：`module-map-zh.md`（保持更新）
  - 自动生成：`python3 scripts/generate-module-map.py --project-root /path/to/project`

### 严格执行
- 任何变更都必须更新 `docs/task-briefs/latest.md`。
- 缺少 git 或未更新简报会导致校验失败。
- 执行归档：`python3 scripts/archive-task-brief.py`。
- 新建简报：`python3 scripts/start-task-brief.py --archive-current`。

### 检索优先实践
1. 大型项目先读 `docs/module-map-zh.md`。
2. 用搜索定位入口、服务、契约定义。
3. 仅加载 3-5 个关键文件，避免整文件倾倒。
4. 修改前确认依赖与副作用。

### 常见方案
- 代码检索/索引：Sourcegraph/Cody、ctags+rg、SCIP/LSIF。
- RAG 框架：LlamaIndex、LangChain、Haystack。
- 任务型 Agent：Aider、Cline、OpenHands/SWE-agent。

### 支持的 AI Agent
本工具包为 8 个 AI 编码助手提供 Python 适配器：

| Agent | CLI 命令 | API Key 环境变量 |
|-------|----------|-----------------|
| Aider | `aider` | `OPENAI_API_KEY` |
| Claude CLI | `claude` | `ANTHROPIC_API_KEY` |
| Cursor | `cursor` | - |
| GitHub Copilot | `gh copilot` | `GITHUB_TOKEN` |
| OpenAI CLI | `openai` | `OPENAI_API_KEY` |
| Gemini CLI | `gemini` / `gcloud` | `GOOGLE_API_KEY` |
| Ollama | `ollama` | - (本地模型) |
| Continue.dev | `continue` | - |

使用 `python3 scripts/core/env_detector.py --agents-only` 查看可用的 Agent。

## 架构注意事项（参考）
### 常见根因
- 查询/过滤能力不足，导致全量扫描 + 内存分页。
- 交付优先，接口层堆叠业务与重复逻辑。
- 响应式链路混入阻塞 IO（导入导出/文件写入）。
- 缺少数据规模与性能基线，问题被延后暴露。

### 方案选择（按规模/一致性）
- 列表/统计：小规模可全量扫；中规模需服务端过滤或索引表；大规模用预聚合/读写分离。
- 计数一致性：低并发可读改写+纠偏；中并发用乐观锁；高并发用原子计数或事件投影。
- 导入导出：小文件用专用线程池隔离；大文件用异步任务 + 流式处理。
- 接口层治理：重复逻辑多时抽 UseCase/Assembler，接口仅做入参/出参与路由。

### 设计阶段预防
- 明确数据规模上限、QPS 与响应目标，并写入文档。
- 设定数据访问规则：默认禁止全量扫；列表必须可扩展筛选。
- 计数类必须选定一致性策略（原子/乐观锁/事件投影三选一）。
- 阻塞任务必须隔离到专用线程池或后台任务。
- 最小测试集必须覆盖：权限、幂等、状态流转、导入/导出。

## 常见问题
- CI 失败时先跑 `python3 scripts/validate-context.py`。
- 分层不同步时跑 `python3 scripts/sync-core.py`。

## 相关链接
- 人类使用说明：`user-guide.md`
- 发布流程（中文）：`release-zh.md`
- 常见问题：`faq.md`
- 模块地图：`module-map-zh.md`

## Windows 使用提示
- 验证：`scripts\\verify.cmd` 或 `scripts\\verify.ps1`
- 发布：`scripts\\release.cmd X.Y.Z` 或 `scripts\\release.ps1 X.Y.Z`
