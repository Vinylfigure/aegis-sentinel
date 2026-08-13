"use client";

/* Mutation scorecard: the six poison cases, what detected each, and the
 * headline detection-rate meter — all DERIVED from the real artifacts
 * (lib/data/mutations.ts checks the loaded verdicts / compile_errors
 * actually carry each detection). Any silent PASS would be a
 * build-stopping bug — the meter is the product's report card. */

import Link from "next/link";
import { detectionRate, mutationPoisons } from "@/lib/data/mutations";
import { MiniChip, VerdictBadge } from "./Badges";
import styles from "./MutationScorecard.module.css";

export default function MutationScorecard() {
  const poisons = mutationPoisons();
  const rate = detectionRate();
  return (
    <div className={styles.panel} data-testid="mutation-scorecard">
      <div className={styles.head}>
        <span className={styles.title}>Mutation scorecard</span>
        <span className={styles.sub}>
          six poisons, deliberately seeded (PRD §6) — detections read from the
          sealed artifacts
        </span>
      </div>
      <div className={styles.rows}>
        {poisons.map((p) => (
          <div key={p.id} className={styles.row}>
            <div className={styles.poison}>{p.poison}</div>
            <div className={styles.detector}>
              {p.detector.kind === "verdict" ? (
                <Link href={`/proof/${p.detector.slug}`} className={styles.vlink}>
                  <VerdictBadge state={p.detector.state} />
                </Link>
              ) : p.detector.kind === "ecode" ? (
                <MiniChip tone="red">{p.detector.code}</MiniChip>
              ) : (
                <MiniChip tone="red">not detected</MiniChip>
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
