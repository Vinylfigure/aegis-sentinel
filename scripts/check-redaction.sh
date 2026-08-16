#!/usr/bin/env bash
# Redaction gate: the repo must contain zero client-name or personal-name
# occurrences (Owner directive, 2026-08-12; see docs/DECISIONS.md D-R1).
# Patterns are stored base64-encoded so this script does not itself trip the gate.
set -uo pipefail
cd "$(dirname "$0")/.."

EXCLUDES=(--exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.next
          --exclude-dir=.vercel --exclude-dir=.venv --exclude-dir=__pycache__)

FAIL=0

# Substring patterns (client name; surname; personal email local-part).
for b64 in "Y2hhaW5saW5r" "bHlvbg==" "bWFnaWMuam9l"; do
  pat="$(printf '%s' "$b64" | base64 -d)"
  if grep -rniI "${EXCLUDES[@]}" -e "$pat" .; then
    echo "redaction gate: found forbidden pattern (${b64})" >&2
    FAIL=1
  fi
done

# First name checked with word boundaries to avoid false positives.
first="$(printf '%s' "bWlrZQ==" | base64 -d)"
if grep -rniIw "${EXCLUDES[@]}" -e "$first" .; then
  echo "redaction gate: found forbidden first name" >&2
  FAIL=1
fi

exit "$FAIL"
