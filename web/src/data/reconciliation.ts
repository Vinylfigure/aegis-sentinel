/**
 * B2 — derivations over the REC01 reconciliation artifact.
 *
 * Sibling to `derived.ts`, which is scoped to the A2 *seed*; artifact
 * derivations live here. Every function takes its report explicitly (no
 * module-level singleton read), so the deletion-falsifier probes bite and
 * nothing here can be tempted into a hardcoded count.
 *
 * Discipline carried from the backend: counts are diagnostics, never
 * evidence (HANDOFF §2) — the rendered deltas are the truth, and where the
 * artifact's own `counts` disagree the divergence is surfaced, not smoothed.
 */

import type {
  AssuranceState,
  Delta,
  DeltaBucket,
  DispositionRecord,
  ReconciliationReport,
  ReconciliationSource,
} from "@/data/types";

/* ------------------------------------------------------------------ */
/* Ladder                                                              */
/* ------------------------------------------------------------------ */

/**
 * The linear ladder, per `LADDER_TRANSITIONS` in schema/models.py.
 * STALE is deliberately absent: it is a re-entry state (RATIFIED -> STALE
 * -> DISCOVERED), not a sixth rung, and drawing it in line would imply a
 * progression that does not exist.
 */
export const LADDER_RUNGS = [
  "UNDEFINED",
  "DEFINED",
  "DISCOVERED",
  "RECONCILED",
  "RATIFIED",
] as const;

export type LadderRung = (typeof LADDER_RUNGS)[number];

/** The gate sentence the engine itself enforces (schema.models.advance). */
export const LADDER_GATE_RULE =
  "blocked while any delta is undispositioned (schema.models.advance)";

export type LadderPosition =
  | { kind: "rung"; index: number }
  /** Reached RATIFIED and left the strip — STALE is re-entry, not a rung. */
  | { kind: "off-strip"; label: AssuranceState };

/**
 * Where an AssuranceState sits relative to the linear strip.
 *
 * The `never` arm is the point: an AssuranceState the stepper does not
 * handle fails the build here rather than rendering a strip with no current
 * rung and no `aria-current` landmark. Found by the B2 adversarial verifier,
 * which set `after_dispositions` to STALE — a legal state reachable from
 * RATIFIED (schema/models.py LADDER_TRANSITIONS) — and watched every rung
 * report "not reached" while tsc and the build stayed green.
 */
export function ladderPosition(state: AssuranceState): LadderPosition {
  switch (state) {
    case "UNDEFINED":
    case "DEFINED":
    case "DISCOVERED":
    case "RECONCILED":
    case "RATIFIED":
      return { kind: "rung", index: LADDER_RUNGS.indexOf(state) };
    case "STALE":
      return { kind: "off-strip", label: state };
    default: {
      const exhaustive: never = state;
      return exhaustive;
    }
  }
}

/** True once the human freeze (D-L1) has happened — including STALE, which
 * is only reachable from RATIFIED. Anything asserting "RATIFIED not reached"
 * must derive it from this, never state it unconditionally. */
export function ratifiedReached(state: AssuranceState): boolean {
  const position = ladderPosition(state);
  return (
    position.kind === "off-strip" || position.index >= LADDER_RUNGS.indexOf("RATIFIED")
  );
}

/* ------------------------------------------------------------------ */
/* Buckets                                                             */
/* ------------------------------------------------------------------ */

export interface BucketMeta {
  bucket: DeltaBucket;
  /** Open buckets gate the ladder; resolved ones do not. `OPEN_BUCKETS` in
   * reconcile/engine.py. */
  open: boolean;
  label: string;
  /** The precedence rule, lifted from reconcile/engine.py's docstring. */
  rule: string;
}

/**
 * Open questions first, then the resolved states. The `Record<DeltaBucket,
 * BucketMeta>` below is what makes this exhaustive: adding a member to
 * `DeltaBucket` fails `tsc` here rather than silently rendering five panels.
 */
const BUCKET_META: Record<DeltaBucket, BucketMeta> = {
  conflict: {
    bucket: "conflict",
    open: true,
    label: "Conflict",
    rule: "present in every source but with mismatched attributes.",
  },
  unresolvable: {
    bucket: "unresolvable",
    open: true,
    label: "Unresolvable",
    rule: "no canonical key derivable (null or garbled email); the source-side member ref is preserved.",
  },
  left_only: {
    bucket: "left_only",
    open: true,
    label: "Left only",
    rule: "present in the authoritative source but absent from at least one other source. Absence dominates attribute comparison.",
  },
  right_only: {
    bucket: "right_only",
    open: true,
    label: "Right only",
    rule: "present in some source but absent from the authoritative source.",
  },
  excluded: {
    bucket: "excluded",
    open: false,
    label: "Excluded",
    rule: "matches a ratified boundary exclusion. Born dispositioned — the ratified exclusion (D-9) is its human resolution; the engine never invents one.",
  },
  intersection: {
    bucket: "intersection",
    open: false,
    label: "Intersection",
    rule: "present in every source with no attribute mismatch. Agreement needs no sign-off.",
  },
};

