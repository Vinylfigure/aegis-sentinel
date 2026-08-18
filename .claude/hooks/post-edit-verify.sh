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

# L-052 escalation: a written path that repeats an adjacent directory segment
# (web/web/src/...) is the signature of a relative path resolved from a
# drifted cwd. The run-side half of L-052 is carried by verify-web.sh
# self-anchoring; a self-anchoring script cannot anchor a heredoc path, so
# the write side needs its own check. Fires before verify so the stray file
# is reported even when it would otherwise lint clean.
rel=${file#"$DIR"/}
if printf '%s\n' "$rel" | awk -F/ '{for(i=2;i<=NF;i++) if($i==$(i-1)) exit 0; exit 1}'; then
  printf 'cwd-drift: %s repeats a path segment — a previous cd probably persisted. Delete the stray file and rewrite with an absolute path.\n' "$file" >&2
  exit 2
fi

if ! output=$("$VERIFY" quick "$file" 2>&1); then
  mkdir -p "$(dirname "$SIGNALS")"
  printf 'verify-fail:%s\n' "$file" >> "$SIGNALS"
  printf 'verify.sh quick failed for %s:\n%s\n' "$file" "$output" >&2
  exit 2
fi
exit 0
