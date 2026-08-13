"use client";

/* Set-based reconciliation board: six bucket columns fed by the real
 * reconciler output — `buckets` carries full membership, `deltas` the
 * exception records. intersection green · left_only / right_only amber ·
 * conflicts / unresolvable red · excluded dim. Ghost chips render the
 * negative space (sources where the member was expected but absent);
 * excluded cards carry their ratified disposition_ref. Clicking a delta
 * focuses its story in the rail's WhyCompletePanel. */

import { DELTA_BUCKETS } from "@/lib/types/artifacts";
import type { DeltaBucket, DeltaObject, ReconciliationResult } from "@/lib/types/artifacts";
import { useEngagementStore } from "@/lib/state/engagementStore";
import { DispositionBadge, GhostChip, PresentChip } from "./Badges";
import styles from "./ReconciliationBoard.module.css";

export const BUCKET_LABEL: Record<DeltaBucket, string> = {
  intersection: "intersection",
  left_only: "left only",
  right_only: "right only",
  conflicts: "conflicts",
  unresolvable: "unresolvable",
  excluded: "excluded",
};

const BUCKET_SUB: Record<DeltaBucket, string> = {
  intersection: "agreed by all declared sources",
  left_only: "authoritative-side only — absent downstream",
  right_only: "downstream only — no authoritative anchor",
  conflicts: "sources disagree on attributes",
  unresolvable: "identity join failed",
  excluded: "removed by rule — with disposition",
};

const BUCKET_TONE: Record<DeltaBucket, string> = {
  intersection: "green",
  left_only: "amber",
  right_only: "amber",
  conflicts: "red",
  unresolvable: "red",
  excluded: "dim",
};

/** How many corroborated members to list before folding into "+N more". */
const MEMBER_CHIP_CAP = 9;

function DeltaCard({ delta }: { delta: DeltaObject }) {
  const selected = useEngagementStore((s) => s.selectedDeltaId);
  const selectDelta = useEngagementStore((s) => s.selectDelta);
  const needsDisposition = delta.bucket !== "intersection";
  return (
    <button
      className={`${styles.card} ${selected === delta.delta_id ? styles.sel : ""}`}
      onClick={() => selectDelta(selected === delta.delta_id ? null : delta.delta_id)}
      data-delta={delta.delta_id}
    >
      <div className={styles.key}>{delta.member_key}</div>
      {delta.display_name && delta.display_name !== delta.member_key && (
        <div className={styles.name}>{delta.display_name}</div>
      )}
      <div className={styles.chips}>
        {delta.sources_present.map((s) => (
          <PresentChip key={s} source={s} />
        ))}
        {delta.sources_absent.map((s) => (
          <GhostChip key={s} source={s} />
        ))}
      </div>
      {(delta.owner || needsDisposition) && (
        <div className={styles.foot}>
          {delta.owner && <span className={styles.owner}>{delta.owner}</span>}
          {needsDisposition && (
            <DispositionBadge
              disposition={delta.disposition ?? undefined}
              dispositionRef={delta.disposition_ref ?? undefined}
            />
          )}
        </div>
      )}
    </button>
  );
}

export default function ReconciliationBoard({ recon }: { recon: ReconciliationResult }) {
  return (
    <div className={styles.scroll}>
      <div className={styles.board}>
        {DELTA_BUCKETS.map((bucket) => {
          const deltas = recon.deltas.filter((d) => d.bucket === bucket);
          const carded = new Set(deltas.map((d) => d.member_key));
          const plain = (recon.buckets[bucket] ?? []).filter((m) => !carded.has(m));
          const count = (recon.buckets[bucket] ?? []).length;
          return (
            <div
              key={bucket}
              className={`${styles.col} ${styles[`tone_${BUCKET_TONE[bucket]}`]}`}
              data-bucket={bucket}
            >
              <div className={styles.colHead}>
                <span className={styles.colName}>{BUCKET_LABEL[bucket]}</span>
                <span className={styles.colCount}>{count}</span>
              </div>
              <div className={styles.colSub}>{BUCKET_SUB[bucket]}</div>
              <div className={styles.cards}>
                {count === 0 && <div className={styles.empty}>— none —</div>}
                {deltas.map((d) => (
                  <DeltaCard key={d.delta_id} delta={d} />
                ))}
                {plain.length > 0 && (
                  <div className={styles.members}>
                    {plain.slice(0, MEMBER_CHIP_CAP).map((m) => (
                      <code key={m} className={styles.member}>
                        {m}
                      </code>
                    ))}
                    {plain.length > MEMBER_CHIP_CAP && (
                      <span className={styles.more}>
                        +{plain.length - MEMBER_CHIP_CAP} more
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
