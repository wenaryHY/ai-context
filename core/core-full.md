# Core Context (Full)

## Goal
Build full-stack systems that are evolvable, testable, observable, and secure under high performance constraints.

## Mandatory Rules
- **Naming**: self-descriptive, unambiguous, consistent vocabulary.
- **Boundaries**: DTO/VO/Request/Response/Domain models required.
- **Contracts**: OpenAPI/Proto are the single source of truth.
- **Separation**: frontend and backend only communicate via contracts.
- **Security**: least privilege, encryption in transit/at rest, audit logs.
- **Performance**: SLOs with P95/P99 targets, fallback/timeout/limit.

## Architecture Practices
- Dependency direction: outer -> inner; Domain is framework-agnostic.
- Controllers/handlers orchestrate; services/use-cases hold business logic.
- Prefer event-driven or CQRS when complexity demands.

## Contract Discipline
- OpenAPI: versioned endpoints, unified error envelope, pagination consistency.
- Proto: versioned package/service, append-only fields, no breaking changes.
- Maintain changelog for any contract change.

## Frontend Rules (summary)
- Single SCSS entry for global layout/themes.
- Limited scoped styles for local adjustments only.
- Vue-first components; Lit + Shadow DOM uses isolated stylesheet output.
- Rsbuild/Vite selection per project with isolated entry/output.

## Backend Rules (summary)
- Spring Boot and Go+Rust are separate project types.
- Internal services prefer gRPC; external APIs prefer REST/Finder.
- Standardized error mapping and traceId propagation.

## Reliability and Observability
- Metrics/logs/traces are mandatory for critical paths.
- Error budgets and rollback strategies required for high-risk changes.

## Collaboration and Change Control
- Contract-first workflow and PR-based merges only.
- Avoid multi-AI conflicts by module boundaries and small PRs.

## Related Docs
- Frontend: `../frontend.md`
- Backend: `../backend.md`
- Collaboration: `../collaboration-protocol.md`
- Contracts: `../docs/contracts/README.md`
