#!/usr/bin/env bash
# The merge arm, per the locked merge boundary (docs/MERGE-POLICY.md,
# DL-2026-08-25-merge-boundary): maintenance-grade work builds and merges
# itself; Intent-tier decisions and operator-boundary files stay the operator's.
#
# ONE ENGINE, MANY REPOS. Everything below the `janus:merge-config:end`
# sentinel is the shared engine body; the block above it is this repo's
# configuration. Another repo's copy differs only in that block — its
# scripts/test-hooks.sh pins the sha256 of the body against the
# `Engine-sha256:` line in its docs/MERGE-POLICY.md, so a copy that drifts
# from the contract fails its own fixture suite (Policy-version 2).
#
# UNKNOWN IS NOT PERMISSION. Every read that feeds a gate is tri-state: the
# payload, or a failure sentinel that the gate turns into a HOLD with the
# reason on the report line. A read that cannot be completed never becomes
# "none exist" — that is exactly how the previous engine let a failed
# changed-file listing skip the boundary gate and a failed human-check listing
# read as "no human is looking" (audit 2026-09-02, overlord#275 D1/D2).
#
#   - Eligibility is by HEAD PREFIX (allowlist in the config block); `intent/`
#     and `heartbeat/` are never eligible; an unknown prefix is skipped loudly.
#   - A linked `Closes #N` issue must be open, not Intent-tier, and free of
#     gating labels; LINKED_ISSUE=required makes the link itself mandatory and
#     LINKED_ISSUE_KINDS names the title prefixes / labels that make it eligible.
#   - The PR's own labels gate too: `machinery-change` (a human decided this
#     needs a human — DL-2026-09-01-v2-build-merge), `question:`, `loop:hold`,
#     `human-check:`, `intent:`, `goal:`.
#   - A diff touching an operator-boundary file self-merges only when every
#     changed line is a positively-recognised tightening with nothing removed
#     (R1, MERGE-POLICY rule 2). The classifier reads ONE `gh pr diff` per PR
#     and slices the per-file hunk; an unreadable diff or hunk is operator-only.
#     The changed-file list comes from the paginated files API and must match
#     the PR's own `changedFiles` count, or the PR holds.
#   - Identity is NOT a signal: agent sessions push under the operator's login,
#     so an author allowlist cannot tell hand-typed from agent-opened. No
#     author gate exists (MERGE-POLICY.md, "identity is not a signal").
#   - `mergeStateStatus` BLOCKED / BEHIND / UNKNOWN and `reviewDecision`
#     REVIEW_REQUIRED hold: an engine merges, it never approves (L-116).
#   - The merge itself is pinned to the head SHA the gates read
#     (`--match-head-commit`): a push between read and act fails the merge,
#     never the gate.
#
# State lives in the PR's own lifecycle comments (MARKER): a rerun against an
# unchanged head SHA is a no-op; a new push is eligible again. Conflicting
# eligible PRs get one rebase-request comment per head SHA; PRs held on a
# policy verdict get one "Action: held" comment per head SHA (overlord-ui
# surfaces it). Holds caused by an unreadable read post NO comment — they are
# transient and already on the report line; a comment per outage would spam.
#
# Exit status: 0 after a complete pass (every PR has a report line, holds
# included); 1 when a RUN-LEVEL read failed (repo, open-PR list, human-check
# list, label set) — nothing was decided, and the workflow goes red so the
# outage is visible instead of reading as "nothing to do".
#
# --dry-run: print one line per PR ("<num>\t<action>\t<reason>"), mutate
# nothing. --probe: report whether this token can see checks at all (one line,
# exit 1 when it cannot) — the capability canary for the scope failure that
# blanked overlord-ui's arm for weeks. scripts/test-hooks.sh drives all three
# modes with a stubbed gh, including injected read failures.
set -uo pipefail

