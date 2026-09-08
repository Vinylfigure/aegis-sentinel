#!/usr/bin/env bash
# The ready step: a draft the merge engine would merge next is marked ready
# for review, so the engine can. Runs immediately before scripts/auto-merge.sh
# in the same firing.
#
# WHY. Every dispatched run opens its PR as a DRAFT first (L-097: the artifact
# that makes a run visible is created before the expensive part), and nothing
# in the fleet flipped it back — the engine skips drafts unconditionally, so a
# finished, green delivery sat as "draft" until a person noticed. Draft state
# had no exit that a machine could take.
#
# WHAT IT DOES NOT DO. It never decides eligibility of its own: the head-prefix
# allowlist is read from the `janus:merge-config` block of scripts/auto-merge.sh
# in this same checkout, so the flip and the merge cannot disagree about which
# heads are maintenance-grade. And draft state is still an operator hold when a
# session SAYS so — a PR carrying a recorded ask (`<!-- janus:ask:v1 -->`), a
# held-for-operator marker, or the engine's own "Action: held" comment stays a
# draft whatever its checks say (L-20260902-ready-after-verify: "ready" means
# verified, and the recorded ask is how a session withholds it).
#
# GATES, every one a HOLD on failure, never a flip:
#   - isDraft; base is the repository's default branch (a stacked PR is not);
#   - head prefix in ELIGIBLE_PREFIXES and not in FORBIDDEN_PREFIXES;
#   - no gating label on the PR;
#   - no CHANGES_REQUESTED review;
#   - mergeable == MERGEABLE (CONFLICTING and UNKNOWN both hold);
#   - no hold marker in the PR's comments, and not already acted on this head;
#   - the head commit is older than READY_QUIET_HOURS (default 2) — a run
#     still pushing, or a verifier still running on a fresh head, is left alone;
#   - every check green (`gh pr checks`, the engine's own parser).
#
# UNKNOWN IS NOT PERMISSION. Every read is tri-state, like the engine's: the
# payload, or a failure sentinel the gate turns into a reported skip. A read
# that cannot be completed is never "none exist".
#
# State lives in the PR's own lifecycle comment (MARKER + `Head: <sha>`), so a
# rerun on an unchanged head is a no-op and a new push is eligible again.
#
# --dry-run: one line per PR ("<num>\t<action>\t<reason>"), mutate nothing.
# Exit 0 after a complete pass (holds included); 1 when a RUN-LEVEL read failed
# (repo, default branch, open-PR list) — nothing was decided, and the workflow
# goes red so the outage is visible instead of reading as "nothing to do".
set -uo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1

command -v gh >/dev/null 2>&1 || { echo "ready-drafts: gh not found" >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "ready-drafts: jq not found" >&2; exit 1; }

MARKER='<!-- janus:ready-drafts:v1 -->'
GH_FAIL='__GH_FAIL__'
GATING_LABELS="question: loop:hold human-check: human-action: plan: intent: goal: machinery-change"
QUIET_HOURS="${READY_QUIET_HOURS:-2}"
case "$QUIET_HOURS" in ''|*[!0-9]*) echo "ready-drafts: READY_QUIET_HOURS must be a whole number of hours" >&2; exit 1 ;; esac

# --- eligibility comes from the engine, never from here -----------------------
ENGINE="${READY_DRAFTS_ENGINE:-$ROOT/scripts/auto-merge.sh}"
if [ ! -f "$ENGINE" ]; then echo "ready-drafts: $ENGINE not found — with no merge engine there is nothing to be eligible for" >&2; exit 1; fi
block=$(sed -n '/^# janus:merge-config:start/,/^# janus:merge-config:end/p' "$ENGINE")
ELIGIBLE_PREFIXES=$(printf '%s\n' "$block" | sed -n 's/^ELIGIBLE_PREFIXES="\([^"]*\)".*/\1/p' | head -1)
FORBIDDEN_PREFIXES=$(printf '%s\n' "$block" | sed -n 's/^FORBIDDEN_PREFIXES="\([^"]*\)".*/\1/p' | head -1)
if [ -z "$ELIGIBLE_PREFIXES" ]; then echo "ready-drafts: no ELIGIBLE_PREFIXES in the engine's janus:merge-config block" >&2; exit 1; fi

