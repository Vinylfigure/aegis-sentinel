/* Ontology-drift tripwire — compile-time only, no runtime exports used.
 *
 * Asserts assignability between the hand-mirrored ontology/artifact
 * types (what the components render) and the codegen output in
 * ./generated/ (from schemas/*.schema.json, the backend's frozen
 * contract). If the backend renames a field, changes an enum, or
 * retypes a property, `tsc --noEmit` fails HERE with the exact type.
 *
 * `DeepComplete<T>` models the backend's serialization: pydantic
 * model_dump always emits every field (defaults included), and
 * minItems-constrained arrays arrive as plain arrays — so optional
 * markers become required and tuples widen to arrays before comparing.
 *
 * Directions:
 * - enums: mutual (a value added or removed on either side fails).
 * - records the backend seals (VerdictRecord, Population, Claim,
 *   Disposition, EQC): mutual, modulo documented deltas.
 * - render-only shapes (CapabilityEntry): generated → local (the page
 *   must accept whatever the backend emits); CompileError: local →
 *   generated (the artifact carries extra rendered/E-code fields the
 *   base schema doesn't pin).
 */

import type {
  Assertion,
  Claim,
  Disposition,
  EvidenceQualityContract,
  Population,
  VerdictRecord,
} from "./ontology";
import type {
  AccessMode,
  CapabilityEntry,
  CompileError,
  DeltaBucket,
  PaginationMethod,
  TemporalShapeKind,
} from "./artifacts";
import type * as GenPopulation from "./generated/population";
import type * as GenClaim from "./generated/claim";
import type * as GenAssertion from "./generated/assertion";
import type * as GenVerdict from "./generated/verdict-record";
import type * as GenEqc from "./generated/evidence-quality-contract";
import type * as GenCapability from "./generated/capability-entry";
import type * as GenDisposition from "./generated/disposition";
import type * as GenCompileError from "./generated/compile-error";

/* ------------------------------ machinery ------------------------------ */

/** All keys present (serialized form), tuples widened to arrays. */
type DeepComplete<T> = T extends readonly (infer U)[]
  ? DeepComplete<U>[]
  : T extends object
    ? { [K in keyof T]-?: DeepComplete<T[K]> }
    : T;

type Extends<A, B> = [A] extends [B] ? true : never;
type Mutual<A, B> = [A] extends [B] ? ([B] extends [A] ? true : never) : never;

/* ------------------------------ enums ---------------------------------- */

export type CheckVerdictState = Mutual<VerdictRecord["state"], GenVerdict.VerdictState>;
export type CheckUnknownWhyCode = Mutual<
  NonNullable<VerdictRecord["why_code"]>,
  GenVerdict.UnknownWhyCode
>;
export type CheckD7Family = Mutual<
  NonNullable<VerdictRecord["d7_family"]>,
  GenVerdict.D7Family
>;
export type CheckAssuranceState = Mutual<Population["state"], GenPopulation.AssuranceState>;
export type CheckPopulationType = Mutual<Population["type"], GenPopulation.PopulationType>;
export type CheckSourceRole = Mutual<
  Population["sources"][number]["role"],
  GenPopulation.SourceRole
>;
export type CheckAssertionType = Mutual<Assertion["type"], GenAssertion.AssertionType>;
export type CheckDispositionValue = Mutual<
  Disposition["value"],
  GenDisposition.DispositionValue
>;
export type CheckAccessMode = Mutual<AccessMode, GenCapability.AccessMode>;
export type CheckTemporalShapeKind = Mutual<
  TemporalShapeKind,
  GenCapability.TemporalShapeKind
>;
export type CheckPaginationMethod = Mutual<
  PaginationMethod,
  GenCapability.PaginationMethod
>;
/** DeltaBucket has no dedicated schema; pin the reconciler's six here. */
export type CheckDeltaBuckets = Mutual<
  DeltaBucket,
  "intersection" | "left_only" | "right_only" | "conflicts" | "unresolvable" | "excluded"
>;

/* ------------------------------ records -------------------------------- */

