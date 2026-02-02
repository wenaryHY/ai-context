# Usage and Verification

## Quick Start
1. Pick a core tier:
   - `core/core-min.md` for small tasks
   - `core/core.md` for multi-file changes
   - `core/core-full.md` for architecture decisions
2. Load one module doc: `frontend.md` or `backend.md`.
3. Add `docs/contracts/README.md` only when contracts change.

## Local Verification
Run these before committing:

```bash
python3 scripts/sync-core.py --check
python3 scripts/validate-context.py
```

If `core/core-full.md` changed, regenerate tiers:

```bash
python3 scripts/sync-core.py
```

## Windows Verification
Use PowerShell or CMD:

```powershell
scripts\\verify.ps1
```

```bat
scripts\\verify.cmd
```

## CI Verification
Pull requests run:
- `scripts/validate-context.py`
- `scripts/sync-core.py --check`

Check GitHub Actions for pass/fail status.

## Task Brief Enforcement (Strict)
- Any change requires updating `docs/task-briefs/latest.md`.
- Validation fails if git is missing or the brief is not updated.
- Use `python3 scripts/archive-task-brief.py` to create the archive entry.
- Use `python3 scripts/start-task-brief.py --archive-current` to start a new brief.
- Module map generator: `python3 scripts/generate-module-map.py --project-root /path/to/project`.

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
