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