# --- tri-state reads ----------------------------------------------------------
ghj() {
  local errf out
  errf=$(mktemp)
  if out=$(gh "$@" 2>"$errf"); then
    rm -f "$errf"; printf '%s' "$out"; return 0
  fi
  printf '%s %s' "$GH_FAIL" "$(tr '\n' ' ' <"$errf" | head -c 240)"
  rm -f "$errf"; return 1
}
unreadable() { case "$1" in "$GH_FAIL"*|"") return 0 ;; esac; return 1; }
why() { printf '%s' "${1#"$GH_FAIL" }"; }
ghpages() {
  local raw joined
  raw=$(ghj api --paginate "$@") || { printf '%s' "$raw"; return 1; }
  joined=$(printf '%s' "$raw" | jq -sc 'add // []' 2>/dev/null) || { printf '%s shape: pages were not JSON arrays' "$GH_FAIL"; return 1; }
  printf '%s' "$joined"
}

CHECKS_WHY=""
checks_green() {
  local num=$1 out err nfail npend ntotal errfile
  CHECKS_WHY=""
  errfile=$(mktemp)
  out=$(gh pr checks "$num" 2>"$errfile" || true)
  err=$(tr '\n' ' ' <"$errfile" | head -c 240); rm -f "$errfile"
  if [ -z "$out" ]; then CHECKS_WHY="no checks visible to this token${err:+: $err}"; return 1; fi
  ntotal=$(printf '%s\n' "$out" | grep -c . || true)
  nfail=$(printf '%s\n' "$out" | awk -F'\t' '$2 == "fail"' | grep -c . || true)
  npend=$(printf '%s\n' "$out" | awk -F'\t' '$2 == "pending"' | grep -c . || true)
  if [ "${nfail:-0}" -gt 0 ]; then CHECKS_WHY="$nfail failing: $(printf '%s\n' "$out" | awk -F'\t' '$2 == "fail" {print $1}' | paste -sd, -)"; return 1; fi
  if [ "${npend:-0}" -gt 0 ]; then CHECKS_WHY="$npend pending: $(printf '%s\n' "$out" | awk -F'\t' '$2 == "pending" {print $1}' | paste -sd, -)"; return 1; fi
  if [ "${ntotal:-0}" -eq 0 ]; then CHECKS_WHY="no checks reported"; return 1; fi
  local odd
  odd=$(printf '%s\n' "$out" | awk -F'\t' '$2 != "pass" && $2 != "fail" && $2 != "pending" && $2 != "skipping" {print $1 "=" $2}' | head -3 | paste -sd, -)
  if [ -n "$odd" ]; then CHECKS_WHY="unrecognised check states: ${odd}"; return 1; fi
  return 0
}

# Seconds since the epoch for an ISO-8601 stamp; empty when neither GNU nor
# BSD date can parse it (the caller holds — a guessed age is a guessed flip).
epoch_of() {
  local iso=$1 s
  s=$(date -u -d "$iso" +%s 2>/dev/null) && { printf '%s' "$s"; return 0; }
  s=$(date -u -j -f '%Y-%m-%dT%H:%M:%SZ' "$iso" +%s 2>/dev/null) && { printf '%s' "$s"; return 0; }
  return 1
}

prefix_class() {
  local head=$1 p
  for p in $FORBIDDEN_PREFIXES; do case "$head" in "$p"*) echo forbidden; return ;; esac; done
  for p in $ELIGIBLE_PREFIXES; do case "$head" in "$p"*) echo eligible; return ;; esac; done
  echo unknown
}

