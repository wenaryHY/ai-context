# Task Brief (Latest)

## Context to Load
- `core/core.md`
- `backend.md`
- `docs/module-map.md`

## Scope
- In-scope: Add project infrastructure files (LICENSE, CHANGELOG, CONTRIBUTING, .editorconfig, .gitignore), enhance README, add new AI adapters (ChatGPT, Copilot, Gemini), add architecture solutions document, update validation script.
- Out-of-scope: No runtime code changes, no contract changes.
- Do-not-touch: Core rules content (core-full.md), existing adapter content.
- Dependencies: `scripts/validate-context.py` (updated to include new files), `README.md` (enhanced).

## Acceptance
- Behavior: All new files pass validation; project has proper open-source infrastructure.
- Non-functional: No breaking changes to existing functionality.
- Tests/verification: `python3 scripts/validate-context.py` passes with new files in REQUIRED_FILES list.

## Notes
- Key files: LICENSE, CHANGELOG.md, CONTRIBUTING.md, .editorconfig, .gitignore, README.md, adapters/*.md, backend-architecture-review/solutions.md.
- Risks/assumptions: Users may need to update their forks to include new required files.
