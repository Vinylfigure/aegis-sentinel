"use client";

import { FLOWS } from "@/data/seed";
import type { ControlPoint } from "@/lib/types/authoring";
import { useProgramStore } from "@/lib/state/programStore";
import styles from "./Rail.module.css";

const ALL: Record<string, ControlPoint> = {};
FLOWS.forEach((f) =>
  f.seq.forEach((s) => {
    if (s.cp) ALL[s.cp.id] = s.cp;
  })
);

const NAT_BADGE: Record<string, [string, string]> = {
  cfg: ["bdCfg", "CONFIGURABLE"],
  auto: ["bdAuto", "AUTOMATED"],
  manual: ["bdMan", "MANUAL"],
};

export default function ProcessRail() {
  const selectedCp = useProgramStore((s) => s.selectedCp);
  const c = ALL[selectedCp];

  return (
    <div>
      <h2 className={styles.h2}>Control point</h2>
      {!c ? (
        <p className={styles.empty}>Click a diamond on any flow.</p>
      ) : (
        <div className={styles.dt}>
          <span className={styles.code}>{c.id}</span>
          <h3>{c.name}</h3>
          <div className={styles.badges}>
            <span
              className={`${styles.bd} ${styles[NAT_BADGE[c.nat][0] as keyof typeof styles]}`}
            >
              {NAT_BADGE[c.nat][1]}
            </span>
            <span
              className={`${styles.bd} ${c.fn === "prev" ? styles.bdPrev : styles.bdDet}`}
            >
              {c.fn === "prev" ? "PREVENTATIVE" : "DETECTIVE"}
            </span>
          </div>
          <div className={styles.frow}>
            <label>What it enforces</label>
            <div>{c.what}</div>
          </div>
          <div className={styles.frow}>
            <label>Data element</label>
            <div>
              <b>{c.el}</b>
              <br />
              <code>{c.api}</code>
            </div>
          </div>
          <div className={styles.frow}>
            <label>Type of evidence</label>
            <div>{c.ev}</div>
          </div>
          <div className={styles.frow}>
            <label>Completeness &amp; accuracy</label>
            <div>{c.ca}</div>
          </div>
          {c.gap && (
            <div className={styles.gap}>
              <b>Watch</b>
              <p>{c.gap}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
