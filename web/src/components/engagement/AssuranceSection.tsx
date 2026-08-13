"use client";

/* "Assurance" rail section — shown when engagement data loads, on the
 * engagement routes: ladder-state counts, the five verdict-state counts
 * colored, and the mutation detection rate. */

import { ladderCounts, loadEngagement, verdictCounts } from "@/lib/data/engagement";
import { detectionRate } from "@/lib/data/mutations";
import { ASSURANCE_STATES, VERDICT_STATES } from "@/lib/types/ontology";
import railStyles from "@/components/Rail.module.css";
import styles from "./AssuranceSection.module.css";

const VERDICT_TONE: Record<string, string> = {
  PASS: styles.tGreen,
  FAIL: styles.tRed,
  UNKNOWN: styles.tAmber,
  EXCLUDED: styles.tFaint,
  EXCEPTION: styles.tPurple,
};

export default function AssuranceSection() {
  const load = loadEngagement();
  const ladder = ladderCounts(load);
  const verdicts = verdictCounts(load);
  const rate = detectionRate();

  return (
    <div data-testid="assurance-section">
      <h2 className={railStyles.h2}>Assurance</h2>

      <div className={styles.ladder}>
        {ASSURANCE_STATES.map((s) => (
          <div key={s} className={`${styles.lrow} ${ladder[s] ? "" : styles.zero}`}>
            <span className={styles.lname}>{s}</span>
            <b className={styles.lcount}>{ladder[s]}</b>
          </div>
        ))}
      </div>

      <div className={styles.verdicts}>
        {VERDICT_STATES.map((s) => (
          <div key={s} className={`${styles.vcell} ${VERDICT_TONE[s]}`}>
            <b>{verdicts[s]}</b>
            <span>{s}</span>
          </div>
        ))}
      </div>

      <div className={railStyles.gauge + " " + railStyles.g}>
        <div className={railStyles.v}>
          {rate.pct}%
        </div>
        <div className={railStyles.l}>
          detection rate · {rate.detected}/{rate.total} poisons
        </div>
        <div className={railStyles.bar}>
          <i style={{ width: `${rate.pct}%` }} />
        </div>
      </div>
    </div>
  );
}
