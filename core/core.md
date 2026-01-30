# Core Context (Standard)

## Goal
Build evolvable, testable, and observable full-stack systems under high performance and security constraints.

## Must
- **Naming**: self-descriptive, no ambiguity. Use precise terms (e.g., `authorUsername`).
- **Boundaries**: DTO/VO/Request/Response/Domain models are mandatory.
- **Contracts**: contract-first APIs (OpenAPI/Proto). Versioning required.
- **Separation**: frontend and backend are decoupled; APIs are the only boundary.

## Should
- Controllers/handlers orchestrate only; business logic in services/use-cases.
- Unified error envelope and traceId in all external responses.
- Observability for key paths: metrics, logs, traces with P95/P99 targets.
- Use a single SCSS global entry for layout/themes; scoped only for local tweaks.
- Build tool choice per project (Rsbuild or Vite) with isolated entry/output.

## Avoid
- Cross-layer dependencies (Domain should not depend on infra/frameworks).
- Contract changes without changelog and compatibility notes.
- Repeating global tokens in component-scoped styles.

## Modules (link)
- Frontend rules: `frontend.md`
- Backend rules: `backend.md`
- Collaboration protocol: `collaboration-protocol.md`

## Checklist
- Names precise and consistent?
- Contract updated and reviewed?
- DTO/VO boundaries clear?
- Observability and security included?
