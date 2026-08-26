import {
  OPEN_BUCKETS,
  RESOLVED_BUCKETS,
  attributeDisagreements,
  countPairs,
  d7Classify,
  resolveDisposition,
  type BucketMeta,
  type Delta,
  type ReconciliationReport,
} from "@/data";
import styles from "../reconciliation.module.css";

/**
 * The six buckets as first-class delta objects. Split per `OPEN_BUCKETS` in
 * reconcile/engine.py: the four open buckets gate the ladder; intersection
 * and excluded are resolved states, not open questions.
 *
 * Counts render only beside the deltas, labelled diagnostic (HANDOFF §2). The
 * rendered delta list is the truth — where the artifact's own count
 * disagrees, the divergence is flagged rather than silently preferred.
 */
export function BucketBoard({
  report,
  selectedRef,
  onSelect,
}: {
  report: ReconciliationReport;
  selectedRef: string | null;
  onSelect: (ref: string) => void;
}) {
  const pairs = countPairs(report);
  const pairFor = (bucket: string) => pairs.find((p) => p.bucket === bucket);

  const renderGroup = (title: string, blurb: string, metas: readonly BucketMeta[], id: string) => (
    <section aria-labelledby={id} className={styles.bucketGroup}>
      <h3 id={id} className={styles.bucketGroupTitle}>
        {title}
      </h3>
      <p className={styles.bucketGroupBlurb}>{blurb}</p>
      <div className={styles.bucketPanels}>
        {metas.map((meta) => {
          const deltas = report.buckets[meta.bucket];
          const pair = pairFor(meta.bucket);
          const diverges = pair !== undefined && pair.artifact !== pair.rendered;
          return (
            <div key={meta.bucket} className={styles.bucketPanel}>
              <div className={styles.bucketHeader}>
                <span className={styles.bucketName}>{meta.bucket}</span>
                <span className={styles.bucketCount}>
                  {deltas.length} rendered
                  <span className={styles.diagnostic}>
                    {" "}
                    · artifact counts {pair?.artifact ?? "—"} · diagnostic
                  </span>
                </span>
              </div>
              {diverges && (
                <p className={styles.divergence}>
                  Count divergence: the artifact says {pair?.artifact}, {deltas.length}{" "}
                  {deltas.length === 1 ? "delta is" : "deltas are"} on screen. The deltas
                  are the truth.
                </p>
              )}
              <p className={styles.bucketRule}>{meta.rule}</p>
              {deltas.length === 0 ? (
                <p className={styles.empty}>No deltas in this bucket.</p>
              ) : (
                <ul className={styles.deltaList}>
                  {deltas.map((delta) => (
                    <li key={delta.member_ref}>
                      <DeltaCard
                        report={report}
                        delta={delta}
                        open={meta.open}
                        selected={selectedRef === delta.member_ref}
                        onSelect={onSelect}
                      />
                    </li>
                  ))}
                </ul>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );

  return (
    <div className={styles.panel}>
      {renderGroup(
        "Open questions — these gate the ladder",
        "Each attaches to the population undispositioned, so schema.models.advance keeps blocking DISCOVERED→RECONCILED until a human answers it.",
        OPEN_BUCKETS,
        "bucket-open",
      )}
      {renderGroup(
        "Resolved — not questions",
        "Presence everywhere needs no sign-off; an excluded delta is born dispositioned because the ratified boundary exclusion (D-9) is its human resolution.",
        RESOLVED_BUCKETS,
        "bucket-resolved",
      )}
      <p className={styles.countsNote}>{report.counts_note}</p>
      <p className={styles.manualNote}>
        Dispositions, ratifications and residual-UNKNOWN acceptance are manual by
        design (docs/invariants.md №11). This surface displays and attributes them;
        it never sets one.
      </p>
    </div>
  );
}

function DeltaCard({
  report,
  delta,
  open,
  selected,
  onSelect,
}: {
  report: ReconciliationReport;
  delta: Delta;
  open: boolean;
  selected: boolean;
  onSelect: (ref: string) => void;
}) {
  const answer = resolveDisposition(report, delta.member_ref);
  const classification = d7Classify(delta.cause);
  const disagreements =
    delta.bucket === "conflict" ? attributeDisagreements(report, delta.member_ref) : [];
  const exclusion = report.boundary_exclusions.find((e) => e.member === delta.member_ref);

  return (
    <div className={selected ? `${styles.delta} ${styles.deltaSelected}` : styles.delta}>
      <button
        type="button"
        className={styles.deltaButton}
        aria-pressed={selected}
        aria-label={`Select delta ${delta.member_ref}`}
        onClick={() => onSelect(delta.member_ref)}
      >
        <code className={styles.ref}>{delta.member_ref}</code>
      </button>

      <p className={styles.deltaChips}>
        <span className={styles.bucketName}>{delta.bucket}</span>
        {classification && (
          <span className={styles.d7Chip}>
            {classification.family} · {classification.whyCode}
          </span>
        )}
      </p>

      <p className={styles.deltaOwner}>
        {delta.owner ? `owner: ${delta.owner}` : "no owner recorded on the delta"}
      </p>

      {answer ? (
        <div className={styles.disposition}>
          <p className={styles.dispositionHead}>
            <span className={styles.dispositionValue}>{answer.record.value}</span>
            <span className={styles.dispositionOwner}>{answer.record.owner}</span>
            <span className={styles.provenance}>
              recorded {answer.source === "inline" ? "inline on the delta" : "in the top-level dispositions map"}
            </span>
          </p>
          <p className={styles.rationale}>
            {answer.record.rationale ?? "no rationale recorded"}
          </p>
        </div>
      ) : (
        open && (
          <p className={styles.undispositioned}>
            UNDISPOSITIONED — blocks DISCOVERED→RECONCILED
          </p>
        )
      )}

      {disagreements.length > 0 && (
        <div
          className={styles.tableWrap}
          tabIndex={0}
          role="region"
          aria-label="Attribute disagreements"
        >
          <table className={styles.attrTable}>
            <caption className={styles.caption}>
              Attribute disagreement (D-8) — a successful join, disagreeing values.
            </caption>
            <thead>
              <tr>
                <th scope="col">Attribute</th>
                {report.sources.map((s) => (
                  <th key={s.name} scope="col">
                    {s.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {disagreements.map((row) => (
                <tr key={row.attribute}>
                  <th scope="row">{row.attribute}</th>
                  {report.sources.map((s) => (
                    <td key={s.name}>
                      {row.bySource[s.name] ?? <span className={styles.absent}>absent</span>}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {delta.bucket === "excluded" &&
        (exclusion ? (
          <p className={styles.exclusion}>
            ratified exclusion <code className={styles.ref}>{exclusion.ref}</code> by{" "}
            {exclusion.ratified_by}
          </p>
        ) : (
          <p className={styles.undispositioned}>
            No ratifying exclusion found for this ref.
          </p>
        ))}
    </div>
  );
}
