# GitHub Copilot Adapter

## Overview

本适配器针对 GitHub Copilot（包括 Copilot Chat）优化上下文策略。Copilot 的特点是深度集成 IDE，擅长代码补全和内联建议。

## Copilot 特点

| 能力 | 强项 | 弱项 |
|------|------|------|
| 代码补全 | ⭐⭐⭐ | - |
| 函数生成 | ⭐⭐⭐ | - |
| 架构设计 | ⭐ | 缺乏长上下文 |
| 规范遵循 | ⭐⭐ | 需要重复提示 |

## Load Strategy

### Copilot Chat（推荐）

Copilot Chat 支持 `@workspace` 指令，可以引用项目文件：

```text
@workspace 请根据 /ai-context/core/core-min.md 的规则...
```

### 推荐加载顺序

1. 将核心规则放入项目根目录的 `.github/copilot-instructions.md`
2. 在 Chat 中引用具体模块文档
3. 使用 `/explain` 和 `/fix` 命令时附带规则提示

## Copilot Instructions 配置

在项目根目录创建 `.github/copilot-instructions.md`：

```markdown
# Copilot Instructions

## 代码风格
- 命名必须自解释，禁止 `data`、`temp`、`obj` 等模糊命名
- 同类概念词汇统一（userId 和 accountId 不混用）

## 架构规范
- Controller 只做编排，业务逻辑在 Service/UseCase
- 必须定义 DTO/VO/Request/Response，禁止裸露 Entity

## 前端规范
- 全局样式统一在 SCSS 入口
- 组件内只允许 scoped 局部样式

## 后端规范
- Service 层进行事务控制
- 统一异常映射，不允许底层异常外泄

## 安全
- 默认拒绝，最小权限
- 参数校验在入口层完成
```

## Copilot Chat Commands

### 代码解释
```text
/explain 这个函数

请同时检查：
1. 命名是否符合 core/core-min.md 的规范
2. 是否存在面条代码
```

### 代码修复
```text
/fix

修复时请遵循：
- 保持 DTO/VO 边界
- 不要跨层调用
```

### 代码生成
```text
/generate 创建一个 FeedbackService

要求：
- 遵循 backend.md 的分层规范
- 使用 DTO/VO 进行数据转换
- 包含基本的异常处理
```

### 测试生成
```text
/tests

测试覆盖：
- 正常流程
- 边界条件
- 权限校验
- 幂等性
```

## 内联提示技巧

### 函数签名提示
```java
// 根据 core/core-min.md 规范：
// - 返回 VO 不是 Entity
// - 参数使用 Request DTO
public FeedbackVO createFeedback(CreateFeedbackRequest request) {
    // Copilot 会根据注释生成符合规范的实现
}
```

### 类结构提示
```java
/**
 * Feedback 用例层
 * 
 * 职责：
 * - 业务编排
 * - 事务控制
 * - DTO/VO 转换
 * 
 * 依赖：
 * - FeedbackRepository (数据访问)
 * - NotificationService (通知)
 */
@Service
public class FeedbackUseCase {
    // Copilot 会生成符合描述的方法
}
```

### 规范引用注释
```typescript
// 根据 frontend.md SCSS 规范：
// - 使用全局 tokens 变量
// - 不在组件内重复定义颜色
const styles = {
    // Copilot 会使用 CSS 变量而非硬编码颜色
}
```

## VS Code 设置

### settings.json
```json
{
    "github.copilot.enable": {
        "*": true,
        "markdown": true,
        "yaml": true
    },
    "github.copilot.advanced": {
        "inlineSuggestCount": 3
    }
}
```

### 工作区设置
```json
{
    "github.copilot.chat.localeOverride": "zh-CN",
    "github.copilot.editor.enableAutoCompletions": true
}
```

## 与 Cursor 协同使用

当同时使用 Copilot 和 Cursor 时：

| 工具 | 适用场景 |
|------|----------|
| Copilot | 内联补全、快速函数生成 |
| Cursor | 多文件重构、架构讨论 |

### 工作流建议
```text
1. Cursor：加载规则，讨论方案
2. Copilot：生成代码框架
3. Cursor：审查和优化
4. Copilot：补充细节和测试
```

## Best Practices

### Do ✅
- 在 `.github/copilot-instructions.md` 中定义项目规范
- 使用详细的函数签名和注释引导生成
- 结合 Copilot Chat 的 `@workspace` 引用规则文件
- 生成后检查是否符合分层和命名规范

### Don't ❌
- 期望 Copilot 记住复杂的架构规则
- 在没有上下文的情况下生成大段代码
- 忽略生成代码的边界检查
- 让 Copilot 处理跨模块的复杂重构

## Related Docs
- `cursor.md` - Cursor 适配器
- `claude.md` - Claude 适配器
- `chatgpt.md` - ChatGPT 适配器
