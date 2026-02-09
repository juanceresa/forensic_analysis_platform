#!/usr/bin/env bash

set -euo pipefail

echo "== Public Readiness Check =="

failures=0

pass() {
  echo "OK"
}

fail() {
  echo "FAIL"
  failures=$((failures + 1))
}

echo
echo "-- No private doc paths tracked"
if rg -q '^(\.claude/|\.claudes/|docs/plans/|docs/internal_docx/|docs/strategy/|docs/architecture/POSTURING\.md|docs/guides/(ADMIN_GUIDE|ANALYST_GUIDE)\.md)' < <(git ls-files); then
  fail
else
  pass
fi

echo
echo "-- No local case data tracked"
if rg -q '^cases/' < <(git ls-files); then
  fail
else
  pass
fi

echo
echo "-- No env files tracked"
if rg -q '(^|/)\.env(\.local)?$' < <(git ls-files); then
  fail
else
  pass
fi

echo
echo "-- No obvious credentials in tracked files"
if git grep -nE '(AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY)' -- . >/dev/null 2>&1; then
  fail
else
  pass
fi

echo
echo "-- Private paths not present in git history (basic check)"
if rg -q '^(\.claude/|\.claudes/|docs/plans/|docs/internal_docx/|docs/strategy/|docs/architecture/POSTURING\.md|docs/guides/(ADMIN_GUIDE|ANALYST_GUIDE)\.md)' < <(git log --all --name-only --pretty=format:); then
  fail
else
  pass
fi

echo
if [[ "$failures" -eq 0 ]]; then
  echo "PASS: repository looks ready for public exposure."
  exit 0
fi

echo "FAIL: $failures checks failed."
echo "Run history sanitize if needed:"
echo "  bash scripts/sanitize_history_for_public_release.sh --yes-i-know-this-rewrites-history"
exit 1
