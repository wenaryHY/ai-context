# Backend Architecture Solutions

Context: plugin-trace backend (Halo plugin). Solution proposals for issues documented in `issues.md`.

## Overview

本文档针对 `issues.md` 中识别的五个关键问题，提供分阶段的解决方案。每个方案都考虑了：
- 短期快速修复（Quick Win）
- 中期结构优化（Structural）
- 长期架构演进（Architectural）

---

## 1. 全量扫描与内存过滤/分页

### 问题回顾
- `client.list(...).collectList()` + 内存过滤/分页
- 数据量增长后性能下降、内存压力增大

### 解决方案

#### 短期（Quick Win）
```java
// 1. 添加数据规模边界定义
public interface DataScaleLimits {
    int SMALL_DATA_THRESHOLD = 1000;    // 允许全量扫描
    int MEDIUM_DATA_THRESHOLD = 10000;  // 需要服务端过滤
    int LARGE_DATA_THRESHOLD = 100000;  // 需要预聚合
}

// 2. 在列表接口添加规模检查和降级
public Mono<PageResult<FeedbackVO>> listFeedbacks(FeedbackQuery query) {
    return countFeedbacks(query.getFilters())
        .flatMap(count -> {
            if (count > DataScaleLimits.MEDIUM_DATA_THRESHOLD) {
                return Mono.error(new TooManyResultsException(
                    "Please narrow your filters. Results: " + count));
            }
            return doListFeedbacks(query);
        });
}
```

#### 中期（Structural）
```java
// 1. 引入服务端过滤器抽象
public interface FilterableRepository<T> {
    Flux<T> findByFilters(Map<String, Object> filters, Pageable pageable);
    Mono<Long> countByFilters(Map<String, Object> filters);
}

// 2. 为高频查询添加索引表或视图
// 创建 feedback_summary 索引表
@Entity
public class FeedbackSummary {
    private String feedbackId;
    private String status;
    private String categoryId;
    private LocalDateTime createdAt;
    // 仅存储过滤和排序所需字段
}

// 3. 使用索引表进行列表查询
public Flux<FeedbackVO> listFeedbacks(FeedbackQuery query) {
    return feedbackSummaryRepo.findByFilters(query.toFilters(), query.getPageable())
        .flatMap(summary -> feedbackRepo.findById(summary.getFeedbackId()))
        .map(this::toVO);
}
```

#### 长期（Architectural）
```text
读写分离架构：

┌─────────────┐     ┌─────────────┐
│   Write     │────>│   Event     │
│   Model     │     │   Store     │
└─────────────┘     └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Read      │
                    │   Model     │
                    │  (预聚合)    │
                    └─────────────┘

- 写操作发布事件
- 异步构建读模型（按状态/分类/时间预聚合）
- 列表查询直接访问读模型
```

---

## 2. 计数器并发问题

### 问题回顾
- 投票/评论计数使用 read-modify-write
- 并发时可能出现竞态条件和计数漂移

### 解决方案

#### 短期（Quick Win）
```java
// 1. 添加乐观锁版本字段
@Version
private Long version;

// 2. 使用重试机制
@Retryable(value = OptimisticLockingFailureException.class, maxAttempts = 3)
public Mono<Void> incrementVoteCount(String feedbackId) {
    return feedbackRepo.findById(feedbackId)
        .flatMap(feedback -> {
            feedback.setVoteCount(feedback.getVoteCount() + 1);
            return feedbackRepo.save(feedback);
        })
        .then();
}
```

#### 中期（Structural）
```java
// 1. 原子更新操作（如果 ORM 支持）
public interface FeedbackRepository {
    @Modifying
    @Query("UPDATE Feedback f SET f.voteCount = f.voteCount + :delta WHERE f.id = :id")
    Mono<Integer> incrementVoteCount(String id, int delta);
}

// 2. 或使用专用计数器服务
@Service
public class CounterService {
    private final Map<String, AtomicLong> counters = new ConcurrentHashMap<>();
    
    public void increment(String key) {
        counters.computeIfAbsent(key, k -> new AtomicLong(0)).incrementAndGet();
    }
    
    // 定期同步到数据库
    @Scheduled(fixedRate = 5000)
    public void syncToDatabase() {
        counters.forEach((key, value) -> {
            long count = value.getAndSet(0);
            if (count > 0) {
                feedbackRepo.incrementVoteCount(key, (int) count).subscribe();
            }
        });
    }
}
```

#### 长期（Architectural）
```text
事件驱动计数：

┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Vote      │────>│   Event     │────>│   Counter   │
│   Action    │     │   Bus       │     │   Aggregate │
└─────────────┘     └─────────────┘     └─────────────┘

- 投票操作发布事件（VoteCreated, VoteDeleted）
- 计数器服务订阅事件，原子更新计数
- 支持纠偏任务定期校准
```

---

## 3. 接口层臃肿与重复

