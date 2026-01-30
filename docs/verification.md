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

## CI Verification
Pull requests run:
- `scripts/validate-context.py`
- `scripts/sync-core.py --check`

Check GitHub Actions for pass/fail status.
