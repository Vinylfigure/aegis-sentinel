"use client";

import { FLOWS } from "@/data/seed";
import { useProgramStore } from "@/lib/state/programStore";
import styles from "./Process.module.css";

export default function ProcessPage() {
  const selectedCp = useProgramStore((s) => s.selectedCp);
  const selectCp = useProgramStore((s) => s.selectCp);

  return (
    <div>
      <p className="sub">
        Assets as nodes tinted by the data classification they carry, ITGC
        processes as left-to-right chains, and control points sitting on the
        flow between systems. Click any diamond — the panel expands it into
        nature, function, the exact data element collected, and the evidence
        type. The graph is the scope, the diamonds are the program.
      </p>

      <div className={styles.ctx}>
        <span className={styles.chip}>
          <b>Product:</b> Core subscription + Card
        </span>
        <span className={`${styles.chip} ${styles.chipT1}`}>
          T1 — regulated (tradeline · CHD · NPI)
        </span>
        <span className={`${styles.chip} ${styles.chipT2}`}>
          T2 — confidential (PII · secrets)
        </span>
        <span className={styles.chip}>T3 — internal</span>
      </div>
      <div className={styles.legend}>
        <span className={styles.li}>
          <span className={`${styles.sq} ${styles.sqP}`} /> preventative
          control point
        </span>
        <span className={styles.li}>
          <span className={`${styles.sq} ${styles.sqD}`} /> detective control
          point
        </span>
        <span className={styles.li}>
          <span className={`${styles.sq} ${styles.sqM}`} /> manual control
          point
        </span>
        <span className={styles.li}>
          <span className={`${styles.ci} ${styles.ciR}`} /> node carries T1
          data
        </span>
        <span className={styles.li}>
          <span className={`${styles.ci} ${styles.ciA}`} /> T2
        </span>
      </div>

      {FLOWS.map((f) => (
        <div key={f.id} className={styles.lane}>
          <div className={styles.laneh}>
            <span className={styles.id}>{f.id}</span>
            <b>{f.name}</b>
            <span>{f.sub}</span>
          </div>
          <div className={styles.flow}>
            <div className={styles.chain}>
              {f.seq.map((step, i) => {
                if (step.node) {
                  const n = step.node;
                  const tierCls =
                    n.tier === 1
                      ? styles.t1
                      : n.tier === 2
                        ? styles.t2
                        : styles.t3;
                  return (
                    <div key={i} className={`${styles.node} ${tierCls}`}>
                      <div className={styles.bubble}>
                        {n.label}
                        {n.tier < 3 && (
                          <span className={styles.tier}>T{n.tier}</span>
                        )}
                      </div>
                      <div className={styles.nl}>{n.sub}</div>
                    </div>
                  );
                }
                const c = step.cp!;
                const cls =
                  c.nat === "manual"
                    ? styles.cpMan
                    : c.fn === "prev"
                      ? styles.cpPrev
                      : styles.cpDet;
                return (
                  <div key={i} className={styles.edge}>
                    <div className={styles.wire} />
                    <button
                      className={`${styles.cp} ${cls} ${selectedCp === c.id ? styles.sel : ""}`}
                      onClick={() => selectCp(c.id)}
                    >
                      <i>{c.id}</i>
                    </button>
                    <div className={styles.wire} />
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
