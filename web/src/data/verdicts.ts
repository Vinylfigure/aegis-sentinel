/**
 * B3 — derivations over verdicts.json and poisons.json.
 *
 * Same discipline as `reconciliation.ts`: every function takes its artifact
 * explicitly, so deletion AND value falsifiers both bite (L-054/L-056).
 *
 * One distinction worth stating loudly, because it looks like a
 * contradiction and is not: PRD §2 forbids a *coverage* percentage against
 * a denominator left of RATIFIED, and B2 renders none. The **assurance
 * defect detection rate** here is a different metric entirely — PRD §7's
 * headline, `detected / introduced`, whose denominator is the mutation
 * suite's own seeded defects. That one is required, not forbidden. Do not
 * "fix" it away.
 */

import type {
  CompileError,
  PoisonCase,
  PoisonVerdictGroup,
  PoisonsArtifact,
  UnknownWhy,
  VerdictRecord,
  VerdictState,
  VerdictsArtifact,
} from "@/data/types";

/* ------------------------------------------------------------------ */
/* The five states                                                     */
/* ------------------------------------------------------------------ */

export interface VerdictStateMeta {
  state: VerdictState;
  /** One line on what the state MEANS — the states are never interchangeable
   * (HANDOFF §2), so each carries its own definition on screen. */
  meaning: string;
  /** The companion field the schema requires with this state, if any. */
  requires: keyof VerdictRecord | null;
  /** Token suffix for the state's visual treatment. Text always carries the
   * state too — colour is redundant encoding, never the only signal. */
  tone: "ok" | "fail" | "unknown" | "excluded" | "exception";
}

/**
 * Exhaustive by construction: `Record<VerdictState, …>` means adding a member
 * to `VerdictState` fails `tsc` here rather than silently rendering four
 * states. This is the B2 lesson (L-056) applied at authoring time instead of
 * after a verifier finds it.
 */
const STATE_META: Record<VerdictState, VerdictStateMeta> = {
  PASS: {
    state: "PASS",
    meaning:
      "the assertion held, and the evidence was fit to prove it (invariant №5).",
    requires: null,
    tone: "ok",
  },
  FAIL: {
    state: "FAIL",
    meaning: "the assertion did not hold. A clean finding — not an error.",
    requires: null,
    tone: "fail",
  },
  UNKNOWN: {
    state: "UNKNOWN",
    meaning:
      "the question could not be answered. Carries a why-code and blocks ratification unless dispositioned (invariant №12).",
    requires: "unknown_cause",
    tone: "unknown",
  },
  EXCLUDED: {
    state: "EXCLUDED",
    meaning:
      "out of scope by a ratified boundary decision — never a silent N/A (D-9).",
    requires: "ratification_ref",
    tone: "excluded",
  },
  EXCEPTION: {
    state: "EXCEPTION",
    meaning:
      "a legitimate exception, dispositioned by a named human with a review date.",
    requires: "disposition_ref",
    tone: "exception",
  },
};

/** Presentation order: the states that demand attention first. */
export const VERDICT_STATES: readonly VerdictStateMeta[] = [
  STATE_META.FAIL,
  STATE_META.UNKNOWN,
  STATE_META.EXCEPTION,
  STATE_META.EXCLUDED,
  STATE_META.PASS,
];

export function verdictStateMeta(state: VerdictState): VerdictStateMeta {
  return STATE_META[state];
}

/* ------------------------------------------------------------------ */
/* Combined record roster (B4)                                         */
/* ------------------------------------------------------------------ */

/** The poisons verdict_records grouping keys. The Record lookup below makes
 * this exhaustive: a fourth family in the artifact type fails tsc here
 * rather than silently dropping its records from every roster. */
const POISON_GROUP_COMPLETE: Record<PoisonVerdictGroup, true> = {
  existence: true,
  non_existence: true,
  timing: true,
};
export const POISON_VERDICT_GROUPS: readonly PoisonVerdictGroup[] = Object.keys(
  POISON_GROUP_COMPLETE,
) as PoisonVerdictGroup[];