# janus:merge-config:start
MERGE_METHOD="merge"   # merge | squash — this repo's history is merge commits
ELIGIBLE_PREFIXES="claude/ fix/"   # 58 of 59 merged heads are claude/<issue>-<slug> or claude/<date>-heartbeat-reflect; reflect/ledger PRs self-merge by fleet policy
FORBIDDEN_PREFIXES="intent/ heartbeat/"
LINKED_ISSUE="optional"   # optional | required — dispatched PRs cite their task as Closes #N, heartbeat reflects close nothing
LINKED_ISSUE_KINDS=""     # when required: space-separated title prefixes / labels that make the linked issue eligible (e.g. "task: tier:auto")
REBASE_HINT="The next session or heartbeat firing that owns this branch should \`git fetch origin\`, merge \`main\` in, resolve the conflicts, and push; this arm will pick the PR up again on its next run."
# janus:merge-config:end

DRY=0; PROBE=0
case "${1:-}" in
  --dry-run) DRY=1 ;;
  --probe) PROBE=1 ;;
esac

command -v gh >/dev/null 2>&1 || { echo "auto-merge: gh not found" >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "auto-merge: jq not found" >&2; exit 1; }

MARKER='<!-- janus:automerge:v1 -->'
GH_FAIL='__GH_FAIL__'
GATING_LABELS="machinery-change question: loop:hold human-check: intent: goal:"

# --- tri-state reads ----------------------------------------------------------
# stdout is the payload on success. On failure stdout is "__GH_FAIL__ <stderr
# head>" and the return code is 1. No value is ever substituted for a failed
# read: the caller decides, and the decision is always HOLD.
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

# Paginated GET that concatenates the pages into one JSON array. Empty output
# or a page that is not an array is unreadable.
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
  # `gh pr checks` exits non-zero on failing/pending checks by design, so the
  # `|| true` is required here; the OUTPUT is what carries the states.
  out=$(gh pr checks "$num" 2>"$errfile" || true)
  err=$(tr '\n' ' ' <"$errfile" | head -c 240); rm -f "$errfile"
  if [ -z "$out" ]; then CHECKS_WHY="no checks visible to this token${err:+: $err}"; return 1; fi
  ntotal=$(printf '%s\n' "$out" | grep -c . || true)
  nfail=$(printf '%s\n' "$out" | awk -F'\t' '$2 == "fail"' | grep -c . || true)
  npend=$(printf '%s\n' "$out" | awk -F'\t' '$2 == "pending"' | grep -c . || true)
  if [ "${nfail:-0}" -gt 0 ]; then
    CHECKS_WHY="$nfail failing: $(printf '%s\n' "$out" | awk -F'\t' '$2 == "fail" {print $1}' | paste -sd, -)"; return 1
  fi
  if [ "${npend:-0}" -gt 0 ]; then
    CHECKS_WHY="$npend pending: $(printf '%s\n' "$out" | awk -F'\t' '$2 == "pending" {print $1}' | paste -sd, -)"; return 1
  fi
  if [ "${ntotal:-0}" -eq 0 ]; then CHECKS_WHY="no checks reported"; return 1; fi
  # Rows whose state column is none of pass/fail/pending/skipping mean the
  # output shape is not what this parser expects — say so, with a sample.
  local odd
  odd=$(printf '%s\n' "$out" | awk -F'\t' '$2 != "pass" && $2 != "fail" && $2 != "pending" && $2 != "skipping" {print $1 "=" $2}' | head -3 | paste -sd, -)
  if [ -n "$odd" ]; then CHECKS_WHY="unrecognised check states: ${odd} (raw: $(printf '%s' "$out" | head -c 160 | tr '\n\t' '| '))"; return 1; fi
  return 0
}

