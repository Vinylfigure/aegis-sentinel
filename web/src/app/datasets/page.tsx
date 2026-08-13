"use client";

import { ART_RET, CA } from "@/data/seed";
import { useProgramStore } from "@/lib/state/programStore";
import { datasetRegistry } from "@/lib/state/selectors";
import type { CaMethod, Retrieval } from "@/lib/types/authoring";
import styles from "./Datasets.module.css";

export default function DatasetsPage() {
  const controls = useProgramStore((s) => s.controls);
  const systems = useProgramStore((s) => s.systems);
  const setDatasetRet = useProgramStore((s) => s.setDatasetRet);
  const setDatasetCa = useProgramStore((s) => s.setDatasetCa);

  // Derived, never stored: dedupe by system|artifact across all controls.
  const registry = datasetRegistry(controls);

  return (
    <div>
      <p className="hint">
        The dataset registry — derived from control↔system mappings,
        deduplicated. A dataset shared by many controls is the
        test-once-apply-many win; set its artifact type, retrieval channel, and
        C&amp;A method once and every control that rides it inherits.
      </p>
      {registry.map((d) => {
        const s = systems.find((x) => x.id === d.sys);
        return (
          <div key={`${d.sys}|${d.art}`} className={styles.ds}>
            <div className={styles.dsh}>
              <b>{s ? s.name : d.sys}</b>
              <span className={styles.art}>{d.art}</span>
              <span
                className={`${styles.reuse} ${d.ctls.length > 1 ? "" : styles.one}`}
              >
                ×{d.ctls.length} control{d.ctls.length > 1 ? "s" : ""}
              </span>
            </div>
            <div className={styles.dsmeta}>
              <div>
                <label>Retrieval</label>
                <select
                  value={d.ret}
                  onChange={(e) =>
                    setDatasetRet(d.sys, d.art, e.target.value as Retrieval)
                  }
                >
                  {Object.entries(ART_RET).map(([k, v]) => (
                    <option key={k} value={k}>
                      {v}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label>C&amp;A method</label>
                <select
                  value={d.ca}
                  onChange={(e) =>
                    setDatasetCa(d.sys, d.art, e.target.value as CaMethod)
                  }
                >
                  {Object.entries(CA).map(([k, v]) => (
                    <option key={k} value={k}>
                      {v}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className={styles.dsctls}>
              serves <i>{d.ctls.join(" · ")}</i>
            </div>
          </div>
        );
      })}
    </div>
  );
}
