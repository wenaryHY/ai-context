# Claude Adapter

## Load Strategy
Keep the prompt short; attach only the minimum rules needed.

### Recommended Load Order
1) `core/core-min.md`
2) `frontend.md` or `backend.md`
3) `docs/contracts/README.md` if modifying contracts

## Prompt Starter
```
Use the rules from core/core-min.md and the relevant module doc.
Keep output structured and enforce contract-first changes.
```

## When to Use Larger Context
- Use `core/core.md` for multi-file refactors.
- Use `core/core-full.md` for architectural decisions.
