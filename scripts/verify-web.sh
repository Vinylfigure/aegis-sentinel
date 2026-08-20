#!/usr/bin/env bash
# Frontend gate runner, safe from any cwd (ledger L-052: three conductor
# passes ran repo scripts from web/ inside mixed-directory compound commands
# and got exit 127 — this script self-anchors so the caller never cd's).
# Gates mirror .github/workflows/web-verify.yml plus the redaction sweep.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT/web"
npm ci
npm run codegen:check
npx tsc --noEmit
npm run build

cd "$ROOT"
bash scripts/check-redaction.sh
echo "verify-web: all gates green"
