#!/usr/bin/env bash

set -euo pipefail

# Rewrites git history to remove known private/internal paths before making the
# repository public. This is a destructive operation that requires force-push.

if [[ "${1:-}" != "--yes-i-know-this-rewrites-history" ]]; then
  echo "Refusing to run without explicit confirmation."
  echo
  echo "Run:"
  echo "  $0 --yes-i-know-this-rewrites-history"
  exit 1
fi

if ! command -v git-filter-repo >/dev/null 2>&1; then
  echo "git-filter-repo is required."
  echo "Install:"
  echo "  brew install git-filter-repo"
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree is not clean. Commit/stash changes first."
  exit 1
fi

backup_tag="pre-public-sanitize-$(date +%Y%m%d%H%M%S)"
git tag "$backup_tag"
echo "Created safety tag: $backup_tag"

git filter-repo --force \
  --invert-paths \
  --path .claude \
  --path .claudes \
  --path docs/plans \
  --path docs/internal_docx \
  --path docs/architecture/POSTURING.md \
  --path docs/strategy \
  --path docs/guides/ADMIN_GUIDE.md \
  --path docs/guides/ANALYST_GUIDE.md \
  --path .env \
  --path .env.local \
  --path farmer_vault/.env.local

cat <<'EOF'
History rewrite complete.

Next steps:
1. Re-run public readiness checks:
   bash scripts/check_public_readiness.sh

2. Force-push rewritten refs:
   git push --force-with-lease origin --all
   git push --force-with-lease origin --tags

3. If needed, recover from backup tag:
   git checkout <pre-public-sanitize-...>
EOF