/**
 * Every verdict record the engagement carries: verdicts.json plus the
 * records embedded in poisons.verdict_records, deduped by record_id. The
 * real artifacts are disjoint so the dedup is normally a no-op; it existed
 * because the B1 mocks duplicated the records, and it stays because an
 * artifact repeating a record_id should collapse, not double-render. Order
 * is verdicts.json first, then poison families in group order.
 */
export function combinedRecords(
  verdicts: VerdictsArtifact,
  poisons: PoisonsArtifact,
): VerdictRecord[] {
  const seen = new Set<string>();
  const out: VerdictRecord[] = [];
  const add = (record: VerdictRecord) => {
    if (seen.has(record.record_id)) return;
    seen.add(record.record_id);
    out.push(record);
  };
  for (const record of verdicts) add(record);
  for (const group of POISON_VERDICT_GROUPS) {
    for (const record of poisons.verdict_records[group]) add(record);
  }
  return out;
}

/* ------------------------------------------------------------------ */
/* Record deep links (C3)                                              */
/* ------------------------------------------------------------------ */

/** DOM id for a record's card on /verdicts. Raw — getElementById handles
 * `@` and `.`; the `record=` prefix avoids the `state-*` section ids. One
 * shared helper pair so every producer and the consumer agree by
 * construction. */
export function verdictRecordAnchor(recordId: string): string {
  return `record=${recordId}`;
}

/** Href that opens /verdicts with the record selected and scrolled into
 * view (hash parsed client-side; static-export-safe). */
export function verdictRecordHref(recordId: string): string {
  return `/verdicts#record=${encodeURIComponent(recordId)}`;
}

/* ------------------------------------------------------------------ */
/* Runs (C2)                                                           */
/* ------------------------------------------------------------------ */

/** One run's records, folded from the combined roster. Two run ids across
 * the engagement are DATA (the walking-skeleton run plus the poison run),
 * not a defect — the defect signal is a cross-run control_id disagreement,
 * which crossRunControl() carries. runMetadata() survives for within-group
 * folds; its old cross-collection breach use is retired because it cannot
 * distinguish two legitimate runs from one corrupted one. */
export interface RunGroup {
  runId: string;
  controlId: string;
  collectedAt: string;
  records: VerdictRecord[];
}

export function verdictRuns(
  verdicts: VerdictsArtifact,
  poisons: PoisonsArtifact,
): RunGroup[] {
  const groups = new Map<string, VerdictRecord[]>();
  for (const record of combinedRecords(verdicts, poisons)) {
    const existing = groups.get(record.run_id);
    if (existing) existing.push(record);
    else groups.set(record.run_id, [record]);
  }
  return [...groups.entries()].map(([runId, records]) => ({
    runId,
    controlId: runMetadata(records, "control_id").values.join(", "),
    collectedAt: runMetadata(records, "collected_at").values.join(", "),
    records,
  }));
}

/** The one cross-run fact that IS a breach when inconsistent: every run in
 * the engagement tests the same control. */
export function crossRunControl(groups: readonly RunGroup[]): {
  values: string[];
  consistent: boolean;
} {
  const values = [...new Set(groups.map((g) => g.controlId))];
  return { values, consistent: values.length <= 1 };
}

/* ------------------------------------------------------------------ */
/* Records                                                             */
/* ------------------------------------------------------------------ */

export function recordsByState(
  records: readonly VerdictRecord[],
  state: VerdictState,
): VerdictRecord[] {
  return records.filter((r) => r.status === state);
}

/**
 * The conditional-field invariant, checked rather than assumed: EXCLUDED
 * requires a ratification_ref, EXCEPTION a disposition_ref, UNKNOWN a
 * why-code. A record that breaks it is a schema violation on the wire, and
 * the page says so instead of rendering a state whose justification is
 * missing. Nothing in the current fixture trips this — that is the point of
 * checking rather than trusting.
 */
export interface ConditionalBreach {
  record: VerdictRecord;
  missing: keyof VerdictRecord;
}

