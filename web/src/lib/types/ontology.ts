/* Ontology types — mirrored 1:1 from the backend pydantic models
 * (src/aegis_sentinel/schema/{models,enums}.py), via their JSON Schema
 * export under schemas/ontology/*.schema.json. Field names are EXACT
 * (snake_case, as the backend serializes them). Do not rename fields
 * here — rename upstream first, then re-mirror.
 *
 * These are the ontology's own objects (Population, Claim, Assertion,
 * EvidenceQualityContract, Disposition, the compiled Verdict) — NOT the
 * wire artifacts the pipeline emits into artifacts/demo-engagement/
 * (verdicts.json's VerdictRecord, reconciliation.json's
 * ReconciliationResult, etc.), which have their own distinct shapes in
 * ./artifacts.ts.
 *
 * Drift protection: src/lib/types/checks.ts asserts assignability
 * between these mirrors and the codegen output in
 * src/lib/types/generated/ (from schemas/**\/*.schema.json) — a backend
 * rename or enum change fails `tsc` here.
 */

/* ---------------- population.py ---------------- */

export const POPULATION_TYPES = ["entity", "event", "relationship"] as const;
export type PopulationType = (typeof POPULATION_TYPES)[number];

/** The assurance-state ladder. Coverage is never computed against a
 * denominator left of RATIFIED. */
export const ASSURANCE_STATES = [
  "UNDEFINED",
  "DEFINED",
  "DISCOVERED",
  "RECONCILED",
  "RATIFIED",
  "STALE",
] as const;
export type AssuranceState = (typeof ASSURANCE_STATES)[number];

export const SOURCE_ROLES = [
  "authoritative",
  "contributing",
  "corroborating",
  "discovery",
  "exclusion",
] as const;
export type SourceRole = (typeof SOURCE_ROLES)[number];

export interface SourceRef {
  system: string;
  role: SourceRole;
  ref: string;
}

export interface DerivationRule {
  description: string;
  sources: SourceRef[];
}

/** Closed date/time interval. */
export interface Period {
  start: string;
  end: string;
}

export const DELTA_BUCKETS = [
  "intersection",
  "left_only",
  "right_only",
  "conflict",
  "unresolvable",
  "excluded",
] as const;
export type DeltaBucket = (typeof DELTA_BUCKETS)[number];

export const DISPOSITION_VALUES = [
  "implemented",
  "inherited",
  "shared",
  "vendor_managed",
  "compensating",
  "not_applicable",
] as const;
export type DispositionValue = (typeof DISPOSITION_VALUES)[number];

/** Nothing exits silently: `not_applicable` demands a rationale (enforced
 * backend-side, not structurally here). */
export interface Disposition {
  value: DispositionValue;
  rationale: string | null;
  owner: string;
}

/** A reconciliation difference as a first-class object with an owner and
 * a disposition — never just a count. */
export interface Delta {
  bucket: DeltaBucket;
  member_ref: string;
  owner: string | null;
  disposition: Disposition | null;
}

export interface Population {
  id: string;
  name: string;
  type: PopulationType;
  definition: string;
  period: Period;
  /** Invariant: exactly one of derivation_rule / authoritative_source is
   * non-null — the general case vs. the degenerate case (HANDOFF §2, D-5). */
  derivation_rule: DerivationRule | null;
  authoritative_source: SourceRef | null;
  size: number | null;
  exclusions: string[];
  deltas: Delta[];
  state: AssuranceState;
}

/* ---------------- claim.py ---------------- */

/** Note the ratified spelling "NON-EXISTENCE" (hyphen, not underscore). */
export const ASSERTION_TYPES = [
  "STATE",
  "EVENT",
  "SEQUENCE",
  "AGGREGATE",
  "EXISTENCE",
  "NON-EXISTENCE",
  "TIMING",
] as const;
export type AssertionType = (typeof ASSERTION_TYPES)[number];

export interface TimingConstraint {
  days: number;
  business_days: boolean;
}

/** A lettered, typed, testable attribute of a claim. The type constrains
 * admissible evidence; TIMING must say its window. */
export interface Assertion {
  id: string;
  type: AssertionType;
  description: string;
  attribute: string | null;
  timing: TimingConstraint | null;
}

/** Invariants: no verdict without a claim; no claim without a defined
 * population (structural: population_id is required). */
export interface Claim {
  id: string;
  statement: string;
  population_id: string;
  assertions: Assertion[];
  framework_refs: string[];
}

/* ---------------- contract.py (evidence quality contract) ---------------- */

export interface QualityProperty {
  method: string;
  failure_mode: string;
}

/** The five EQC properties: each an independent named method with an
 * independent failure mode. */
export interface EvidenceQuality {
  provenance: QualityProperty;
  integrity: QualityProperty;
  population: QualityProperty;
  semantics: QualityProperty;
  temporal_validity: QualityProperty;
}

/** Full identity plus the five properties; a contract declares which
 * assertion types it is entitled to support (invariant: no PASS unless
 * the evidence is fit to prove the claim). */
export interface EvidenceQualityContract {
  id: string;
  source: string;
  tenant: string;
  population_ref: string;
  endpoint: string;
  parameters: Record<string, string>;
  time_window: Period;
  schema_version: string;
  collector_version: string;
  auth_context: string;
  contract_hash: string;
  quality: EvidenceQuality;
  supported_assertion_types: AssertionType[];
}

/* ---------------- verdict.py ---------------- */

/** The five ratified verdict states (D-V1), never interchangeable. */
export const VERDICT_STATES = ["PASS", "FAIL", "UNKNOWN", "EXCLUDED", "EXCEPTION"] as const;
export type VerdictState = (typeof VERDICT_STATES)[number];

/** UNKNOWN why-codes (D-U1). */
export const UNKNOWN_WHY_CODES = [
  "UNKNOWN_DISCOVERY",
  "UNKNOWN_OWNER",
  "UNKNOWN_POPULATION",
  "UNKNOWN_EVIDENCE",
  "UNKNOWN_TESTABILITY",
] as const;
export type UnknownWhy = (typeof UNKNOWN_WHY_CODES)[number];

/**
 * The ontology's own compiled Verdict model (schemas/ontology/verdict.schema.json)
 * — the abstract object the ten-stage lineage's "evaluates to" arrow points
 * at. This is NOT the wire VerdictRecord artifact verdicts.json emits
 * (see ./artifacts.ts): the two are different shapes for the same concept
 * (this file's Verdict uses `state`/`unknown_why`/`exception_disposition_ref`;
 * the wire record uses `status`/`unknown_cause`/`disposition_ref` and carries
 * many more reproducibility/identity fields). Deliberately no assignability
 * assertion between them in checks.ts — asserting them equal would paper
 * over exactly that divergence.
 */
export interface Verdict {
  state: VerdictState;
  message: string | null;
  unknown_why: UnknownWhy | null;
  ratification_ref: string | null;
  exception_disposition_ref: string | null;
}
