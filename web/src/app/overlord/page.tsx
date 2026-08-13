"use client";

import { useState } from "react";
import { useProgramStore } from "@/lib/state/programStore";
import { buildManifest, LLM_TASKS, missions } from "@/lib/state/selectors";
import styles from "./Overlord.module.css";

export default function OverlordPage() {
  const products = useProgramStore((s) => s.products);
  const systems = useProgramStore((s) => s.systems);
  const controls = useProgramStore((s) => s.controls);
  const [manifest, setManifest] = useState<string | null>(null);

  const det = missions(controls, systems);

  function exportManifest() {
    const json = buildManifest(products, systems, controls);
    setManifest(json);
    // download as a file as well
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "aegis-mission-manifest.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div>
      <div className={styles.ovintro}>
        <b>Overlord console.</b> One deterministic collector mission per unique
        dataset — target, retrieval surface, verdict attributes, cadence,
        C&amp;A, evidence destination. The LLM lane sits above the verdict
        path: triage, narrative, mapping — never verdicts. This is the scope of
        what each Sentinel is allowed to do, generated from everything
        upstream.
      </div>

      {det.map((m) => (
        <div key={m.id} className={styles.mission}>
          <div className={styles.mh}>
            <span className={styles.mid}>{m.id}</span>
            <b>Collect: {m.art}</b>
            <span className={`${styles.lane} ${styles.laneDet}`}>
              DETERMINISTIC · VERDICT PATH
            </span>
          </div>
          <div className={styles.mgrid}>
            <div className={styles.mg}>
              <label>Target</label>
              <div>
                <b>{m.sysName}</b>{" "}
                {m.scopeUnresolved && (
                  <span className={styles.warn}>⚠ scope unresolved</span>
                )}
              </div>
            </div>
            <div className={styles.mg}>
              <label>Surface</label>
              <div>{m.surface}</div>
            </div>
            <div className={styles.mg}>
              <label>C&amp;A</label>
              <div>{m.ca}</div>
            </div>
            <div className={styles.mg}>
              <label>Cadence</label>
              <div>{m.cadence}</div>
            </div>
            <div className={styles.mg}>
              <label>Verdicts served</label>
              <div>
                <b>{m.ctls.join(", ")}</b>
              </div>
            </div>
            <div className={styles.mg}>
              <label>Evidence</label>
              <div>hash + raw → WORM store</div>
            </div>
          </div>
        </div>
      ))}

      {LLM_TASKS.map((t) => (
        <div key={t.id} className={`${styles.mission} ${styles.agent}`}>
          <div className={styles.mh}>
            <span className={styles.mid}>{t.id}</span>
            <b>{t.name}</b>
            <span className={`${styles.lane} ${styles.laneLlm}`}>
              LLM LANE · NON-VERDICT
            </span>
          </div>
          <div className={styles.mgrid}>
            <div className={styles.mg}>
              <label>Boundary</label>
              <div>{t.boundary}</div>
            </div>
          </div>
        </div>
      ))}

      <div className={styles.exportRow}>
        <button className="btn" onClick={exportManifest}>
          Export mission manifest
        </button>
        {manifest !== null && (
          <textarea className="outarea" readOnly value={manifest} />
        )}
      </div>
    </div>
  );
}
