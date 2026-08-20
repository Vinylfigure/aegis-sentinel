/**
 * Issue #43 — fusing live verdict/compile-error state onto the /process
 * graph. Every function takes its records/errors explicitly (same
 * discipline as `web/src/data/verdicts.ts`/`registry.ts`, L-054/L-056): a
 * mutation to the underlying artifact — a record's status flips, a
 * compile error is added or removed — changes what these functions return,
 * so the tint and gate on screen are never hardcoded to today's fixture.
 *
 * The join from a `ProcessControlPoint` to its records/errors is the
 * seed's own explicit `verdictSpecIds`/`compileErrorClaimIds` (types.ts) —
 * not a derived-by-adjacency guess like `relatedControls` in
 * ProcessGraph.tsx uses for library controls. Two points can share
 * flanking systems yet test different specs, so adjacency would be wrong
 * here.
 */

import { VERDICT_STATES } from "@/data/verdicts";
import type { CompileError, ProcessControlPoint, VerdictRecord, VerdictState } from "@/data/types";

/**
 * The worst of the given states, in VERDICT_STATES' attention-first order
 * (FAIL > UNKNOWN > EXCEPTION > EXCLUDED > PASS). `null` means no states —
 * a point/node with nothing wired renders as "no live data", never a
 * silent PASS.
 */
export function worstOfStates(
  states: readonly VerdictState[],
): VerdictState | null {
  const present = new Set(states);
  for (const meta of VERDICT_STATES) {
    if (present.has(meta.state)) return meta.state;
  }
  return null;
}

/** The worst state among the given records — see `worstOfStates`. */
export function worstVerdictState(
  records: readonly VerdictRecord[],
): VerdictState | null {
  return worstOfStates(records.map((r) => r.status));
}

/** Records associated with a control point via its explicit spec_id list. */
export function pointVerdictRecords(
  point: ProcessControlPoint,
  records: readonly VerdictRecord[],
): VerdictRecord[] {
  const specIds = point.verdictSpecIds;
  if (!specIds || specIds.length === 0) return [];
  return records.filter((r) => specIds.includes(r.spec_id));
}

/** Compile errors gating a control point via its explicit claim_id list. */
export function pointCompileErrors(
  point: ProcessControlPoint,
  errors: readonly CompileError[],
): CompileError[] {
  const claimIds = point.compileErrorClaimIds;
  if (!claimIds || claimIds.length === 0) return [];
  return errors.filter((e) => claimIds.includes(e.claim_id));
}