export const BUCKET_ORDER: readonly BucketMeta[] = [
  BUCKET_META.conflict,
  BUCKET_META.unresolvable,
  BUCKET_META.left_only,
  BUCKET_META.right_only,
  BUCKET_META.excluded,
  BUCKET_META.intersection,
];

export const OPEN_BUCKETS: readonly BucketMeta[] = BUCKET_ORDER.filter((b) => b.open);
export const RESOLVED_BUCKETS: readonly BucketMeta[] = BUCKET_ORDER.filter((b) => !b.open);

export function bucketMeta(bucket: DeltaBucket): BucketMeta {
  return BUCKET_META[bucket];
}

/* ------------------------------------------------------------------ */
/* Identity                                                            */
/* ------------------------------------------------------------------ */

/** Port of `canonical_email` in reconcile/minimal.py — trimmed, lower-cased,
 * empty becomes null. The engine additionally requires an `@` before it will
 * key on the value. */
export function canonicalIdentity(raw: string | null | undefined): string | null {
  if (raw === null || raw === undefined) return null;
  const trimmed = raw.trim().toLowerCase();
  if (trimmed.length === 0 || !trimmed.includes("@")) return null;
  return trimmed;
}

export const CANONICAL_RULE =
  "canonical identity = trimmed, lower-cased email (reconcile.minimal.canonical_email)";

/**
 * Bucket deltas use a prefixed `member_ref` (`email:…`, `okta:…`) while
 * `boundary_exclusions[].member` is a bare identifier — README Q6. Joining
 * the two needs this, and every screen that uses it says so rather than
 * stripping silently.
 */
export function strippedMemberRef(ref: string): string {
  const marker = ref.indexOf(":");
  return marker === -1 ? ref : ref.slice(marker + 1);
}

export const PREFIX_JOIN_NOTE =
  "matched by stripping the member_ref prefix — boundary_exclusions carry a bare identifier (README Q6)";

/* ------------------------------------------------------------------ */
/* Dispositions (README Q5 — two moments, not two truths)              */
/* ------------------------------------------------------------------ */

export type DispositionSource = "inline" | "map";

export interface ResolvedDisposition {
  record: DispositionRecord;
  /** Which of the artifact's two records this came from. Rendered, so the
   * choice is visible rather than hidden inside a merge. */
  source: DispositionSource;
}

/**
 * The artifact records dispositions twice: inline on the delta (only the
 * EXCLUDED delta, born dispositioned) and in the top-level `dispositions`
 * map (the human acts applied after the first verdict was recorded). These
 * are two *moments*, not a contradiction — the buckets are the
 * pre-disposition snapshot. Inline wins where present; the map answers the
 * rest.
 */
export function resolveDisposition(
  report: ReconciliationReport,
  memberRef: string,
): ResolvedDisposition | null {
  const delta = findDelta(report, memberRef);
  if (delta?.disposition) return { record: delta.disposition, source: "inline" };
  const mapped = report.dispositions[memberRef];
  if (mapped) return { record: mapped, source: "map" };
  return null;
}

export function findDelta(report: ReconciliationReport, memberRef: string): Delta | null {
  for (const meta of BUCKET_ORDER) {
    const found = report.buckets[meta.bucket].find((d) => d.member_ref === memberRef);
    if (found) return found;
  }
  return null;
}

export interface DeltaEntry {
  meta: BucketMeta;
  delta: Delta;
}

/** Every delta, flattened in BUCKET_ORDER. */
export function deltaEntries(report: ReconciliationReport): DeltaEntry[] {
  return BUCKET_ORDER.flatMap((meta) =>
    report.buckets[meta.bucket].map((delta) => ({ meta, delta })),
  );
}

export interface Blocker {
  ref: string;
  bucket: DeltaBucket | null;
  answer: ResolvedDisposition | null;
}

/**
 * One row per `ladder.blocked_by_open_deltas` ref, joined back to its bucket
 * and its disposition. The spine of the why-complete rail: it is what turns
 * "RECONCILED" from a claim into an argument.
 */
export function openBlockers(report: ReconciliationReport): Blocker[] {
  return report.ladder.blocked_by_open_deltas.map((ref) => ({
    ref,
    bucket: findDelta(report, ref)?.bucket ?? null,
    answer: resolveDisposition(report, ref),
  }));
}

