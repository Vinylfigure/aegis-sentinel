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
# dependency metadata. `git grep` searches tracked content natively, so
# untracked directories are excluded automatically regardless of name.
#
# Deliberately not `git ls-files -z | xargs -0 grep`: that pipeline has two
# sharp edges `git grep` doesn't. With zero tracked files, `xargs -r` exits 0
# without ever invoking grep, and the caller can't tell that "nothing to
# search" apart from grep's own 0 ("found a match") — flipping the gate to a
# false fail on an empty/pre-first-commit tree. And when one tracked path is
# a dangling symlink, batching every file into one grep argv makes GNU grep's
# file-open error override its match-found exit status even when a *real*
# hit was found and printed in the same run — silently defeating the gate.
# `git grep` never opens a symlink target (it reads the blob, i.e. the link
# text itself) and correctly reports "no match" on zero tracked files.
scan() { git grep -niI "$@"; }

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
