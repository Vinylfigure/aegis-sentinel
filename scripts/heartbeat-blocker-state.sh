#!/usr/bin/env bash
# Fast-path fingerprint for the build-heartbeat's claim-check (issue #172).
#
# WHY. The heartbeat fires every 4h and re-derives the same answer — every
# EXECUTION-PLAN.md box ticked, the same blocked task: issues — dozens of
# times in a row (L-014/L-015: the discipline of re-checking before acting is
# right; the *mechanical cost* of re-deriving an unchanged answer is what
# repeated use now demonstrates needs a cheap gate on top).
#
# WHAT IT DOES NOT DO. It never talks to GitHub itself. A heartbeat session
# already reads issues/PRs through its own approved GitHub MCP tools (L-015:
# encode only the discipline the scaffold adds on top of what the platform
# already provides) — this script is a pure function over whatever JSON that
# session already fetched, mirroring the collectors' injected-transport
# discipline (`src/aegis_sentinel/collectors/`) applied to shell. It decides
# nothing about which issues count as blockers beyond "open task:/question:
# labeled" (below); it never trims that set by staleness or content.
#
# USAGE
#   heartbeat-blocker-state.sh fingerprint <issues.json> <prs.json>
#   heartbeat-blocker-state.sh check       <issues.json> <prs.json>
#   heartbeat-blocker-state.sh update      <issues.json> <prs.json>
#
# <issues.json> — a JSON array of open issues, each carrying at least
#   number, labels, updated_at, comments (count). labels may be plain
#   strings (the GitHub MCP tools' shape) or {"name": "..."} objects (the
#   raw GitHub REST/gh-CLI shape used elsewhere in this repo, e.g.
#   scripts/auto-merge.sh's ghj().labels[]?.name) — both are normalized
#   before matching. Only entries labeled task:/task/question:/question are
#   fingerprinted; everything else is ignored so unrelated issue traffic
#   never forces the full path.
# <prs.json> — a JSON array of open PRs, each carrying at least number,
#   mergeable_state, head sha, and CI conclusion. Every PR in the array
#   counts (the caller passes only the open ones).
#
# `check` prints "unchanged: ..." and exits 0 when the fingerprint matches
# the last `update`; prints "changed: ..." and exits 1 otherwise (including
# when no baseline has ever been recorded — no baseline is never permission
# to skip). `update` overwrites the baseline; the caller commits it.
set -uo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

STATE_FILE="${HEARTBEAT_STATE_FILE:-$ROOT/.claude/heartbeat-state.json}"

usage() {
  echo "usage: heartbeat-blocker-state.sh fingerprint|check|update <issues.json> <prs.json>" >&2
  exit 64
}

command -v jq >/dev/null 2>&1 || { echo "heartbeat-blocker-state: jq not found" >&2; exit 1; }

sha256() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum | cut -d' ' -f1
  elif command -v shasum >/dev/null 2>&1; then shasum -a 256 | cut -d' ' -f1
  else echo "heartbeat-blocker-state: no sha256sum/shasum available" >&2; exit 1
  fi
}

# Canonical, order-independent JSON for one input: filter (issues only),
# sort by number, sort object keys, compact — so re-fetching the same GitHub
# state in a different page order never reads as "changed". label_name
# normalizes both label shapes this repo's tooling actually produces
# (plain strings from the MCP tools; {"name": ...} objects from raw
# GitHub REST/gh-CLI) so a shape mismatch fails loudly (jq error, nonzero
# exit) rather than silently miscategorizing or crashing on a bare
# startswith() over a non-string.
canon_issues() {
  jq -Sc '
    def label_name: if type == "string" then . elif type == "object" then (.name // "") else (tostring) end;
    map(select(
      ((.labels // []) | map(label_name)) as $l
      | any($l[]; . == "task" or . == "task:" or . == "question" or . == "question:" or startswith("task:") or startswith("question:"))
    )) | sort_by(.number)
  ' "$1"
}
canon_prs() {
  jq -Sc 'sort_by(.number)' "$1"
}

# Computes the fingerprint or fails loudly. Never returns a blank/partial
# fingerprint on a jq error: canon_issues/canon_prs run in this same
# process (not a nested subshell) so a failure here reaches the caller's
# $? — but because the *caller* invokes this via `fp=$(fingerprint ...)`,
# a command substitution, callers MUST check $? themselves; a swallowed
# failure previously meant `update` could write an empty "" fingerprint to
# the git-tracked baseline while reporting success.
fingerprint() {
  local issues=$1 prs=$2 blob issues_canon prs_canon
  issues_canon=$(canon_issues "$issues") || return 1
  prs_canon=$(canon_prs "$prs") || return 1
  blob="$issues_canon"$'\n'"$prs_canon"
  printf '%s' "$blob" | sha256
}

[ $# -eq 3 ] || usage
CMD=$1; ISSUES=$2; PRS=$3
[ -f "$ISSUES" ] || { echo "heartbeat-blocker-state: no such file: $ISSUES" >&2; exit 1; }
[ -f "$PRS" ] || { echo "heartbeat-blocker-state: no such file: $PRS" >&2; exit 1; }

case "$CMD" in
  fingerprint)
    fp=$(fingerprint "$ISSUES" "$PRS")
    if [ $? -ne 0 ] || [ -z "$fp" ]; then
      echo "heartbeat-blocker-state: could not compute a fingerprint from $ISSUES / $PRS (malformed input?)" >&2
      exit 1
    fi
    echo "$fp"
    ;;
  check)
    fp=$(fingerprint "$ISSUES" "$PRS")
    if [ $? -ne 0 ] || [ -z "$fp" ]; then
      echo "heartbeat-blocker-state: could not compute a fingerprint from $ISSUES / $PRS (malformed input?)" >&2
      exit 1
    fi
    if [ ! -f "$STATE_FILE" ]; then
      echo "changed: no baseline recorded yet at $STATE_FILE"
      exit 1
    fi
    prev=$(jq -r '.fingerprint // empty' "$STATE_FILE" 2>/dev/null)
    if [ -z "$prev" ]; then
      echo "changed: baseline at $STATE_FILE is unreadable or missing a fingerprint field"
      exit 1
    fi
    if [ "$fp" = "$prev" ]; then
      recorded=$(jq -r '.updated_at_utc // "unknown time"' "$STATE_FILE" 2>/dev/null)
      echo "unchanged: blocker set matches the baseline recorded at ${recorded}"
      exit 0
    fi
    echo "changed: fingerprint differs from baseline (was ${prev:0:12}..., now ${fp:0:12}...)"
    exit 1
    ;;
  update)
    fp=$(fingerprint "$ISSUES" "$PRS")
    if [ $? -ne 0 ] || [ -z "$fp" ]; then
      echo "heartbeat-blocker-state: could not compute a fingerprint from $ISSUES / $PRS (malformed input?) — baseline left untouched" >&2
      exit 1
    fi
    tmp=$(mktemp)
    jq -n --arg fp "$fp" --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '{fingerprint: $fp, updated_at_utc: $ts}' >"$tmp"
    mv "$tmp" "$STATE_FILE"
    echo "recorded fingerprint ${fp:0:12}... at $STATE_FILE"
    ;;
  *)
    usage
    ;;
esac
