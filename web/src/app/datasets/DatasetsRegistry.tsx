"use client";

import { useState } from "react";
import {
  GaugeList,
  sectionsFromSeed,
} from "@/components/GaugesRail/GaugesRail";
import { RailLayout } from "@/components/RailLayout/RailLayout";
import { StageTabs } from "@/components/StageTabs/StageTabs";
import {
  countDatasetReferences,
  deriveDatasetRegistry,
  type CaMethod,
  type ControlsSeed,
  type GaugesSeed,
  type RetrievalChannel,
  type ScopeSeed,
} from "@/data";
import styles from "./datasets.module.css";

/* ------------------------------------------------------------------ */
/* State: retrieval + C&A per derived dataset, set once, inherited     */
/* ------------------------------------------------------------------ */

interface DatasetUiState {
  retrieval: RetrievalChannel;
  caMethod: CaMethod;
}

type RegistryState = Record<string, DatasetUiState>;

export function DatasetsRegistry({
  seed,
  scope,
  gauges,
}: {
  seed: ControlsSeed;
  scope: ScopeSeed;
  gauges: GaugesSeed;
}) {
  const registry = deriveDatasetRegistry(seed.controls);

  const [state, setState] = useState<RegistryState>(() => {
    const initial: RegistryState = {};
    for (const dataset of registry) {
      initial[dataset.key] = {
        retrieval: dataset.retrieval,
        caMethod: dataset.caMethod,
      };
    }
    return initial;
  });

  const stateOf = (key: string, fallback: DatasetUiState): DatasetUiState =>
    state[key] ?? fallback;

  const setRetrieval = (key: string, retrieval: RetrievalChannel) =>
    setState((prev) => {
      const current = prev[key];
      return current ? { ...prev, [key]: { ...current, retrieval } } : prev;
    });

  const setCaMethod = (key: string, caMethod: CaMethod) =>
    setState((prev) => {
      const current = prev[key];
      return current ? { ...prev, [key]: { ...current, caMethod } } : prev;
    });

  /* -- gauges (structure is derived, so these are derivation facts) -- */

  const references = countDatasetReferences(seed.controls);
  const gaugeSections = sectionsFromSeed(gauges, {
    "datasets.uniqueCount": registry.length,
    "datasets.avgControlsPerDataset":
      registry.length > 0 ? (references / registry.length).toFixed(1) : "—",
  });

  const retrievalOptions = Object.entries(seed.retrievalChannels) as [
    RetrievalChannel,
    string,
  ][];
  const caOptions = Object.entries(seed.caMethods) as [CaMethod, string][];

  const rail = (
    <>
      <GaugeList sections={gaugeSections} />
      <p className={styles.railNote}>
        Derived, not authored: {registry.length} unique datasets deduplicated
        from {references} control↔system mappings. A dataset shared by many
        controls is the test-once-apply-many win.
      </p>
    </>
  );

  return (
    <RailLayout rail={rail} railLabel="Dataset gauges">
      <div className={styles.main}>
        <StageTabs current={3} />
        <h1 className={styles.h1}>
          Dataset registry <span className={styles.h1Dot}>·</span> derived from
          the controls
        </h1>
        <p className={styles.sub}>
          The dataset registry — derived from control↔system mappings,
          deduplicated. A dataset shared by many controls is the
          test-once-apply-many win; set its retrieval channel and C&amp;A
          method once and every control that rides it inherits.
        </p>
        {registry.map((dataset) => {
          const system = scope.systems.find((s) => s.id === dataset.systemId);
          const current = stateOf(dataset.key, dataset);
          const reuse = dataset.controlIds.length;
          return (
            <article key={dataset.key} className={styles.ds}>
              <div className={styles.dsHead}>
                <b className={styles.dsSystem}>
                  {system ? system.name : dataset.systemId}
                </b>
                <span className={styles.dsArtifact}>{dataset.artifact}</span>
                <span
                  className={
                    reuse > 1 ? styles.reuse : `${styles.reuse} ${styles.reuseOne}`
                  }
                >
                  ×{reuse} control{reuse > 1 ? "s" : ""}
                </span>
              </div>
              <div className={styles.dsMeta}>
                <div>
                  <span className={styles.metaLabel}>Retrieval</span>
                  <div
                    className={styles.seg}
                    role="group"
                    aria-label={`Retrieval channel — ${dataset.artifact}`}
                  >
                    {retrievalOptions.map(([value, text]) => {
                      const selected = current.retrieval === value;
                      return (
                        <button
                          key={value}
                          type="button"
                          className={
                            selected
                              ? `${styles.segBtn} ${styles.selRet}`
                              : styles.segBtn
                          }
                          aria-pressed={selected}
                          onClick={() => setRetrieval(dataset.key, value)}
                        >
                          {text}
                        </button>
                      );
                    })}
                  </div>
                </div>
                <div>
                  <span className={styles.metaLabel}>C&amp;A method</span>
                  <div
                    className={styles.seg}
                    role="group"
                    aria-label={`Completeness and accuracy method — ${dataset.artifact}`}
                  >
                    {caOptions.map(([value, text]) => {
                      const selected = current.caMethod === value;
                      return (
                        <button
                          key={value}
                          type="button"
                          className={
                            selected
                              ? `${styles.segBtn} ${styles.selCa}`
                              : styles.segBtn
                          }
                          aria-pressed={selected}
                          onClick={() => setCaMethod(dataset.key, value)}
                        >
                          {text}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>
              <p className={styles.serves}>
                serves{" "}
                <span className={styles.servesIds}>
                  {dataset.controlIds.join(" · ")}
                </span>
              </p>
            </article>
          );
        })}
      </div>
    </RailLayout>
  );
}
