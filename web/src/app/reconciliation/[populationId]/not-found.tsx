import Link from "next/link";
import { engagementReconciliations } from "@/data";
import styles from "../reconciliation.module.css";

/** The 404 is data-driven too: it lists the populations that do exist by
 * iterating the same array the routes are generated from. */
export default function ReconciliationNotFound() {
  return (
    <div className={styles.indexMain}>
      <h1 className={styles.h1}>No such population</h1>
      <p className={styles.sub}>
        That population id has no reconciliation report in the data layer.
      </p>
      {engagementReconciliations.length === 0 ? (
        <p className={styles.empty}>No reconciliation reports in the data layer.</p>
      ) : (
        <ul className={styles.notFoundList}>
          {engagementReconciliations.map((report) => (
            <li key={report.population_id}>
              <Link className={styles.cta} href={`/reconciliation/${report.population_id}`}>
                <code className={styles.ref}>{report.population_id}</code> —{" "}
                {report.population_name}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
