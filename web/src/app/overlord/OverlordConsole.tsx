"use client";

import { useState, type ReactNode } from "react";
import {
  GaugeList,
  sectionsFromSeed,
} from "@/components/GaugesRail/GaugesRail";
import { RailLayout } from "@/components/RailLayout/RailLayout";
import { StageTabs } from "@/components/StageTabs/StageTabs";
import {
  deriveCadence,
  deriveDatasetRegistry,
  type ControlsSeed,
  type GaugesSeed,
  type ScopeSeed,
} from "@/data";
import styles from "./overlord.module.css";

/** Every collector mission ships evidence the same way. */
const EVIDENCE_DESTINATION = "hash + raw → WORM store";

function MissionField({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <span className={styles.mLabel}>{label}</span>
      <div className={styles.mValue}>{children}</div>
    </div>
  );
}

export function OverlordConsole({
  seed,
  scope,
  gauges,
}: {
  seed: ControlsSeed;
  scope: ScopeSeed;
  gauges: GaugesSeed;
}) {
  const registry = deriveDatasetRegistry(seed.controls);
  const missions = registry.map((dataset, index) => ({
    id: `C-${String(index + 1).padStart(2, "0")}`,
    dataset,
    system: scope.systems.find((s) => s.id === dataset.systemId),
    cadence: deriveCadence(dataset),
  }));

  const [manifest, setManifest] = useState<string | null>(null);

  const gaugeSections = sectionsFromSeed(gauges, {
    "agents.deterministicCount": missions.length,
    "agents.llmLaneCount": seed.llmLane.length,
  });

  /* -- manifest: generated client-side from everything upstream ------ */

  const buildManifest = () => {
    const document = {
      generated: new Date().toISOString(),
      scope: {
        products: scope.products
          .filter((product) => product.inScope)
          .map((product) => product.name),
        systems_in: scope.systems
          .filter((system) => system.scope === "in")
          .map((system) => system.name),
        unresolved: scope.systems
          .filter((system) => system.scope === "unknown")
          .map((system) => system.name),
      },
      collectors: missions.map((mission) => ({
        id: mission.id,
        target: mission.system?.name ?? mission.dataset.systemId,
        artifact: mission.dataset.artifact,
        surface: seed.retrievalChannels[mission.dataset.retrieval],
        ca: seed.caMethods[mission.dataset.caMethod],
        cadence: mission.cadence,
        controls: mission.dataset.controlIds,
        lane: "deterministic-verdict",
      })),
      llm_lane: seed.llmLane.map((task) => ({
        id: task.id,
        task: task.name,
        verdict_authority: false,
      })),
    };
    setManifest(JSON.stringify(document, null, 1));
  };

  const rail = (
    <>
      <GaugeList sections={gaugeSections} />
      <button type="button" className={styles.btn} onClick={buildManifest}>
        Export mission manifest
      </button>
      {manifest !== null ? (
        <textarea
          className={styles.out}
          readOnly
          value={manifest}
          aria-label="Mission manifest"
        />
      ) : null}
    </>
  );

  return (
    <RailLayout rail={rail} railLabel="Agent gauges">
      <div className={styles.main}>
        <StageTabs current={4} />
        <h1 className={styles.h1}>
          Overlord console <span className={styles.h1Dot}>·</span> generated,
          not authored
        </h1>
        <p className={styles.intro}>
          <b>Overlord console.</b> One deterministic collector mission per
          unique dataset — target, retrieval surface, verdict attributes,
          cadence, C&amp;A, evidence destination. The LLM lane sits above the
          verdict path: triage, narrative, mapping — never verdicts. This is
          the scope of what each agent is allowed to do, generated from
          everything upstream.
        </p>
        {missions.map((mission) => (
          <article key={mission.id} className={styles.mission}>
            <div className={styles.mHead}>
              <span className={styles.mid}>{mission.id}</span>
              <b className={styles.mName}>Collect: {mission.dataset.artifact}</b>
              <span className={`${styles.lane} ${styles.laneDet}`}>
                DETERMINISTIC · VERDICT PATH
              </span>
            </div>
            <div className={styles.mGrid}>
              <MissionField label="Target">
                <b>{mission.system?.name ?? mission.dataset.systemId}</b>
                {mission.system && mission.system.scope !== "in" ? (
                  <span className={styles.warnFlag}> ⚠ scope unresolved</span>
                ) : null}
              </MissionField>
              <MissionField label="Surface">
                {seed.retrievalChannels[mission.dataset.retrieval]}
              </MissionField>
              <MissionField label="C&A">
                {seed.caMethods[mission.dataset.caMethod]}
              </MissionField>
              <MissionField label="Cadence">{mission.cadence}</MissionField>
              <MissionField label="Verdicts served">
                <b>{mission.dataset.controlIds.join(", ")}</b>
              </MissionField>
              <MissionField label="Evidence">{EVIDENCE_DESTINATION}</MissionField>
            </div>
          </article>
        ))}
        {seed.llmLane.map((task) => (
          <article
            key={task.id}
            className={`${styles.mission} ${styles.missionAgent}`}
          >
            <div className={styles.mHead}>
              <span className={styles.mid}>{task.id}</span>
              <b className={styles.mName}>{task.name}</b>
              <span className={`${styles.lane} ${styles.laneLlm}`}>
                LLM LANE · NON-VERDICT
              </span>
            </div>
            <div className={styles.mGrid}>
              <MissionField label="Boundary">{task.boundary}</MissionField>
            </div>
          </article>
        ))}
      </div>
    </RailLayout>
  );
}
