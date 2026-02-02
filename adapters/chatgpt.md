# ChatGPT Adapter

## Overview

本适配器针对 OpenAI ChatGPT（包括 GPT-4、GPT-4o 等）优化上下文加载策略。

## Load Strategy

ChatGPT 具有较大的上下文窗口（GPT-4: 8K/32K/128K），但响应质量与上下文长度成反比。建议：

- **保持精简**：即使窗口大，也优先加载必要内容
- **结构化输入**：使用清晰的 Markdown 格式
- **分段对话**：复杂任务分多轮完成

## Recommended Load Order

### 小任务（单文件修改）
```text
1. core/core-min.md
2. 一个模块文档（frontend.md 或 backend.md）
```

### 中等任务（多文件重构）
```text
1. core/core.md
2. 一个模块文档
3. docs/contracts/README.md（如涉及 API 变更）
```

### 复杂任务（架构设计）
```text
1. core/core-full.md
2. 一个模块文档
3. docs/contracts/README.md
4. docs/module-map.md（大型项目）
```

## Prompt Starters

### 通用前缀
```markdown
请遵循以下规则进行开发：

1. 核心规则见 `core/core-min.md`
2. 模块规则见 `[frontend|backend].md`
3. 契约变更需先更新 CHANGELOG

任务：[具体任务描述]
```

### 代码审查
```markdown
请根据以下规则审查代码：

规则来源：
- 命名规范：见 core/core-min.md 的 Naming 部分
- 分层架构：见 backend.md 的架构规范
- 契约一致性：见 docs/contracts/README.md

待审查代码：
[粘贴代码]
```

### 架构讨论
```markdown
我需要进行架构设计，请参考：

1. core/core-full.md - 核心架构原则
2. backend.md - 后端分层规范
3. collaboration-protocol.md - 协作规范

背景：[项目背景]
目标：[设计目标]
约束：[已知约束]
```

## Context Management Tips

### 多轮对话策略
```text
Round 1: 加载规则 + 分析现状
Round 2: 提出方案 + 讨论权衡
Round 3: 确认方案 + 输出代码
Round 4: 审查 + 迭代
```

### 避免上下文丢失
```markdown
每轮开始时添加摘要：

上一轮结论：
- [结论1]
- [结论2]

本轮目标：
- [目标]
```

### 使用 Custom Instructions（自定义指令）

在 ChatGPT 的 Custom Instructions 中添加：

**What would you like ChatGPT to know about you?**
```text
我是一名全栈开发者，使用 AI Context Toolkit 管理开发规范。
项目技术栈：Vue + Spring Boot
核心规则文件：core/core.md
```

**How would you like ChatGPT to respond?**
```text
- 遵循契约优先原则
- 代码输出包含：架构建议、权衡理由、测试策略
- 使用中文交流，代码注释用英文
- 引用规则时指明来源文件
```

## Integration with ChatGPT API

### System Message 示例
```python
system_message = """
你是一个遵循 AI Context Toolkit 规范的开发助手。

核心原则：
- 命名自解释，禁止歧义
- DTO/VO/Request/Response 边界清晰
- 契约（OpenAPI/Proto）是唯一事实源
- 前后端仅通过契约通信

输出要求：
- 架构建议 + 权衡理由 + 风险点
- 代码需包含清晰的目录结构说明
- API 变更需附带契约更新建议
"""
```

### 动态加载规则
```python
def build_context(task_type: str) -> str:
    base = read_file("core/core-min.md")
    
    if task_type == "frontend":
        base += "\n\n" + read_file("frontend.md")
    elif task_type == "backend":
        base += "\n\n" + read_file("backend.md")
    
    if task_type in ["api", "contract"]:
        base += "\n\n" + read_file("docs/contracts/README.md")
    
    return base
```

## Best Practices

### Do ✅
- 使用结构化 Markdown 格式化输入
- 分阶段完成复杂任务
- 在对话开始时声明使用的规则文件
- 每轮结束时确认理解是否正确

### Don't ❌
- 一次性加载所有文档（即使窗口够大）
- 在单轮中完成复杂架构设计
- 假设 ChatGPT 记住了之前对话的所有细节
- 忽略输出的规则引用检查

## Related Docs
- `cursor.md` - Cursor 适配器
- `claude.md` - Claude 适配器
- `plain.md` - 通用文本适配器
