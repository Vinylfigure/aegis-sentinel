import type { Metadata } from "next";
import Link from "next/link";
import { LadderStepper } from "@/components/LadderStepper/LadderStepper";
import {
  BUCKET_ORDER,
  countPairs,
  engagementReconciliations,
  formatPeriod,
  openBlockers,
  reconciledClaimHolds,
} from "@/data";
import styles from "./reconciliation.module.css";

export const metadata: Metadata = { title: "Reconciliation" };

/**
 * B2 — /reconciliation: the population index. One card per reconciliation
 * report in the data layer, each showing where the population sits on the
 * assurance ladder and how many of its blocking deltas a named human
 * answered. Everything iterates `engagementReconciliations`; nothing here is
 * authored, including the counts.
 */
export default function ReconciliationPage() {
  const reports = engagementReconciliations;

  return (
    <div className={styles.indexMain}>
      <h1 className={styles.h1}>
        Reconciliation <span className={styles.h1Dot}>·</span> population completeness
      </h1>
      <p className={styles.sub}>
        Set-based reconciliation over canonical identity. Every difference between
        the declared sources is a first-class delta with an owner and a
        disposition — never a count.
      </p>

      {reports.length === 0 ? (
        <p className={styles.empty}>No reconciliation reports in the data layer.</p>
      ) : (
        <ul className={styles.cards}>
          {reports.map((report) => {
            const blockers = openBlockers(report);
            const answered = blockers.filter((b) => b.answer !== null).length;
            return (
              <li key={report.population_id} className={styles.card}>
                <h2 className={styles.cardTitle}>
                  <Link
                    className={styles.cardLink}
                    href={`/reconciliation/${report.population_id}`}
                  >
                    {report.population_name}
                  </Link>
                </h2>
                <p className={styles.cardMeta}>
                  <code className={styles.ref}>{report.population_id}</code>
                  <span className={styles.metaSep}>·</span>
                  {report.population_type}
                  <span className={styles.metaSep}>·</span>
                  {report.tenant}
                  <span className={styles.metaSep}>·</span>
                  {formatPeriod(report.period)}
                </p>

                <LadderStepper
                  ladder={report.ladder}
                  blockers={blockers}
                  claimHolds={reconciledClaimHolds(report)}
                  variant="condensed"
                />

                <p className={styles.cardBlockers}>
                  {blockers.length === 0
                    ? "No deltas blocked the ladder."
                    : `${answered} of ${blockers.length} blocking deltas answered by a named human.`}
                </p>

                <ul className={styles.bucketStrip}>
                  {countPairs(report).map((pair) => (
                    <li key={pair.bucket} className={styles.bucketChip}>
                      <span className={styles.bucketName}>{pair.bucket}</span>
                      <span className={styles.bucketCount}>
                        {pair.rendered}
                        <span className={styles.diagnostic}> diagnostic</span>
                      </span>
                    </li>
                  ))}
                </ul>

                <p className={styles.cardCta}>
                  <Link className={styles.cta} href={`/reconciliation/${report.population_id}`}>
                    Why this population is complete →
                  </Link>
                </p>
              </li>
            );
          })}
        </ul>
      )}

      {reports.length > 0 && <p className={styles.countsNote}>{reports[0]?.counts_note}</p>}

      <p className={styles.bucketOrderNote}>
        Bucket precedence (reconcile/engine.py):{" "}
        {BUCKET_ORDER.map((b) => b.bucket).join(" → ")}.
      </p>
    </div>
  );
}
