#!/usr/bin/env bash
set -euo pipefail

python3 scripts/sync-core.py --check
python3 scripts/validate-context.py
echo "Verification passed."
