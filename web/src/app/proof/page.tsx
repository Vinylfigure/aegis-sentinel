import type { Metadata } from "next";
import Link from "next/link";
import {
  VERDICT_STATES,
  engagementVerdictRecords,
  recordsByState,
} from "@/data";
import styles from "./proof.module.css";

export const metadata: Metadata = { title: "Proof" };

/**
 * B4 — /proof: index of every verdict record's lineage page, grouped by the
 * five states (VERDICT_STATES is exhaustive — a sixth state fails tsc, so a
 * record can never silently miss the index).
 */
export default function ProofIndexPage() {
  const records = engagementVerdictRecords;

  return (
    <div className={styles.main}>
      <h1 className={styles.h1}>
        Proof <span className={styles.h1Dot}>·</span> per-verdict lineage
      </h1>
      <p className={styles.sub}>
        Every verdict record, traced through the ten-stage chain from commitment
        to verdict. Stages the wire does not yet carry are labelled, not faked.
      </p>

      {records.length === 0 ? (
        <p className={styles.empty}>No verdict records in the data layer.</p>
      ) : (
        VERDICT_STATES.map((meta) => {
          const inState = recordsByState(records, meta.state);
          if (inState.length === 0) return null;
          return (
            <section
              key={meta.state}
              aria-labelledby={`proof-${meta.state}`}
              className={styles.indexSection}
            >
              <h2 id={`proof-${meta.state}`} className={styles.indexTitle}>
                {meta.state}
                <span className={styles.indexCount}>
                  {inState.length} {inState.length === 1 ? "record" : "records"}
                  <span className={styles.diagnostic}> · diagnostic</span>
                </span>
              </h2>
              <ul className={styles.indexList}>
                {inState.map((record) => (
                  <li key={record.record_id}>
                    <Link
                      className={styles.jumpLink}
                      href={`/proof/${encodeURIComponent(record.record_id)}`}
                    >
                      <code className={styles.mono}>{record.record_id}</code>
                    </Link>
                    <p className={styles.indexMessage}>{record.message ?? "(no message on the record)"}</p>
                  </li>
                ))}
              </ul>
            </section>
          );
        })
      )}
    </div>
  );
}
