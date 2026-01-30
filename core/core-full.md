# Core Context (Full)

<!-- Source of truth. Run scripts/sync-core.py to regenerate core.md and core-min.md. -->

<!-- tier:min:start -->
## Goal
Build full-stack systems that are evolvable, testable, observable, and secure under high performance constraints.

## Must
- **Naming**: self-descriptive, unambiguous, consistent vocabulary.
- **Boundaries**: DTO/VO/Request/Response/Domain models required.
- **Contracts**: OpenAPI/Proto are the single source of truth.
- **Separation**: frontend and backend only communicate via contracts.
- **Security**: least privilege, encryption in transit/at rest, audit logs.
- **Performance**: SLOs with P95/P99 targets, fallback/timeout/limit.

## Avoid
- Cross-layer dependencies (Domain should not depend on infra/frameworks).
- Contract changes without changelog and compatibility notes.
- Mixing build tools on the same entry/output.

## Checklist
- Names precise and consistent?
- Contract updated and reviewed?
- DTO/VO boundaries clear?
- Performance and security covered?
<!-- tier:min:end -->

<!-- tier:standard:start -->
## Should
- Controllers/handlers orchestrate only; business logic in services/use-cases.
- Unified error envelope and traceId in all external responses.
- Observability for key paths: metrics, logs, traces with P95/P99 targets.
- Use a single SCSS global entry for layout/themes; scoped only for local tweaks.
- Build tool choice per project (Rsbuild or Vite) with isolated entry/output.

## Modules (link)
- Frontend rules: `../frontend.md`
- Backend rules: `../backend.md`
- Collaboration protocol: `../collaboration-protocol.md`
<!-- tier:standard:end -->

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
