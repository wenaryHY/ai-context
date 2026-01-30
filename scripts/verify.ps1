$ErrorActionPreference = "Stop"

python3 scripts/sync-core.py --check
python3 scripts/validate-context.py

Write-Host "Verification passed."
