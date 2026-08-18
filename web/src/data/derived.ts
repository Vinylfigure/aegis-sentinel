/**
 * Derived collections (A4) — computed in code from the seed exports,
 * never authored as JSON. The dataset registry is the workbench
 * prototype's dedupe of control↔system dataset mappings: a dataset is
 * identified by (system, artifact); every control that names the same
 * pair rides the same dataset (test-once-apply-many). The Overlord
 * missions are one deterministic collector per unique dataset.
 */

import type {
  CaMethod,
  ControlsSeed,
  RetrievalChannel,
  SeedControl,
} from "@/data/types";

export interface DerivedDataset {
  /** Stable identity: `${systemId}|${artifact}`. */
  key: string;
  /** SeedSystem id the dataset is collected from. */
  systemId: string;
  artifact: string;
  /** From the first control mapping that names this dataset. */
  retrieval: RetrievalChannel;
  caMethod: CaMethod;
  /** Every control served by this dataset, in seed order. */
  controlIds: string[];
}

/** Dedupe control dataset mappings by (system, artifact). */
export function deriveDatasetRegistry(
  controls: readonly SeedControl[],
): DerivedDataset[] {
  const byKey = new Map<string, DerivedDataset>();
  for (const control of controls) {
    for (const dataset of control.datasets) {
      const key = `${dataset.system}|${dataset.artifact}`;
      let entry = byKey.get(key);
      if (!entry) {
        entry = {
          key,
          systemId: dataset.system,
          artifact: dataset.artifact,
          retrieval: dataset.retrieval,
          caMethod: dataset.caMethod,
          controlIds: [],
        };
        byKey.set(key, entry);
      }
      entry.controlIds.push(control.id);
    }
  }
  return [...byKey.values()];
}

/** Total dataset references across all controls (the reuse numerator). */
export function countDatasetReferences(controls: readonly SeedControl[]): number {
  return controls.reduce((total, control) => total + control.datasets.length, 0);
}

/** Average controls served per unique dataset, formatted as the gauge shows it. */
export function datasetReuseAverage(seed: ControlsSeed): string {
  const registry = deriveDatasetRegistry(seed.controls);
  if (registry.length === 0) return "—";
  return (countDatasetReferences(seed.controls) / registry.length).toFixed(1);
}

/**
 * Prototype cadence rule for a collector mission: config artifacts run
 * daily plus event-driven on change; snapshot retrieval runs weekly;
 * everything else runs daily.
 */
export function deriveCadence(dataset: DerivedDataset): string {
  if (dataset.artifact.toLowerCase().includes("config")) {
    return "daily · +event-driven on change";
  }
  if (dataset.retrieval === "shot") return "weekly";
  return "daily";
}