/** Blockers with no disposition anywhere. Non-empty means the ladder's
 * `after_dispositions` claim is contradicted by the deltas. */
export function unansweredBlockers(report: ReconciliationReport): Blocker[] {
  return openBlockers(report).filter((b) => b.answer === null);
}

/** True only when every blocker was answered by a named human. */
export function reconciledClaimHolds(report: ReconciliationReport): boolean {
  return unansweredBlockers(report).length === 0;
}

/* ------------------------------------------------------------------ */
/* Counts as diagnostics                                               */
/* ------------------------------------------------------------------ */

export interface CountPair {
  bucket: DeltaBucket;
  /** What the artifact says. */
  artifact: number;
  /** What is actually on screen. This one is the truth. */
  rendered: number;
}

export function countPairs(report: ReconciliationReport): CountPair[] {
  return BUCKET_ORDER.map((meta) => ({
    bucket: meta.bucket,
    artifact: report.counts[meta.bucket],
    rendered: report.buckets[meta.bucket].length,
  }));
}

export function countsDivergence(report: ReconciliationReport): CountPair[] {
  return countPairs(report).filter((p) => p.artifact !== p.rendered);
}

/* ------------------------------------------------------------------ */
/* The join                                                            */
/* ------------------------------------------------------------------ */

export interface JoinRow {
  /** Canonical email where one could be derived, else the source-side ref. */
  key: string;
  canonical: string | null;
  /** Source name -> that source's member ref, or null when absent. */
  cells: Record<string, string | null>;
  inCanonicalMembers: boolean;
  bucket: DeltaBucket | null;
  /** Raw email as the source stated it — shown verbatim for unjoinable rows
   * so the garbled key is visible rather than described. */
  rawEmail: string | null;
}

/**
 * The join matrix: one row per canonical identity, plus a row for every
 * source member that could not be keyed at all. Nothing is dropped — a
 * member either keys, or appears as a named join failure.
 */
export function joinMatrix(report: ReconciliationReport): {
  keyed: JoinRow[];
  unjoinable: JoinRow[];
} {
  const sourceNames = report.sources.map((s) => s.name);
  const emptyCells = (): Record<string, string | null> =>
    Object.fromEntries(sourceNames.map((n) => [n, null]));

  const keyed = new Map<string, JoinRow>();
  const unjoinable: JoinRow[] = [];

  for (const source of report.sources) {
    for (const member of source.members) {
      const canonical = canonicalIdentity(member.email);
      if (canonical === null) {
        unjoinable.push({
          key: member.ref,
          canonical: null,
          cells: { ...emptyCells(), [source.name]: member.ref },
          inCanonicalMembers: false,
          bucket: findDelta(report, member.ref)?.bucket ?? null,
          rawEmail: member.email,
        });
        continue;
      }
      const existing = keyed.get(canonical);
      if (existing) {
        existing.cells[source.name] = member.ref;
        continue;
      }
      keyed.set(canonical, {
        key: canonical,
        canonical,
        cells: { ...emptyCells(), [source.name]: member.ref },
        inCanonicalMembers: report.canonical_members.includes(canonical),
        bucket: findDelta(report, `email:${canonical}`)?.bucket ?? null,
        rawEmail: member.email,
      });
    }
  }

  return {
    keyed: [...keyed.values()].sort((a, b) => a.key.localeCompare(b.key)),
    unjoinable: unjoinable.sort((a, b) => a.key.localeCompare(b.key)),
  };
}

/* ------------------------------------------------------------------ */
/* D-7 join-failure taxonomy                                           */
/* ------------------------------------------------------------------ */

/**
 * D-7 decomposes UNKNOWN by *why the deterministic join failed*
 * (knowledge/01_corpus/02_design_decisions/
 * Aegis_Design_Fix_D7_UNKNOWN_Decomposition.md §1), and D-U1 maps each
 * family onto a why-code. The wire carries only the bucket, so this is an
 * inference — every rendering of it says so (README Q9).
 *
 * `conflict` is deliberately absent: a conflict is a *successful* join with
 * disagreeing attributes, which is D-8 model reconciliation, not a join
 * failure. Filing it under D-7 would misreport what happened.
 */
export type D7Family = "basis-missing" | "identity-fuzzy" | "no-basis-anywhere";

export interface D7Classification {
  family: D7Family;
  whyCode: "UNKNOWN_EVIDENCE" | "UNKNOWN_POPULATION";
  meaning: string;
}

