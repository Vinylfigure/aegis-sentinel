import Link from "next/link";
import { engagementVerdictRecords } from "@/data";
import styles from "../proof.module.css";

/** Data-driven 404: lists the verdict records that do exist, from the same
 * array the routes are generated from. */
export default function ProofNotFound() {
  return (
    <div className={styles.main}>
      <h1 className={styles.h1}>No such verdict record</h1>
      <p className={styles.sub}>
        That record id has no verdict record in the data layer.
      </p>
      {engagementVerdictRecords.length === 0 ? (
        <p className={styles.empty}>No verdict records in the data layer.</p>
      ) : (
        <ul className={styles.notFoundList}>
          {engagementVerdictRecords.map((record) => (
            <li key={record.record_id}>
              <Link
                className={styles.jumpLink}
                href={`/proof/${encodeURIComponent(record.record_id)}`}
              >
                <code className={styles.mono}>{record.record_id}</code> — {record.status}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
