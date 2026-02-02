# Human Usage Guide

## Who This Is For
This guide is for humans who maintain and use the AI context repository.

## Daily Workflow
1. Pick the smallest core tier that fits the task.
2. Load only one module doc (`frontend.md` or `backend.md`).
3. Add contract guidance only when APIs change.

## Large Project Context Strategy
### Symptoms
- The model edits a narrow slice and misses global impacts.
- Global constraints drift across long sessions.

### Remedies
- Layered context: core + one module + task brief.
- Retrieval-first: search/RAG for relevant slices.
- Staged workflow: analyze -> edit -> verify.
- Guardrails: enforce contract/naming/consistency checklists.
- Multi-agent roles: analyzer, editor, reviewer.

### Templates and Index
- Task brief: `../examples/prompts/task-brief.md`
- Staged workflow: `../examples/prompts/analyze-edit-verify.md`
- Module map: `module-map.md`
- Generate module map: `python3 scripts/generate-module-map.py --project-root /path/to/project`

### Enforcement (Strict)
- Any change must update `docs/task-briefs/latest.md`.
- Validation fails if git is unavailable or the brief is not updated.
- Archive the brief with `python3 scripts/archive-task-brief.py`.
- Start a new brief with `python3 scripts/start-task-brief.py --archive-current`.

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

## Edit Rules Safely
1. Edit `core/core-full.md` only.
2. Regenerate tiers:
   - `python3 scripts/sync-core.py`
3. Verify:
   - `python3 scripts/validate-context.py`

## When to Use Each File
- `core/core-min.md`: quick fixes, single file.
- `core/core.md`: refactors or multi-file tasks.
- `core/core-full.md`: architecture and policy work.

## Troubleshooting
- If CI fails, run `python3 scripts/validate-context.py`.
- If tiers are out of sync, run `python3 scripts/sync-core.py`.
