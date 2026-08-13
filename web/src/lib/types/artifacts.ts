/* Engagement-artifact types — the mock bundle Phase B renders.
 *
 * Shapes not yet frozen upstream (Capability Registry entry is SCH02;
 * the reconciler's DeltaObject is REC01; the proof graph is the P1
 * lineage view). Field names follow the backend convention (snake_case)
 * and the PRD-v3 §3 capability-entry schema. Guessed fields are noted
 * inline for reconciliation against SCH01/SCH02/REC01.
 */

import type {
  Claim,
  DispositionValue,
  Period,
  Population,
  PopulationType,
  VerdictRecord,
} from "@/lib/types/ontology";

/* ---------------- capability registry (PRD-v3 §3 / SCH02) ---------------- */

export const ACCESS_MODES = [
  "direct-api",
  "official-mcp",
  "community-mcp",
  "custom-adapter",
  "playwright",
] as const;
export type AccessMode = (typeof ACCESS_MODES)[number];

export const TEMPORAL_SHAPES = [
  "state-only",
  "event-history",
  "full-history",
  "snapshot-cadence",
] as const;
export type TemporalShape = (typeof TEMPORAL_SHAPES)[number];

export interface CapabilityTemporal {
  shape: TemporalShape;
  /** Retention window in days — only for event-history. */
  window_days?: number;
  /** Cadence label — only for snapshot-cadence. */
  cadence?: string;
}

export interface PopulationYielded {
  type: PopulationType;
  name: string;
}

export interface CapabilityProvenance {
  researched_by: string;
  researched_at: string;
  doc_version: string;
  ratified_by: string;
}

export interface CapabilityEntry {
  entry_id: string;
  system: string;
  surface: string;
  access_modes: AccessMode[];
  populations_yielded: PopulationYielded[];
  attributes: string[];
  temporal: CapabilityTemporal;
  join_keys: string[];
  auth_scope: string;
  pagination: "cursor" | "page" | "none";
  rate_limits?: string;
  history_caveats: string[];
  provenance: CapabilityProvenance;
}

/* ---------------- compile errors (PRD-v3 §3) ---------------- */

export interface ECode {
  code: "E204" | "E117" | "E302";
  message: string;
  suggestion?: string;
  /** Where the error was raised — guessed refs, pending SCH02. */
  claim_ref?: string;
  assertion_ref?: string;
}

/* ---------------- reconciliation (REC01 — shape guessed) ---------------- */

export const DELTA_BUCKETS = [
  "intersection",
  "left_only",
  "right_only",
  "conflicts",
  "unresolvable",
  "excluded",
] as const;
export type DeltaBucket = (typeof DELTA_BUCKETS)[number];

/** REI mechanized: justification + owner + review date (PRD-v3 §2).
 *  Backend Disposition is {value, rationale}; this richer shape is the
 *  delta-disposition guess for REC01. */
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
  display_name?: string;
  /** Source ids where this member WAS observed. */
  sources_present: string[];
  /** Negative space: sources where this member was expected but absent. */
  sources_absent: string[];
  owner?: string;
  disposition?: DeltaDisposition;
}

export interface ReconciliationResult {
  population_ref: string;
  canonical_identity_keys: string[];
  /** Diagnostic member counts per source — a smell test, not evidence. */
  source_counts: Record<string, number>;
  deltas: DeltaObject[];
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
  verdict_ref: string;
  nodes: ProofNode[];
  edges: ProofEdge[];
}

/* ---------------- manifest + bundle ---------------- */

export interface EngagementManifest {
  manifest_version: string;
  snapshot_hash: string;
  ratified_by: string;
  ratified_at: string;
  engagement: string;
  period: Period;
  boundary: string;
  notes?: string;
}

export interface EngagementArtifacts {
  manifest: EngagementManifest;
  capability_registry: CapabilityEntry[];
  populations: Population[];
  reconciliations: ReconciliationResult[];
  claims: Claim[];
  verdicts: VerdictRecord[];
  compile_errors: ECode[];
  proof_graphs: ProofGraph[];
}
