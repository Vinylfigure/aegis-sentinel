"use client";

/* The assurance-state ladder as a six-step stepper. Current state lit;
 * RATIFIED shows ratifier + manifest version; an open-disposition count
 * visually BLOCKS the DISCOVERED→RECONCILED connector — the ladder
 * discipline made visible. */

import { ASSURANCE_STATES } from "@/lib/types/ontology";
import type { AssuranceState } from "@/lib/types/ontology";
import styles from "./LadderStepper.module.css";

export default function LadderStepper({
  state,
  openDispositions,
  ratifiedBy,
  manifestVersion,
}: {
  state: AssuranceState;
  openDispositions: number;
  ratifiedBy: string;
  manifestVersion: string;
}) {
  const currentIdx = ASSURANCE_STATES.indexOf(state);
  const blocked = state === "DISCOVERED" && openDispositions > 0;

  return (
    <div className={styles.stepper} data-state={state}>
      {ASSURANCE_STATES.map((s, i) => {
        const reached = i <= currentIdx && state !== "STALE";
        const isCurrent = s === state;
        const connectorBlocked = blocked && s === "RECONCILED";
        return (
          <div key={s} className={styles.stepWrap}>
            {i > 0 && (
              <div
                className={`${styles.connector} ${
                  connectorBlocked
                    ? styles.connBlocked
                    : i <= currentIdx && state !== "STALE"
                      ? styles.connDone
                      : ""
                }`}
              >
                {connectorBlocked && (
                  <span className={styles.blockTag}>
                    blocked · {openDispositions} open disposition
                    {openDispositions > 1 ? "s" : ""}
                  </span>
                )}
              </div>
            )}
            <div
              className={`${styles.step} ${reached ? styles.reached : ""} ${
                isCurrent ? styles.current : ""
              } ${s === "STALE" && isCurrent ? styles.stale : ""}`}
            >
              <div className={styles.dot} />
              <div className={styles.label}>{s}</div>
              {s === "RATIFIED" && state === "RATIFIED" && (
                <div className={styles.meta}>
                  {ratifiedBy} · {manifestVersion}
                </div>
              )}
              {s === "STALE" && state === "STALE" && (
                <div className={styles.meta}>re-enters at DISCOVERED</div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
