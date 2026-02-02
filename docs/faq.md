# FAQ and Troubleshooting

## Why does CI fail?
- Run `python3 scripts/validate-context.py` to find missing or empty files.
- Run `python3 scripts/sync-core.py --check` to verify tiers are in sync.

## How do I update rules safely?
1. Edit `core/core-full.md` only.
2. Run `python3 scripts/sync-core.py`.
3. Run `python3 scripts/validate-context.py`.

## I updated contracts. What next?
- Update `templates/contracts/CHANGELOG.md`.
- Ensure OpenAPI/Proto changes are backward compatible or versioned.

## My prompt feels too long. What should I do?
- Use `core/core-min.md` plus only one module doc.
- Avoid loading both frontend and backend rules in the same prompt.

## The model misses global context in large projects. What can I do?
- Use layered context: core + one module + task brief (scope/boundaries).
- Rely on retrieval (search/RAG) instead of loading everything.
- Split work into stages: analyze -> edit -> verify.
- Enforce guardrails: contract and consistency checklists.
- Assign a reviewer agent for cross-module checks.
- See templates: `examples/prompts/task-brief.md`, `examples/prompts/analyze-edit-verify.md`.

## Why does validation fail with "task brief enforcement"?
- Any change requires updating `docs/task-briefs/latest.md`.
- Validation also requires a git checkout with `git` available.
- Run `python3 scripts/archive-task-brief.py` to satisfy the archive check.
- Use `python3 scripts/start-task-brief.py --archive-current` to create a new brief.

## How do I generate a module map draft?
- Run `python3 scripts/generate-module-map.py --project-root /path/to/project`.

## What are common architecture pitfalls and how do I avoid them?
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
