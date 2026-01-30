# Core Context (Min)

## Goal
Build full-stack systems with high performance and security using clear boundaries and contract-first APIs.

## Must
- Use self-descriptive, unambiguous names (no vague terms like `author`).
- Avoid spaghetti code; use DTO/VO/Request/Response/Domain models.
- Enforce frontend-backend separation; REST/Finder APIs are contract-first.
- Prefer consistent error envelopes and versioned contracts.

## Should
- Keep business logic out of controllers; place in service/use-case layers.
- Ensure key paths have latency/error metrics (P95/P99).
- Use a single SCSS entry for global layout/themes; allow limited scoped styles.

## Avoid
- Mixing build tools on the same entry.
- Changing contracts without versioning or changelog updates.

## Checklist
- Naming clear and unambiguous?
- DTO/VO boundaries explicit?
- Contract updated before implementation?
- Performance/security requirements covered?
