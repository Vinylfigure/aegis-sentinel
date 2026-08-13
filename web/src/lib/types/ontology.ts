/* Ontology types — mirrored 1:1 from the backend pydantic models on
 * sch01/ontology (src/aegis_sentinel/schema/{population,claim,contract,
 * disposition,verdict}.py). Field names are EXACT (snake_case, as the
 * backend serializes them). Do not rename fields here — rename upstream
 * first, then re-mirror.
 *
 * Frontend-only additions are explicitly flagged with `verdict_id`
 * (see VerdictRecord) — everything else is a straight projection.
 */

/* ---------------- population.py ---------------- */

export const POPULATION_TYPES = ["ENTITY", "EVENT", "RELATIONSHIP"] as const;
export type PopulationType = (typeof POPULATION_TYPES)[number];

/** The assurance-state ladder (PRD-v3 §2), in ladder order. */
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
  "AUTHORITATIVE",
  "CONTRIBUTING",
  "CORROBORATING",
  "DISCOVERY",
  "EXCLUSION",
] as const;
export type SourceRole = (typeof SOURCE_ROLES)[number];

export interface Source {
  source_id: string;
  role: SourceRole;
}

export interface DerivationRule {
  rule_text: string;
  source_refs: string[];
}

/** Closed date interval (ISO dates). */
export interface Period {
  start: string;
  end: string;
}

export interface Exclusion {
  member_id: string;
  rationale: string;
}

export interface OpenDeltaRef {
  delta_id: string;
  owner: string;
}

export interface Population {
  population_id: string;
  name: string;
  type: PopulationType;
  definition: string;
  derivation_rule: DerivationRule;
  sources: Source[];
  period: Period;
  size: number | null;
  exclusions: Exclusion[];
  open_deltas: OpenDeltaRef[];
  state: AssuranceState;
}

/* ---------------- claim.py ---------------- */

export const ASSERTION_TYPES = [
  "STATE",
  "EVENT",
  "SEQUENCE",
  "AGGREGATE",
  "EXISTENCE",
  "NON_EXISTENCE",
  "TIMING",
] as const;
export type AssertionType = (typeof ASSERTION_TYPES)[number];

export interface FrameworkMapping {
  framework: string;
  control_id: string;
}

export interface Assertion {
  assertion_id: string;
  claim_ref: string;
  type: AssertionType;
  predicate_text: string;
  population_ref: string;
}

export interface Claim {
  claim_id: string;
  statement: string;
  population_ref: string;
  framework_mappings: FrameworkMapping[];
  assertions: Assertion[];
}

/* ---------------- contract.py ---------------- */

export interface QualityProperty {
  method: string;
}

export interface Parameter {
  name: string;
  value: string;
}

export interface EvidenceQualityContract {
  source_system: string;
  tenant: string;
  population_ref: string;
  endpoint: string;
  parameters: Parameter[];
  time_window: Period;
  schema_version: string;
  collector_version: string;
  retrieved_at: string | null;
  auth_context: string;
  contract_hash: string | null;
  provenance: QualityProperty;
  integrity: QualityProperty;
  population: QualityProperty;
  semantics: QualityProperty;
  temporal_validity: QualityProperty;
  supported_assertion_types: AssertionType[];
}

/* ---------------- verdict.py ---------------- */

export const VERDICT_STATES = [
  "PASS",
  "FAIL",
  "UNKNOWN",
  "EXCLUDED",
  "EXCEPTION",
] as const;
export type VerdictState = (typeof VERDICT_STATES)[number];

export const UNKNOWN_WHY_CODES = [
  "UNKNOWN_DISCOVERY",
  "UNKNOWN_OWNER",
  "UNKNOWN_POPULATION",
  "UNKNOWN_EVIDENCE",
  "UNKNOWN_TESTABILITY",
] as const;
export type UnknownWhyCode = (typeof UNKNOWN_WHY_CODES)[number];

export const D7_FAMILIES = [
  "basis_missing",
  "identity_fuzzy",
  "no_basis_anywhere",
] as const;
export type D7Family = (typeof D7_FAMILIES)[number];

/** D-U1 mapping: each D-7 cause family names exactly one why-code. */
export const D7_FAMILY_WHY: Record<D7Family, UnknownWhyCode> = {
  basis_missing: "UNKNOWN_EVIDENCE",
  identity_fuzzy: "UNKNOWN_POPULATION",
  no_basis_anywhere: "UNKNOWN_TESTABILITY",
};

export interface VerdictRecord {
  /** FRONTEND-ONLY route key. SCH01 has no verdict_id — record identity
   *  upstream is record_hash. Flagged for reconciliation with SCH01. */
  verdict_id: string;
  claim_ref: string;
  assertion_ref: string;
  population_ref: string;
  manifest_version: string;
  snapshot_hash: string;
  contract_hash: string;
  state: VerdictState;
  evaluated_at: string;
  message: string | null;
  why_code: UnknownWhyCode | null;
  d7_family: D7Family | null;
  ratification_ref: string | null;
  disposition_ref: string | null;
  evidence_refs: string[];
  record_hash: string | null;
}

/* ---------------- disposition.py ---------------- */

export const DISPOSITION_VALUES = [
  "IMPLEMENTED_LOCALLY",
  "INHERITED",
  "SHARED",
  "VENDOR_MANAGED",
  "COMPENSATING",
  "NA_WITH_RATIONALE",
] as const;
export type DispositionValue = (typeof DISPOSITION_VALUES)[number];

export interface Disposition {
  value: DispositionValue;
  rationale: string | null;
}
