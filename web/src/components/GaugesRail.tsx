"use client";

import { useState } from "react";
import { useProgramStore } from "@/lib/state/programStore";
import {
  avgReuse,
  buildManifest,
  controlPosture,
  datasetRegistry,
  LLM_TASKS,
  scopeSummary,
  scopeTally,
  scopeVerdict,
  systemScopeCounts,
  triggeredRegimes,
} from "@/lib/state/selectors";
import styles from "./Rail.module.css";

function Gauge({
  tone,
  value,
  label,
  barPct,
}: {
  tone: "g" | "a" | "p" | "c" | "r";
  value: string | number;
  label: string;
  barPct?: number;
}) {
  return (
    <div className={`${styles.gauge} ${styles[tone]}`}>
      <div className={styles.v}>{value}</div>
      <div className={styles.l}>{label}</div>
      {barPct !== undefined && (
        <div className={styles.bar}>
          <i style={{ width: `${barPct}%` }} />
        </div>
      )}
    </div>
  );
}

export default function GaugesRail() {
  const products = useProgramStore((s) => s.products);
  const systems = useProgramStore((s) => s.systems);
  const controls = useProgramStore((s) => s.controls);
  const resetScope = useProgramStore((s) => s.resetScope);
  const [out, setOut] = useState<string | null>(null);

  const tally = scopeTally(products);
  const verdict = scopeVerdict(tally);
  const { inS, unk } = systemScopeCounts(systems);
  const regimes = triggeredRegimes(products);
  const posture = controlPosture(controls);
  const registry = datasetRegistry(controls);

  return (
    <div>
      <h2 className={styles.h2}>Scope</h2>
      <div
        className={`${styles.assert} ${
          verdict.state === "clear" ? styles.clear : styles.blocked
        }`}
      >
        <div className={styles.verdict}>{verdict.verdict}</div>
        <p>{verdict.note}</p>
      </div>
      <div className={styles.tallies}>
        <div className={`${styles.tally} ${styles.tIn}`}>
          <b>{tally.tIn}</b>
          <span>In</span>
        </div>
        <div className={`${styles.tally} ${styles.tUnk}`}>
          <b>{tally.tUnk}</b>
          <span>Unknown</span>
        </div>
        <div className={`${styles.tally} ${styles.tOut}`}>
          <b>{tally.tOut}</b>
          <span>Out</span>
        </div>
      </div>
      <Gauge tone="g" value={inS} label="systems in scope" />
      <Gauge tone="a" value={unk} label="unresolved — taints mappings" />

      <h2 className={styles.h2}>Regimes</h2>
      {regimes.map(({ regime, lit }) => (
        <div
          key={regime.id}
          className={`${styles.reg} ${lit ? styles.lit : ""}`}
        >
          <div className={styles.dot} />
          <div>
            <b>{regime.name}</b>
            <span>{regime.why}</span>
          </div>
        </div>
      ))}

      <h2 className={styles.h2}>Control posture</h2>
      <Gauge
        tone="g"
        value={`${posture.cfgPrevPct}%`}
        label="configurable · preventative"
        barPct={posture.cfgPrevPct}
      />
      <Gauge
        tone="r"
        value={posture.manualCount}
        label="manual controls — automation backlog"
      />
      <Gauge
        tone="a"
        value={posture.noDatasetCount}
        label="controls with no dataset"
      />

      <h2 className={styles.h2}>Datasets</h2>
      <Gauge tone="c" value={registry.length} label="unique datasets" />
      <Gauge
        tone="p"
        value={avgReuse(controls, registry)}
        label="avg controls per dataset"
      />

      <h2 className={styles.h2}>Sentinels</h2>
      <Gauge tone="g" value={registry.length} label="deterministic collectors" />
      <Gauge
        tone="p"
        value={LLM_TASKS.length}
        label="llm-lane tasks (non-verdict)"
      />

      <button
        className="btn"
        onClick={() => setOut(buildManifest(products, systems, controls))}
      >
        Export mission manifest
      </button>
      <button
        className="btn ghost"
        onClick={() => setOut(scopeSummary(products))}
      >
        Build scope summary
      </button>
      <button
        className="btn ghost"
        onClick={() => {
          resetScope();
          setOut(null);
        }}
      >
        Reset scope
      </button>
      {out !== null && <textarea className="outarea" readOnly value={out} />}
    </div>
  );
}
