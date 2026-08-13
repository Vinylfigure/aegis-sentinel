#!/usr/bin/env bash
# Stack-agnostic verification dispatcher. /bootstrap fills in the real commands.
#
# Usage:
#   scripts/verify.sh quick [file]   # fast per-file check (<10s): format/lint/typecheck
#   scripts/verify.sh full           # the whole truth: tests + build (+ graph refresh)
#
# Contract:
# - `quick` is wired to the PostToolUse hook: it must be FAST and exit nonzero
#   with useful output on failure (the agent sees stderr and iterates).
# - `full` is the closed loop for /verify-loop and the verifier agent: exit 0
#   means the project is genuinely healthy.
# - Bootstrapped to Python (ruff + pytest): quick lints/format-checks the
#   changed file, full runs the scaffold fixture suite plus lint, format
#   check, and tests across the project.
set -uo pipefail

MODE="${1:-full}"
FILE="${2:-}"

case "$MODE" in
  quick)
    # janus:bootstrap:quick:start
    # Python (ruff lint + format check) per file; *.sh/*.json arms are the
    # template's own plumbing and stay wired for every child.
    case "$FILE" in
      *.sh) bash -n "$FILE" ;;
      *.json) if command -v jq >/dev/null 2>&1; then jq . "$FILE" >/dev/null; fi ;;
      *.py) ruff check "$FILE" && ruff format --check "$FILE" && "$(dirname "$0")/check-purity.sh" "$FILE" ;;
      # A dispatched agent's only shell grants are named runners like this
      # script, so a YAML file it writes is unverifiable unless the check
      # lives here. That gap cost a real run: the work order for the issue
      # template asked for a YAML parse, no allowlisted command could do
      # one, and the agent burned 50 turns on denials instead.
      *.yml|*.yaml) python3 -c 'import sys,yaml; yaml.safe_load(open(sys.argv[1]))' "$FILE" ;;
      *) exit 0 ;;
    esac
    # janus:bootstrap:quick:end
    ;;
  full)
    # janus:bootstrap:full:start
    # Scaffold plumbing fixtures, redaction gate, then the real Python
    # suite: lint, format check, tests.
    "$(dirname "$0")/test-hooks.sh" \
      && "$(dirname "$0")/check-redaction.sh" \
      && ruff check . \
      && ruff format --check . \
      && pytest
    # janus:bootstrap:full:end
    ;;
  *)
    echo "usage: verify.sh quick [file] | full" >&2
    exit 64
    ;;
esac
