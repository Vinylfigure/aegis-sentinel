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
  Delta,
  DerivationRule,
  Disposition,
  Period,
  Population,
  PopulationType,
  SourceRef,
  SourceRole,
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

/** Registry file as emitted (`registry.json`): ratified/draft entries plus
 * the compiler's own E-code findings against them (TYP01). */
export interface RegistryFile {
  entries: CapabilityEntry[];
  compile_errors: CompileError[];
  note?: string;
}

/* ---------------- compile errors (TYP01 E-codes) ----------------
 * Mirrored from compile/checker.py's CompileError — a pydantic model, but
 * one that carries compiler text rather than a domain object, and one
 * whose `code` is pattern-validated (`^E\d{3}$`) rather than a closed enum
 * on the backend, so it stays a plain string here too. Known codes today:
 * E117 (no usable capability for a derivation source), E118 (usable but
 * not manifest-granted), E204 (temporal insufficiency), E302 (schema-
 * version drift). No backend JSON Schema is generated for it (compiler
 * output, not `schema/models.py`), so it stays local-only/unchecked in
 * checks.ts. */

export interface CompileError {
  code: string;
  claim_id: string;
  message: string;
  suggestion: string | null;
}

/* ---------------- reconciliation (REC01 SetReconcileResult) ----------------
 * Mirrored from reconcile/engine.py's `reconcile_sets()` output as
 * serialized into `reconciliation.json` by
 * scripts/build_demo_engagement.py — one report per population (today's
 * demo engagement emits exactly one, for pop-termination-events). This
 * replaces an earlier, unverified shape (`ReconciliationResult`/
 * `DeltaObject` with invented fields like `canonical_identity_keys`/
 * `basis_complete`/`member_key`) that matched neither this wire artifact
 * nor any backend schema — see issue #162. */

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

/** One source's raw member view before reconciliation (`SourceMember` in
 * engine.py): a join-key email plus whatever attributes that source
 * asserts, compared across sources for CONFLICT detection. */
export interface ReconciliationSourceMember {
  ref: string;
  email: string;
  attributes: Record<string, string>;
}

/** One named member-set with its source role (`SourceSet` in engine.py).
 * `capability_id` is null for sources with no registry entry (e.g. a
 * ticketing system used only as corroborating evidence). */
export interface ReconciliationSource {
  name: string;
  role: SourceRole;
  capability_id: string | null;
  members: ReconciliationSourceMember[];
}

/** A ratified boundary exclusion (`BoundaryExclusion` in engine.py) — the
 * human act happened upstream; this only records the ref (D-9). */
export interface BoundaryExclusion {
  member: string;
  ref: string;
  ratified_by: string;
}

/** One bucket entry naming a delta still blocking the ladder before its
 * disposition, or having already been dispositioned. */
export interface LadderBlockedDelta {
  bucket: DeltaBucket;
  cause: D7Family | null;
  ref: string;
  dispositioned: boolean;
}

export interface ReconciliationLadder {
  at_first_verdict: AssuranceState;
  after_dispositions: AssuranceState;
  blocked_by_open_deltas: LadderBlockedDelta[];
}

/** One population's full reconciliation report, as `reconciliation.json`
 * emits it. `buckets`/`counts` are keyed by every `DeltaBucket`; `deltas`
 * inside `population.deltas` (ontology.ts) is the same objects minus
 * `intersection` (engine.py only attaches open questions + EXCLUDED). */
export interface ReconciliationReport {
  population_id: string;
  population_name: string;
  population_type: PopulationType;
  definition: string;
  derivation_rule: DerivationRule | null;
  authoritative_source: SourceRef | null;
  period: Period;
  tenant: string;
  sources: ReconciliationSource[];
  canonical_members: string[];
  buckets: Record<DeltaBucket, Delta[]>;
  /** Diagnostics only — never evidence (HANDOFF §2). */
  counts: Record<DeltaBucket, number>;
  counts_note: string;
  dispositions: Record<string, Disposition>;
  ladder: ReconciliationLadder;
  boundary_exclusions: BoundaryExclusion[];
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

/** `verdicts.json` is a bare array on the wire — no envelope, no
 * `compile_errors` alongside it (those live in `registry.json`, TYP01's
 * own output). No `VerdictsFile` wrapper type exists for the same reason
 * `PopulationsFile`/`ReconciliationFile` don't (issue #162): inventing an
 * envelope the backend never emits is exactly the drift this file exists
 * to catch, not reproduce. */

/** A commitment as `commitments.json` emits it (keyed by id) — a real
 * pydantic model (`schemas/ontology/commitment.schema.json`), not
 * derived; included here rather than ontology.ts because it is only
 * ever consumed as this wire bundle. */
export interface Commitment {
  id: string;
  name: string;
  source: string;
  obligation: string;
  claim_ids: string[];
}

export type CommitmentsFile = Record<string, Commitment>;

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

/** Mirrored from `manifest.py::ManifestSnapshot` / `snapshot.json` — the
 * ratified scope grant (D-L1: ratification IS the freeze), not the
 * invented `manifest_version`/`snapshot_hash`/`boundary`/`summary` shape
 * this replaces (issue #162; that shape matched no backend model or wire
 * file). */
export interface ManifestCollectorGrant {
  id: string;
  permissions: string[];
}

export interface ManifestBlocks {
  boundary: string[];
  capabilities: string[];
  claims: string[];
  collectors: ManifestCollectorGrant[];
  evidence_contracts: string[];
  populations: string[];
  tests: string[];
}

export interface ManifestSnapshot {
  version: number;
  lifecycle: LifecycleState;
  ratified_by: string | null;
  ratified_at: string | null;
  blocks: ManifestBlocks;
}

export interface EngagementArtifacts {
  manifest: ManifestSnapshot;
  capability_registry: CapabilityEntry[];
  commitments: CommitmentsFile;
  populations: Population[];
  reconciliations: ReconciliationReport[];
  verdicts: VerdictRecord[];
  compile_errors: CompileError[];
  proof_graphs: ProofGraph[];
}
