/* Engagement-artifact types — the REAL pipeline output shapes.
 *
 * Mirrored 1:1 from artifacts/demo-engagement/*.json as emitted by
 * scripts/build_demo_engagement.py against the frozen schemas
 * (capability-entry SCH02, reconciler REC01, verdict-record SCH01).
 * Field names are EXACT (snake_case). Drift protection: src/lib/types/
 * checks.ts asserts assignability against the codegen output in
 * src/lib/types/generated/.
 *
 * These are the WIRE shapes (what artifacts/demo-engagement/*.json
 * actually contains), which are distinct from the ontology's own pydantic
 * objects in ./ontology.ts — see that file's header.
 */

import type {
  AssuranceState,
  DispositionValue,
  Period,
  Population,
  PopulationType,
  UnknownWhy,
  VerdictState,
} from "@/lib/types/ontology";

/* ------------- shared wire fragments ------------- */

/** ISO-8601 timestamp string (artifacts serialize datetimes as strings). */
export type IsoDateTime = string;

/** Lowercase 64-char hex sha256. */
export type Sha256 = string;

/** Severity vocabulary per schemas/verdict-record.schema.json — independent
 * of status: a passing critical control still tells the consumer the
 * stakes. */
export const SEVERITIES = ["critical", "high", "medium", "low", "informational"] as const;
export type Severity = (typeof SEVERITIES)[number];

/* ------------- capability registry (SCH02, capability_entry@0.1.0) ------- */

export const ACCESS_MODES = [
  "direct-api",
  "official-mcp",
  "community-mcp",
  "custom-adapter",
  "playwright",
] as const;
export type AccessMode = (typeof ACCESS_MODES)[number];

export const TEMPORAL_KINDS = [
  "state-only",
  "event-history",
  "full-history",
  "snapshot-cadence",
] as const;
export type TemporalKind = (typeof TEMPORAL_KINDS)[number];

export const PAGINATION_METHODS = ["cursor", "page", "none"] as const;
export type PaginationMethod = (typeof PAGINATION_METHODS)[number];

/** D-L1: ratification IS the freeze. */
export const LIFECYCLE_STATES = ["draft", "frozen", "superseded"] as const;
export type LifecycleState = (typeof LIFECYCLE_STATES)[number];

export interface CapabilityTemporal {
  kind: TemporalKind;
  /** Retention window in days — event-history only; null otherwise. */
  window_days: number | null;
  cadence: string | null;
}

export interface CapabilityPagination {
  method: PaginationMethod;
  /** How the collector proves it drained every page. */
  exhaustion_method: string;
}

export interface CapabilityPopulationYield {
  type: PopulationType;
  description: string;
  attributes: string[];
}

export interface CapabilityProvenance {
  researched_by: string;
  researched_at: string;
  doc_version: string | null;
  /** Cartographer's whole authority — citations, never annexation. */
  citations: string[];
}

export interface CapabilityEntry {
  id: string;
  system: string;
  surface: string;
  access_modes: AccessMode[];
  populations_yielded: CapabilityPopulationYield[];
  temporal: CapabilityTemporal;
  join_keys: string[];
  auth_scope: string;
  pagination: CapabilityPagination;
  provenance: CapabilityProvenance;
  rate_limits: string | null;
  ratified_by: string | null;
  lifecycle: LifecycleState;
  history_caveats: string[];
}

export interface CapabilityRegistryFile {
  entries: CapabilityEntry[];
}

/* ---------------- compile errors (TYP01 E-codes) ----------------
 * Compiler-output text, never a pydantic model — no backend schema exists
 * for this shape, so it stays local-only/unchecked in checks.ts. */

export interface CompileError {
  code: "E204" | "E117" | "E302";
  message: string;
  /** The exact compiler-output line — render verbatim. */
  rendered: string;
  claim_ref: string;
  /** null for claim-level errors (E117/E302); set for E204. */
  assertion_ref: string | null;
  /* E204 extras */
  capability_window_days?: number;
  required_window?: Period;
  satisfiable_via?: string[];
  /* E117 extras */
  missing_source?: string;
}

/* ---------------- reconciliation (REC01 DeltaObject) ---------------- */

export const DELTA_BUCKETS = [
  "intersection",
  "left_only",
  "right_only",
  "conflict",
  "unresolvable",
  "excluded",
] as const;
export type DeltaBucket = (typeof DELTA_BUCKETS)[number];

/** D-7 join-failure cause family — a pure function of `DeltaBucket`
 * (schema/models.py's `_D7_FAMILY_BY_BUCKET`). A `conflict` (and
 * `intersection`/`excluded`) carries no family: a conflict is a successful
 * join with disagreeing attributes (D-8), not a join failure. */
export const D7_FAMILIES = ["basis-missing", "identity-fuzzy", "no-basis-anywhere"] as const;
export type D7Family = (typeof D7_FAMILIES)[number];

/** REI mechanized: justification + owner + review date (PRD-v3 §2). */
export interface DeltaDisposition {
  value: DispositionValue;
  justification: string;
  owner: string;
  review_date: string;
}

