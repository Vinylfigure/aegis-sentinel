/* Lane model — derives the termination-lane flow graph from the REAL
 * engagement artifacts. Layout is deterministic and hand-tuned (the lane
 * is small); every verdict/state painted on the canvas is looked up from
 * the loaded artifacts, never asserted here.
 *
 *   HRIS ──[TA-1]── Okta ──[TA-2]──●──[TA-3]── GitHub
 *                                  ├──[ E117 ]── GCP      (did not compile)
 *                                  ├──[TA-3]── Slack
 *                                  └──[excl.]── corp-IT   (out of scope, RAT-2026-031)
 */

import type { EngagementLoad } from "@/lib/data/engagement";
import { verdictSlug } from "@/lib/data/engagement";
import type { Population, VerdictRecord, VerdictState } from "@/lib/types/ontology";
import type {
  CapabilityEntry,
  CompileError,
  ReconciliationResult,
} from "@/lib/types/artifacts";

/* ---------------- severity ---------------- */

/** Worst-first ordering used to tint nodes by the worst verdict touching them. */
const SEVERITY: (VerdictState | "UNCOMPILED")[] = [
  "UNCOMPILED",
  "FAIL",
  "UNKNOWN",
  "EXCEPTION",
  "PASS",
  "EXCLUDED",
];

export type NodeTint = VerdictState | "UNCOMPILED" | null;

export function worstOf(states: (VerdictState | "UNCOMPILED")[]): NodeTint {
  let worst: NodeTint = null;
  for (const s of states) {
    if (worst === null || SEVERITY.indexOf(s) < SEVERITY.indexOf(worst)) worst = s;
  }
  return worst;
}

/* ---------------- model shapes ---------------- */

export interface LaneGate {
  gateId: string;
  /** Control-activity label painted on the gate (TA-1 / TA-2 / TA-3). */
  label: string;
  kind: "verdict" | "compile-error";
  verdict?: VerdictRecord;
  /** Companion verdicts sealed at the same control point (e.g. the feed's UNKNOWN). */
  related: VerdictRecord[];
  error?: CompileError;
  /** One-line hover summary. */
  summary: string;
  slug?: string;
}

export interface LaneSystem {
  systemId: string;
  name: string;
  descriptor: string;
  population?: Population;
  reconciliation?: ReconciliationResult;
  capabilities: CapabilityEntry[];
  tint: NodeTint;
  ghost?: boolean;
}

export interface CohortFlow {
  /** Total flowing through this edge (drives stroke weight). */
  weight: number | null;
  /** e.g. "15 workers" / "19 accounts · 15 clean · 4 flagged". */
  label: string;
}

export interface LaneEdgeModel {
  edgeId: string;
  source: string;
  target: string;
  eventKind: string;
  gate?: LaneGate;
  cohort: CohortFlow;
  /** Population flowing across this edge (drawer target). */
  populationRef?: string;
  capability?: CapabilityEntry;
  excluded?: boolean;
}

export interface LaneModel {
  systems: Record<string, LaneSystem>;
  edges: LaneEdgeModel[];
  gates: Record<string, LaneGate>;
}

/* ---------------- helpers ---------------- */

function byAssertion(load: EngagementLoad, ref: string): VerdictRecord | undefined {
  return load.artifacts.verdicts.find((v) => v.assertion_ref === ref);
}

function recFor(load: EngagementLoad, popId: string): ReconciliationResult | undefined {
  return load.artifacts.reconciliations.find((r) => r.population_ref === popId);
}

function popFor(load: EngagementLoad, popId: string): Population | undefined {
  return load.artifacts.populations.find((p) => p.population_id === popId);
}

function capsFor(load: EngagementLoad, system: string): CapabilityEntry[] {
  return load.artifacts.capability_registry.filter((e) => e.system === system);
}

/** "N account(s) tested; M clean" → { tested, clean } (derived, not asserted). */
function testedClean(message: string | null): { tested: number; clean: number } | null {
  const m = message?.match(/(\d+)\s+account\(s\) tested;\s*(\d+)\s+clean/);
  return m ? { tested: Number(m[1]), clean: Number(m[2]) } : null;
}

