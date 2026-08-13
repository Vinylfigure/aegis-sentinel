/* Engagement-artifact types — the REAL pipeline output shapes.
 *
 * Mirrored 1:1 from artifacts/demo-engagement/*.json as emitted by
 * scripts/emit_demo_artifacts.py (VAL02) against the frozen schemas
 * (capability-entry SCH02, reconciler DeltaObject REC01, verdict-record
 * SCH01). Field names are EXACT (snake_case). Drift protection:
 * src/lib/types/checks.ts asserts assignability against the codegen
 * output in src/lib/types/generated/.
 */

import type {
  AssuranceState,
  DispositionValue,
  Period,
  Population,
  PopulationType,
  VerdictRecord,
  VerdictState,
} from "@/lib/types/ontology";

/* ------------- capability registry (SCH02, capability-entry@0.1.0) ------- */

export const ACCESS_MODES = [
  "DIRECT_API",
  "OFFICIAL_MCP",
  "COMMUNITY_MCP",
  "CUSTOM_ADAPTER",
  "PLAYWRIGHT",
] as const;
export type AccessMode = (typeof ACCESS_MODES)[number];

export const TEMPORAL_SHAPE_KINDS = [
  "STATE_ONLY",
  "EVENT_HISTORY",
  "FULL_HISTORY",
  "SNAPSHOT_CADENCE",
] as const;
export type TemporalShapeKind = (typeof TEMPORAL_SHAPE_KINDS)[number];

export const PAGINATION_METHODS = ["CURSOR", "PAGE", "NONE"] as const;
export type PaginationMethod = (typeof PAGINATION_METHODS)[number];

export interface CapabilityTemporal {
  kind: TemporalShapeKind;
  /** Retention window in days — EVENT_HISTORY only; null otherwise. */
  window_days: number | null;
}

export interface CapabilityPagination {
  method: PaginationMethod;
  /** How the collector proves it drained every page. */
  exhaustion_method: string;
}

export interface PopulationYield {
  name: string;
  type: PopulationType;
}

export interface PopulationAttributes {
  population_name: string;
  fields_exposed: string[];
}

export interface SourceCitation {
  title: string;
  url: string;
}

export interface CapabilityProvenance {
  researched_by: string;
  researched_at: string;
  doc_version: string;
  ratified_by: string | null;
  source_citations: SourceCitation[];
}

export interface CapabilityEntry {
  entry_id: string;
  system: string;
  surface: string;
  access_modes: AccessMode[];
  populations_yielded: PopulationYield[];
  attributes: PopulationAttributes[];
  temporal: CapabilityTemporal;
  join_keys: string[];
  auth_scope: string;
  pagination: CapabilityPagination;
  rate_limits: string;
  history_caveats: string[];
  provenance: CapabilityProvenance;
  schema_version: string;
}

export interface CapabilityRegistryFile {
  entries: CapabilityEntry[];
}

/* ---------------- compile errors (TYP01 E-codes) ---------------- */

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
  "conflicts",
  "unresolvable",
  "excluded",
] as const;
export type DeltaBucket = (typeof DELTA_BUCKETS)[number];

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