# --- repo identity + run-level reads -------------------------------------------
REPO="${GITHUB_REPOSITORY:-}"
if [ -z "$REPO" ]; then
  repo_json=$(ghj repo view --json nameWithOwner)
  if unreadable "$repo_json"; then printf '*\tskip\tHOLD: could not resolve the repo (%s)\n' "$(why "$repo_json")"; exit 1; fi
  REPO=$(printf '%s' "$repo_json" | jq -r '.nameWithOwner // empty' 2>/dev/null)
  if [ -z "$REPO" ]; then printf '*\tskip\tHOLD: could not resolve the repo (no nameWithOwner in the reply)\n'; exit 1; fi
fi

# --probe: can this token see checks at all? Reads the newest merged PR (one
# that certainly had checks) and reports what `gh pr checks` returns. The
# scope failure this catches (missing checks:/statuses:/actions: read) is
# otherwise indistinguishable from "every PR is red".
if [ "$PROBE" -eq 1 ]; then
  merged_json=$(ghj pr list --state merged --limit 1 --json number)
  if unreadable "$merged_json"; then printf 'probe\tHOLD\tcould not list merged PRs (%s)\n' "$(why "$merged_json")"; exit 1; fi
  last=$(printf '%s' "$merged_json" | jq -r '.[0].number // empty' 2>/dev/null)
  if [ -z "$last" ]; then printf 'probe\tHOLD\tno merged PR to probe against\n'; exit 1; fi
  if checks_green "$last"; then
    printf 'probe\tchecks-visible\tall green on #%s\n' "$last"; exit 0
  fi
  case "$CHECKS_WHY" in
    "no checks visible"*|"no checks reported"*) printf 'probe\tHOLD\t%s (on #%s)\n' "$CHECKS_WHY" "$last"; exit 1 ;;
    *) printf 'probe\tchecks-visible\t%s (on #%s)\n' "$CHECKS_WHY" "$last"; exit 0 ;;
  esac
fi

REPORT=""

# The label set: a gating label that does not exist in this repo makes that
# rule vacuous — say so once per run rather than silently never matching.
label_json=$(ghj label list --limit 300 --json name)
if unreadable "$label_json"; then printf '*\tskip\tHOLD: could not read the label set (%s)\n' "$(why "$label_json")"; exit 1; fi
for l in human-check: question: loop:hold machinery-change; do
  if ! printf '%s' "$label_json" | jq -e --arg l "$l" 'any(.[]; .name == $l)' >/dev/null 2>&1; then
    REPORT="${REPORT}*\tnote\tlabel ${l} absent in this repo — that gate is vacuous here\n"
  fi
done

# Open human-check: issues, ONCE per run, paginated. Unreadable holds every PR.
hc_json=$(ghpages "repos/$REPO/issues?labels=human-check%3A&state=open&per_page=100")
if unreadable "$hc_json"; then
  HC_UNREADABLE="$(why "$hc_json")"
else
  HC_UNREADABLE=""
fi

prs=$(ghj pr list --state open --limit 200 --json number,title,headRefName,body,isDraft,labels,author,reviewDecision,mergeStateStatus,changedFiles,headRefOid,mergeable,reviews)
if unreadable "$prs"; then printf '%b*\tskip\tHOLD: could not list open PRs (%s)\n' "$REPORT" "$(why "$prs")"; exit 1; fi
nprs=$(printf '%s' "$prs" | jq 'length' 2>/dev/null || echo bad)
if [ "$nprs" = "bad" ]; then printf '%b*\tskip\tHOLD: open-PR list was not JSON\n' "$REPORT"; exit 1; fi
if [ "$nprs" -ge 200 ]; then printf '%b*\tskip\tHOLD: open-PR list hit the 200 cap; refusing to act on a truncated view\n' "$REPORT"; exit 1; fi

# --- helpers over one PR --------------------------------------------------------
prefix_class() {
  local head=$1 p
  for p in $FORBIDDEN_PREFIXES; do case "$head" in "$p"*) echo forbidden; return ;; esac; done
  for p in $ELIGIBLE_PREFIXES; do case "$head" in "$p"*) echo eligible; return ;; esac; done
  echo unknown
}

