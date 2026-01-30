# Collaboration Protocol (Multi-AI on Same Project)

## 目标

在多 AI 并行修改同一项目时，最大化并行度并最小化冲突。核心原则是：**边界清晰、契约优先、分支隔离、合并门禁**。

## 分工与边界（必须）

- 按模块/上下文分工：Frontend / Backend / Contracts / Infra / Docs。
- 每个任务只允许修改单一模块的文件，跨模块变更必须先做合并评审。
- 同一时段不允许多 AI 修改同一文件。

## 推荐结构目录（建议）

```text
contracts/
  openapi/
    openapi.yaml
  proto/
    service/v1/
      service.proto
  CHANGELOG.md
doc/ai-context/
  frontend.md
  backend.md
  collaboration-protocol.md
frontend/
  src/
  package.json
backend-springboot/
  src/
  build.gradle
backend-go/
  cmd/
  internal/
backend-rust/
  crates/
infra/
  ci/
  deploy/
```

## 契约优先（必须）

- API/Proto 先变更，再做实现。
- 契约变更需要记录在 `contracts/CHANGELOG.md`（若无则创建）。
- 契约变更需声明：新增/修改/废弃字段、兼容性与版本策略。

## 分支策略（必须）

- 每个 AI 对应一个分支：`ai/<task-name>`。
- 任何变更必须通过 PR 合并，禁止直接推 main。
- PR 范围尽量小（单主题、单模块、单契约）。

## 合并顺序（必须）

1) 合并契约层（OpenAPI/Proto）
2) 合并实现层（Service/Controller/Client）
3) 合并文档与示例

## 冲突预防与处理（必须）

- 合并前先 rebase 到最新 main。
- 若发生冲突，由**合并仲裁人**统一裁决（指定一人/AI）。
- 冲突解决后必须补充/更新测试。

## CI 合并门禁（必须）

- Lint/Format/Type-check 必过
- Contract diff 必过（OpenAPI/Proto 兼容性检查）
- 单测/集成测试必过

## 变更记录（必须）

- 每个 PR 必须包含变更摘要与影响范围说明。
- 涉及契约变更必须更新变更日志与版本号。

## 最小交叉原则（建议）

- 通过任务拆分和依赖排序降低交叉范围。
- 优先通过扩展/新增避免改动公共核心文件。