export interface DeltaObject {
  delta_id: string;
  bucket: DeltaBucket;
  /** This delta's D-7 family, or null for conflict/intersection/excluded. */
  cause: D7Family | null;
  /** Canonical member identity (join-key value, e.g. employee_id or login). */
  member_key: string;
  display_name: string;
  /** Source ids where this member WAS observed. */
  sources_present: string[];
  /** Negative space: sources where this member was expected but absent. */
  sources_absent: string[];
  owner: string | null;
  disposition: DeltaDisposition | null;
  /** Ratified disposition record id (e.g. DISP-2026-102), human-issued. */
  disposition_ref: string | null;
}

export interface ReconciliationResult {
  population_ref: string;
  canonical_identity_keys: string[];
  /** Diagnostic member counts per source — a smell test, not evidence. */
  source_counts: Record<string, number>;
  deltas: DeltaObject[];
  /** Full bucket membership (canonical member keys), delta or not. */
  buckets: Record<DeltaBucket, string[]>;
  /** The reconciled population membership (canonical keys, sorted). */
  members: string[];
  /** Whether every declared source was collected to exhaustion. */
  basis_complete: boolean;
  basis_notes: string[];
  /** Non-blocking observations (out-of-scope identities, bot principals…). */
  diagnostics: string[];
  ladder_state: AssuranceState;
}

export interface ReconciliationFile {
  engagement: string;
  reconciliations: ReconciliationResult[];
}

export interface PopulationsFile {
  engagement: string;
  populations: Population[];
}

/* ---------------- verdicts bundle ---------------- */

export type SupportFieldValue = string | number | boolean | ReadonlyArray<string>;

export interface VerdictSupport {
  /** `| undefined` because tsc infers phantom `key?: undefined` props for
   * keys present in some JSON records but not others; consumers must
   * narrow on lookup anyway. */
  field_values: Record<string, SupportFieldValue | undefined>;
  record_hashes: Sha256[];
}

/**
 * One verdict record as emitted (verdicts.json entries and the records
 * embedded in poisons.json). Conditional fields follow D-V1/D-U1: UNKNOWN
 * carries unknown_cause, EXCLUDED carries ratification_ref, EXCEPTION
 * carries disposition_ref. This is the WIRE record — see ontology.ts's
 * `Verdict` for the ontology's own, differently-shaped compiled object.
 */
export interface VerdictRecord {
  /** The claim's Assertion this verdict evaluates, of the type actually
   * tested. */
  assertion_id: string;
  chain_prev: Sha256 | null;
  /** The Claim this verdict was evaluated against. */
  claim_id: string;
  collected_at: IsoDateTime;
  completeness_ref: string;
  control_id: string;
  /** Present only on EXCEPTION records. */
  disposition_ref?: string;
  evidence_refs: string[];
  /** Optional on the wire (schemas/verdict-record.schema.json required list). */
  message?: string;
  population_count: number;
  population_id: string;
  /** Present only on EXCLUDED records. */
  ratification_ref?: string;
  record_hash: Sha256;
  record_id: string;
  run_id: string;
  /** const-pinned by the wire schema; a version bump is a reviewed change. */
  schema_version: "0.1.0";
  /** Optional on the wire; independent of status. */
  severity?: Severity;
  source: string;
  source_version: string;
  spec_hash: Sha256;
  spec_id: string;
  status: VerdictState;
  /** Present when the record carries member-level supporting values. */
  support?: VerdictSupport;
  test_function_version: string;
  /** Present only on UNKNOWN records (D-U1). */
  unknown_cause?: UnknownWhy;
}

export interface VerdictsFile {
  engagement: string;
  manifest_version: string;
  verdicts: VerdictRecord[];
  compile_errors: CompileError[];
}

/* ---------------- proof graph (P1 lineage view) ---------------- */

export const PROOF_NODE_KINDS = [
  "commitment",
  "requirement",
  "claim",
  "population",
  "source",
  "reconciliation",
  "contract",
  "snapshot",
  "assertion",
  "verdict",
] as const;
export type ProofNodeKind = (typeof PROOF_NODE_KINDS)[number];

export interface ProofNode {
  node_id: string;
  kind: ProofNodeKind;
  label: string;
  /** Id of the underlying record (population_id, claim_id, hash…). */
  ref: string;
}

export interface ProofEdge {
  from: string;
  to: string;
  relation: string;
}

export interface ProofGraph {
  /** record_hash of the verdict this lineage proves. */
  verdict_ref: string;
  nodes: ProofNode[];
  edges: ProofEdge[];
}

/* ---------------- manifest + bundle ---------------- */

export interface ManifestSummary {
  claims: number;
  compile_error_codes: string[];
  populations_by_state: Partial<Record<AssuranceState, number>>;
  verdict_states_present: VerdictState[];
}

export interface EngagementManifest {
  manifest_version: string;
  snapshot_hash: string;
  ratified_by: string;
  ratified_at: string;
  engagement: string;
  period: Period;
  boundary: string;
  notes?: string;
  summary: ManifestSummary;
}

export interface EngagementArtifacts {
  manifest: EngagementManifest;
  capability_registry: CapabilityEntry[];
  populations: Population[];
  reconciliations: ReconciliationResult[];
  verdicts: VerdictRecord[];
  compile_errors: CompileError[];
  proof_graphs: ProofGraph[];
}
