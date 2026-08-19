/**
 * Typed export barrel for the data layer (A2 seed + the C2 engagement
 * artifacts, imported from artifacts/demo-engagement/ via @artifacts/*).
 *
 * Each JSON file is first ASSIGNED (not `as`-cast) to a `Widen<T>` of its
 * hand-authored type: assignment checks assignability recursively, so a
 * missing or renamed field in any record of any array fails `tsc --noEmit`.
 * (`as T` only checks top-level comparability and swallows per-record
 * errors — proven by the adversarial verifier.) `Widen` relaxes literal
 * unions to their primitives because JSON module inference widens string
 * literals to `string`; enum VALUES therefore remain unchecked until C1's
 * codegen lands assignability checks. The single `as T` after the checked
 * assignment only re-narrows those enum strings.
 */

import { combinedRecords } from "@/data/verdicts";
import type {
  ControlsSeed,
  GaugesSeed,
  PoisonsArtifact,
  ProcessSeed,
  ReconciliationReport,
  RegistryArtifact,
  ScopeSeed,
  VerdictsArtifact,
} from "@/data/types";

import controlsJson from "@/data/seed/controls.json";
import gaugesJson from "@/data/seed/gauges.json";
import processJson from "@/data/seed/process.json";
import scopeJson from "@/data/seed/scope.json";

import poisonsJson from "@artifacts/poisons.json";
import reconciliationJson from "@artifacts/reconciliation.json";
import registryJson from "@artifacts/registry.json";
import verdictsJson from "@artifacts/verdicts.json";

export type * from "@/data/types";

/* Derived collections (A4) — computed from the seeds, never authored. */
export * from "@/data/derived";

/* Reconciliation derivations (B2) — computed from the engagement artifact. */
export * from "@/data/reconciliation";

/* Verdict + registry derivations (B3) — computed from the engagement artifacts. */
export * from "@/data/verdicts";
export * from "@/data/registry";

/* Proof-lineage derivations (B4). */
export * from "@/data/proof";

/** Literal unions -> primitives, recursively; structure and key presence
 * are preserved so assignment still checks them. */
type Widen<T> = T extends string
  ? string
  : T extends number
    ? number
    : T extends boolean
      ? boolean
      : T extends readonly (infer E)[]
        ? readonly Widen<E>[]
        : T extends object
          ? { [K in keyof T]: Widen<T[K]> }
          : T;

/** The checked assignment: fails to compile unless `json` matches the
 * widened shape of T field-for-field, at every depth. */
function checked<T>(json: Widen<T>): T {
  return json as T;
}

/* Seed data (A2) — prototype-ported, Meridian Financial demo company. */
export const scopeSeed = checked<ScopeSeed>(scopeJson);
export const controlsSeed = checked<ControlsSeed>(controlsJson);
export const processSeed = checked<ProcessSeed>(processJson);
export const gaugesSeed = checked<GaugesSeed>(gaugesJson);

/* Engagement data (C2) — the pipeline-emitted, pydantic-validated
 * artifacts/demo-engagement/ files themselves, imported via @artifacts/*.
 * Never vendored: the imports point at the drift-tested originals, so the
 * enum-value hole Widen<T> leaves open is closed at the source. */
export const engagementVerdicts = checked<VerdictsArtifact>(verdictsJson);
export const engagementReconciliation = checked<ReconciliationReport>(reconciliationJson);
export const engagementRegistry = checked<RegistryArtifact>(registryJson);
export const engagementPoisons = checked<PoisonsArtifact>(poisonsJson);

/**
 * The population list the /reconciliation routes iterate. One report today;
 * C2 maps over the real artifacts/demo-engagement output, so a second
 * population is a data-only change. Built FROM the checked export above, so
 * the `checked<T>` assignability position (L-053) is untouched.
 */
export const engagementReconciliations: ReconciliationReport[] = [engagementReconciliation];

/**
 * Every verdict record in the engagement (verdicts.json + the records
 * embedded in poisons.verdict_records, deduped) — the roster /proof routes
 * are generated from. Built FROM the checked exports above; the checked<T>
 * assignability position (L-053) is untouched.
 */
export const engagementVerdictRecords = combinedRecords(
  engagementVerdicts,
  engagementPoisons,
);