/* VerdictRecord — mutual, modulo record_hash: the schema allows null
 * (pre-seal), the artifacts are always sealed, and routes key off the
 * hash, so the local mirror pins it to string. */
export type CheckVerdictRecordUp = Extends<VerdictRecord, DeepComplete<GenVerdict.VerdictRecord>>;
export type CheckVerdictRecordDown = Extends<
  Omit<DeepComplete<GenVerdict.VerdictRecord>, "record_hash">,
  Omit<VerdictRecord, "record_hash">
>;

export type CheckPopulationUp = Extends<Population, DeepComplete<GenPopulation.Population>>;
export type CheckPopulationDown = Extends<DeepComplete<GenPopulation.Population>, Population>;

export type CheckClaimUp = Extends<Claim, DeepComplete<GenClaim.Claim>>;
export type CheckClaimDown = Extends<DeepComplete<GenClaim.Claim>, Claim>;

export type CheckAssertionUp = Extends<Assertion, DeepComplete<GenAssertion.Assertion>>;
export type CheckAssertionDown = Extends<DeepComplete<GenAssertion.Assertion>, Assertion>;

export type CheckDispositionUp = Extends<Disposition, DeepComplete<GenDisposition.Disposition>>;
export type CheckDispositionDown = Extends<
  DeepComplete<GenDisposition.Disposition>,
  Disposition
>;

export type CheckEqcUp = Extends<
  EvidenceQualityContract,
  DeepComplete<GenEqc.EvidenceQualityContract>
>;
export type CheckEqcDown = Extends<
  DeepComplete<GenEqc.EvidenceQualityContract>,
  EvidenceQualityContract
>;

/* CapabilityEntry — generated → local: whatever a ratified entry emits,
 * the registry page must render. (Local pins schema_version to plain
 * string so future registry versions still render.) */
export type CheckCapabilityEntry = Extends<
  DeepComplete<GenCapability.CapabilityEntry>,
  CapabilityEntry
>;

/* CompileError — local → generated: the artifact rows carry `rendered`
 * and per-E-code extras beyond the base compile-error schema. */
export type CheckCompileError = Extends<
  CompileError,
  DeepComplete<GenCompileError.CompileError>
>;

/* --------------------------- the tripwire ------------------------------ */

/* Each Check* alias evaluates to `true` when aligned and `never` on
 * drift; `true satisfies never` is the compile error that names the
 * drifted type. This const is the whole point of the file — do not
 * remove entries. */
export const ONTOLOGY_DRIFT_CHECKS = {
  verdict_state: true satisfies CheckVerdictState,
  unknown_why_code: true satisfies CheckUnknownWhyCode,
  d7_family: true satisfies CheckD7Family,
  assurance_state: true satisfies CheckAssuranceState,
  population_type: true satisfies CheckPopulationType,
  source_role: true satisfies CheckSourceRole,
  assertion_type: true satisfies CheckAssertionType,
  disposition_value: true satisfies CheckDispositionValue,
  access_mode: true satisfies CheckAccessMode,
  temporal_shape_kind: true satisfies CheckTemporalShapeKind,
  pagination_method: true satisfies CheckPaginationMethod,
  delta_buckets: true satisfies CheckDeltaBuckets,
  verdict_record_up: true satisfies CheckVerdictRecordUp,
  verdict_record_down: true satisfies CheckVerdictRecordDown,
  population_up: true satisfies CheckPopulationUp,
  population_down: true satisfies CheckPopulationDown,
  claim_up: true satisfies CheckClaimUp,
  claim_down: true satisfies CheckClaimDown,
  assertion_up: true satisfies CheckAssertionUp,
  assertion_down: true satisfies CheckAssertionDown,
  disposition_up: true satisfies CheckDispositionUp,
  disposition_down: true satisfies CheckDispositionDown,
  eqc_up: true satisfies CheckEqcUp,
  eqc_down: true satisfies CheckEqcDown,
  capability_entry: true satisfies CheckCapabilityEntry,
  compile_error: true satisfies CheckCompileError,
} as const;