# --- run-level reads ----------------------------------------------------------
REPO="${GITHUB_REPOSITORY:-}"
if [ -z "$REPO" ]; then
  repo_json=$(ghj repo view --json nameWithOwner)
  if unreadable "$repo_json"; then printf '*\tskip\tHOLD: could not resolve the repo (%s)\n' "$(why "$repo_json")"; exit 1; fi
  REPO=$(printf '%s' "$repo_json" | jq -r '.nameWithOwner // empty' 2>/dev/null)
  if [ -z "$REPO" ]; then printf '*\tskip\tHOLD: could not resolve the repo (no nameWithOwner in the reply)\n'; exit 1; fi
fi
default_json=$(ghj repo view --json defaultBranchRef)
if unreadable "$default_json"; then printf '*\tskip\tHOLD: could not read the default branch (%s)\n' "$(why "$default_json")"; exit 1; fi
DEFAULT_BRANCH=$(printf '%s' "$default_json" | jq -r '.defaultBranchRef.name // empty' 2>/dev/null)
if [ -z "$DEFAULT_BRANCH" ]; then printf '*\tskip\tHOLD: default branch unreadable (no defaultBranchRef in the reply)\n'; exit 1; fi

prs=$(ghj pr list --state open --limit 200 --json number,headRefName,baseRefName,isDraft,labels,mergeable,headRefOid,reviews,reviewDecision)
if unreadable "$prs"; then printf '*\tskip\tHOLD: could not list open PRs (%s)\n' "$(why "$prs")"; exit 1; fi
nprs=$(printf '%s' "$prs" | jq 'length' 2>/dev/null || echo bad)
if [ "$nprs" = "bad" ]; then printf '*\tskip\tHOLD: open-PR list was not JSON\n'; exit 1; fi
if [ "$nprs" -ge 200 ]; then printf '*\tskip\tHOLD: open-PR list hit the 200 cap; refusing to act on a truncated view\n'; exit 1; fi

REPORT=""
skip() { REPORT="${REPORT}$1\tskip\t$2\n"; }
now=$(date -u +%s)