# Echoes "eligible" or a skip/HOLD reason for a linked issue.
issue_eligibility() {
  local closes_num=$1 issue_json state title body labels tier_line is_intent k ok
  issue_json=$(ghj issue view "$closes_num" --json state,title,body,labels)
  if unreadable "$issue_json"; then echo "HOLD: could not read linked issue #$closes_num ($(why "$issue_json"))"; return; fi
  state=$(printf '%s' "$issue_json" | jq -r '.state // empty' 2>/dev/null)
  if [ -z "$state" ]; then echo "HOLD: linked issue #$closes_num has no readable state"; return; fi
  title=$(printf '%s' "$issue_json" | jq -r '.title // ""')
  body=$(printf '%s' "$issue_json" | jq -r '.body // ""')
  labels=$(printf '%s' "$issue_json" | jq -r '[.labels[]?.name] | join(",")')

  if [ "$state" != "OPEN" ]; then echo "linked issue #$closes_num is not open"; return; fi
  case ",$labels," in
    *,question:,*|*,loop:hold,*|*,human-check:,*|*,intent:,*|*,goal:,*)
      echo "linked issue #$closes_num carries a gating label"; return ;;
  esac
  is_intent=0
  case "$title" in "Intent Phase"*|"intent:"*) is_intent=1 ;; esac
  tier_line=$(printf '%s' "$body" | awk '/^### Review tier/{found=1;next} found && NF{print;exit}')
  case "$tier_line" in *Check*|*Digest*) is_intent=1 ;; esac
  if [ "$is_intent" -eq 1 ]; then echo "Intent-tier (issue #$closes_num)"; return; fi
  if [ -n "$LINKED_ISSUE_KINDS" ]; then
    ok=0
    for k in $LINKED_ISSUE_KINDS; do
      case "$title" in "$k"*) ok=1 ;; esac
      case ",$labels," in *,"$k",*) ok=1 ;; esac
    done
    if [ "$ok" -eq 0 ]; then echo "linked issue #$closes_num is not task-tier (needs one of: $LINKED_ISSUE_KINDS)"; return; fi
  fi
  echo "eligible"
}

BOUNDARY_PATTERN='^(CLAUDE\.md$|\.claude/rules/|\.claude/hooks/|\.claude/settings\.json$|\.github/workflows/|\.github/CODEOWNERS$|docs/MERGE-POLICY\.md$|scripts/test-hooks\.sh$|scripts/(auto-merge|preflight|channel-check|verify|wire-secret|check-[a-z-]+)\.sh$)'

# Classifies the diff on each touched boundary file as a positively-tightening
# change (self-merge candidate) or not (operator-only). Fails closed: the
# absence of a recognised widening pattern is not evidence of tightening —
# only a diff that is ENTIRELY additions of fixture/test/deny/guard lines (or
# comments/blank lines), with nothing removed and no grant/credential pattern
# added, verdicts "tightening-only". One unrecognised or removed line, or one
# widening pattern anywhere, verdicts operator-only for the whole PR.
WIDEN_PATTERN='Bash\(|allowedTools|"allow"|permissions:|secrets\.[A-Za-z_]|credential|apiKey|API_KEY|token:'
TIGHTEN_PATTERN='fixture|assert|deny|guard|test|check|threshold|protection'

file_hunk() {
  local full=$1 f=$2
  printf '%s\n' "$full" | awk -v f="$f" '/^diff --git /{p=($0 ~ (" b/" f "$"))} p'
}

