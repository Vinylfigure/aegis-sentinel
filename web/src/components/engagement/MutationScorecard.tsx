"use client";

/* Mutation scorecard: the six poison cases, what detected each, and the
 * headline detection-rate meter. Any silent PASS would be a
 * build-stopping bug — the meter is the product's report card. */

import Link from "next/link";
import { detectionRate, MUTATION_POISONS } from "@/lib/data/mutations";
import { MiniChip, VerdictBadge } from "./Badges";
import styles from "./MutationScorecard.module.css";

export default function MutationScorecard() {
  const rate = detectionRate();
  return (
    <div className={styles.panel} data-testid="mutation-scorecard">
      <div className={styles.head}>
        <span className={styles.title}>Mutation scorecard</span>
        <span className={styles.sub}>six poisons, deliberately seeded (PRD §6)</span>
      </div>
      <div className={styles.rows}>
        {MUTATION_POISONS.map((p) => (
          <div key={p.id} className={styles.row}>
            <div className={styles.poison}>{p.poison}</div>
            <div className={styles.detector}>
              {p.detector.kind === "verdict" ? (
                <Link href={`/proof/${p.detector.verdict_id}`} className={styles.vlink}>
                  <VerdictBadge state={p.detector.state} />
                </Link>
              ) : (
                <MiniChip tone="red">{p.detector.code}</MiniChip>
              )}
              <span className={styles.note}>{p.detector.note}</span>
            </div>
            <div className={p.detected ? styles.hit : styles.miss}>
              {p.detected ? "detected" : "SILENT"}
            </div>
          </div>
        ))}
      </div>
      <div className={styles.meterRow}>
        <span className={styles.meterLabel}>
          assurance defect detection rate — {rate.detected}/{rate.total}
        </span>
        <b className={styles.meterPct}>{rate.pct}%</b>
      </div>
      <div className={styles.meter}>
        <i style={{ width: `${rate.pct}%` }} />
      </div>
    </div>
  );
}
