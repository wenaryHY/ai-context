# Release and Publishing

## Automatic Release (GitHub Actions)
1. Ensure working tree is clean.
2. Update required docs and changelogs:
   - `core/core-full.md` (if rules changed)
   - `templates/contracts/CHANGELOG.md` (if contracts changed)
3. Run verification:
   - `python3 scripts/sync-core.py --check`
   - `python3 scripts/validate-context.py`
4. Tag and push:
   - Linux/macOS: `./scripts/release.sh X.Y.Z`
   - Windows: `scripts\\release.cmd X.Y.Z` or `scripts\\release.ps1 X.Y.Z`

Pushing the tag triggers the GitHub Actions release workflow.

## Manual Release (Optional)
If you prefer manual releases, you can still:
1. Create a tag with timestamp in the message.
2. Push the tag to GitHub.
3. Create a release using GitHub UI.

The timestamp must come from the system command:

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"
```

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
