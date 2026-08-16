/**
 * Typed export barrel for the data layer (A2 seed + B1 mock engagement).
 *
 * Importing the JSON through the hand-authored types here is what makes
 * `tsc --noEmit` structurally check every data file against
 * `web/src/data/types.ts` — a missing or renamed field in any JSON file
 * fails the build. (JSON module inference widens string literals to
 * `string`, so enum VALUES are not literal-checked until C1's codegen
 * lands assignability checks; structure and field presence are.)
 */

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

import poisonsJson from "@/data/engagement/poisons.json";
import reconciliationJson from "@/data/engagement/reconciliation.json";
import registryJson from "@/data/engagement/registry.json";
import verdictsJson from "@/data/engagement/verdicts.json";

export type * from "@/data/types";

/* Seed data (A2) — prototype-ported, Meridian Financial demo company. */
export const scopeSeed: ScopeSeed = scopeJson as ScopeSeed;
export const controlsSeed: ControlsSeed = controlsJson as ControlsSeed;
export const processSeed: ProcessSeed = processJson as ProcessSeed;
export const gaugesSeed: GaugesSeed = gaugesJson as GaugesSeed;

/* Mock engagement (B1) — the six poison cases, shaped to the
 * artifacts/demo-engagement contracts; C2 swaps these for the real files. */
export const engagementVerdicts: VerdictsArtifact = verdictsJson as VerdictsArtifact;
export const engagementReconciliation: ReconciliationReport =
  reconciliationJson as ReconciliationReport;
export const engagementRegistry: RegistryArtifact = registryJson as RegistryArtifact;
export const engagementPoisons: PoisonsArtifact = poisonsJson as PoisonsArtifact;
