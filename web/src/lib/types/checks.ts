/* Ontology-drift tripwire — compile-time only, no runtime exports used.
 *
 * Asserts assignability between the hand-mirrored ontology/artifact types
 * (what the components render) and the codegen output in ./generated/
 * (from schemas/**\/*.schema.json, the backend's frozen contract). If the
 * backend renames a field, changes an enum, or retypes a property,
 * `tsc --noEmit` fails HERE with the exact type.
 *
 * `DeepComplete<T>` models the backend's serialization: pydantic
 * model_dump always emits every field (defaults included), and
 * minItems-constrained arrays arrive as plain arrays — so optional
 * markers become required and tuples widen to arrays before comparing.
 *
 * Directions:
 * - enums: mutual (a value added or removed on either side fails).
 * - records the backend seals (Population, Claim, Assertion, Disposition,
 *   EvidenceQualityContract, the ontology Verdict, the wire VerdictRecord):
 *   mutual, modulo documented deltas.
 * - render-only shapes (CapabilityEntry): generated → local (the page
 *   must accept whatever the backend emits).
 *
 * `compile-error` (TYP01 E-codes) has no backend JSON Schema at all — it's
 * compiler-output text, never a pydantic model — so it is deliberately
 * absent here: CompileError in ./artifacts.ts stays local-only/unchecked.
 *
 * DELIBERATELY ABSENT: no assignability assertion between the ontology
 * `Verdict` model (./ontology.ts — `state`/`unknown_why`/
 * `exception_disposition_ref`) and the wire `VerdictRecord`
 * (./artifacts.ts — `status`/`unknown_cause`/`disposition_ref`, plus the
 * full reproducibility/identity tuple). Those are two different shapes for
 * the same concept; asserting them equal would paper over exactly that
 * divergence (see ontology.ts's Verdict doc comment).
 */

import type {
  Assertion,
  Claim,
  Disposition,
  EvidenceQualityContract,
  Population,
  SourceRef,
  Verdict,
} from "./ontology";
import type {
  AccessMode,
  CapabilityEntry,
  D7Family,
  DeltaBucket,
  PaginationMethod,
  TemporalKind,
  VerdictRecord,
} from "./artifacts";
import type * as GenPopulation from "./generated/population";
import type * as GenClaim from "./generated/claim";
import type * as GenAssertion from "./generated/assertion";
import type * as GenVerdict from "./generated/verdict";
import type { AegisSentinelVerdictRecord } from "./generated/verdict-record";
import type * as GenDelta from "./generated/delta";
import type * as GenEqc from "./generated/evidence-quality-contract";
import type * as GenCapability from "./generated/capability-entry";
import type * as GenDisposition from "./generated/disposition";

/* ------------------------------ machinery ------------------------------ */

/** All keys present (serialized form), tuples widened to arrays. */
type DeepComplete<T> = T extends readonly (infer U)[]
  ? DeepComplete<U>[]
  : T extends object
    ? { [K in keyof T]-?: DeepComplete<T[K]> }
    : T;

type Extends<A, B> = [A] extends [B] ? true : never;
type Mutual<A, B> = [A] extends [B] ? ([B] extends [A] ? true : never) : never;

/**
 * json-schema-to-typescript represents the wire verdict-record schema's
 * `additionalProperties: false` object as `{[k: string]: unknown} & {...}`.
 * The index signature is the tool's encoding, not the contract's — stripped
 * here so the named properties compare exactly.
 */
type StripIndex<T> = {
  [K in keyof T as string extends K ? never : K]: T[K];
};

/* ------------------------------ enums ---------------------------------- */

export type CheckVerdictState = Mutual<Verdict["state"], GenVerdict.VerdictState>;
export type CheckUnknownWhy = Mutual<NonNullable<Verdict["unknown_why"]>, GenVerdict.UnknownWhy>;
export type CheckAssuranceState = Mutual<Population["state"], GenPopulation.AssuranceState>;
export type CheckPopulationType = Mutual<Population["type"], GenPopulation.PopulationType>;
export type CheckSourceRole = Mutual<SourceRef["role"], GenPopulation.SourceRole>;
export type CheckAssertionType = Mutual<Assertion["type"], GenAssertion.AssertionType>;
export type CheckDispositionValue = Mutual<
  Disposition["value"],
  GenDisposition.DispositionValue
