/* Lane model — derives the termination-lane flow graph from the REAL
 * engagement artifacts. Layout is deterministic and hand-tuned (the lane
 * is small); every verdict/state painted on the canvas is looked up from
 * the loaded artifacts, never asserted here.
 *
 * This engagement carries exactly one reconciled population
 * (pop-termination-events) that threads through HRIS (authoritative,
 * existence check) → Okta (revocation-timing checks, one per member) →
 * GitHub (residual-access / NON-EXISTENCE check). GCP break-glass
 * accounts are a second, DIFFERENT population (pop-breakglass-capable)
 * that never compiled (E117: no ratified capability entry for
 * breakglass.config) — it has no reconciliation report of its own, and
 * none is invented here.
 *
 *   HRIS ──[TA-1]── Okta ──[TA-2]──●──[TA-3]── GitHub
 *                                  └──[ E117 ]── GCP      (did not compile)
 */

import type { EngagementLoad } from "@/lib/data/engagement";
import { verdictSlug } from "@/lib/data/engagement";
import type { Population, VerdictState } from "@/lib/types/ontology";
import type {
  CapabilityEntry,
  CompileError,
  ReconciliationReport,
  VerdictRecord,
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

/** The single worst VerdictRecord among a group sealed at the same control
 * point (same ordering as worstOf, but returning the record itself so the
 * gate can link somewhere real). */
function worstVerdict(records: VerdictRecord[]): VerdictRecord | undefined {
  let worst: VerdictRecord | undefined;
  for (const r of records) {
    if (!worst || SEVERITY.indexOf(r.status) < SEVERITY.indexOf(worst.status)) worst = r;
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
  reconciliation?: ReconciliationReport;
  capabilities: CapabilityEntry[];
  tint: NodeTint;
  ghost?: boolean;
}

export interface CohortFlow {
  /** Total flowing through this edge (drives stroke weight). */
  weight: number | null;
  /** e.g. "6 terminated workers" / "9 revocation checks · 4 PASS · 1 FAIL". */
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
  return load.artifacts.verdicts.find((v) => v.assertion_id === ref);
}

function recFor(load: EngagementLoad, popId: string): ReconciliationReport | undefined {
  return load.artifacts.reconciliations.find((r) => r.population_id === popId);
}

function popFor(load: EngagementLoad, popId: string): Population | undefined {
  return load.artifacts.populations.find((p) => p.id === popId);
}

function capsFor(load: EngagementLoad, system: string): CapabilityEntry[] {
  return load.artifacts.capability_registry.filter((e) => e.system === system);
}

/** The leading integer in a verdict message ("1 terminated member(s) still
 * hold access…" → 1) — derived from the sealed message text, not asserted
 * separately (same technique the message-parsing in evidence.ts uses). */
function leadingCount(message: string | null | undefined): number | null {
  const m = message?.match(/^(\d+)\s/);
  return m ? Number(m[1]) : null;
}

/** The population id a compile error's own rendered message names
 * ("population pop-breakglass-capable derivation references…") — the
 * compiler owns this text (artifacts.ts's CompileError doc comment); no
 * separate population_id field exists on CompileError to read instead. */
function populationNamedIn(message: string): string | undefined {
  return message.match(/population (\S+)/)?.[1];
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

/** The one population this engagement actually reconciled. */
const POPULATION_ID = "pop-termination-events";

export function buildLaneModel(load: EngagementLoad): LaneModel {
  const a = load.artifacts;

  const pop = popFor(load, POPULATION_ID);
  const rec = recFor(load, POPULATION_ID);

  const existence = byAssertion(load, "am06-hris-existence-A");
  const existencePoison = byAssertion(load, "poison-am06-existence-A");
  const nonexistence = byAssertion(load, "poison-am06-nonexistence-A");
  const timingVerdicts = a.verdicts.filter(
    (v) => v.assertion_id === "cp-idp-deactivation-workday-B"
  );
  const timingGateVerdict = worstVerdict(timingVerdicts);
  const timingRelated = timingVerdicts.filter((v) => v !== timingGateVerdict);
  const e117 = a.compile_errors.find((e) => e.code === "E117");
  const gcpPopulationRef = e117 ? populationNamedIn(e117.message) : undefined;

  const systems: Record<string, LaneSystem> = {
    hris: {
      systemId: "hris",
      name: "HRIS",
      descriptor: "termination feed · authoritative",
      population: pop,
      reconciliation: rec,
      capabilities: capsFor(load, "workday"),
      tint: worstOf(
        [existence?.status, existencePoison?.status].filter(Boolean) as VerdictState[]
      ),
    },
    okta: {
      systemId: "okta",
      name: "Okta",
      descriptor: "identity provider · revocation timing",
      population: pop,
      reconciliation: rec,
      capabilities: capsFor(load, "okta"),
      tint: worstOf(timingVerdicts.map((v) => v.status)),
    },
    github: {
      systemId: "github",
      name: "GitHub",
      descriptor: "source code · residual access",
      population: pop,
      reconciliation: rec,
      capabilities: capsFor(load, "github"),
      tint: worstOf([nonexistence?.status].filter(Boolean) as VerdictState[]),
    },
    gcp: {
      systemId: "gcp",
      name: "GCP",
      descriptor: "cloud IAM · break-glass accounts",
      capabilities: capsFor(load, "gcp"),
      tint: e117 ? "UNCOMPILED" : null,
    },
  };

  /* ---- gates ---- */

  const ta1 = gateFromVerdict(
    "TA-1",
    "TA-1",
    existence,
    existencePoison ? [existencePoison] : [],
    existence?.message ??
      "Existence check — every canonical member must have a termination record in the authoritative feed."
  );

  const ta2 = gateFromVerdict(
    "TA-2",
    "TA-2",
    timingGateVerdict,
    timingRelated,
    timingGateVerdict?.message ??
      "Timely revocation — deactivation must land inside the constraint window."
  );

  const ta3Github = gateFromVerdict(
    "TA-3.github",
    "TA-3",
    nonexistence,
    [],
    nonexistence?.message ?? "Residual access — no terminated member may retain access."
  );

  const gcpGate: LaneGate | undefined = e117
    ? {
        gateId: "E117.gcp",
        label: "TA-3",
        kind: "compile-error",
        error: e117,
        related: [],
        summary: e117.message,
      }
    : undefined;

  /* ---- cohort quantities (derived) ---- */

  const timingCounts: Partial<Record<VerdictState, number>> = {};
  for (const v of timingVerdicts) timingCounts[v.status] = (timingCounts[v.status] ?? 0) + 1;
  const timingLabel = timingVerdicts.length
    ? `${timingVerdicts.length} revocation checks · ` +
      Object.entries(timingCounts)
        .map(([s, n]) => `${n} ${s}`)
        .join(" · ")
    : "—";

  const flagged = leadingCount(nonexistence?.message);
  const githubLabel =
    pop?.size != null && flagged != null
      ? `${pop.size} accounts · ${pop.size - flagged} clean · ${flagged} flagged`
      : (nonexistence?.message ?? "—");

  const edges: LaneEdgeModel[] = [
    {
      edgeId: "hris-okta",
      source: "hris",
      target: "okta",
      eventKind: "termination event",
      gate: ta1,
      cohort: { weight: pop?.size ?? null, label: `${pop?.size ?? "?"} terminated workers` },
      populationRef: POPULATION_ID,
      capability: capsFor(load, "workday")[0],
    },
    {
      edgeId: "okta-fanout",
      source: "okta",
      target: JUNCTION_ID,
      eventKind: "deprovision",
      gate: ta2,
      cohort: { weight: timingVerdicts.length || null, label: timingLabel },
      populationRef: POPULATION_ID,
      capability: capsFor(load, "okta").find((c) => c.id.includes("system_log")),
    },
    {
      edgeId: "fanout-github",
      source: JUNCTION_ID,
      target: "github",
      eventKind: "fan-out",
      gate: ta3Github,
      cohort: { weight: pop?.size ?? null, label: githubLabel },
      populationRef: POPULATION_ID,
      capability: capsFor(load, "github").find((c) => c.id.includes("members")),
    },
    {
      edgeId: "fanout-gcp",
      source: JUNCTION_ID,
      target: "gcp",
      eventKind: "fan-out",
      gate: gcpGate,
      cohort: { weight: null, label: "∅ uncompiled" },
      populationRef: gcpPopulationRef,
      capability: capsFor(load, "gcp")[0],
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
  [JUNCTION_ID]: { x: 958, y: 340 },
  github: { x: 1330, y: 160 },
  gcp: { x: 1330, y: 520 },
};
