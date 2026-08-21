/**
 * HAND-AUTHORED ontology + artifact types (B1).
 *
 * These mirror two primary sources, by hand:
 *  - the ratified ontology enums in `src/aegis_sentinel/schema/enums.py`
 *    (string-literal unions below match the Python enum VALUES exactly), and
 *  - the artifact shapes emitted into `artifacts/demo-engagement/`
 *    (verdicts.json, reconciliation.json, registry.json, poisons.json).
 *
 * C1 replaces this file with codegen from the pydantic JSON-Schema export
 * plus assignability checks; until then, drift between these types and the
 * backend is caught only by eyeball and by `web/src/data/index.ts` importing
 * the mock engagement JSON through them.
 *
 * Conventions: artifact-facing types use snake_case keys (the wire shape is
 * the backend's, kept verbatim — divergence questions live in web/README.md
 * under "SCH01/REC01 shape review questions"). Seed types (prototype-ported
 * demo data, frontend-native) use camelCase.
 */

/* ------------------------------------------------------------------ */
/* Ontology enums (schema/enums.py) as string-literal unions           */
/* ------------------------------------------------------------------ */

export type PopulationType = "entity" | "event" | "relationship";

/** The assurance-state ladder. Coverage is never computed against a
 * denominator left of RATIFIED. */
export type AssuranceState =
  | "UNDEFINED"
  | "DEFINED"
  | "DISCOVERED"
  | "RECONCILED"
  | "RATIFIED"
  | "STALE";

export type SourceRole =
  | "authoritative"
  | "contributing"
  | "corroborating"
  | "discovery"
  | "exclusion";

/** Note the ratified spelling "NON-EXISTENCE" (hyphen, not underscore). */
export type AssertionType =
  | "STATE"
  | "EVENT"
  | "SEQUENCE"
  | "AGGREGATE"
  | "EXISTENCE"
  | "NON-EXISTENCE"
  | "TIMING";

/** The five ratified verdict states (D-V1), never interchangeable. */
export type VerdictState = "PASS" | "FAIL" | "UNKNOWN" | "EXCLUDED" | "EXCEPTION";

/** UNKNOWN why-codes (D-U1). */
export type UnknownWhy =
  | "UNKNOWN_DISCOVERY"
  | "UNKNOWN_OWNER"
  | "UNKNOWN_POPULATION"
  | "UNKNOWN_EVIDENCE"
  | "UNKNOWN_TESTABILITY";

export type DispositionValue =
  | "implemented"
  | "inherited"
  | "shared"
  | "vendor_managed"
  | "compensating"
  | "not_applicable";

/** Set-based reconciliation buckets — counts are diagnostics, never evidence. */
export type DeltaBucket =
  | "intersection"
  | "left_only"
  | "right_only"
  | "conflict"
  | "unresolvable"
  | "excluded";

/** D-L1: ratification IS the freeze. */
export type LifecycleState = "draft" | "frozen" | "superseded";

/* ------------------------------------------------------------------ */
/* Shared artifact fragments                                           */
/* ------------------------------------------------------------------ */

/** ISO-8601 timestamp string (artifacts serialize datetimes as strings). */
export type IsoDateTime = string;

/** Lowercase 64-char hex sha256 (SHA256 pattern in schema/models.py). */
export type Sha256 = string;

export interface TimeWindow {
  start: IsoDateTime;
  end: IsoDateTime;
}

/** Severity vocabulary per schemas/verdict-record.schema.json (answers README
 * Q7 — the wire schema carried the ratified set all along; the earlier
 * three-value guess was wrong). */
export type Severity =
  | "critical"
  | "high"
  | "medium"
  | "low"
  | "informational";

/* ------------------------------------------------------------------ */
/* verdicts.json — array of VerdictRecord                              */
/* ------------------------------------------------------------------ */

export type SupportFieldValue =
  | string
  | number
  | boolean
  | ReadonlyArray<string>;

export interface VerdictSupport {
  /** `| undefined` because tsc infers phantom `key?: undefined` props for
   * keys present in some JSON records but not others; consumers must
   * narrow on lookup anyway. */
  field_values: Record<string, SupportFieldValue | undefined>;
  record_hashes: Sha256[];
}

