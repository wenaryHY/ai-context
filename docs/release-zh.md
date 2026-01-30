# 发布流程（中文）

## 自动发布（GitHub Actions）
1. 确保工作区干净。
2. 更新必要文档与变更记录：
   - 规则变更：`core/core-full.md`
   - 契约变更：`templates/contracts/CHANGELOG.md`
3. 执行校验：
   - `python3 scripts/sync-core.py --check`
   - `python3 scripts/validate-context.py`
4. 打标签并推送：
   - Linux/macOS：`./scripts/release.sh X.Y.Z`
   - Windows：`scripts\\release.cmd X.Y.Z` 或 `scripts\\release.ps1 X.Y.Z`

推送标签后会触发 GitHub Actions 自动创建 Release。

## 手动发布（可选）
1. 生成系统时间戳：
   - `date -u +"%Y-%m-%dT%H:%M:%SZ"`
2. 使用带时间戳的 tag message 打标签并推送。
3. 在 GitHub UI 创建 Release。

## 时间戳要求
时间戳必须来自系统命令，不允许手工推断。