# $1 = PR number, $2 = newline-separated boundary files (already listed once).
boundary_verdict() {
  local num=$1 files=$2 f fdiff added removed full
  full=$(ghj pr diff "$num")
  if unreadable "$full"; then echo "could not read the diff ($(why "$full")) — cannot classify, operator-only"; return; fi
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    fdiff=$(file_hunk "$full" "$f")
    if [ -z "$fdiff" ]; then echo "no readable diff for ${f} — cannot classify, operator-only"; return; fi
    added=$(printf '%s\n' "$fdiff" | grep -E '^\+' | grep -Ev '^\+\+\+' || true)
    removed=$(printf '%s\n' "$fdiff" | grep -E '^-' | grep -Ev '^---' || true)
    if [ -n "$added" ] && printf '%s\n' "$added" | grep -qE "$WIDEN_PATTERN"; then
      echo "widens a tool grant or credential reference (${f})"; return
    fi
    if [ -n "$removed" ] && printf '%s\n' "$removed" | grep -qvE '^-\s*(#.*)?$'; then
      echo "removes existing boundary-file content (${f})"; return
    fi
    if [ -n "$added" ] && printf '%s\n' "$added" | grep -qvE "^\+\s*(#.*)?\$|${TIGHTEN_PATTERN}"; then
      echo "adds content that isn't a recognised tightening pattern (${f})"; return
    fi
  done <<EOF2
$files
EOF2
  echo "tightening-only"
}

# 0 = acted on this head already, 1 = not acted, 2 = comments unreadable.
# A match needs BOTH the marker and the head line in one comment body, so a
# human quoting a SHA cannot forge "already acted".
ACTED_WHY=""
already_acted() {
  local num=$1 sha=$2 comments
  comments=$(ghpages "repos/$REPO/issues/$num/comments?per_page=100")
  if unreadable "$comments"; then ACTED_WHY="$(why "$comments")"; return 2; fi
  if printf '%s' "$comments" | jq -e --arg m "$MARKER" --arg sha "$sha" \
      'any(.[]; (.body // "" | contains($m)) and (.body // "" | contains("Head: " + $sha)))' >/dev/null 2>&1; then
    return 0
  fi
  return 1
}

# One "Action: held" lifecycle comment per head SHA for a POLICY hold. Never
# under --dry-run; never when the comment thread is unreadable (a write on an
# unknown state is the thing this engine exists to refuse).
post_held_comment() {
  local n=$1 s=$2 why=$3
  [ "$DRY" -eq 1 ] && return
  [ -n "$s" ] || return
  already_acted "$n" "$s"; case $? in 0|2) return ;; esac
  gh pr comment "$n" --body "$MARKER
Action: held
Reason: $why
Head: $s" >/dev/null 2>&1
}

# A policy hold: report + lifecycle comment. An unknown-read hold: report only.
hold_policy() { post_held_comment "$1" "$2" "$3"; REPORT="${REPORT}$1\tskip\tHOLD: $3\n"; }
hold_unknown() { REPORT="${REPORT}$1\tskip\tHOLD: $2\n"; }

