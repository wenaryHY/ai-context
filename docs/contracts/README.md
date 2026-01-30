# Contract-First Guidelines

## Purpose
Contracts are the single source of truth for API behavior and data models. Always update the contract before changing implementations.

## When to Use Which Contract
- OpenAPI: HTTP/REST/Finder APIs exposed to frontend or external clients.
- Proto: gRPC/internal service communication and multi-language SDK generation.

## Versioning Rules
- OpenAPI: use path versioning (`/v1/...`) or header versioning, never both in one API.
- Proto: include version in `package` and `service` names (e.g., `example.v1`).
- Deprecation must be explicit and time-bounded (announce, support, remove).

## Compatibility Rules
- Allowed: add optional fields, add new endpoints/services, add new enum values (append only).
- Not allowed: rename fields, change field types/semantics, remove fields/endpoints.
- Breaking changes require a new version and a migration plan.

## Change Process
1. Update contract files (OpenAPI/Proto).
2. Update `templates/contracts/CHANGELOG.md`.
3. Regenerate clients/servers if applicable.
4. Implement changes and add tests.

## Review Checklist
- Is the contract updated and reviewed?
- Are error codes and pagination consistent?
- Is backward compatibility preserved?
- Does the changelog reflect the change?
