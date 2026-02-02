# Google Gemini Adapter

## Overview

本适配器针对 Google Gemini（包括 Gemini Pro、Gemini Ultra）优化上下文加载策略。Gemini 具有超长上下文窗口（最高 1M tokens），但仍需注意质量与长度的权衡。

## Gemini 特点

| 能力 | 强项 | 注意事项 |
|------|------|----------|
| 长上下文 | ⭐⭐⭐ 最高 1M tokens | 质量可能随长度下降 |
| 多模态 | ⭐⭐⭐ 图片+代码 | 适合 UI 审查 |
| 推理 | ⭐⭐⭐ | 需要清晰指令 |
| 代码生成 | ⭐⭐ | 需要示例引导 |

## Load Strategy

### 利用长上下文优势

Gemini 的长上下文窗口允许加载更多规则文件，但建议：

```text
✅ 推荐：核心规则 + 模块文档 + 相关代码片段
❌ 避免：一次性加载所有文档 + 整个代码库
```

### 推荐加载顺序

#### 小任务
```text
1. core/core-min.md
2. 一个模块文档
```

#### 中等任务
```text
1. core/core.md
2. 一个模块文档
3. docs/contracts/README.md
4. 相关代码文件（3-5 个）
```

#### 大型任务（利用长上下文）
```text
1. core/core-full.md
2. frontend.md + backend.md（如需跨栈）
3. docs/module-map.md
4. 相关代码目录
5. 契约文件（openapi.yaml）
```

## Prompt Starters

### 通用前缀（中文）
```markdown
你是一个遵循 AI Context Toolkit 规范的开发助手。

核心规则：
[粘贴 core/core-min.md 内容]

模块规则：
[粘贴 frontend.md 或 backend.md 内容]

任务：
[具体任务描述]
```

### 代码审查（利用多模态）
```markdown
请审查以下代码和架构图：

规则参考：
- 分层架构：见 backend.md
- 命名规范：见 core/core-min.md

[粘贴代码]
[上传架构图/截图]

请检查：
1. 代码是否符合分层规范
2. 命名是否自解释
3. 图中架构是否与代码一致
```

### 大型项目分析
```markdown
我需要分析一个大型项目，请根据以下规则：

规则文件：
[粘贴 core/core-full.md]
[粘贴 docs/module-map.md]

项目代码：
[粘贴多个文件内容]

请提供：
1. 架构概览
2. 潜在问题
3. 改进建议
```

## Google AI Studio 使用技巧

### System Instructions 配置
```text
你是一个严格遵循 AI Context Toolkit 规范的开发助手。

必须遵守的规则：
1. 命名自解释，禁止模糊命名
2. DTO/VO/Request/Response 边界清晰
3. 契约优先，先更新 OpenAPI/Proto 再实现
4. 前后端仅通过契约通信

输出格式：
- 架构建议需说明权衡理由
- 代码输出需包含目录结构
- API 变更需附带契约更新
```

### 温度设置建议
| 任务类型 | 温度 | 原因 |
|----------|------|------|
| 代码生成 | 0.2-0.4 | 需要准确性 |
| 架构讨论 | 0.5-0.7 | 允许创意 |
| 代码审查 | 0.1-0.3 | 需要严谨 |

## Gemini API 集成

### Python SDK 示例
```python
import google.generativeai as genai

# 加载规则文件
def load_context(task_type: str) -> str:
    base = read_file("core/core.md")
    
    if task_type == "frontend":
        base += "\n\n" + read_file("frontend.md")
    elif task_type == "backend":
        base += "\n\n" + read_file("backend.md")
    elif task_type == "fullstack":
        base += "\n\n" + read_file("frontend.md")
        base += "\n\n" + read_file("backend.md")
    
    return base

# 配置模型
genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel(
    model_name="gemini-pro",
    system_instruction=load_context("backend")
)

# 发送请求
response = model.generate_content(
    "请帮我设计一个反馈系统的 API 接口",
    generation_config=genai.types.GenerationConfig(
        temperature=0.3,
        max_output_tokens=2048,
    )
)
```

### 多模态代码审查
```python
import PIL.Image

# 加载架构图
image = PIL.Image.open("architecture.png")

# 组合审查
response = model.generate_content([
    load_context("backend"),
    "请审查以下架构图是否符合规范：",
    image,
    "代码实现：\n" + read_file("src/service.py")
])
```

## Vertex AI 使用

### 配置示例
```python
import vertexai
from vertexai.generative_models import GenerativeModel, Part

vertexai.init(project="your-project", location="us-central1")

model = GenerativeModel(
    model_name="gemini-1.5-pro",
    system_instruction=[load_context("fullstack")]
)

# 长上下文分析
code_files = [
    Part.from_text(read_file(f)) 
    for f in ["src/api.py", "src/service.py", "src/model.py"]
]

response = model.generate_content([
    "分析以下代码的架构问题：",
    *code_files
])
```

## Best Practices

### Do ✅
- 利用长上下文加载完整规则集
- 使用多模态能力审查 UI 和架构图
- 在 System Instructions 中固定核心规则
- 分阶段处理复杂任务，每阶段确认理解

### Don't ❌
- 仅因为上下文窗口大就加载所有内容
- 忽略输出质量与上下文长度的关系
- 在单次请求中完成整个项目分析
- 假设 Gemini 会自动应用所有规则

## 与其他工具对比

| 场景 | 推荐工具 | 原因 |
|------|----------|------|
| 大型代码库分析 | Gemini | 长上下文 |
| 快速代码补全 | Copilot | IDE 集成 |
| 多文件重构 | Cursor | 编辑能力 |
| 深度架构讨论 | Claude | 推理能力 |
| 通用对话 | ChatGPT | 广泛兼容 |

## Related Docs
- `cursor.md` - Cursor 适配器
- `claude.md` - Claude 适配器
- `chatgpt.md` - ChatGPT 适配器
- `copilot.md` - GitHub Copilot 适配器
