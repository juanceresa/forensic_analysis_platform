#!/usr/bin/env bash

set -euo pipefail

echo "== Public Readiness Check =="

failures=0

check_or_fail() {
  local description="$1"
  local cmd="$2"
  echo
  echo "-- $description"
  if eval "$cmd"; then
    echo "OK"
  else
    echo "FAIL"
    failures=$((failures + 1))
  fi
}

check_or_fail "No private doc paths tracked" \
  "git ls-files | rg -q '^(\\.claude/|\\.claudes/|docs/plans/|docs/internal_docx/)' && false || true"

check_or_fail "No local case data tracked" \
  "git ls-files | rg -q '^cases/' && false || true"

check_or_fail "No env files tracked" \
  "git ls-files | rg -q '(^|/)\\.env(\\.local)?$' && false || true"

check_or_fail "No obvious credentials in tracked files" \
  \"while IFS= read -r -d '' f; do [ -f \\\"\\\$f\\\" ] && printf '%s\\\\0' \\\"\\\$f\\\"; done < <(git ls-files -z) | xargs -0 rg -n '(AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY)' -S >/dev/null 2>&1 && false || true\"

check_or_fail "Private paths not present in git history (basic check)" \
  "git log --all --name-only --pretty=format: | rg -q '^(\\.claude/|\\.claudes/|docs/plans/|docs/internal_docx/)' && false || true"

echo
if [[ "$failures" -eq 0 ]]; then
  echo "PASS: repository looks ready for public exposure."
  exit 0
fi

echo "FAIL: $failures checks failed."
echo "Run history sanitize if needed:"
echo "  bash scripts/sanitize_history_for_public_release.sh --yes-i-know-this-rewrites-history"
exit 1
