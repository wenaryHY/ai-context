# Context Usage Guide

## Choose the Right Tier
- **core-min.md**: quick edits, small tasks, single file changes.
- **core.md**: refactors, multi-file changes, cross-module tasks.
- **core-full.md**: architecture, policy, or system-wide decisions.

## Compose Modules (Minimal Set)
Always start with the smallest set that still covers the task:
1) Core tier (`core/core-min.md` or `core/core.md`)
2) One module doc (`frontend.md` or `backend.md`)
3) `docs/contracts/README.md` when changing APIs/contracts
4) `collaboration-protocol.md` when multiple AIs are working

## Avoid Overlong Prompts
- Do not attach both frontend and backend docs unless necessary.
- Avoid combining `core-full.md` with multiple module docs.
- Prefer contract templates over long prose when discussing APIs.

## Verification and Release
- Usage and verification: `verification.md`
- Versioning strategy: `versioning.md`
- Release process: `release.md`

## Recommended Links
- Frontend rules: `../frontend.md`
- Backend rules: `../backend.md`
- Collaboration protocol: `../collaboration-protocol.md`
- Contract guidance: `contracts/README.md`
- Human guide: `user-guide.md`
- 中文使用说明: `usage-zh.md`
- 发布流程（中文）: `release-zh.md`
- FAQ: `faq.md`
