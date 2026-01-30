# Release and Publishing

## Automatic Release (GitHub Actions)
1. Ensure working tree is clean.
2. Update required docs and changelogs:
   - `core/core-full.md` (if rules changed)
   - `templates/contracts/CHANGELOG.md` (if contracts changed)
3. Run verification:
   - `python3 scripts/sync-core.py --check`
   - `python3 scripts/validate-context.py`
4. Tag and push:
   - Linux/macOS: `./scripts/release.sh X.Y.Z`
   - Windows: `scripts\\release.cmd X.Y.Z` or `scripts\\release.ps1 X.Y.Z`

Pushing the tag triggers the GitHub Actions release workflow.

## Manual Release (Optional)
If you prefer manual releases, you can still:
1. Create a tag with timestamp in the message.
2. Push the tag to GitHub.
3. Create a release using GitHub UI.

The timestamp must come from the system command:

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"
```