export function conditionalBreaches(
  records: readonly VerdictRecord[],
): ConditionalBreach[] {
  const breaches: ConditionalBreach[] = [];
  for (const record of records) {
    const required = STATE_META[record.status].requires;
    if (required === null) continue;
    const value = record[required];
    if (value === undefined || value === null || value === "") {
      breaches.push({ record, missing: required });
    }
  }
  return breaches;
}

/** Why-code tallies, for the UNKNOWN breakdown. D-U1 makes the why-code the
 * axis; per-cause rate is itself a verdict input (D-7 §5). */
export function unknownCauses(
  records: readonly VerdictRecord[],
): { cause: UnknownWhy; records: VerdictRecord[] }[] {
  const groups = new Map<UnknownWhy, VerdictRecord[]>();
  for (const record of recordsByState(records, "UNKNOWN")) {
    const cause = record.unknown_cause;
    if (!cause) continue;
    const existing = groups.get(cause);
    if (existing) existing.push(record);
    else groups.set(cause, [record]);
  }
  return [...groups.entries()].map(([cause, rs]) => ({ cause, records: rs }));
}

/**
 * verdicts.json is a bare array with no run envelope (README Q3), so run
 * metadata is folded out of the records. If records disagree on a field the
 * disagreement is returned rather than silently taking the first — a single
 * run that reports two run_ids is a defect, not a rendering detail.
 */
export function runMetadata(
  records: readonly VerdictRecord[],
  field: "run_id" | "control_id" | "schema_version" | "collected_at",
): { values: string[]; consistent: boolean } {
  const values = [...new Set(records.map((r) => r[field]))];
  return { values, consistent: values.length <= 1 };
}

/* ------------------------------------------------------------------ */
/* Mutation scorecard (poisons.json)                                   */
/* ------------------------------------------------------------------ */

export interface Scorecard {
  /** Recomputed from the cases on screen — never read from `detection`. */
  renderedDetected: number;
  renderedTotal: number;
  /** What the artifact claims. Shown beside the recomputation. */
  statedDetected: number;
  statedTotal: number;
  statedRate: number;
  /** True when the artifact's own numbers match the cases it ships. */
  agrees: boolean;
  /** PRD §7: any silent PASS is a build-stopping bug. */
  misses: string[];
}

export function scorecard(poisons: PoisonsArtifact): Scorecard {
  const cases = poisons.cases;
  const renderedDetected = cases.filter((c) => c.detected).length;
  const renderedTotal = cases.length;
  const { detected, total, detection_rate, misses } = poisons.detection;
  return {
    renderedDetected,
    renderedTotal,
    statedDetected: detected,
    statedTotal: total,
    statedRate: detection_rate,
    agrees:
      detected === renderedDetected &&
      total === renderedTotal &&
      Math.abs(detection_rate - (renderedTotal === 0 ? 0 : renderedDetected / renderedTotal)) <
        1e-9,
    misses: [...misses],
  };
}

/** The detection rate as a percentage string, computed from the cases on
 * screen. See the module docstring on why a percentage is correct here. */
export function detectionRateText(card: Scorecard): string {
  if (card.renderedTotal === 0) return "no cases";
  return `${Math.round((card.renderedDetected / card.renderedTotal) * 100)}%`;
}

/** Poison cases in a stable order: undetected first — a miss is the only
 * thing on this page that stops a build. */
export function orderedCases(poisons: PoisonsArtifact): PoisonCase[] {
  return [...poisons.cases].sort((a, b) => {
    if (a.detected !== b.detected) return a.detected ? 1 : -1;
    return a.id.localeCompare(b.id);
  });
}

/** Split "UNKNOWN:UNKNOWN_POPULATION" into its parts; an E-code or a bare
 * state passes through as-is. Stringly-typed on the wire (README Q4). */
export function splitClassification(value: string): {
  head: string;
  cause: string | null;
} {
  const marker = value.indexOf(":");
  if (marker === -1) return { head: value, cause: null };
  return { head: value.slice(0, marker), cause: value.slice(marker + 1) };
}

export function compileErrorsOf(poisonCase: PoisonCase): CompileError[] {
  return poisonCase.actual.kind === "compile_error" ? poisonCase.actual.errors : [];
}
