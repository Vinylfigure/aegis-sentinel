#!/usr/bin/env bash
# Fixture tests for the Janus scaffold plumbing: hook behavior plus
# name-level docs cross-references. This is what `verify.sh full` runs for
# the template repo itself, and what CI runs on every PR.
#
# Behavioral tests run against a sandbox copy of the repo (CLAUDE_PROJECT_DIR
# points at a temp dir), so they never touch the real memory files.
set -uo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
FAILS=0

pass() { echo "  ok: $1"; }
fail() { echo "  FAIL: $1" >&2; FAILS=$((FAILS + 1)); }

command -v jq >/dev/null 2>&1 || { echo "test-hooks.sh requires jq" >&2; exit 1; }

echo "== static checks =="
for f in "$ROOT"/.claude/hooks/*.sh "$ROOT"/scripts/*.sh; do
  if bash -n "$f" 2>/dev/null; then pass "bash -n $(basename "$f")"; else fail "bash -n $(basename "$f")"; fi
done
if jq . "$ROOT/.claude/settings.json" >/dev/null 2>&1; then pass "settings.json is valid JSON"; else fail "settings.json is valid JSON"; fi

echo "== frontmatter (skills + agents) =="
# The quick dispatcher's *) arm exits 0 for every .md, so nothing else in the
# repo would catch a malformed or misspelled frontmatter block. Field sets are
# claims about a moving target — /recalibrate re-verifies them against
# code.claude.com/docs/en/skills and the anthropics/skills spec.
SKILL_FIELDS=" name description when_to_use argument-hint arguments disable-model-invocation user-invocable allowed-tools disallowed-tools model effort context agent background hooks paths shell "
AGENT_FIELDS=" name description tools disallowedTools model permissionMode maxTurns skills mcpServers hooks memory background effort isolation color initialPrompt "
check_frontmatter() {
  local file=$1 allowed=$2 expect=$3 label=$4
  if [ "$(head -1 "$file")" != "---" ]; then fail "$label: no frontmatter opening ---"; return; fi
  local end; end=$(awk 'NR>1 && /^---[[:space:]]*$/{print NR; exit}' "$file")
  if [ -z "$end" ]; then fail "$label: unterminated frontmatter block"; return; fi
  # A stray `---` rule in the body would otherwise pose as the closer and turn
  # prose into "fields", so require the whole region to be frontmatter-shaped:
  # a key, an indented continuation, or a list item.
  local stray; stray=$(sed -n "2,$((end - 1))p" "$file" \
    | grep -vE '^[[:space:]]*$|^[[:space:]]|^-[[:space:]]|^[a-zA-Z][a-zA-Z0-9_-]*:' | head -1)
  if [ -n "$stray" ]; then fail "$label: unterminated frontmatter block (body text before closing ---: '${stray:0:40}')"; return; fi
  local bad=""
  while IFS= read -r key; do
    case "$allowed" in *" $key "*) ;; *) bad="$bad $key" ;; esac
  done < <(sed -n "2,$((end - 1))p" "$file" | grep -oE '^[a-zA-Z][a-zA-Z0-9_-]*:' | tr -d ':')
  if [ -n "$bad" ]; then fail "$label: unknown frontmatter field(s):$bad"; else pass "$label: frontmatter fields known"; fi
  local declared; declared=$(sed -n "2,$((end - 1))p" "$file" | sed -n 's/^name:[[:space:]]*//p' | tr -d '"'"'"' ')
  if [ -z "$declared" ] || [ "$declared" = "$expect" ]; then pass "$label: name matches path"; else fail "$label: name '$declared' != '$expect'"; fi
}
for d in "$ROOT"/.claude/skills/*/; do
  check_frontmatter "$d/SKILL.md" "$SKILL_FIELDS" "$(basename "$d")" "skill $(basename "$d")"
done
for f in "$ROOT"/.claude/agents/*.md; do
  check_frontmatter "$f" "$AGENT_FIELDS" "$(basename "$f" .md)" "agent $(basename "$f" .md)"
done

echo "== docs consistency (name-level) =="
# Keeps docs/ honest about the tree: names, paths, and counts only — semantic
# accuracy stays on SELF-IMPROVEMENT.md rule 1 and /recalibrate.
if [ ! -f "$ROOT/docs/ARCHITECTURE.md" ]; then
  echo "  skip: no docs/ARCHITECTURE.md (docs pruned — checks opt out)"
else
  for d in "$ROOT"/.claude/skills/*/; do
    name=$(basename "$d")
    if grep -q -- "/$name" "$ROOT/docs/USAGE.md"; then pass "skill /$name in USAGE.md"; else fail "skill /$name missing from docs/USAGE.md — add a trigger-table row"; fi
  done
  for f in "$ROOT"/.claude/hooks/*.sh; do
    b=$(basename "$f")
    if grep -q "$b" "$ROOT/docs/ARCHITECTURE.md"; then pass "hook $b in ARCHITECTURE.md"; else fail "hook $b missing from docs/ARCHITECTURE.md hook table"; fi
  done
  for f in "$ROOT"/.claude/agents/*.md; do
    a=$(basename "$f" .md)
    if grep -q "$a" "$ROOT/docs/ARCHITECTURE.md"; then pass "agent $a in ARCHITECTURE.md"; else fail "agent $a missing from docs/ARCHITECTURE.md"; fi
  done
  for t in $(grep -ohE '[A-Za-z0-9_.-]+\.sh' "$ROOT"/docs/*.md | sort -u); do
    if [ -f "$ROOT/scripts/$t" ] || [ -f "$ROOT/.claude/hooks/$t" ]; then pass "docs script ref $t exists"; else fail "docs reference $t but no such file in scripts/ or .claude/hooks/"; fi
  done
  # recalibrated-at is deliberately absent from this list: it is written only
  # by a completed /recalibrate run (L-020), so its absence is a valid state.
  for p in .github/workflows/verify.yml .claude/settings.json .claude/memory/LEARNINGS.md .claude/memory/sources-seen.md; do
    if [ -e "$ROOT/$p" ]; then pass "component-map path $p exists"; else fail "component-map path $p missing from tree"; fi
  done
  n=$(ls "$ROOT"/.claude/hooks/*.sh 2>/dev/null | wc -l | tr -d ' ')
  if grep -qE "hooks/ +$n shell hooks" "$ROOT/docs/ARCHITECTURE.md"; then pass "component-map hook count is $n"; else fail "component map hook count != $n (expected line matching 'hooks/ +$n shell hooks')"; fi
  n=$(ls -d "$ROOT"/.claude/skills/*/ 2>/dev/null | wc -l | tr -d ' ')
  if grep -qE "skills/ +$n skills" "$ROOT/docs/ARCHITECTURE.md"; then pass "component-map skill count is $n"; else fail "component map skill count != $n (expected line matching 'skills/ +$n skills')"; fi
  n=$(ls "$ROOT"/.claude/agents/*.md 2>/dev/null | wc -l | tr -d ' ')
  if grep -qE "agents/ +$n subagents" "$ROOT/docs/ARCHITECTURE.md"; then pass "component-map agent count is $n"; else fail "component map agent count != $n (expected line matching 'agents/ +$n subagents')"; fi
fi

echo "== sandbox setup =="
SANDBOX=$(mktemp -d)
trap 'rm -rf "$SANDBOX"' EXIT
mkdir -p "$SANDBOX/.claude" "$SANDBOX/scripts"
cp -r "$ROOT/.claude/hooks" "$SANDBOX/.claude/hooks"
cp -r "$ROOT/.claude/memory" "$SANDBOX/.claude/memory"
cp "$ROOT/CLAUDE.md" "$SANDBOX/CLAUDE.md"
rm -f "$SANDBOX/.claude/memory/.session-signals" "$SANDBOX/.claude/memory/.nudged-"*
printf '#!/usr/bin/env bash\nexit 0\n' > "$SANDBOX/scripts/verify.sh"
chmod +x "$SANDBOX/scripts/verify.sh"
export CLAUDE_PROJECT_DIR="$SANDBOX"
SIGNALS="$SANDBOX/.claude/memory/.session-signals"
pass "sandbox at $SANDBOX"

echo "== prompt-signal.sh =="
echo '{"prompt":"please add a login page"}' | "$SANDBOX/.claude/hooks/prompt-signal.sh"
[ ! -f "$SIGNALS" ] && pass "normal prompt logs nothing" || fail "normal prompt logs nothing"
echo '{"prompt":"no, that is wrong, undo that"}' | "$SANDBOX/.claude/hooks/prompt-signal.sh"
grep -q '^correction:' "$SIGNALS" 2>/dev/null && pass "correction prompt logs a signal" || fail "correction prompt logs a signal"
# Enriched signal: keyword and excerpt travel with the timestamp, so a later
# session can tell WHY it fired (a bare timestamp forced guessing — L-031).
line=$(grep '^correction:' "$SIGNALS" 2>/dev/null | tail -1)
printf '%s' "$line" | grep -qi ':no,:' && pass "correction signal carries matched keyword" || fail "correction signal carries matched keyword (got: $line)"
printf '%s' "$line" | grep -qi 'no, that is wrong' && pass "correction signal carries prompt excerpt" || fail "correction signal carries prompt excerpt (got: $line)"
rm -f "$SIGNALS"
long=$(printf 'wrong %.0s' $(seq 1 40))
echo "{\"prompt\":\"$long\"}" | "$SANDBOX/.claude/hooks/prompt-signal.sh"
line=$(grep '^correction:' "$SIGNALS" 2>/dev/null | tail -1)
[ -n "$line" ] && [ "${#line}" -le 130 ] && pass "excerpt truncated to a bounded line" || fail "excerpt truncated to a bounded line (len ${#line})"
[ "$(wc -l < "$SIGNALS")" -eq 1 ] && pass "multiline-safe: one signal = one line" || fail "multiline-safe: one signal = one line"

echo "== stop-reflect-nudge.sh =="
out=$(echo '{"session_id":"t1"}' | "$SANDBOX/.claude/hooks/stop-reflect-nudge.sh")
echo "$out" | jq -e '.decision == "block"' >/dev/null 2>&1 && pass "signals present -> block" || fail "signals present -> block (got: $out)"
[ -f "$SANDBOX/.claude/memory/.nudged-t1" ] && pass "nudge marker created" || fail "nudge marker created"
out=$(echo '{"session_id":"t1"}' | "$SANDBOX/.claude/hooks/stop-reflect-nudge.sh")
[ -z "$out" ] && pass "second stop same session -> silent (loop guard)" || fail "second stop same session -> silent (got: $out)"
rm -f "$SIGNALS" "$SANDBOX/.claude/memory/.nudged-t1"
out=$(echo '{"session_id":"t2"}' | "$SANDBOX/.claude/hooks/stop-reflect-nudge.sh")
[ -z "$out" ] && [ ! -f "$SANDBOX/.claude/memory/.nudged-t2" ] && pass "clean session -> silent, no marker" || fail "clean session -> silent, no marker"

echo "== post-edit-verify.sh =="
echo '{"tool_input":{"file_path":"'"$SANDBOX"'/src/app.py"}}' | "$SANDBOX/.claude/hooks/post-edit-verify.sh"
[ $? -eq 0 ] && pass "passing verify -> exit 0" || fail "passing verify -> exit 0"
printf '#!/usr/bin/env bash\n[ "$1" = quick ] && { echo "lint error: undefined name"; exit 1; }\nexit 0\n' > "$SANDBOX/scripts/verify.sh"
err=$(echo '{"tool_input":{"file_path":"'"$SANDBOX"'/src/app.py"}}' | "$SANDBOX/.claude/hooks/post-edit-verify.sh" 2>&1 >/dev/null)
rc=$?
[ $rc -eq 2 ] && pass "failing verify -> exit 2" || fail "failing verify -> exit 2 (got $rc)"
echo "$err" | grep -q "lint error" && pass "failure output reaches stderr" || fail "failure output reaches stderr"
grep -q '^verify-fail:' "$SIGNALS" 2>/dev/null && pass "failure logs a signal" || fail "failure logs a signal"
echo '{"tool_input":{"file_path":"'"$SANDBOX"'/.claude/memory/LEARNINGS.md"}}' | "$SANDBOX/.claude/hooks/post-edit-verify.sh"
[ $? -eq 0 ] && pass "memory files exempt from the loop" || fail "memory files exempt from the loop"
rm -f "$SIGNALS"

# L-052 escalation: doubled adjacent path segment = cwd drift (web/web/src/...).
printf '#!/usr/bin/env bash\nexit 0\n' > "$SANDBOX/scripts/verify.sh"
echo '{"tool_input":{"file_path":"'"$SANDBOX"'/web/src/app/page.tsx"}}' | "$SANDBOX/.claude/hooks/post-edit-verify.sh"
[ $? -eq 0 ] && pass "cwd-drift: normal path -> exit 0" || fail "cwd-drift: normal path -> exit 0"
echo '{"tool_input":{"file_path":"'"$SANDBOX"'/web/src/components/Ladder/Ladder.tsx"}}' | "$SANDBOX/.claude/hooks/post-edit-verify.sh"
[ $? -eq 0 ] && pass "cwd-drift: Dir/Dir.ext is not a doubled segment" || fail "cwd-drift: Dir/Dir.ext is not a doubled segment"
err=$(echo '{"tool_input":{"file_path":"'"$SANDBOX"'/web/web/src/app/page.tsx"}}' | "$SANDBOX/.claude/hooks/post-edit-verify.sh" 2>&1 >/dev/null)
rc=$?
[ $rc -eq 2 ] && pass "cwd-drift: doubled segment -> exit 2" || fail "cwd-drift: doubled segment -> exit 2 (got $rc)"
echo "$err" | grep -q "repeats a path segment" && pass "cwd-drift: message names the cause" || fail "cwd-drift: message names the cause"
echo '{"tool_input":{"file_path":"'"$SANDBOX"'/web/web/src/app/page.tsx"}}' | "$SANDBOX/.claude/hooks/post-edit-verify.sh" >/dev/null 2>&1
[ $? -eq 2 ] && pass "cwd-drift: repeat case still exit 2 (no latch)" || fail "cwd-drift: repeat case still exit 2 (no latch)"
grep -q '^verify-fail:' "$SIGNALS" 2>/dev/null && fail "cwd-drift must not log a verify-fail signal" || pass "cwd-drift must not log a verify-fail signal"
rm -f "$SIGNALS"

echo "== verify.sh dispatcher (template contract) =="
# Runs the REAL repo dispatcher (the sandbox copy is a stub). Asserts only
# what survives /bootstrap: the *.sh/*.json arms, the usage exit, and the
# sentinel markers. Never runs `full` here (recursion) or the *) fallback
# (bootstrap replaces it).
mkdir -p "$SANDBOX/fixtures"
printf '#!/usr/bin/env bash\nexit 0\n' > "$SANDBOX/fixtures/good.sh"
printf '#!/usr/bin/env bash\nif true; then\n' > "$SANDBOX/fixtures/bad.sh"
printf '{ "unterminated":\n' > "$SANDBOX/fixtures/bad.json"
# Repo-specific (aegis-sentinel): the *.yml quick arm exists because a work
# order once burned 50 turns unable to verify YAML (L-039) — keep it guarded.
printf 'name: fine\nbody:\n  - type: markdown\n' > "$SANDBOX/fixtures/good.yml"
printf 'name: broken\nbody:\n  - type: [unclosed\n' > "$SANDBOX/fixtures/bad.yml"
"$ROOT/scripts/verify.sh" quick "$SANDBOX/fixtures/good.sh" >/dev/null 2>&1 && pass "quick: valid .sh -> exit 0" || fail "quick: valid .sh -> exit 0"
"$ROOT/scripts/verify.sh" quick "$SANDBOX/fixtures/bad.sh" >/dev/null 2>&1 && fail "quick: broken .sh -> nonzero" || pass "quick: broken .sh -> nonzero"
"$ROOT/scripts/verify.sh" quick "$SANDBOX/fixtures/bad.json" >/dev/null 2>&1 && fail "quick: broken .json -> nonzero" || pass "quick: broken .json -> nonzero"
"$ROOT/scripts/verify.sh" quick "$SANDBOX/fixtures/good.yml" >/dev/null 2>&1 && pass "quick: valid .yml -> exit 0" || fail "quick: valid .yml -> exit 0"
"$ROOT/scripts/verify.sh" quick "$SANDBOX/fixtures/bad.yml" >/dev/null 2>&1 && fail "quick: broken .yml -> nonzero" || pass "quick: broken .yml -> nonzero"
"$ROOT/scripts/verify.sh" bogus >/dev/null 2>&1
rc=$?
[ "$rc" -eq 64 ] && pass "unknown mode -> exit 64" || fail "unknown mode -> exit 64 (got $rc)"
for m in quick:start quick:end full:start full:end; do
  grep -q "janus:bootstrap:$m" "$ROOT/scripts/verify.sh" && pass "sentinel janus:bootstrap:$m present" || fail "sentinel janus:bootstrap:$m present"
done

echo "== session-start.sh =="
# Seed controlled CLAUDE.md state (L-009): these fixtures must pass in bootstrapped
# children too, so never depend on the live repo's facts block.
printf '# Sandbox project\n\n- App stack: NOT BOOTSTRAPPED — run /bootstrap.\n' > "$SANDBOX/CLAUDE.md"
out=$(echo '{"source":"startup"}' | "$SANDBOX/.claude/hooks/session-start.sh")
echo "$out" | grep -q "bootstrap" && pass "un-bootstrapped repo -> bootstrap nudge" || fail "un-bootstrapped repo -> bootstrap nudge (got: $out)"
# Leftover signals: a session that died or skipped the Stop nudge must not lose its lessons.
printf 'correction:2026-01-01T00:00:00Z\nverify-fail:/tmp/x\n' > "$SIGNALS"
out=$(echo '{"source":"startup"}' | "$SANDBOX/.claude/hooks/session-start.sh")
echo "$out" | grep -q "unprocessed learning signal" && pass "leftover signals -> reflect nudge" || fail "leftover signals -> reflect nudge (got: $out)"
out=$(echo '{"source":"compact"}' | "$SANDBOX/.claude/hooks/session-start.sh")
echo "$out" | grep -q "unprocessed learning signal" && fail "compact -> no duplicate signals line (got: $out)" || pass "compact -> no duplicate signals line"
echo "$out" | grep -q "Learning signals pending: 2" && pass "compact line reports pending count" || fail "compact line reports pending count (got: $out)"
rm -f "$SIGNALS"
out=$(echo '{"source":"startup"}' | "$SANDBOX/.claude/hooks/session-start.sh")
echo "$out" | grep -q "unprocessed" && fail "no signals -> silent (got: $out)" || pass "no signals -> silent"
# Decouple ledger fixtures from the shipped ledger's real entries: truncate the
# sandbox copy to header + marker so the fixtures below control what exists.
awk '{print} /<!-- entries below this line -->/{exit}' "$SANDBOX/.claude/memory/LEARNINGS.md" > "$SANDBOX/.claude/memory/LEARNINGS.md.tmp" \
  && mv "$SANDBOX/.claude/memory/LEARNINGS.md.tmp" "$SANDBOX/.claude/memory/LEARNINGS.md"
out=$(echo '{"source":"startup"}' | "$SANDBOX/.claude/hooks/session-start.sh")
echo "$out" | grep -q "consider /evolve" && fail "clean ledger -> no memory line" || pass "clean ledger -> no memory line"
printf '\n## L-900 · 2026-01-01 · Fixture entry\n- Trigger: fixture\n- Rule: fixture rule\n- Scope: project\n- Evidence: 2\n- Status: candidate\n' >> "$SANDBOX/.claude/memory/LEARNINGS.md"
out=$(echo '{"source":"startup"}' | "$SANDBOX/.claude/hooks/session-start.sh")
echo "$out" | grep -q "1 with Evidence >= 2" && pass "ripe learning counted (spec text not miscounted)" || fail "ripe learning counted (got: $out)"
# Regression: multi-digit Evidence must count as ripe (numeric >=, not a [2-9] first-digit match).
awk '{print} /<!-- entries below this line -->/{exit}' "$SANDBOX/.claude/memory/LEARNINGS.md" > "$SANDBOX/.claude/memory/LEARNINGS.md.tmp" \
  && mv "$SANDBOX/.claude/memory/LEARNINGS.md.tmp" "$SANDBOX/.claude/memory/LEARNINGS.md"
printf '\n## L-901 · 2026-01-01 · Double-digit evidence fixture\n- Trigger: fixture\n- Rule: fixture rule\n- Scope: project\n- Evidence: 10\n- Status: candidate\n' >> "$SANDBOX/.claude/memory/LEARNINGS.md"
out=$(echo '{"source":"startup"}' | "$SANDBOX/.claude/hooks/session-start.sh")
echo "$out" | grep -q "1 candidate learnings, 1 with Evidence >= 2" && pass "Evidence: 10 counts as ripe" || fail "Evidence: 10 counts as ripe (got: $out)"
# Regression: a non-candidate entry's Evidence must not leak into the next entry
# (replicated children start with high-Evidence 'inherited' entries).
awk '{print} /<!-- entries below this line -->/{exit}' "$SANDBOX/.claude/memory/LEARNINGS.md" > "$SANDBOX/.claude/memory/LEARNINGS.md.tmp" \
  && mv "$SANDBOX/.claude/memory/LEARNINGS.md.tmp" "$SANDBOX/.claude/memory/LEARNINGS.md"
printf '\n## L-902 · 2026-01-01 · Inherited high-evidence fixture\n- Trigger: fixture\n- Rule: fixture rule\n- Scope: portable\n- Evidence: 3\n- Status: inherited\n\n## L-903 · 2026-01-01 · Fresh candidate fixture\n- Trigger: fixture\n- Rule: fixture rule\n- Scope: project\n- Evidence: 1\n- Status: candidate\n' >> "$SANDBOX/.claude/memory/LEARNINGS.md"
out=$(echo '{"source":"startup"}' | "$SANDBOX/.claude/hooks/session-start.sh")
echo "$out" | grep -q "consider /evolve" && fail "non-candidate Evidence must not leak to next entry (got: $out)" || pass "non-candidate Evidence must not leak to next entry"
out=$(echo '{"source":"compact"}' | "$SANDBOX/.claude/hooks/session-start.sh")
echo "$out" | grep -qi "compacted" && pass "compact source -> workspace-rescue line" || fail "compact source -> workspace-rescue line (got: $out)"

echo "== session-start.sh: build-plan continuation =="
mkdir -p "$SANDBOX/docs"
printf -- '- [x] **T-DONE** — finished\n- [ ] **T-NEXT** — first open task\n- [ ] **T-LATER** — second open task\n' > "$SANDBOX/docs/EXECUTION-PLAN.md"
out=$(echo '{"source":"startup"}' | "$SANDBOX/.claude/hooks/session-start.sh")
echo "$out" | grep -q "next unblocked task is T-NEXT" && pass "plan present -> first unticked task surfaced" || fail "plan present -> first unticked task surfaced (got: $out)"
printf -- '- [x] **T-DONE** — finished\n- [x] **T-NEXT** — also finished\n' > "$SANDBOX/docs/EXECUTION-PLAN.md"
out=$(echo '{"source":"startup"}' | "$SANDBOX/.claude/hooks/session-start.sh")
echo "$out" | grep -q "Build plan" && fail "all boxes ticked -> silent (got: $out)" || pass "all boxes ticked -> silent"
rm -f "$SANDBOX/docs/EXECUTION-PLAN.md"
out=$(echo '{"source":"startup"}' | "$SANDBOX/.claude/hooks/session-start.sh")
echo "$out" | grep -q "Build plan" && fail "no plan file -> silent (got: $out)" || pass "no plan file -> silent"

echo "== session-start.sh: recalibration staleness =="
STAMPF="$SANDBOX/.claude/memory/recalibrated-at"
# Bootstrapped sandbox: overwrite via printf (sed -i diverges BSD/GNU), restore via cp below.
printf '# Sandbox project\n\n- App stack: wired (fixture)\n' > "$SANDBOX/CLAUDE.md"
rm -f "$STAMPF"
out=$(echo '{"source":"startup"}' | "$SANDBOX/.claude/hooks/session-start.sh")
echo "$out" | grep -q "recalibrate" && pass "bootstrapped + no stamp -> stale nudge" || fail "bootstrapped + no stamp -> stale nudge (got: $out)"
date +%s > "$STAMPF"
out=$(echo '{"source":"startup"}' | "$SANDBOX/.claude/hooks/session-start.sh")
echo "$out" | grep -q "recalibrate" && fail "fresh stamp -> silent (got: $out)" || pass "fresh stamp -> silent"
echo 1750000000 > "$STAMPF"   # 2025-06-15: fixed past epoch, always >30d old — fixture never rots
out=$(echo '{"source":"startup"}' | "$SANDBOX/.claude/hooks/session-start.sh")
echo "$out" | grep -q "recalibrate" && pass "old stamp -> stale nudge" || fail "old stamp -> stale nudge (got: $out)"
printf 'not-a-number\n' > "$STAMPF"
out=$(echo '{"source":"startup"}' | "$SANDBOX/.claude/hooks/session-start.sh")
echo "$out" | grep -q "recalibrate" && pass "garbage stamp -> treated stale, no crash" || fail "garbage stamp -> treated stale (got: $out)"
printf '# Sandbox project\n\n- App stack: NOT BOOTSTRAPPED — run /bootstrap.\n' > "$SANDBOX/CLAUDE.md"
rm -f "$STAMPF"
out=$(echo '{"source":"startup"}' | "$SANDBOX/.claude/hooks/session-start.sh")
echo "$out" | grep -q "recalibrate" && fail "un-bootstrapped -> staleness gated off (got: $out)" || pass "un-bootstrapped -> staleness gated off"

echo "== merge-policy: the engine body pin (one body, byte-identical across repos) =="
# The engine body below the config sentinel is the fleet's, pinned by sha in
# docs/MERGE-POLICY.md. A local edit to it is drift, and drift is a red build
# here rather than a quiet divergence from the policy every arm reads (L-007).
am_sha() { if command -v sha256sum >/dev/null 2>&1; then sha256sum | cut -d' ' -f1; else shasum -a 256 | cut -d' ' -f1; fi; }
engine_sha=$(sed -n '/^# janus:merge-config:end/,$p' "$ROOT/scripts/auto-merge.sh" | am_sha)
pinned_sha=$(grep -oE '^Engine-sha256: [0-9a-f]{64}' "$ROOT/docs/MERGE-POLICY.md" | cut -d' ' -f2)
[ -n "$pinned_sha" ] && [ "$engine_sha" = "$pinned_sha" ] \
  && pass "merge-policy: Engine-sha256 in docs/MERGE-POLICY.md matches the engine body below the config sentinel" \
  || fail "merge-policy: Engine-sha256 drift — body is $engine_sha, docs/MERGE-POLICY.md pins '${pinned_sha:-none}' (bump the pin in the same PR; MERGE-POLICY.md is a boundary file, so the operator merges)"
grep -q '^Policy-version: 2$' "$ROOT/docs/MERGE-POLICY.md" && pass "merge-policy: Policy-version 2 declared" || fail "merge-policy: docs/MERGE-POLICY.md must declare 'Policy-version: 2'"
grep -q 'janus:merge-config:start' "$ROOT/scripts/auto-merge.sh" && grep -q 'janus:merge-config:end' "$ROOT/scripts/auto-merge.sh" && pass "merge-policy: config sentinels present" || fail "merge-policy: config sentinels missing from scripts/auto-merge.sh"
grep -q '^ELIGIBLE_PREFIXES="claude/ fix/"' "$ROOT/scripts/auto-merge.sh" && grep -q '^MERGE_METHOD="merge"' "$ROOT/scripts/auto-merge.sh" \
  && pass "merge-policy: this repo's config block is claude/ and fix/ heads, merge commits" \
  || fail "merge-policy: this repo's config block drifted from claude/ fix/ heads, merge commits (docs/MERGE-POLICY.md states it)"
! grep -qE "^ghj\(\) \{ gh .*\|\| echo '\[\]'" "$ROOT/scripts/auto-merge.sh" && pass "merge-policy: no read substitutes [] on failure" || fail "merge-policy: a read still substitutes [] on failure"
grep -q -- '--probe' "$ROOT/scripts/auto-merge.sh" && pass "merge-policy: the engine has a --probe canary" || fail "merge-policy: the engine must carry --probe (the workflow runs it unguarded)"

echo "== ready-drafts.sh (stubbed gh: a green, unheld, quiet draft is marked ready; everything else holds) =="
# The ready step reads its allowlist from an engine's config block, so the
# fixture ships its own block — the assertions must not drift with this repo's
# real ELIGIBLE_PREFIXES. Every gh shape the script asks for has a case; the
# mutating verbs record a count so idempotence and --dry-run are provable.
RD="$SANDBOX/ready-drafts"; mkdir -p "$RD/bin"
cat > "$RD/engine.sh" <<'EOF'
# janus:merge-config:start
MERGE_METHOD="merge"
ELIGIBLE_PREFIXES="task/ claude/"
FORBIDDEN_PREFIXES="intent/ heartbeat/"
# janus:merge-config:end
EOF
cat > "$RD/bin/gh" <<'EOF'
#!/usr/bin/env bash
args="$*"
pr() { printf '{"number":%s,"headRefName":"%s","baseRefName":"%s","isDraft":%s,"labels":[%s],"mergeable":"%s","headRefOid":"%s","reviews":[],"reviewDecision":""}' "$@"; }
case "$args" in
  *"repo view --json defaultBranchRef"*) echo '{"defaultBranchRef":{"name":"main"}}' ;;
  *"pr list --state open"*)
    if [ -n "${RD_LIST_FAILS:-}" ]; then echo "stub: list refused" >&2; exit 1; fi
    printf '[%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s]\n' \
      "$(pr 600 task/fix-y main true '' MERGEABLE old600)" \
      "$(pr 601 codex/x main true '' MERGEABLE old601)" \
      "$(pr 602 task/stacked task/fix-y true '' MERGEABLE old602)" \
      "$(pr 603 task/held main true '' MERGEABLE old603)" \
      "$(pr 604 task/young main true '' MERGEABLE young604)" \
      "$(pr 605 task/red main true '' MERGEABLE old605)" \
      "$(pr 606 task/blind main true '' MERGEABLE old606)" \
      "$(pr 607 task/asked main true '{"name":"question:"}' MERGEABLE old607)" \
      "$(pr 608 task/conflict main true '' CONFLICTING old608)" \
      "$(pr 609 intent/phase main true '' MERGEABLE old609)" \
      "$(pr 610 task/shipped main false '' MERGEABLE old610)" \
      "$(pr 611 task/acted main true '' MERGEABLE old611)" ;;
  *"issues/603/comments"*) echo '[{"body":"<!-- janus:ask:v1 -->\nAsk: Merge or send it back"}]' ;;
  *"issues/611/comments"*) echo '[{"body":"<!-- janus:ready-drafts:v1 -->\nAction: marked-ready\nHead: old611"}]' ;;
  *"issues/"*"/comments"*) echo '[]' ;;
  *"commits/young604"*) printf '{"commit":{"committer":{"date":"%s"}}}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" ;;
  *"commits/"*) echo '{"commit":{"committer":{"date":"2020-01-01T00:00:00Z"}}}' ;;
  *"pr checks 605"*) printf 'ci\tfail\t1m\thttps://example.invalid\n' ;;
  *"pr checks 606"*) : ;;
  *"pr checks"*) printf 'ci\tpass\t1m\thttps://example.invalid\n' ;;
  *"pr ready"*) if [ -n "${RD_MUST_NOT_WRITE:-}" ]; then echo "MUST NOT BE CALLED: $args" >&2; exit 1; fi; echo "$args" >> "$RD_LOG"; exit 0 ;;
  *"pr comment"*) if [ -n "${RD_MUST_NOT_WRITE:-}" ]; then echo "MUST NOT BE CALLED: $args" >&2; exit 1; fi; echo "$args" >> "$RD_LOG"; exit 0 ;;
  *) echo "stub: unexpected gh $args" >&2; exit 1 ;;
esac
EOF
chmod +x "$RD/bin/gh"
: > "$RD/log"
out=$(GITHUB_REPOSITORY=example/rd READY_DRAFTS_ENGINE="$RD/engine.sh" RD_LOG="$RD/log" PATH="$RD/bin:$PATH" bash "$ROOT/scripts/ready-drafts.sh"); rc=$?
[ "$rc" -eq 0 ] && pass "ready-drafts: complete pass exits 0" || fail "ready-drafts: complete pass exits 0 (got $rc: $out)"
echo "$out" | grep -qF "$(printf '600\tready\tmarked ready for review (head old600)')" && pass "ready-drafts: green, quiet, unheld eligible draft is marked ready" || fail "ready-drafts: green draft marked ready (got: $out)"
grep -q "^pr ready 600$" "$RD/log" && pass "ready-drafts: gh pr ready was called for the flipped PR" || fail "ready-drafts: gh pr ready called (log: $(cat "$RD/log"))"
grep -q "^pr comment 600 --body <!-- janus:ready-drafts:v1 -->" "$RD/log" && pass "ready-drafts: the flip leaves a lifecycle comment carrying the marker" || fail "ready-drafts: lifecycle comment posted (log: $(cat "$RD/log"))"
[ "$(grep -c '^pr ready' "$RD/log")" -eq 1 ] && pass "ready-drafts: exactly one PR was flipped" || fail "ready-drafts: exactly one PR flipped (log: $(cat "$RD/log"))"
echo "$out" | grep -qF "$(printf '601\tskip\tunknown head prefix (codex/x)')" && pass "ready-drafts: a prefix outside the engine's allowlist is never touched" || fail "ready-drafts: unknown prefix skipped (got: $out)"
echo "$out" | grep -qF "$(printf '602\tskip\tbase is task/fix-y, not main')" && pass "ready-drafts: a stacked PR (base != default branch) is skipped" || fail "ready-drafts: stacked PR skipped (got: $out)"
echo "$out" | grep -qF "$(printf '603\tskip\tdraft is held by a recorded ask (janus:ask:v1)')" && pass "ready-drafts: a draft carrying a recorded ask stays the operator's" || fail "ready-drafts: recorded ask holds (got: $out)"
echo "$out" | grep -qE "$(printf '604\tskip\thead is 0h old, younger than the 2h quiet window')" && pass "ready-drafts: a head inside the quiet window is left alone" || fail "ready-drafts: quiet window holds (got: $out)"
echo "$out" | grep -qF "$(printf '605\tskip\tchecks not all green (1 failing: ci)')" && pass "ready-drafts: a red check holds" || fail "ready-drafts: red check holds (got: $out)"
echo "$out" | grep -qF "$(printf '606\tskip\tchecks not all green (no checks visible to this token')" && pass "ready-drafts: unreadable checks hold — unknown is not permission" || fail "ready-drafts: unreadable checks hold (got: $out)"
echo "$out" | grep -qF "$(printf '607\tskip\tPR carries gating label question:')" && pass "ready-drafts: a gating label holds" || fail "ready-drafts: gating label holds (got: $out)"
echo "$out" | grep -qF "$(printf '608\tskip\tbranch conflicting with main')" && pass "ready-drafts: a conflicting branch holds" || fail "ready-drafts: conflicting holds (got: $out)"
echo "$out" | grep -qF "$(printf '609\tskip\tIntent/heartbeat-tier head prefix (intent/phase)')" && pass "ready-drafts: a forbidden prefix holds" || fail "ready-drafts: forbidden prefix holds (got: $out)"
echo "$out" | grep -qF "$(printf '610\tskip\tnot a draft')" && pass "ready-drafts: a non-draft is reported, not touched" || fail "ready-drafts: non-draft reported (got: $out)"
echo "$out" | grep -qF "$(printf '611\tskip\talready marked ready for head old611')" && pass "ready-drafts: once per head SHA — an acted head is a no-op" || fail "ready-drafts: idempotent per head (got: $out)"
: > "$RD/log"
out=$(GITHUB_REPOSITORY=example/rd READY_DRAFTS_ENGINE="$RD/engine.sh" RD_LOG="$RD/log" RD_MUST_NOT_WRITE=1 PATH="$RD/bin:$PATH" bash "$ROOT/scripts/ready-drafts.sh" --dry-run); rc=$?
[ "$rc" -eq 0 ] && echo "$out" | grep -qF "$(printf '600\tready\twould mark ready for review (head old600)')" && pass "ready-drafts: --dry-run previews the flip" || fail "ready-drafts: --dry-run previews the flip (rc $rc, got: $out)"
[ ! -s "$RD/log" ] && pass "ready-drafts: --dry-run calls neither pr ready nor pr comment" || fail "ready-drafts: --dry-run mutated (log: $(cat "$RD/log"))"
out=$(GITHUB_REPOSITORY=example/rd READY_DRAFTS_ENGINE="$RD/engine.sh" RD_LOG="$RD/log" RD_LIST_FAILS=1 PATH="$RD/bin:$PATH" bash "$ROOT/scripts/ready-drafts.sh"); rc=$?
[ "$rc" -eq 1 ] && echo "$out" | grep -qF "HOLD: could not list open PRs" && pass "ready-drafts: an unreadable PR list is a red run, never 'nothing to do'" || fail "ready-drafts: unreadable PR list -> exit 1 with reason (rc $rc, got: $out)"
out=$(GITHUB_REPOSITORY=example/rd READY_DRAFTS_ENGINE="$RD/no-such-engine.sh" PATH="$RD/bin:$PATH" bash "$ROOT/scripts/ready-drafts.sh" 2>&1); rc=$?
[ "$rc" -eq 1 ] && echo "$out" | grep -qF "nothing to be eligible for" && pass "ready-drafts: no engine, no allowlist, no flip" || fail "ready-drafts: missing engine refuses (rc $rc, got: $out)"
grep -q 'ready-drafts.sh' "$ROOT/.github/workflows/auto-merge.yml" && pass "auto-merge.yml runs the ready step" || fail "auto-merge.yml must run scripts/ready-drafts.sh before the engine"
awk '/ready-drafts.sh/{r=NR} /run: \.\/scripts\/auto-merge.sh$/{m=NR} END{exit !(r && m && r < m)}' "$ROOT/.github/workflows/auto-merge.yml" && pass "auto-merge.yml runs the ready step BEFORE the merge pass" || fail "auto-merge.yml: the ready step must precede the armed merge pass"

echo
if [ "$FAILS" -eq 0 ]; then
  echo "ALL SCAFFOLD TESTS PASSED"
  exit 0
else
  echo "$FAILS TEST(S) FAILED" >&2
  exit 1
fi
