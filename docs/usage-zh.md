# 中文使用说明

## 适用对象
本说明面向维护和使用本仓库的人类用户。

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

## 常见问题
- CI 失败时先跑 `python3 scripts/validate-context.py`。
- 分层不同步时跑 `python3 scripts/sync-core.py`。