const D7_BY_BUCKET: Partial<Record<DeltaBucket, D7Classification>> = {
  left_only: {
    family: "basis-missing",
    whyCode: "UNKNOWN_EVIDENCE",
    meaning:
      "in the authoritative source but absent from a corroborating one — the basis is not where it should be.",
  },
  unresolvable: {
    family: "identity-fuzzy",
    whyCode: "UNKNOWN_POPULATION",
    meaning: "the join key itself is soft — no canonical key could be derived.",
  },
  right_only: {
    family: "no-basis-anywhere",
    whyCode: "UNKNOWN_POPULATION",
    meaning: "keys to nothing in the authoritative source — it is in no declared population.",
  },
};

export function d7Family(bucket: DeltaBucket): D7Classification | null {
  return D7_BY_BUCKET[bucket] ?? null;
}

export const D7_INFERENCE_CAVEAT =
  "cause family inferred from the bucket; not carried on the wire (README Q9)";

/** Refs grouped by D-7 family, for the taxonomy strip. */
export function d7Groups(
  report: ReconciliationReport,
): { classification: D7Classification; refs: string[] }[] {
  const groups = new Map<D7Family, { classification: D7Classification; refs: string[] }>();
  for (const { delta } of deltaEntries(report)) {
    const classification = d7Family(delta.bucket);
    if (!classification) continue;
    const existing = groups.get(classification.family);
    if (existing) existing.refs.push(delta.member_ref);
    else groups.set(classification.family, { classification, refs: [delta.member_ref] });
  }
  return [...groups.values()];
}

/* ------------------------------------------------------------------ */
/* Attribute disagreement (D-8)                                        */
/* ------------------------------------------------------------------ */

export interface AttributeDisagreement {
  attribute: string;
  /** Source name -> the value that source holds. */
  bySource: Record<string, string>;
}

/**
 * What a CONFLICT delta actually disagrees about. Read straight out of
 * `sources[].members[].attributes`, so deleting an attribute changes the
 * panel. Mirrors `_conflicting_attributes` in reconcile/engine.py.
 */
export function attributeDisagreements(
  report: ReconciliationReport,
  memberRef: string,
): AttributeDisagreement[] {
  const canonical = canonicalIdentity(strippedMemberRef(memberRef));
  if (canonical === null) return [];

  const byAttribute = new Map<string, Record<string, string>>();
  for (const source of report.sources) {
    for (const member of source.members) {
      if (canonicalIdentity(member.email) !== canonical) continue;
      for (const [attribute, value] of Object.entries(member.attributes)) {
        if (value === undefined) continue;
        const row = byAttribute.get(attribute) ?? {};
        row[source.name] = value;
        byAttribute.set(attribute, row);
      }
    }
  }

  return [...byAttribute.entries()]
    .filter(([, bySource]) => new Set(Object.values(bySource)).size > 1)
    .map(([attribute, bySource]) => ({ attribute, bySource }));
}

/* ------------------------------------------------------------------ */
/* Derivation basis (invariant №3)                                     */
/* ------------------------------------------------------------------ */

export interface DerivationBasis {
  /** Exactly one of these is set — invariant №3, validated backend-side. */
  kind: "derivation_rule" | "authoritative_source" | "undeclared";
  description: string;
  authoritative: ReconciliationSource[];
  corroborating: ReconciliationSource[];
}

/**
 * Where the population came from. The degenerate case is a single
 * authoritative source; the general case is a derivation rule over several
 * (HANDOFF §2, D-5). Invariant №3 requires one or the other — `undeclared`
 * exists so a violation renders as a visible defect rather than an empty rail.
 */
export function derivationBasis(report: ReconciliationReport): DerivationBasis {
  const authoritative = report.sources.filter((s) => s.role === "authoritative");
  const corroborating = report.sources.filter((s) => s.role !== "authoritative");

  if (report.derivation_rule) {
    return {
      kind: "derivation_rule",
      description: report.derivation_rule.description,
      authoritative,
      corroborating,
    };
  }
  if (report.authoritative_source) {
    return {
      kind: "authoritative_source",
      description: `derives from ${report.authoritative_source.system} (${report.authoritative_source.ref}) as the authoritative source — the degenerate case of a derivation rule.`,
      authoritative,
      corroborating,
    };
  }
  return {
    kind: "undeclared",
    description:
      "no derivation rule and no authoritative source on the artifact — invariant №3 violated.",
    authoritative,
    corroborating,
  };
}

/* ------------------------------------------------------------------ */
/* Formatting                                                          */
/* ------------------------------------------------------------------ */

/** Date-only, UTC, locale-independent — the artifact's periods are day
 * boundaries and a locale-formatted string would differ between the server
 * render and the client hydration. */
export function formatPeriodDay(iso: string): string {
  return iso.slice(0, 10);
}

export function formatPeriod(period: { start: string; end: string }): string {
  return `${formatPeriodDay(period.start)} → ${formatPeriodDay(period.end)}`;
}
