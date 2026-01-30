# AI Context Toolkit

This repo provides layered, reusable context rules and templates for AI-assisted development.

## Quick Start
1. Pick a core tier:
   - `core/core-min.md` for small tasks
   - `core/core.md` for refactors
   - `core/core-full.md` for architecture work
2. Load one module doc: `frontend.md` or `backend.md`.
3. Use `docs/usage.md` for guidance and `examples/prompts/` for templates.

## Human Guides
- `docs/user-guide.md`
- `docs/usage-zh.md`
- `docs/release-zh.md`
- `docs/faq.md`

## Verify
```bash
python3 scripts/sync-core.py --check
python3 scripts/validate-context.py
```

## Release
```bash
./scripts/release.sh X.Y.Z
```

See `docs/release.md` and `docs/versioning.md` for details.
