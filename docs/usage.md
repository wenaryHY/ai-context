# Context Usage Guide

## Choose the Right Tier
- **core-min.md**: quick edits, small tasks, single file changes.
- **core.md**: refactors, multi-file changes, cross-module tasks.
- **core-full.md**: architecture, policy, or system-wide decisions.

## Compose Modules (Minimal Set)
Always start with the smallest set that still covers the task:
1) Core tier (`core/core-min.md` or `core/core.md`)
2) One module doc (`frontend.md` or `backend.md`)
3) `docs/contracts/README.md` when changing APIs/contracts
4) `collaboration-protocol.md` when multiple AIs are working

## Avoid Overlong Prompts
- Do not attach both frontend and backend docs unless necessary.
- Avoid combining `core-full.md` with multiple module docs.
- Prefer contract templates over long prose when discussing APIs.

## Large Project Context Strategy
### Symptoms
- The model edits only a small slice and misses cross-module impacts.
- Global constraints are forgotten between steps.

### Remedies
- Layered context: core + one module + task brief (scope, boundaries, do-not-touch).
- Retrieval-first: search or RAG to pull only relevant code slices.
- Staged workflow: analyze -> edit -> verify, with explicit checkpoints.
- Guardrails: mandatory checklists for contracts, naming, and consistency.
- Multi-agent roles: analyzer, editor, reviewer with clear boundaries.

### Templates
- Task brief: `../examples/prompts/task-brief.md`
- Staged workflow: `../examples/prompts/analyze-edit-verify.md`
- Module map: `module-map.md` (keep it updated)
  - Generate: `python3 scripts/generate-module-map.py --project-root /path/to/project`

### Enforcement (Strict)
- Any change requires updating `docs/task-briefs/latest.md`.
- Validation fails if git is missing or the brief is not updated.
- Archive the brief with `python3 scripts/archive-task-brief.py`.
- Start a new brief with `python3 scripts/start-task-brief.py --archive-current`.

### Retrieval-first Workflow (Practical)
1. Start with `docs/module-map.md` if the project is large.
2. Run targeted searches for entrypoints, services, and contracts.
3. Load only 3-5 key files; avoid full file dumps.
4. Confirm dependencies and side effects before editing.

### Common Options
- Code search/index: Sourcegraph/Cody, ctags+rg, SCIP/LSIF.
- RAG frameworks: LlamaIndex, LangChain, Haystack.
- Task agents: Aider, Cline, OpenHands/SWE-agent.

## Architecture Notes (Reference)
### Root causes
- Limited query/filter support leads to full scans and in-memory paging.
- Delivery-first choices push business logic into handlers.
- Blocking IO (CSV/files) inside reactive paths reduces throughput.
- Missing scale/QPS budgets hide risks until late.

### Solutions by scale
- Lists/stats: small data can scan; medium needs server filters or index tables; large uses pre-aggregation or read models.
- Counters: low concurrency allow read-modify-write; medium use optimistic lock; high use atomic or event-driven updates.
- Import/export: small files use boundedElastic; large files use async jobs + streaming.
- Endpoint hygiene: move shared logic to use-cases/assemblers.

### Design-time prevention
- Define data scale/QPS targets and document limits.
- Default to server-side filtering; avoid full scans by default.
- Pick one counter strategy upfront.
- Isolate blocking IO to dedicated threads or async jobs.
- Minimum tests: auth, idempotency, state transitions, import/export.

## Verification and Release
- Usage and verification: `verification.md`
- Versioning strategy: `versioning.md`
- Release process: `release.md`

## Recommended Links
- Frontend rules: `../frontend.md`
- Backend rules: `../backend.md`
- Collaboration protocol: `../collaboration-protocol.md`
- Contract guidance: `contracts/README.md`
- Module map: `module-map.md`
- Human guide: `user-guide.md`
- 中文使用说明: `usage-zh.md`
- 发布流程（中文）: `release-zh.md`
- FAQ: `faq.md`
