param(
  [Parameter(Mandatory = $true)]
  [string]$Version
)

if ($Version -notmatch '^[0-9]+\.[0-9]+\.[0-9]+$') {
  Write-Error "Invalid version: $Version"
  exit 1
}

if (-not (git rev-parse --is-inside-work-tree 2>$null)) {
  Write-Error "Not a git repository."
  exit 1
}

if (git status --porcelain) {
  Write-Error "Working tree is not clean. Commit changes before releasing."
  exit 1
}

$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$tag = "v$Version"

git tag -a $tag -m "Release $tag ($timestamp)"
git push origin $tag

Write-Host "Released $tag at $timestamp"
