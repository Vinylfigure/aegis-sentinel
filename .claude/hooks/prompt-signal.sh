#!/usr/bin/env bash
# UserPromptSubmit hook: silent correction detector.
# If the user's prompt looks like a correction, log a signal for the Stop-hook
# nudge. Never blocks, never emits output — a false positive costs one line of
# "no lesson" later. Each signal carries the matched keyword and a short
# excerpt so a LATER session can tell why it fired: a bare timestamp forced
# the leftover-signals path to guess (L-031).
set -uo pipefail

command -v jq >/dev/null 2>&1 || exit 0

DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
SIGNALS="$DIR/.claude/memory/.session-signals"

prompt=$(jq -r '.prompt // empty' 2>/dev/null) || exit 0
[ -n "$prompt" ] || exit 0

# A background agent's own <task-notification> report arrives on this same
# prompt-submit channel and can contain ordinary review prose ("wrong",
# "undo that", ...) that trips the keyword regex below despite no human
# having typed anything (L-079, 7 recurrences 2026-08-26..2026-09-08). Such a
# report IS the whole prompt when it fires, so anchor to the start rather
# than matching the tag anywhere — a human correction that merely quotes or
# pastes a <task-notification> tag inside real corrective text must still log.
if printf '%s' "$prompt" | grep -qE '^[[:space:]]*<task-notification'; then
  exit 0
fi

PATTERN="(^|[^a-z])(no,|wrong|not what i|don'?t do|stop doing|you should have|that'?s incorrect|undo that)([^a-z]|$)"
if printf '%s' "$prompt" | grep -qiE "$PATTERN"; then
  # First matched keyword, lowercased; excerpt = first 60 chars, one line,
  # colons stripped so the field separators stay unambiguous.
  keyword=$(printf '%s' "$prompt" | grep -oiE "$PATTERN" | head -1 \
    | tr '[:upper:]' '[:lower:]' | tr -cd 'a-z, ' | sed 's/^ *//;s/ *$//')
  excerpt=$(printf '%s' "$prompt" | tr '\n\r\t:' '   ' | cut -c1-60)
  mkdir -p "$(dirname "$SIGNALS")"
  printf 'correction:%s:%s:%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${keyword:-match}" "$excerpt" >> "$SIGNALS"
fi
exit 0
