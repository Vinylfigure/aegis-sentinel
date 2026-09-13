import { Fragment } from "react";
import { ASSURANCE_STATES, type AssuranceState } from "@/lib/types/ontology";
import styles from "./Ladder.module.css";

/** The assurance ladder — UNDEFINED → DEFINED → DISCOVERED → RECONCILED →
 * RATIFIED (STALE is off-ladder decay and only shown when current).
 * `blockedAfter` renders a broken rung: the transition the population
 * cannot make (e.g. DEFINED —E117→ DISCOVERED). */
export default function Ladder({
  current,
  blockedAfter,
  blockedLabel,
  compact = false,
}: {
  current: AssuranceState;
  blockedAfter?: AssuranceState;
  blockedLabel?: string;
  compact?: boolean;
}) {
  const steps = ASSURANCE_STATES.filter((s) => s !== "STALE");
  const currentIdx = steps.indexOf(current as (typeof steps)[number]);

  return (
    <div
      className={`${styles.ladder} ${compact ? styles.compact : ""}`}
      aria-label={`assurance state ${current}`}
    >
      {steps.map((s, i) => {
        const done = i <= currentIdx;
        const isCurrent = s === current;
        const rungBlocked = i > 0 && blockedAfter === steps[i - 1];
        return (
          <Fragment key={s}>
            {i > 0 && (
              <span
                className={[
                  styles.rung,
                  rungBlocked ? styles.rungBlocked : "",
                  !rungBlocked && done ? styles.rungDone : "",
                ].join(" ")}
                aria-hidden
              >
                {rungBlocked && blockedLabel && (
                  <em className={styles.blockedNote}>{blockedLabel}</em>
                )}
              </span>
            )}
            <span className={styles.stepCol}>
              <span
                className={[
                  styles.dot,
                  done ? styles.dotDone : "",
                  isCurrent ? styles.dotCurrent : "",
                ].join(" ")}
                aria-hidden
              />
              <span
                className={`${styles.label} ${isCurrent ? styles.labelCurrent : done ? styles.labelDone : ""}`}
              >
                {s}
              </span>
            </span>
          </Fragment>
        );
      })}
    </div>
  );
}
