#!/usr/bin/env bash
# PostToolUse hook (Edit|Write|MultiEdit): the inner verification loop.
# Runs the quick check on the edited file; on failure, exits 2 with the
# failure output on stderr so Claude sees it immediately and iterates.
# While un-bootstrapped, verify.sh quick only checks the scaffold's own
# *.sh/*.json plumbing, so the template stays quiet for app code.
set -uo pipefail

command -v jq >/dev/null 2>&1 || exit 0

DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
VERIFY="$DIR/scripts/verify.sh"
SIGNALS="$DIR/.claude/memory/.session-signals"

[ -x "$VERIFY" ] || exit 0

file=$(jq -r '.tool_input.file_path // empty' 2>/dev/null) || exit 0
[ -n "$file" ] || exit 0

# Never verify-loop on Janus's own memory/plumbing.
case "$file" in
  */.claude/memory/*|*/LEARNINGS.md) exit 0 ;;
esac

if ! output=$("$VERIFY" quick "$file" 2>&1); then
  mkdir -p "$(dirname "$SIGNALS")"
  printf 'verify-fail:%s\n' "$file" >> "$SIGNALS"
  printf 'verify.sh quick failed for %s:\n%s\n' "$file" "$output" >&2
  exit 2
fi
exit 0
