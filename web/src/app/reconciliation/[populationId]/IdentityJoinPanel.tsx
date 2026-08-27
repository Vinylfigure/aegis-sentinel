import {
  BUCKET_ORDER,
  CANONICAL_RULE,
  d7Groups,
  joinMatrix,
  sourceCoverage,
  type ReconciliationReport,
  type RegistryArtifact,
} from "@/data";
import styles from "../reconciliation.module.css";

/**
 * The join panel states the rule before the results: how canonical identity
 * is derived, then the six-bucket precedence, then the matrix. The point is
 * that nothing was silently dropped — every source member either keys to a
 * canonical identity or appears below as a named join failure.
 *
 * D-7 (knowledge/01_corpus/02_design_decisions/
 * Aegis_Design_Fix_D7_UNKNOWN_Decomposition.md §1) supplies the cause
 * families; D-U1 supplies the why-codes. The family is carried on the wire
 * as `Delta.cause` (README Q9) — only the why-code/meaning display strings
 * are attached client-side.
 */
export function IdentityJoinPanel({
  report,
  registry,
  selectedRef,
  onSelect,
}: {
  report: ReconciliationReport;
  registry: RegistryArtifact;
  selectedRef: string | null;
  onSelect: (ref: string) => void;
}) {
  const { keyed, unjoinable } = joinMatrix(report);
  const groups = d7Groups(report);
  const coverageByName = new Map(sourceCoverage(report, registry).map((c) => [c.name, c]));

  return (
    <div className={styles.panel}>
      <p className={styles.rule}>{CANONICAL_RULE}</p>
      <ol className={styles.precedence}>
        {BUCKET_ORDER.map((meta) => (
          <li key={meta.bucket} className={styles.precedenceItem}>
            <span className={styles.bucketName}>{meta.bucket}</span> — {meta.rule}
          </li>
        ))}
      </ol>

      <ul className={styles.sourceChips}>
        {report.sources.map((source) => {
          const coverage = coverageByName.get(source.name);
          return (
            <li
              key={source.name}
              className={
                source.role === "authoritative"
                  ? `${styles.sourceChip} ${styles.sourceAuthoritative}`
                  : styles.sourceChip
              }
            >
              <span className={styles.sourceName}>{source.name}</span>
              <span className={styles.sourceRole}>{source.role}</span>
              <span className={styles.sourceCount}>
                {source.members.length}
                <span className={styles.diagnostic}> members · diagnostic</span>
              </span>
              {coverage?.windowDays !== null && coverage?.windowDays !== undefined && (
                <span
                  className={
                    coverage.coversPeriod ? styles.coverageOk : styles.coverageInsufficient
                  }
                >
                  {coverage.coversPeriod
                    ? `retains ${coverage.windowDays}d — covers the report period`
                    : `retains only ${coverage.windowDays}d — may not cover the whole report period`}
                </span>
              )}
            </li>
          );
        })}
      </ul>

      {/* A scrollable region needs to be focusable, or keyboard users cannot
          reach the columns that overflow (WCAG 2.1.1). */}
      <div
        className={styles.tableWrap}
        tabIndex={0}
        role="region"
        aria-label="Canonical identity join matrix"
      >
        <table className={styles.matrix}>
          <caption className={styles.caption}>
            Canonical identity join — one row per identity, one column per declared
            source. A cell holds that source&apos;s member ref, or the word
            &ldquo;absent&rdquo;.
          </caption>
          <thead>
            <tr>
              <th scope="col">Canonical identity</th>
              {report.sources.map((source) => (
                <th key={source.name} scope="col">
                  {source.name}
                </th>
              ))}
              <th scope="col">Bucket</th>
            </tr>
          </thead>
          <tbody>
            {keyed.map((row) => {
              const ref = `email:${row.key}`;
              const selected = selectedRef === ref;
              return (
                <tr key={row.key} className={selected ? styles.rowSelected : undefined}>
                  <th scope="row">
                    <button
                      type="button"
                      className={styles.rowButton}
                      aria-pressed={selected}
                      aria-label={`Select ${row.key}`}
                      onClick={() => onSelect(ref)}
                    >
                      <code className={styles.ref}>{row.key}</code>
                    </button>
                    {!row.inCanonicalMembers && (
                      <span className={styles.notCanonical}>
                        not in canonical_members
                      </span>
                    )}
                  </th>
                  {report.sources.map((source) => {
                    const cell = row.cells[source.name] ?? null;
                    return (
                      <td key={source.name}>
                        {cell === null ? (
                          <span className={styles.absent}>absent</span>
                        ) : (
                          <code className={styles.cellRef}>{cell}</code>
                        )}
                      </td>
                    );
                  })}
                  <td>
                    <span className={styles.bucketName}>{row.bucket ?? "—"}</span>
                  </td>
                </tr>
              );
            })}
          </tbody>

          {unjoinable.length > 0 && (
            <tbody className={styles.unjoinableGroup}>
              <tr>
                <th scope="rowgroup" colSpan={report.sources.length + 2}>
                  No canonical key derivable — these sit outside the join
                </th>
              </tr>
              {unjoinable.map((row) => {
                const selected = selectedRef === row.key;
                return (
                  <tr key={row.key} className={selected ? styles.rowSelected : undefined}>
                    <th scope="row">
                      <button
                        type="button"
                        className={styles.rowButton}
                        aria-pressed={selected}
                        aria-label={`Select ${row.key}`}
                        onClick={() => onSelect(row.key)}
                      >
                        <code className={styles.ref}>{row.key}</code>
                      </button>
                      <span className={styles.rawEmail}>
                        raw value: <code>{row.rawEmail ?? "(none)"}</code>
                      </span>
                    </th>
                    {report.sources.map((source) => {
                      const cell = row.cells[source.name] ?? null;
                      return (
                        <td key={source.name}>
                          {cell === null ? (
                            <span className={styles.absent}>absent</span>
                          ) : (
                            <code className={styles.cellRef}>{cell}</code>
                          )}
                        </td>
                      );
                    })}
                    <td>
                      <span className={styles.bucketName}>{row.bucket ?? "—"}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          )}
        </table>
      </div>

      <div className={styles.d7}>
        <h3 className={styles.d7Title}>Join-failure taxonomy (D-7)</h3>
        {groups.length === 0 ? (
          <p className={styles.empty}>No join failures — every identity keyed.</p>
        ) : (
          <ul className={styles.d7Groups}>
            {groups.map((group) => (
              <li key={group.classification.family} className={styles.d7Group}>
                <span className={styles.d7Family}>{group.classification.family}</span>
                <span className={styles.whyCode}>{group.classification.whyCode}</span>
                <p className={styles.d7Meaning}>{group.classification.meaning}</p>
                <ul className={styles.d7Refs}>
                  {group.refs.map((ref) => (
                    <li key={ref}>
                      <code className={styles.ref}>{ref}</code>
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        )}
        <p className={styles.caveat}>
          Attribute conflicts are not join failures — a conflict is a successful
          join with disagreeing attributes (D-8 model reconciliation), shown on its
          delta below.
        </p>
      </div>
    </div>
  );
}