>;
export type CheckAccessMode = Mutual<AccessMode, GenCapability.AccessMode>;
export type CheckTemporalKind = Mutual<TemporalKind, GenCapability.TemporalKind>;
export type CheckPaginationMethod = Mutual<PaginationMethod, GenCapability.PaginationMethod>;
export type CheckDeltaBucket = Mutual<DeltaBucket, GenDelta.DeltaBucket>;
/** D7Family has no dedicated schema (schema/models.py's `cause` is a
 * computed property, never a serialized model field) — pinned instead
 * against the enum's own real values (schema/enums.py D7Family) so a
 * rename there still fails this file. */
export type CheckD7Family = Mutual<
  D7Family,
  "basis-missing" | "identity-fuzzy" | "no-basis-anywhere"
>;

/* ------------------------------ records -------------------------------- */

export type CheckVerdictUp = Extends<Verdict, DeepComplete<GenVerdict.Verdict>>;
export type CheckVerdictDown = Extends<DeepComplete<GenVerdict.Verdict>, Verdict>;

export type CheckPopulationUp = Extends<Population, DeepComplete<GenPopulation.Population>>;
export type CheckPopulationDown = Extends<DeepComplete<GenPopulation.Population>, Population>;

export type CheckClaimUp = Extends<Claim, DeepComplete<GenClaim.Claim>>;
export type CheckClaimDown = Extends<DeepComplete<GenClaim.Claim>, Claim>;

export type CheckAssertionUp = Extends<Assertion, DeepComplete<GenAssertion.Assertion>>;
export type CheckAssertionDown = Extends<DeepComplete<GenAssertion.Assertion>, Assertion>;

export type CheckDispositionUp = Extends<
  Disposition,
  DeepComplete<GenDisposition.DispositionRecord>
>;
export type CheckDispositionDown = Extends<
  DeepComplete<GenDisposition.DispositionRecord>,
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
 * the registry page must render. */
export type CheckCapabilityEntry = Extends<
  DeepComplete<GenCapability.CapabilityEntry>,
  CapabilityEntry
>;

/* ------------------------- the wire verdict record ---------------------- */

type GenVerdictRecord = StripIndex<AegisSentinelVerdictRecord>;

/**
 * Mutual modulo `support`: the schema leaves `support.field_values` an open
 * object (`{"type": "object"}` — member-level values vary per assertion),
 * which the tool emits as `{}`. The hand type refines it to
 * `Record<string, SupportFieldValue | undefined>`, which the schema
 * permits but a mutual `Extends` would reject. So `support` is compared
 * one-directionally (hand assignable to schema) below, and the rest of the
 * record compares exactly with `support` omitted.
 *
 * No `DeepComplete` here (unlike the ontology records above): the wire
 * schema's `message`/`severity`/`ratification_ref`/`disposition_ref`/
 * `unknown_cause` are only conditionally required (`if status=X then
 * required: [...]`, per the allOf blocks) — json-schema-to-typescript
 * doesn't model that conditional as a TS conditional type, so the
 * generated shape leaves them optional same as the hand type; forcing
 * them required here would fail on every conditionally-absent field.
 */
export type CheckVerdictRecordUp = Extends<
  Omit<VerdictRecord, "support">,
  Omit<GenVerdictRecord, "support">
>;
export type CheckVerdictRecordDown = Extends<
  Omit<GenVerdictRecord, "support">,
  Omit<VerdictRecord, "support">
>;
export type CheckVerdictRecordSupport = NonNullable<VerdictRecord["support"]> extends NonNullable<
  GenVerdictRecord["support"]
>
  ? true
  : never;

/* --------------------------- the tripwire ------------------------------ */

/* Each Check* alias evaluates to `true` when aligned and `never` on drift;
 * `true satisfies never` is the compile error that names the drifted type.
 * This const is the whole point of the file — do not remove entries. */
export const ONTOLOGY_DRIFT_CHECKS = {
  verdict_state: true satisfies CheckVerdictState,
  unknown_why: true satisfies CheckUnknownWhy,
  assurance_state: true satisfies CheckAssuranceState,
  population_type: true satisfies CheckPopulationType,
  source_role: true satisfies CheckSourceRole,
  assertion_type: true satisfies CheckAssertionType,
  disposition_value: true satisfies CheckDispositionValue,
  access_mode: true satisfies CheckAccessMode,
  temporal_kind: true satisfies CheckTemporalKind,
  pagination_method: true satisfies CheckPaginationMethod,
  delta_bucket: true satisfies CheckDeltaBucket,
  d7_family: true satisfies CheckD7Family,
  verdict_up: true satisfies CheckVerdictUp,
  verdict_down: true satisfies CheckVerdictDown,
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
  verdict_record_up: true satisfies CheckVerdictRecordUp,
  verdict_record_down: true satisfies CheckVerdictRecordDown,
  verdict_record_support: true satisfies CheckVerdictRecordSupport,
} as const;
