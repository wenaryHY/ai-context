# Task Briefs

## Purpose
Keep a running record of task briefs for auditability and context continuity.

## Files
- `latest.md`: required and updated on every change.
- `archive/`: immutable history of task briefs.

## Workflow
1. Edit `latest.md` before making changes.
2. Run `python3 scripts/archive-task-brief.py` to archive it.
3. Run `python3 scripts/validate-context.py` to verify.

## Helpers
- Start a new brief: `python3 scripts/start-task-brief.py --archive-current`
- Archive latest: `python3 scripts/archive-task-brief.py`

## Archive Layout
- Default: `archive/<branch>/<title>/<timestamp>.md`
- Flat mode: `python3 scripts/archive-task-brief.py --flat`
- Disable branch folder: `python3 scripts/archive-task-brief.py --no-branch`
- Disable title folder: `python3 scripts/archive-task-brief.py --no-title`

## Rules
- `latest.md` must include all required fields.
- Any change requires updating `latest.md`.
- `archive/` must contain a copy of the latest brief.
