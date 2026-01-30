# Human Usage Guide

## Who This Is For
This guide is for humans who maintain and use the AI context repository.

## Daily Workflow
1. Pick the smallest core tier that fits the task.
2. Load only one module doc (`frontend.md` or `backend.md`).
3. Add contract guidance only when APIs change.

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