### 问题回顾
- Auth、幂等性、用户信息构建在多个 Endpoint 重复
- 维护成本高，行为不一致风险

### 解决方案

#### 短期（Quick Win）
```java
// 1. 提取通用逻辑到工具类
@Component
public class EndpointHelper {
    
    public Mono<UserProfile> buildUserProfile(ServerRequest request) {
        return ReactiveSecurityContextHolder.getContext()
            .map(ctx -> ctx.getAuthentication())
            .flatMap(auth -> userService.getProfile(auth.getName()));
    }
    
    public <T> Mono<T> withIdempotency(String key, Supplier<Mono<T>> action) {
        return idempotencyStore.checkAndLock(key)
            .flatMap(locked -> locked ? action.get() : Mono.error(new DuplicateRequestException()));
    }
}

// 2. 在 Endpoint 中使用
public Mono<ServerResponse> createFeedback(ServerRequest request) {
    return endpointHelper.buildUserProfile(request)
        .flatMap(profile -> endpointHelper.withIdempotency(
            "create-feedback-" + profile.getId(),
            () -> feedbackService.create(request.bodyToMono(FeedbackRequest.class), profile)
        ))
        .flatMap(result -> ServerResponse.ok().bodyValue(result));
}
```

#### 中期（Structural）
```java
// 1. 引入 UseCase/ApplicationService 层
@Service
public class FeedbackUseCase {
    
    public Mono<FeedbackVO> createFeedback(CreateFeedbackCommand cmd, UserContext userCtx) {
        // 所有业务逻辑集中在这里
        return validateCommand(cmd)
            .then(checkPermissions(userCtx))
            .then(feedbackService.create(cmd.toEntity(), userCtx))
            .map(this::toVO);
    }
}

// 2. Endpoint 只做路由和参数转换
public class FeedbackEndpoint {
    
    public Mono<ServerResponse> create(ServerRequest request) {
        return request.bodyToMono(CreateFeedbackRequest.class)
            .zipWith(userContextResolver.resolve(request))
            .flatMap(tuple -> feedbackUseCase.createFeedback(
                tuple.getT1().toCommand(), 
                tuple.getT2()
            ))
            .flatMap(vo -> ServerResponse.ok().bodyValue(vo));
    }
}

// 3. 使用切面处理横切关注点
@Aspect
@Component
public class EndpointAspects {
    
    @Around("@annotation(Idempotent)")
    public Object handleIdempotency(ProceedingJoinPoint pjp) {
        // 统一幂等性处理
    }
    
    @Around("@annotation(RequiresAuth)")
    public Object handleAuth(ProceedingJoinPoint pjp) {
        // 统一认证处理
    }
}
```

#### 长期（Architectural）
```text
六边形架构重构：

┌─────────────────────────────────────────┐
│               Adapters                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │  REST   │  │  gRPC   │  │  Event  │ │
│  │Endpoint │  │ Handler │  │ Listener│ │
│  └────┬────┘  └────┬────┘  └────┬────┘ │
└───────┼────────────┼────────────┼───────┘
        │            │            │
        ▼            ▼            ▼
┌─────────────────────────────────────────┐
│           Application Layer             │
│  ┌─────────────────────────────────┐   │
│  │          Use Cases              │   │
│  │  (CreateFeedback, VoteFeedback) │   │
│  └─────────────────────────────────┘   │
└───────────────────┬─────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│            Domain Layer                 │
│  ┌──────────┐  ┌──────────────────┐    │
│  │ Entities │  │ Domain Services  │    │
│  └──────────┘  └──────────────────┘    │
└─────────────────────────────────────────┘
```

---

## 4. 响应式流中的阻塞 IO

### 问题回顾
- CSV 解析/导入导出、文件写入在响应式流中执行
- 阻塞事件循环，降低吞吐量

### 解决方案

#### 短期（Quick Win）
```java
// 1. 使用 boundedElastic 调度器隔离阻塞操作
public Mono<List<Feedback>> importFromCsv(InputStream inputStream) {
    return Mono.fromCallable(() -> csvParser.parse(inputStream))
        .subscribeOn(Schedulers.boundedElastic())  // 关键：隔离到专用线程池
        .flatMapMany(Flux::fromIterable)
        .flatMap(feedbackService::save)
        .collectList();
}

// 2. 文件操作同样处理
public Mono<Void> writeToFile(String content, Path path) {
    return Mono.fromCallable(() -> {
            Files.writeString(path, content);
            return null;
        })
        .subscribeOn(Schedulers.boundedElastic())
        .then();
}
```

