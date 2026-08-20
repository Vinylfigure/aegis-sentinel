/**
 * C1 — assignability bridge between the hand-authored types and the
 * schema-generated ones in `__generated__/` (produced by
 * web/scripts/codegen.mjs from the committed JSON Schemas; byte-drift
 * guarded by `npm run codegen:check` in scripts/verify-web.sh and CI).
 *
 * Every assertion here is a compile-time fact: if a schema's enum gains,
 * loses, or renames a member — or the wire record's shape moves — `tsc`
 * fails in this file with the exact mismatch. Nothing here exists at
 * runtime, and the `checked<T>(json: Widen<T>)` position in index.ts is
 * untouched (L-053).
 *
 * DELIBERATELY ABSENT: no assertion between the ontology `Verdict` model
 * (schemas/ontology/verdict.schema.json — `unknown_why`,
 * `exception_disposition_ref`, nullable-always-present) and the wire
 * `VerdictRecord` (`unknown_cause`, `disposition_ref`, absent keys). Those
 * are two different shapes for the same concept — open README questions
 * Q1/Q2 — and asserting them equal would paper over exactly the divergence
 * the questions exist to surface. The generated `verdict.ts` is consumed
 * here solely for its two enums.
 *
 * Honest limit (also in web/README.md): this bridge guards the TYPES. It
 * does not close the JSON-enum-value hole — JSON imports still widen
 * literals to `string` (`Widen<T>`). C2 closes that at the source by
 * importing the pipeline-emitted, pydantic-validated artifacts directly.
 */

import type * as GenAssertion from "@/data/__generated__/assertion";
import type * as GenCapability from "@/data/__generated__/capability-entry";
import type * as GenDelta from "@/data/__generated__/delta";
import type * as GenPopulation from "@/data/__generated__/population";
import type { AegisSentinelVerdictRecord } from "@/data/__generated__/verdict-record";
import type * as GenVerdict from "@/data/__generated__/verdict";
import type {
  AssertionType,
  AssuranceState,
  DeltaBucket,
  DispositionValue,
  LifecycleState,
  PaginationMethod,
  PopulationType,
  Severity,
  SourceRole,
  TemporalKind,
  UnknownWhy,
  VerdictRecord,
  VerdictState,
} from "@/data/types";

/** Mutual assignability — resolves to `true` only when A and B are the same
 * set; any drift makes the annotated constant a type error. */
type Exact<A, B> = [A] extends [B] ? ([B] extends [A] ? true : never) : never;

/* ------------------------------------------------------------------ */
/* Enum unions — hand vs schema $defs                                  */
/* ------------------------------------------------------------------ */

const _verdictState: Exact<VerdictState, GenVerdict.VerdictState> = true;
const _unknownWhy: Exact<UnknownWhy, GenVerdict.UnknownWhy> = true;
const _deltaBucket: Exact<DeltaBucket, GenDelta.DeltaBucket> = true;
const _dispositionValue: Exact<DispositionValue, GenDelta.DispositionValue> = true;
const _assuranceState: Exact<AssuranceState, GenPopulation.AssuranceState> = true;
const _populationType: Exact<PopulationType, GenPopulation.PopulationType> = true;
const _sourceRole: Exact<SourceRole, GenPopulation.SourceRole> = true;
const _assertionType: Exact<AssertionType, GenAssertion.AssertionType> = true;
const _lifecycleState: Exact<LifecycleState, GenCapability.LifecycleState> = true;
const _paginationMethod: Exact<PaginationMethod, GenCapability.PaginationMethod> = true;
const _temporalKind: Exact<TemporalKind, GenCapability.TemporalKind> = true;
/** Severity lives on the wire record, not in an ontology $defs — extracted
 * from the generated property union. Answers README Q7. */
const _severity: Exact<Severity, NonNullable<AegisSentinelVerdictRecord["severity"]>> = true;

/* ------------------------------------------------------------------ */
/* The wire verdict record                                             */
/* ------------------------------------------------------------------ */

/**
 * Two mechanical adaptations, each documented and each as narrow as the
 * tool artifact it absorbs — never a blanket weakening:
 *
 * 1. `StripIndex`: json-schema-to-typescript represents the schema's
 *    `allOf` conditional blocks as `{[k: string]: unknown} & {...}`, even
 *    though the schema itself is `additionalProperties: false`. The index
 *    signature is the tool's encoding, not the contract's — stripped here
 *    so the named properties compare exactly.
 * 2. `support.field_values`: the schema leaves it an open object
 *    (`{"type": "object"}` — member-level values vary per assertion), which
 *    the tool emits as `{}`. The hand type refines it to
 *    `Record<string, SupportFieldValue | undefined>`, which the schema
 *    permits but `Exact` would reject. The `support` field is therefore
 *    compared one-directionally (hand assignable to schema) below, and the
 *    rest of the record compares exactly with `support` omitted.
 */
type StripIndex<T> = {
  [K in keyof T as string extends K ? never : K]: T[K];
};

type GenVerdictRecord = StripIndex<AegisSentinelVerdictRecord>;

const _verdictRecord: Exact<
  Omit<VerdictRecord, "support">,
  Omit<GenVerdictRecord, "support">
> = true;

/** Hand support must at least satisfy the schema's support shape. */
const _support: NonNullable<VerdictRecord["support"]> extends NonNullable<
  GenVerdictRecord["support"]
>
  ? true
  : never = true;

/* Reference the constants so `noUnusedLocals`-style tooling and reviewers
 * see them as intentional. */
export const BRIDGE_ASSERTIONS = [
  _verdictState,
  _unknownWhy,
  _deltaBucket,
  _dispositionValue,
  _assuranceState,
  _populationType,
  _sourceRole,
  _assertionType,
  _lifecycleState,
  _paginationMethod,
  _temporalKind,
  _severity,
  _verdictRecord,
  _support,
] as const;