# --- the pass -------------------------------------------------------------------
while read -r num; do
  [ -n "$num" ] || continue
  pr=$(printf '%s' "$prs" | jq -c ".[] | select(.number == $num)")
  draft=$(printf '%s' "$pr" | jq -r 'if has("isDraft") then (.isDraft|tostring) else "unknown" end')
  head=$(printf '%s' "$pr" | jq -r '.headRefName // ""')
  base=$(printf '%s' "$pr" | jq -r '.baseRefName // ""')
  sha=$(printf '%s' "$pr" | jq -r '.headRefOid // empty')
  labels=$(printf '%s' "$pr" | jq -r 'if has("labels") then ([.labels[]?.name] | join(",")) else "__missing__" end')
  mergeable=$(printf '%s' "$pr" | jq -r '.mergeable // "UNKNOWN"')
  rdecision=$(printf '%s' "$pr" | jq -r '.reviewDecision // ""')
  has_reviews=$(printf '%s' "$pr" | jq -r 'if (has("reviews") and (.reviews|type=="array")) then "yes" else "no" end')

  if [ "$draft" = "false" ]; then skip "$num" "not a draft"; continue; fi
  if [ "$draft" != "true" ]; then skip "$num" "HOLD: draft state unreadable"; continue; fi
  if [ -z "$sha" ]; then skip "$num" "HOLD: head SHA unreadable"; continue; fi
  if [ -z "$base" ]; then skip "$num" "HOLD: base branch unreadable"; continue; fi
  if [ "$base" != "$DEFAULT_BRANCH" ]; then skip "$num" "base is ${base}, not ${DEFAULT_BRANCH} — a stacked PR is its author's"; continue; fi
  case "$(prefix_class "$head")" in
    forbidden) skip "$num" "Intent/heartbeat-tier head prefix (${head})"; continue ;;
    unknown) skip "$num" "unknown head prefix (${head}) — not in the engine's maintenance allowlist"; continue ;;
  esac
  if [ "$labels" = "__missing__" ]; then skip "$num" "HOLD: labels unreadable"; continue; fi
  gate_hit=""
  for l in $GATING_LABELS; do case ",$labels," in *,"$l",*) gate_hit="$l"; break ;; esac; done
  if [ -n "$gate_hit" ]; then skip "$num" "PR carries gating label ${gate_hit}"; continue; fi
  if [ "$has_reviews" != "yes" ]; then skip "$num" "HOLD: reviews field unreadable"; continue; fi
  changes_requested=$(printf '%s' "$pr" | jq -r '[.reviews[]? | select(.state == "CHANGES_REQUESTED")] | length')
  if [ "${changes_requested:-0}" -gt 0 ] || [ "$rdecision" = "CHANGES_REQUESTED" ]; then skip "$num" "CHANGES_REQUESTED review pending"; continue; fi
  case "$mergeable" in
    MERGEABLE) ;;
    CONFLICTING) skip "$num" "branch conflicting with ${DEFAULT_BRANCH}"; continue ;;
    *) skip "$num" "mergeable state is ${mergeable} (GitHub still computing, or unreadable; retried next run)"; continue ;;
  esac

  comments=$(ghpages "repos/$REPO/issues/$num/comments?per_page=100")
  if unreadable "$comments"; then skip "$num" "HOLD: could not read PR comments ($(why "$comments"))"; continue; fi
  held=$(printf '%s' "$comments" | jq -r '
    [ .[] | .body // "" ] as $b
    | if any($b[]; contains("<!-- janus:ask:v1 -->")) then "a recorded ask (janus:ask:v1)"
      elif any($b[]; contains("<!-- overlord:held-for-operator:v1 -->")) then "a held-for-operator marker"
      elif any($b[]; contains("<!-- janus:automerge:v1 -->") and contains("Action: held")) then "the merge arm'"'"'s own hold"
      else "" end' 2>/dev/null)
  if [ -n "$held" ]; then skip "$num" "draft is held by ${held} — the operator's"; continue; fi
  if printf '%s' "$comments" | jq -e --arg m "$MARKER" --arg sha "$sha" \
      'any(.[]; (.body // "" | contains($m)) and (.body // "" | contains("Head: " + $sha)))' >/dev/null 2>&1; then
    skip "$num" "already marked ready for head ${sha}"; continue
  fi

  commit_json=$(ghj api "repos/$REPO/commits/$sha")
  if unreadable "$commit_json"; then skip "$num" "HOLD: could not read head commit ($(why "$commit_json"))"; continue; fi
  cdate=$(printf '%s' "$commit_json" | jq -r '.commit.committer.date // .commit.author.date // empty' 2>/dev/null)
  if [ -z "$cdate" ]; then skip "$num" "HOLD: head commit carries no date"; continue; fi
  cepoch=$(epoch_of "$cdate") || { skip "$num" "HOLD: could not parse head commit date (${cdate})"; continue; }
  age_h=$(( (now - cepoch) / 3600 ))
  if [ "$age_h" -lt "$QUIET_HOURS" ]; then skip "$num" "head is ${age_h}h old, younger than the ${QUIET_HOURS}h quiet window — still being worked"; continue; fi

  if ! checks_green "$num"; then skip "$num" "checks not all green (${CHECKS_WHY:-unknown})"; continue; fi

  if [ "$DRY" -eq 1 ]; then REPORT="${REPORT}${num}\tready\twould mark ready for review (head ${sha})\n"; continue; fi
  errf=$(mktemp)
  if gh pr ready "$num" >/dev/null 2>"$errf"; then
    rm -f "$errf"
    gh pr comment "$num" --body "$MARKER
Action: marked-ready
Head: $sha

Checks are green, the branch is not conflicting, the head has been quiet for ${QUIET_HOURS}h and no ask is recorded — marking ready for review so the merge arm can act. A session that wants this held records the ask." >/dev/null 2>&1
    REPORT="${REPORT}${num}\tready\tmarked ready for review (head ${sha})\n"
  else
    REPORT="${REPORT}${num}\tskip\tpr ready command failed ($(tr '\n' ' ' <"$errf" | head -c 160))\n"; rm -f "$errf"
  fi
done < <(printf '%s' "$prs" | jq -r '.[].number' 2>/dev/null)

printf '%b' "$REPORT"
exit 0
