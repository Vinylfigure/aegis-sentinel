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

echo "== verify.sh dispatcher (template contract) =="
# Runs the REAL repo dispatcher (the sandbox copy is a stub). Asserts only
# what survives /bootstrap: the *.sh/*.json arms, the usage exit, and the
# sentinel markers. Never runs `full` here (recursion) or the *) fallback
# (bootstrap replaces it).
mkdir -p "$SANDBOX/fixtures"
printf '#!/usr/bin/env bash\nexit 0\n' > "$SANDBOX/fixtures/good.sh"
printf '#!/usr/bin/env bash\nif true; then\n' > "$SANDBOX/fixtures/bad.sh"
printf '{ "unterminated":\n' > "$SANDBOX/fixtures/bad.json"
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

echo
if [ "$FAILS" -eq 0 ]; then
  echo "ALL SCAFFOLD TESTS PASSED"
  exit 0
else
  echo "$FAILS TEST(S) FAILED" >&2
  exit 1
fi
