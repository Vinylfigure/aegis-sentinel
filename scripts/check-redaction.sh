#!/usr/bin/env bash
# Redaction gate: the repo must contain zero client-name or personal-name
# occurrences (Owner directive, 2026-08-12; see docs/DECISIONS.md D-R1).
# Patterns are stored base64-encoded so this script does not itself trip the gate.
set -uo pipefail
cd "$(dirname "$0")/.."

# Scan git-tracked files only (issue #183): `grep -r .` over the whole
# working tree needed a maintained --exclude-dir per untracked directory
# (build outputs, caches, a differently-named venv), and any name missing
# from that list got scanned like source — false-positiving on third-party
# dependency metadata. `git ls-files` excludes every untracked directory
# automatically, by construction, regardless of name.
scan() { git ls-files -z | xargs -0 -r grep -niI "$@" --; }

FAIL=0

# Substring patterns (client name; surname; personal email local-part).
for b64 in "Y2hhaW5saW5r" "bHlvbg==" "bWFnaWMuam9l"; do
  pat="$(printf '%s' "$b64" | base64 -d)"
  if scan -e "$pat"; then
    echo "redaction gate: found forbidden pattern (${b64})" >&2
    FAIL=1
  fi
done

# First name checked with word boundaries to avoid false positives.
first="$(printf '%s' "bWlrZQ==" | base64 -d)"
if scan -w -e "$first"; then
  echo "redaction gate: found forbidden first name" >&2
  FAIL=1
fi

exit "$FAIL"