/**
 * One verdict record as emitted (verdicts.json entries and the records
 * embedded in poisons.json). Conditional fields follow D-V1/D-U1:
 * UNKNOWN carries unknown_cause, EXCLUDED carries ratification_ref,
 * EXCEPTION carries disposition_ref (see README questions Q1/Q2 on the
 * naming drift vs. schema/models.py Verdict).
 */
export interface VerdictRecord {
  chain_prev: Sha256 | null;
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

/** verdicts.json is a bare array — no run envelope (README question Q3). */
export type VerdictsArtifact = VerdictRecord[];

/* ------------------------------------------------------------------ */
/* reconciliation.json — one population's ReconciliationReport         */
/* ------------------------------------------------------------------ */

export interface DispositionRecord {
  owner: string;
  rationale: string | null;
  value: DispositionValue;
}

/** A reconciliation difference as a first-class object — never just a count. */
export interface Delta {
  bucket: DeltaBucket;
  disposition: DispositionRecord | null;
  member_ref: string;
  owner: string | null;
}

export interface BoundaryExclusion {
  /** Bare identifier — buckets use prefixed member_ref (README question Q6). */
  member: string;
  ratified_by: string;
  ref: string;
}

export interface SourceMember {
  /** See VerdictSupport.field_values on `| undefined`. */
  attributes: Record<string, string | undefined>;
  email: string;
  ref: string;
}

export interface ReconciliationSource {
  members: SourceMember[];
  name: string;
  role: SourceRole;
}

/** Mirrors `SourceRef` in schema/models.py. */
export interface SourceRef {
  ref: string;
  role: SourceRole;
  system: string;
}

/** Mirrors `DerivationRule` in schema/models.py — the general case; an
 * authoritative source is the degenerate case (HANDOFF §2, D-5). */
export interface DerivationRule {
  description: string;
  sources: SourceRef[];
}

export interface ReconciliationLadder {
  after_dispositions: AssuranceState;
  at_first_verdict: AssuranceState;
  blocked_by_open_deltas: string[];
}

export interface ReconciliationReport {
  /** Invariant №3: exactly one of `derivation_rule` / `authoritative_source`
   * is non-null (validated backend-side in schema/models.py). */
  authoritative_source: SourceRef | null;
  boundary_exclusions: BoundaryExclusion[];
  /** All six DeltaBucket keys are present, each possibly empty. */
  buckets: Record<DeltaBucket, Delta[]>;
  canonical_members: string[];
  counts: Record<DeltaBucket, number>;
  counts_note: string;
  definition: string;
  derivation_rule: DerivationRule | null;
  /** Keyed by member_ref. Records the human disposition act; the bucket-inline
   * field is the pre-disposition snapshot of the same delta (README Q5). */
  dispositions: Record<string, DispositionRecord>;
  ladder: ReconciliationLadder;
  period: TimeWindow;
  population_id: string;
  population_name: string;
  population_type: PopulationType;
  sources: ReconciliationSource[];
  tenant: string;
}

/* ------------------------------------------------------------------ */
/* registry.json — capability entries + compile errors                 */
/* ------------------------------------------------------------------ */

/** Compiler-error shape (E-codes, e.g. E117). */
export interface CompileError {
  claim_id: string;
  code: string;
  message: string;
  suggestion: string | null;
}

/** Ontology per capability_entry.schema.json $defs (answers README Q8). */
export type PaginationMethod = "cursor" | "page" | "none";

/** Temporal capability vocabulary — not in schema/enums.py (README Q8). */
/** Ontology per capability_entry.schema.json $defs (answers README Q8) —
 * including `snapshot-cadence`, which the hand-authored guess had missed. */
export type TemporalKind =
  | "state-only"
  | "event-history"
  | "full-history"
  | "snapshot-cadence";

export interface RegistryPagination {
  exhaustion_method: string;
  method: PaginationMethod;
}

export interface RegistryPopulationYielded {
  attributes: string[];
  description: string;
  type: PopulationType;
}

export interface RegistryProvenance {
  citations: string[];
  doc_version: string | null;
  researched_at: IsoDateTime;
  researched_by: string;
}

export interface RegistryTemporal {
  cadence: string | null;
  kind: TemporalKind;
  window_days: number | null;
}

export interface RegistryEntry {
  access_modes: string[];
  auth_scope: string;
  history_caveats: string[];
  id: string;
  join_keys: string[];
  lifecycle: LifecycleState;
  pagination: RegistryPagination;
  populations_yielded: RegistryPopulationYielded[];
  provenance: RegistryProvenance;
  rate_limits: string | null;
  ratified_by: string | null;
  surface: string;
  system: string;
  temporal: RegistryTemporal;
}

export interface RegistryArtifact {
  compile_errors: CompileError[];
  entries: RegistryEntry[];
  /** DEMO-ONLY caveat — /registry must render it verbatim (see web/README.md). */
  note: string;
}

/* ------------------------------------------------------------------ */
/* contracts.json — the Evidence Quality Contracts (Q14, issue #48)    */
/* ------------------------------------------------------------------ */

export interface QualityProperty {
  method: string;
  failure_mode: string;
}

/** The five EQC properties: each an independent named method with an
 * independent failure mode (schema: evidence_quality_contract.schema.json). */
export interface EvidenceQuality {
  provenance: QualityProperty;
  integrity: QualityProperty;
  population: QualityProperty;
  semantics: QualityProperty;
  temporal_validity: QualityProperty;
}

export interface EvidenceQualityContract {
  id: string;
  source: string;
  tenant: string;
  population_ref: string;
  endpoint: string;
  parameters: Record<string, string>;
  time_window: TimeWindow;
  schema_version: string;
  collector_version: string;
  auth_context: string;
  contract_hash: string;
  quality: EvidenceQuality;
  supported_assertion_types: AssertionType[];
}

/** Keyed by contract_hash — every emitted verdict record's `spec_hash` IS
 * a key into this map (build_demo_engagement.py). */
export type ContractsArtifact = Record<string, EvidenceQualityContract>;

/* ------------------------------------------------------------------ */
/* poisons.json — mutation scorecard                                   */
/* ------------------------------------------------------------------ */

export type PoisonStage = "compile" | "evaluate";

/** What the pipeline actually produced for a poison: a verdict record or a
 * compile error batch (discriminated on `kind`). */
export type PoisonActual =
  | { kind: "verdict"; record: VerdictRecord }
  | { kind: "compile_error"; errors: CompileError[] };

/** Free-form pointer(s) at the poisoned element — the key set varies per
 * case in the artifact (README question Q4). Known keys so far: */
export interface PoisonEvidence {
  bucket?: string;
  member_ref?: string;
  member?: string;
  login?: string;
  population?: string;
  system?: string;
}

export interface PoisonCase {
  actual: PoisonActual;
  /** Classification string: a VerdictState, "UNKNOWN:<UnknownWhy>", or an
   * E-code — stringly-typed on the wire (README question Q4). */
  actual_class: string;
  detected: boolean;
  evidence: PoisonEvidence;
  expected: string;
  id: string;
  poison: string;
  stage: PoisonStage;
}

export interface PoisonDetection {
  detected: number;
  detection_rate: number;
  misses: string[];
  total: number;
}

/** Grouping keys for the embedded verdict records — lower-snake assertion
 * families, not AssertionType values (README question Q4b). */
export type PoisonVerdictGroup = "existence" | "non_existence" | "timing";

export interface PoisonsArtifact {
  cases: PoisonCase[];
  collected_at: IsoDateTime;
  control_id: string;
  detection: PoisonDetection;
  period: TimeWindow;
  project: string;
  run_id: string;
  tenant: string;
  verdict_records: Record<PoisonVerdictGroup, VerdictRecord[]>;
}

/* ------------------------------------------------------------------ */
/* Seed data (A2): prototype-ported demo data, frontend-native shapes  */
/* ------------------------------------------------------------------ */

/* -- scope.json -- */

export type ScopeResolution = "in" | "unknown" | "out";

export interface SeedDataClass {
  id: string;
  name: string;
  note: string;
  tier: string;
}

export interface SeedProduct {
  id: string;
  name: string;
  description: string;
  /** SeedDataClass ids this product carries. */
  dataClasses: string[];
  /** Default selection state in the demo walkthrough. */
  inScope: boolean;
}

export interface SeedRegime {
  id: string;
  name: string;
  why: string;
  /** SeedDataClass ids that light this regime up. */
  triggeredBy: string[];
}

export interface SeedAssetItem {
  name: string;
  prompt: string;
}

export interface SeedAssetLayer {
  name: string;
  items: SeedAssetItem[];
}

export interface SeedSystem {
  id: string;
  name: string;
  category: string;
  scope: ScopeResolution;
}

export interface ScopeSeed {
  company: {
    id: string;
    name: string;
    description: string;
  };
  products: SeedProduct[];
  dataClasses: SeedDataClass[];
  regimes: SeedRegime[];
  assetLayers: SeedAssetLayer[];
  systems: SeedSystem[];
}

/* -- controls.json -- */

export type ControlNature = "cfg" | "auto" | "manual";
export type ControlFunction = "prev" | "det";
export type RetrievalChannel = "api" | "shot" | "log" | "man";
export type CaMethod = "recon" | "hash" | "trace" | "agent";

export interface SeedControlDataset {
  /** SeedSystem id the dataset is collected from. */
  system: string;
  artifact: string;
  retrieval: RetrievalChannel;
  caMethod: CaMethod;
}

export interface SeedControl {
  id: string;
  name: string;
  domain: string;
  description: string;
  nature: ControlNature;
  function: ControlFunction;
  compensating: boolean;
  /** SeedSystem ids the control operates over. */
  systems: string[];
  datasets: SeedControlDataset[];
}

export interface SeedLlmTask {
  id: string;
  name: string;
  boundary: string;
}

export interface ControlsSeed {
  controls: SeedControl[];
  retrievalChannels: Record<RetrievalChannel, string>;
  caMethods: Record<CaMethod, string>;
  /** LLM lane sits above the verdict path — never verdicts. */
  llmLane: SeedLlmTask[];
}

/* -- process.json -- */

/** Data tier tint on process nodes: 1 regulated, 2 confidential, 3 internal. */
export type ProcessTier = 1 | 2 | 3;

export interface ProcessNode {
  key: string;
  label: string;
  sublabel: string;
  tier: ProcessTier;
}

export interface ProcessLink {
  label: string;
  href: string;
}

export interface ProcessControlPoint {
  /** Engagement surfaces wired to this point (C2). Optional and honest:
   * points whose artifacts do not exist yet carry none. */
  links?: ProcessLink[];
  id: string;
  name: string;
  nature: ControlNature;
  function: ControlFunction;
  enforces: string;
  dataElement: string;
  api: string;
  evidence: string;
  completenessAccuracy: string;
  gap: string | null;
  /** spec_ids of engagement VerdictRecords this gate's live health is
   * derived from (issue #43). Explicit and honest, like `links` above —
   * the seed carries no generic point→record mapping (adjacency guesses
   * are wrong here: two points can share flanking systems yet test
   * different specs). Points without artifacts to show carry none. */
  verdictSpecIds?: string[];
  /** claim_ids of registry CompileErrors that gate this point. */
  compileErrorClaimIds?: string[];
}

export type ProcessStep =
  | { kind: "node"; node: ProcessNode }
  | { kind: "controlPoint"; controlPoint: ProcessControlPoint };

export interface ProcessLane {
  id: string;
  name: string;
  subtitle: string;
  sequence: ProcessStep[];
}

export interface ProcessSeed {
  context: {
    product: string;
    tiers: { id: ProcessTier; label: string }[];
  };
  lanes: ProcessLane[];
}

/* -- gauges.json -- */

export type GaugeTone = "green" | "amber" | "purple" | "cyan" | "red";
export type GaugeKind = "count" | "percent" | "ratio";

export interface SeedGauge {
  id: string;
  label: string;
  tone: GaugeTone;
  kind: GaugeKind;
  /** Derivation key the page computes the live value from. */
  metric: string;
  showBar: boolean;
}

export interface SeedGaugeSection {
  title: string;
  gauges: SeedGauge[];
}

export interface GaugesSeed {
  sections: SeedGaugeSection[];
}
