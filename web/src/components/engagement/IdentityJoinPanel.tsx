"use client";

/* Identity-join panel: canonical join keys and per-source rows with
 * role tags and raw counts — counts labeled diagnostic, not evidence. */

import type { ReconciliationResult } from "@/lib/types/artifacts";
import type { Population } from "@/lib/types/ontology";
import { SourceRoleTag } from "./Badges";
import styles from "./IdentityJoinPanel.module.css";

export default function IdentityJoinPanel({
  population,
  recon,
}: {
  population: Population;
  recon?: ReconciliationResult;
}) {
  return (
    <div className={styles.panel}>
      <div className={styles.head}>
        <span className={styles.title}>Identity join</span>
        <span className={styles.caveat}>counts are diagnostic, not evidence</span>
      </div>
      <div className={styles.keys}>
        <label>canonical join keys</label>
        {(recon?.canonical_identity_keys ?? []).map((k) => (
          <code key={k}>{k}</code>
        ))}
        {!recon && <span className={styles.none}>no reconciliation run recorded</span>}
      </div>
      <div className={styles.rows}>
        {population.sources.map((s) => (
          <div key={s.source_id} className={styles.row}>
            <span className={styles.src}>{s.source_id}</span>
            <SourceRoleTag role={s.role} />
            <span className={styles.count}>
              {recon?.source_counts[s.source_id] !== undefined
                ? `${recon.source_counts[s.source_id]} members`
                : "not enumerated"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