#### 中期（Structural）
```java
// 1. 引入异步任务服务
@Service
public class AsyncTaskService {
    private final TaskExecutor taskExecutor;
    private final TaskRepository taskRepo;
    
    public Mono<Task> submitImportTask(ImportRequest request) {
        Task task = Task.create(TaskType.IMPORT, request);
        return taskRepo.save(task)
            .doOnSuccess(t -> taskExecutor.execute(() -> processImport(t)));
    }
    
    public Mono<TaskStatus> getTaskStatus(String taskId) {
        return taskRepo.findById(taskId).map(Task::getStatus);
    }
}

// 2. 接口返回任务 ID，客户端轮询状态
public Mono<ServerResponse> importFeedbacks(ServerRequest request) {
    return request.bodyToMono(ImportRequest.class)
        .flatMap(asyncTaskService::submitImportTask)
        .flatMap(task -> ServerResponse.accepted()
            .bodyValue(new TaskResponse(task.getId(), "PROCESSING")));
}
```

#### 长期（Architectural）
```text
流式处理架构：

┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Upload    │────>│   Message   │────>│   Worker    │
│   API       │     │   Queue     │     │   Service   │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                        ┌──────▼──────┐
                                        │   Stream    │
                                        │   Process   │
                                        │  (Chunked)  │
                                        └─────────────┘

- 大文件分块上传
- 消息队列解耦
- Worker 流式处理，避免全量内存加载
```

---

## 5. 测试缺失

### 问题回顾
- `src/test/java` 为空
- 行为变更时容易引入回归

### 解决方案

#### 短期（Quick Win）
```java
// 1. 添加核心工作流测试
@SpringBootTest
class FeedbackWorkflowTest {
    
    @Test
    void shouldTransitionStatus_fromPending_toInProgress() {
        // Given
        Feedback feedback = createFeedback(Status.PENDING);
        
        // When
        Mono<Feedback> result = feedbackService.startProcessing(feedback.getId());
        
        // Then
        StepVerifier.create(result)
            .assertNext(f -> assertEquals(Status.IN_PROGRESS, f.getStatus()))
            .verifyComplete();
    }
}

// 2. 添加幂等性测试
@Test
void shouldRejectDuplicateVote() {
    // Given
    String feedbackId = "test-id";
    String userId = "user-1";
    voteService.vote(feedbackId, userId).block();
    
    // When/Then
    StepVerifier.create(voteService.vote(feedbackId, userId))
        .expectError(DuplicateVoteException.class)
        .verify();
}
```

#### 中期（Structural）
```java
// 最小测试集覆盖清单
class MinimalTestSuite {
    
    // 1. 权限测试
    @Nested
    class PermissionTests {
        @Test void anonymousUser_cannotCreateFeedback() { }
        @Test void regularUser_canCreateFeedback() { }
        @Test void admin_canDeleteAnyFeedback() { }
    }
    
    // 2. 幂等性测试
    @Nested
    class IdempotencyTests {
        @Test void duplicateCreate_shouldBeRejected() { }
        @Test void duplicateVote_shouldBeRejected() { }
    }
    
    // 3. 状态流转测试
    @Nested
    class StatusTransitionTests {
        @Test void pending_canTransitionTo_inProgress() { }
        @Test void inProgress_canTransitionTo_resolved() { }
        @Test void resolved_cannotTransitionTo_pending() { }
    }
    
    // 4. 导入导出测试
    @Nested
    class ImportExportTests {
        @Test void importCsv_shouldCreateFeedbacks() { }
        @Test void exportCsv_shouldContainAllFields() { }
        @Test void importInvalidCsv_shouldReportErrors() { }
    }
}
```

#### 长期（Architectural）
```text
测试金字塔：

            ┌───────────┐
            │   E2E     │  少量关键路径
            │   Tests   │
            ├───────────┤
            │Integration│  核心业务流程
            │   Tests   │
            ├───────────┤
            │   Unit    │  大量，快速
            │   Tests   │
            └───────────┘

- 单元测试：纯函数、领域逻辑
- 集成测试：服务交互、数据库操作
- E2E 测试：关键用户路径
```

---

## 实施优先级

| 优先级 | 问题 | 推荐方案 | 预估工作量 |
|:------:|------|----------|-----------|
| 🔴 P0 | 测试缺失 | 短期 + 中期 | 2-3 天 |
| 🟠 P1 | 阻塞 IO | 短期（boundedElastic）| 0.5 天 |
| 🟠 P1 | 接口层重复 | 短期 + 中期 | 2 天 |
| 🟡 P2 | 计数器并发 | 中期（原子更新）| 1 天 |
| 🟡 P2 | 全量扫描 | 短期 + 中期 | 3-5 天 |

---

## 数据规模边界定义

| 规模 | 记录数 | 允许操作 | 优化要求 |
|------|--------|----------|----------|
| 小 | < 1,000 | 全量扫描、内存过滤 | 无 |
| 中 | 1,000 - 10,000 | 服务端过滤 | 添加筛选参数 |
| 大 | > 10,000 | 预聚合、读写分离 | 架构升级 |

当前 plugin-trace 预估为**小规模**场景，短期方案足够。当数据量接近中等规模时，启动中期优化。
