/* The six poison cases (PRD-v3 §6 — the mutation playbook's seed set),
 * DERIVED from the real engagement artifacts — never asserted statically.
 * Each poison names its expected detector (mirroring
 * tests/fixtures/mutations/<x>/expected_outcome.json); `detected` is
 * true only if the loaded verdicts / compile_errors actually contain
 * that detection, with the poison's evidence named. The headline metric:
 * mutated defects that produce compile-error / UNKNOWN / FAIL ÷ defects
 * introduced. Any silent PASS is a build-stopping bug.
 */

import type { VerdictRecord, VerdictState } from "@/lib/types/ontology";
import type { EngagementLoad } from "@/lib/data/engagement";
import { loadEngagement, verdictSlug } from "@/lib/data/engagement";

export interface MutationPoison {
  id: string;
  poison: string;
  /** What fired: a verdict state (with its route slug) or a compile E-code. */
  detector:
    | { kind: "verdict"; state: VerdictState; slug: string; note: string }
    | { kind: "ecode"; code: "E204" | "E117" | "E302"; note: string }
    | { kind: "missing"; note: string };
  detected: boolean;
}

interface VerdictExpectation {
  id: string;
  poison: string;
  claim_ref: string;
  assertion_ref: string;
  state: VerdictState;
  /** Substring the verdict message must carry to count as *naming* the poison. */
  evidence: string;
  note: string;
}

// Mirrors tests/fixtures/mutations/<poison>/expected_outcome.json.
const VERDICT_EXPECTATIONS: VerdictExpectation[] = [
  {
    id: "contractor-absent-hris",
    poison: "Contractor absent from HRIS (in downstream systems only)",
    claim_ref: "TERM.attributability",
    assertion_ref: "TERM-JOIN.a",
    state: "UNKNOWN",
    evidence: "blake",
    note: "UNKNOWN_POPULATION — negative-space left_only delta, sources_absent names the HRIS feed",
  },
  {
    id: "dormant-github-local-account",
    poison: "Dormant GitHub local account",
    claim_ref: "TERM.github.no-residual-access",
    assertion_ref: "TERM-GITHUB.a",
    state: "FAIL",
    evidence: "bm-legacy-bot",
    note: "NON_EXISTENCE fail — bm-legacy-bot named: dormant local account joins to no identity",
  },
  {
    id: "failed-identity-join",
    poison: "Failed identity join (unmappable identity)",
    claim_ref: "TERM.feed-completeness",
    assertion_ref: "TERM-FEED.b",
    state: "UNKNOWN",
    evidence: "identity join failed",
    note: "UNKNOWN_POPULATION · identity_fuzzy — routed to the human resolution queue",
  },
  {
    id: "delayed-revocation",
    poison: "Delayed revocation (9 business days)",
    claim_ref: "TERM.timely-revocation",
    assertion_ref: "TERM-TIMING.a",
    state: "FAIL",
    evidence: "9 business day",
    note: "TIMING fail — business-day arithmetic from HRIS termination date to IdP deactivation",
  },
  {
    id: "legitimate-exception",
    poison: "Legitimate exception (retained access)",
    claim_ref: "TERM.slack.no-residual-access",
    assertion_ref: "TERM-SLACK.a",
    state: "EXCEPTION",
    evidence: "DISP-2026-114",
    note: "EXCEPTION under ratified disposition DISP-2026-114 — surfaced and owned, never a silent PASS",
  },
];

function findVerdict(
  load: EngagementLoad,
  exp: VerdictExpectation
): VerdictRecord | undefined {
  return load.artifacts.verdicts.find(
    (v) => v.claim_ref === exp.claim_ref && v.assertion_ref === exp.assertion_ref
  );
}

/** Derive the six-poison scorecard from the loaded artifacts. */
export function mutationPoisons(load?: EngagementLoad): MutationPoison[] {
  const l = load ?? loadEngagement();
  const rows: MutationPoison[] = [];

  for (const exp of VERDICT_EXPECTATIONS) {
    const v = findVerdict(l, exp);
    const detected =
      !!v && v.state === exp.state && (v.message ?? "").includes(exp.evidence);
    rows.push({
      id: exp.id,
      poison: exp.poison,
      detector:
        v && detected
          ? { kind: "verdict", state: v.state, slug: verdictSlug(v), note: exp.note }
          : {
              kind: "missing",
              note: `expected ${exp.state} on ${exp.assertion_ref} naming "${exp.evidence}" — not found in artifacts`,
            },
      detected,
    });
  }

  // Break-glass poison: detected at compile time, not run time.
  const e117 = l.artifacts.compile_errors.find((e) => e.code === "E117");
  rows.splice(2, 0, {
    id: "breakglass-cloud-account",
    poison: "Break-glass cloud account outside IAM",
    detector: e117
      ? {
          kind: "ecode",
          code: "E117",
          note: `${e117.claim_ref} refuses to compile — ${e117.missing_source ?? "capability"} has no ratified capability entry`,
        }
      : {
          kind: "missing",
          note: "expected E117 (missing capability entry) — not found in compile_errors",
        },
    detected: !!e117,
  });

  return rows;
}

export function detectionRate(load?: EngagementLoad): {
  detected: number;
  total: number;
  pct: number;
} {
  const rows = mutationPoisons(load);
  const total = rows.length;
  const detected = rows.filter((p) => p.detected).length;
  return { detected, total, pct: total ? Math.round((100 * detected) / total) : 0 };
}
