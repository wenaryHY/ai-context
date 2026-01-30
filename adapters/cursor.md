# Cursor Adapter

## How to Load Context
Use a minimal core file plus only the module you need.

### Recommended Load Order
1) `core/core-min.md` (or `core/core.md` for complex tasks)
2) `frontend.md` or `backend.md`
3) `collaboration-protocol.md` only when working with multiple AIs
4) `docs/contracts/README.md` for contract changes

## Suggested Prompt Prefix
Use this as the first message when starting a task:

```
Follow the rules in core/core-min.md and the relevant module docs.
If contracts change, update templates/contracts/CHANGELOG.md first.
```

## When to Use Each Tier
- `core-min.md`: small tasks, quick edits
- `core.md`: refactors, cross-module changes
- `core-full.md`: architecture or policy work

## Related Docs
- `frontend.md`
- `backend.md`
- `collaboration-protocol.md`
