# Contributing to AI Context Toolkit

感谢你对本项目的关注！我们欢迎任何形式的贡献。

Thank you for your interest in contributing! We welcome all kinds of contributions.

## 📋 How to Contribute

### 报告问题 / Report Issues

1. 检查是否已有类似的 Issue
2. 使用清晰的标题描述问题
3. 提供复现步骤和环境信息

### 提交代码 / Submit Code

1. **Fork** 本仓库

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-fix-name
   ```

3. **进行修改**
   - 遵循项目的代码规范
   - 确保通过所有验证

4. **提交变更**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```
   
   提交信息格式：
   - `feat:` 新功能
   - `fix:` 修复 bug
   - `docs:` 文档更新
   - `refactor:` 代码重构
   - `test:` 测试相关
   - `chore:` 构建/工具变更

5. **推送分支**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **创建 Pull Request**
   - 清晰描述变更内容
   - 关联相关 Issue

## ✅ Before Submitting

### 必须通过的检查

```bash
# 1. 验证核心层级同步
python3 scripts/sync-core.py --check

# 2. 验证所有必需文件
python3 scripts/validate-context.py
```

### 任务简报要求

任何变更都必须更新任务简报：

```bash
# 更新当前简报
# 编辑 docs/task-briefs/latest.md

# 或创建新简报
python3 scripts/start-task-brief.py --archive-current
```

## 📝 Code Style

### Python

- 遵循 PEP 8
- 使用 type hints
- 函数和类需要 docstring

### Markdown

- 使用一致的标题层级
- 代码块指定语言
- 链接使用相对路径

### 文档

- 英文文档为主，重要内容提供中文版
- 保持文档与代码同步更新

## 🔧 Development Setup

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/ai-context.git
cd ai-context

# 验证环境
python3 scripts/validate-context.py
```

## 📁 Project Structure Guidelines

### 添加新适配器

在 `adapters/` 目录下创建新文件：

```markdown
# adapters/your-platform.md

## Load Strategy
...

## Recommended Load Order
...

## Prompt Starter
...
```

### 添加新模板

在 `examples/prompts/` 目录下创建新文件，并更新 `README.md`。

### 修改核心规则

1. **只修改** `core/core-full.md`
2. 运行同步脚本：
   ```bash
   python3 scripts/sync-core.py
   ```
3. 验证生成结果

## 🏷️ Pull Request Guidelines

### PR 标题格式

```
<type>(<scope>): <description>

# 示例
feat(adapters): add ChatGPT adapter
fix(scripts): correct sync-core tier extraction
docs(readme): add installation instructions
```

### PR 内容

- 清晰描述变更目的
- 列出主要修改点
- 说明测试情况
- 关联相关 Issue

## 📜 License

贡献的代码将采用本项目相同的 [MIT License](LICENSE)。

## 💬 Questions?

如有问题，欢迎：
- 提交 Issue
- 在 PR 中讨论

感谢你的贡献！ 🎉
