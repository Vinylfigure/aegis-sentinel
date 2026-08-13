#!/usr/bin/env bash
# Per-file verdict-path purity gate (INFRA01). Thin wrapper over
# tests/purity_single.py: exits nonzero with a named violation when the
# file imports an LLM client anywhere in the verdict path, or breaks the
# D-P3 determinism bans in evaluate/ or compile/. Wired into the
# verify.sh quick *.py arm so the PostToolUse hook blocks impure edits
# locally; CI blocks them via verify.sh full (pytest runs the roster).
set -uo pipefail

if [ $# -ne 1 ]; then
  echo "usage: check-purity.sh <file.py>" >&2
  exit 64
fi

ROOT=$(cd "$(dirname "$0")/.." && pwd)
exec python3 "$ROOT/tests/purity_single.py" "$1"
