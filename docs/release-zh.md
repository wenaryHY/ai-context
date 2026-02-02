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