function gateFromVerdict(
  gateId: string,
  label: string,
  verdict: VerdictRecord | undefined,
  related: VerdictRecord[],
  summary: string
): LaneGate | undefined {
  if (!verdict) return undefined;
  return {
    gateId,
    label,
    kind: "verdict",
    verdict,
    related,
    summary,
    slug: verdictSlug(verdict),
  };
}

/* ---------------- the lane ---------------- */

export const JUNCTION_ID = "fanout";

export function buildLaneModel(load: EngagementLoad): LaneModel {
  const a = load.artifacts;

  const feedPass = byAssertion(load, "TERM-FEED.a");
  const feedUnknown = byAssertion(load, "TERM-FEED.b");
  const timingFail = byAssertion(load, "TERM-TIMING.a");
  const joinUnknown = byAssertion(load, "TERM-JOIN.a");
  const githubFail = byAssertion(load, "TERM-GITHUB.a");
  const slackException = byAssertion(load, "TERM-SLACK.a");
  const corpItExcluded = byAssertion(load, "TERM-CORP-IT.a");
  const e117 = a.compile_errors.find((e) => e.code === "E117");

  const joinRec = recFor(load, "TERM.identity-join");

  const systems: Record<string, LaneSystem> = {
    hris: {
      systemId: "hris",
      name: "HRIS",
      descriptor: "termination feed · authoritative",
      population: popFor(load, "TERM.terminations"),
      reconciliation: recFor(load, "TERM.terminations"),
      capabilities: capsFor(load, "hris"),
      tint: worstOf(
        [feedPass?.state, feedUnknown?.state].filter(Boolean) as VerdictState[]
      ),
    },
    okta: {
      systemId: "okta",
      name: "Okta",
      descriptor: "identity provider · deprovision",
      population: popFor(load, "TERM.identity-join"),
      reconciliation: joinRec,
      capabilities: capsFor(load, "okta"),
      tint: worstOf(
        [timingFail?.state, joinUnknown?.state].filter(Boolean) as VerdictState[]
      ),
    },
    github: {
      systemId: "github",
      name: "GitHub",
      descriptor: "source code · org accounts",
      population: popFor(load, "TERM.github.accounts"),
      reconciliation: recFor(load, "TERM.github.accounts"),
      capabilities: capsFor(load, "github"),
      tint: worstOf([githubFail?.state].filter(Boolean) as VerdictState[]),
    },
    gcp: {
      systemId: "gcp",
      name: "GCP",
      descriptor: "cloud IAM · projects",
      population: popFor(load, "TERM.gcp.accounts"),
      reconciliation: recFor(load, "TERM.gcp.accounts"),
      capabilities: capsFor(load, "gcp"),
      tint: e117 ? "UNCOMPILED" : null,
    },
    slack: {
      systemId: "slack",
      name: "Slack",
      descriptor: "workspace members",
      population: popFor(load, "TERM.slack.accounts"),
      reconciliation: recFor(load, "TERM.slack.accounts"),
      capabilities: capsFor(load, "slack"),
      tint: worstOf([slackException?.state].filter(Boolean) as VerdictState[]),
    },
    "corp-it": {
      systemId: "corp-it",
      name: "corp-IT",
      descriptor: "endpoint management",
      capabilities: [],
      tint: corpItExcluded ? "EXCLUDED" : null,
      ghost: true,
    },
  };

  /* ---- gates ---- */

  const ta1 = gateFromVerdict(
    "TA-1",
    "TA-1",
    feedPass,
    feedUnknown ? [feedUnknown] : [],
    "Feed completeness — population of 15 reconciled, zero undispositioned deltas (one identity-join UNKNOWN sealed alongside)."
  );

  const ta2 = gateFromVerdict(
    "TA-2",
    "TA-2",
    timingFail,
    joinUnknown ? [joinUnknown] : [],
    "Timely revocation — marcus.webb: 9 business days from termination to IdP deactivation (> 5)."
  );

  const ta3Github = gateFromVerdict(
    "TA-3.github",
    "TA-3",
    githubFail,
    [],
    "Residual access — dormant local account bm-legacy-bot joins to no identity in any source."
  );

  const gcpGate: LaneGate | undefined = e117
    ? {
        gateId: "E117.gcp",
        label: "TA-3",
        kind: "compile-error",
        error: e117,
        related: [],
        summary:
          "Did not compile — breakglass.config has no ratified capability entry; the claim refuses to evaluate.",
      }
    : undefined;

  const ta3Slack = gateFromVerdict(
    "TA-3.slack",
    "TA-3",
    slackException,
    [],
    "Residual access — kai retained under ratified disposition DISP-2026-114 (contractor-to-advisor conversion)."
  );

  const corpItGate = gateFromVerdict(
    "EXCL.corp-it",
    "scope",
    corpItExcluded,
    [],
    "Out of the lane's TA-3 scope by ratification RAT-2026-031 — device deprovisioning lives in the endpoint lane."
  );

  /* ---- cohort quantities (derived) ---- */

  const cohortIn = popFor(load, "TERM.terminations")?.size ?? null;
  const joined = joinRec ? joinRec.buckets.intersection.length : null;
  const joinExcluded = joinRec ? joinRec.buckets.excluded.length : 0;
  const unresolvable = joinRec ? joinRec.buckets.unresolvable.length : 0;
  const gh = testedClean(githubFail?.message ?? null);
  const sl = testedClean(slackException?.message ?? null);

  const edges: LaneEdgeModel[] = [
    {
      edgeId: "hris-okta",
      source: "hris",
      target: "okta",
      eventKind: "termination event",
      gate: ta1,
      cohort: { weight: cohortIn, label: `${cohortIn ?? "?"} terminated workers` },
      populationRef: "TERM.terminations",
      capability: capsFor(load, "hris")[0],
    },
    {
      edgeId: "okta-fanout",
      source: "okta",
      target: JUNCTION_ID,
      eventKind: "deprovision",
      gate: ta2,
      cohort: {
        weight: joined,
        label: `${joined ?? "?"} joined · ${joinExcluded} dispositioned · ${unresolvable} unresolvable`,
      },
      populationRef: "TERM.identity-join",
      capability: capsFor(load, "okta").find((c) => c.entry_id.includes("system_log")),
    },
    {
      edgeId: "fanout-github",
      source: JUNCTION_ID,
      target: "github",
      eventKind: "fan-out",
      gate: ta3Github,
      cohort: {
        weight: gh?.tested ?? null,
        label: gh
          ? `${gh.tested} accounts · ${gh.clean} clean · ${gh.tested - gh.clean} flagged`
          : "—",
      },
      populationRef: "TERM.github.accounts",
      capability: capsFor(load, "github").find((c) => c.entry_id.includes("org_members")),
    },
    {
      edgeId: "fanout-gcp",
      source: JUNCTION_ID,
      target: "gcp",
      eventKind: "fan-out",
      gate: gcpGate,
      cohort: { weight: null, label: "∅ uncompiled" },
      populationRef: "TERM.gcp.accounts",
      capability: capsFor(load, "gcp")[0],
    },
    {
      edgeId: "fanout-slack",
      source: JUNCTION_ID,
      target: "slack",
      eventKind: "fan-out",
      gate: ta3Slack,
      cohort: {
        weight: sl?.tested ?? null,
        label: sl
          ? `${sl.tested} tested · ${sl.clean} clean · ${sl.tested - sl.clean} exception`
          : "—",
      },
      populationRef: "TERM.slack.accounts",
      capability: capsFor(load, "slack")[0],
    },
    {
      edgeId: "fanout-corp-it",
      source: JUNCTION_ID,
      target: "corp-it",
      eventKind: "out of scope",
      gate: corpItGate,
      cohort: { weight: null, label: "excluded · RAT-2026-031" },
      excluded: true,
    },
  ];

  const gates: Record<string, LaneGate> = {};
  for (const e of edges) if (e.gate) gates[e.gate.gateId] = e.gate;

  return { systems, edges, gates };
}

/* ---------------- deterministic layout (hand-tuned) ---------------- */

export interface LanePosition {
  x: number;
  y: number;
}

export const LANE_LAYOUT: Record<string, LanePosition> = {
  hris: { x: 0, y: 340 },
  okta: { x: 520, y: 340 },
  [JUNCTION_ID]: { x: 958, y: 396 },
  github: { x: 1330, y: 60 },
  gcp: { x: 1330, y: 340 },
  slack: { x: 1330, y: 620 },
  "corp-it": { x: 1290, y: 830 },
};