# --- the pass ---------------------------------------------------------------------
while read -r num; do
  [ -n "$num" ] || continue
  pr=$(printf '%s' "$prs" | jq -c ".[] | select(.number == $num)")
  title=$(printf '%s' "$pr" | jq -r '.title // ""')
  head=$(printf '%s' "$pr" | jq -r '.headRefName // ""')
  body=$(printf '%s' "$pr" | jq -r '.body // ""')
  draft=$(printf '%s' "$pr" | jq -r 'if has("isDraft") then (.isDraft|tostring) else "unknown" end')
  sha=$(printf '%s' "$pr" | jq -r '.headRefOid // empty')
  labels=$(printf '%s' "$pr" | jq -r 'if has("labels") then ([.labels[]?.name] | join(",")) else "__missing__" end')
  mergeable=$(printf '%s' "$pr" | jq -r '.mergeable // "UNKNOWN"')
  mstate=$(printf '%s' "$pr" | jq -r '.mergeStateStatus // "UNKNOWN"')
  rdecision=$(printf '%s' "$pr" | jq -r '.reviewDecision // ""')
  changed=$(printf '%s' "$pr" | jq -r 'if has("changedFiles") then (.changedFiles|tostring) else "unknown" end')
  has_reviews=$(printf '%s' "$pr" | jq -r 'if (has("reviews") and (.reviews|type=="array")) then "yes" else "no" end')

  if [ -z "$sha" ]; then hold_unknown "$num" "head SHA unreadable"; continue; fi
  if [ "$draft" = "true" ]; then REPORT="${REPORT}${num}\tskip\tdraft\n"; continue; fi
  if [ "$draft" != "false" ]; then hold_unknown "$num" "draft state unreadable"; continue; fi
  if [ "$labels" = "__missing__" ]; then hold_unknown "$num" "labels unreadable"; continue; fi

  case "$(prefix_class "$head")" in
    forbidden)
      hold_policy "$num" "$sha" "Intent/heartbeat-tier head prefix (${head})"; continue ;;
    unknown)
      REPORT="${REPORT}${num}\tskip\tunknown head prefix (${head}) — not in the maintenance allowlist\n"; continue ;;
  esac

  # The PR's own labels: machinery-change means a human already decided this
  # needs a human; the rest are the same gates the linked issue carries.
  gate_hit=""
  for l in $GATING_LABELS; do case ",$labels," in *,"$l",*) gate_hit="$l"; break ;; esac; done
  if [ "$gate_hit" = "machinery-change" ]; then
    hold_policy "$num" "$sha" "machinery-change label — operator merges (MERGE-POLICY rule 2)"; continue
  elif [ -n "$gate_hit" ]; then
    hold_policy "$num" "$sha" "PR carries gating label ${gate_hit}"; continue
  fi

  closes_num=$(printf '%s' "$body" | grep -oE 'Closes #[0-9]+' | head -1 | grep -oE '[0-9]+' || true)
  if [ -n "$closes_num" ]; then
    reason=$(issue_eligibility "$closes_num")
    if [ "$reason" != "eligible" ]; then
      case "$reason" in HOLD:*) hold_unknown "$num" "${reason#HOLD: }" ;; *) REPORT="${REPORT}${num}\tskip\t${reason}\n" ;; esac
      continue
    fi
  elif [ "$LINKED_ISSUE" = "required" ]; then
    REPORT="${REPORT}${num}\tskip\tno Closes #N in body\n"; continue
  fi

  already_acted "$num" "$sha"; acted=$?
  if [ "$acted" -eq 2 ]; then hold_unknown "$num" "could not read PR comments; idempotency unprovable (${ACTED_WHY})"; continue; fi
  if [ "$acted" -eq 0 ]; then REPORT="${REPORT}${num}\tskip\talready acted on head ${sha}\n"; continue; fi

  # Changed files: the paginated list must agree with the PR's own count, or
  # the boundary gate would be judging a partial view.
  if [ "$changed" = "unknown" ]; then hold_unknown "$num" "changed-file count unreadable"; continue; fi
  files_json=$(ghpages "repos/$REPO/pulls/$num/files?per_page=100")
  if unreadable "$files_json"; then hold_unknown "$num" "could not list changed files ($(why "$files_json"))"; continue; fi
  files_all=$(printf '%s' "$files_json" | jq -r '.[].filename' 2>/dev/null)
  nfiles=$(printf '%s\n' "$files_all" | grep -c . || true)
  if [ "$changed" -eq 0 ]; then hold_unknown "$num" "PR reports zero changed files"; continue; fi
  if [ "$nfiles" -ne "$changed" ]; then hold_unknown "$num" "changed-file list incomplete (${nfiles} of ${changed})"; continue; fi

  bfiles_all=$(printf '%s\n' "$files_all" | grep -E "$BOUNDARY_PATTERN" || true)
  if [ -n "$bfiles_all" ]; then
    bfiles=$(printf '%s\n' "$bfiles_all" | head -3 | paste -sd, -)
    verdict=$(boundary_verdict "$num" "$bfiles_all")
    if [ "$verdict" != "tightening-only" ]; then
      hold_policy "$num" "$sha" "operator-boundary file in diff (${bfiles}): ${verdict}"; continue
    fi
    # tightening-only: falls through to the ordinary maintenance-grade gates below
  fi

  if [ "$has_reviews" != "yes" ]; then hold_unknown "$num" "reviews field unreadable"; continue; fi
  changes_requested=$(printf '%s' "$pr" | jq -r '[.reviews[]? | select(.state == "CHANGES_REQUESTED")] | length')
  if [ "${changes_requested:-0}" -gt 0 ] || [ "$rdecision" = "CHANGES_REQUESTED" ]; then
    REPORT="${REPORT}${num}\tskip\tCHANGES_REQUESTED review pending\n"; continue
  fi
  if [ "$rdecision" = "REVIEW_REQUIRED" ]; then
    hold_policy "$num" "$sha" "ruleset requires an approval — an engine never approves (L-116)"; continue
  fi

  if [ -n "$HC_UNREADABLE" ]; then hold_unknown "$num" "could not list open human-check: issues (${HC_UNREADABLE})"; continue; fi
  hc_hit=$(printf '%s' "$hc_json" | jq -r --arg n "$num" '[.[] | select(((.title // "") + " " + (.body // "")) | test("#" + $n + "([^0-9]|$)"))] | length')
  if [ "${hc_hit:-0}" -gt 0 ]; then REPORT="${REPORT}${num}\tskip\topen human-check issue references this PR\n"; continue; fi

  if [ "$mergeable" = "MERGEABLE" ]; then
    case "$mstate" in
      CLEAN|HAS_HOOKS|UNSTABLE) ;;
      *) hold_policy "$num" "$sha" "merge state ${mstate}"; continue ;;
    esac
    if ! checks_green "$num"; then
      REPORT="${REPORT}${num}\tskip\tchecks not all green (${CHECKS_WHY:-unknown})\n"; continue
    fi
    if [ "$DRY" -eq 1 ]; then
      REPORT="${REPORT}${num}\tmerge\twould ${MERGE_METHOD}-merge head ${sha}\n"; continue
    fi
    merge_args=(--delete-branch --match-head-commit "$sha")
    case "$MERGE_METHOD" in
      squash) merge_args+=(--squash --subject "$title") ;;
      *) merge_args+=(--merge) ;;
    esac
    errf=$(mktemp)
    if gh pr merge "$num" "${merge_args[@]}" >/dev/null 2>"$errf"; then
      rm -f "$errf"
      gh pr comment "$num" --body "$MARKER
Action: merged
Head: $sha" >/dev/null 2>&1
      REPORT="${REPORT}${num}\tmerged\thead ${sha}\n"
    else
      REPORT="${REPORT}${num}\tskip\tmerge command failed ($(tr '\n' ' ' <"$errf" | head -c 160))\n"; rm -f "$errf"
    fi
  elif [ "$mergeable" = "CONFLICTING" ]; then
    if [ "$DRY" -eq 1 ]; then
      REPORT="${REPORT}${num}\trebase\twould post rebase instruction for head ${sha}\n"; continue
    fi
    if gh pr comment "$num" --body "$MARKER
Action: rebase-requested
Head: $sha

This branch has a merge conflict with \`main\`. ${REBASE_HINT}" >/dev/null 2>&1; then
      REPORT="${REPORT}${num}\trebase-requested\thead ${sha}\n"
    else
      REPORT="${REPORT}${num}\tskip\trebase comment failed\n"
    fi
  else
    REPORT="${REPORT}${num}\tskip\tmergeable state is ${mergeable} (GitHub still computing, or unreadable; retried next run)\n"
  fi
done < <(printf '%s' "$prs" | jq -r '.[].number' 2>/dev/null)

printf '%b' "$REPORT"
exit 0
