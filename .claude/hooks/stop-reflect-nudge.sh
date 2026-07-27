#!/usr/bin/env bash
# Stop hook: the session learning loop.
# If this session accumulated signals (corrections, verification failures),
# block the stop ONCE and ask for /reflect. Clean sessions end silently —
# no ceremony for routine work.
set -uo pipefail

command -v jq >/dev/null 2>&1 || exit 0

DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
SIGNALS="$DIR/.claude/memory/.session-signals"

input=$(cat)
session_id=$(printf '%s' "$input" | jq -r '.session_id // "unknown"')
GUARD="$DIR/.claude/memory/.nudged-$session_id"

# Once per session, by construction (docs don't guarantee stop_hook_active).
[ -f "$GUARD" ] && exit 0

# No signals -> clean session -> silent stop.
[ -s "$SIGNALS" ] || exit 0

corrections=$(grep -c '^correction:' "$SIGNALS" 2>/dev/null || true)
failures=$(grep -c '^verify-fail:' "$SIGNALS" 2>/dev/null || true)

mkdir -p "$(dirname "$GUARD")"
touch "$GUARD"

reason="This session logged ${failures:-0} verification failure(s) and ${corrections:-0} correction(s). Run /reflect to distill them into .claude/memory/LEARNINGS.md (or state in one line why there is no lesson), then stop."
jq -cn --arg r "$reason" '{decision: "block", reason: $r}'
exit 0
