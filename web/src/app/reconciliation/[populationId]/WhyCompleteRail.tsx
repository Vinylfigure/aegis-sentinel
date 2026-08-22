import {
  CANONICAL_RULE,
  D7_INFERENCE_CAVEAT,
  OPEN_BUCKETS,
  attributeDisagreements,
  bucketMeta,
  d7Family,
  derivationBasis,
  findDelta,
  formatPeriod,
  joinMatrix,
  ratifiedReached,
  resolveDisposition,
  type Blocker,
  type ReconciliationReport,
} from "@/data";
import styles from "../reconciliation.module.css";

/**
 * The why-complete rail: the completeness argument, in the order a
 * practitioner asserts it. HANDOFF UI01 defines the answer as derivation rule
 * + reconciliation + dispositions — sections 2, 4 and 5 below — and section 7
 * computes the implication that only holds if 5 covers 4.
 *
 * The conclusion is assembled, never echoed: it is derived from whether every
 * blocker was answered, not from `ladder.after_dispositions`.
 */
export function WhyCompleteRail({
  report,
  blockers,
  claimHolds,
  selectedRef,
  onClear,
}: {
  report: ReconciliationReport;
  blockers: Blocker[];
  claimHolds: boolean;
  selectedRef: string | null;
  onClear: () => void;
}) {
  return (
    <div aria-live="polite">
      <h2 className={styles.railTitle}>
        {selectedRef ? "This member's chain" : "Why this population is complete"}
      </h2>
      {selectedRef ? (
        <SelectedChain report={report} memberRef={selectedRef} onClear={onClear} />
      ) : (
        <Argument report={report} blockers={blockers} claimHolds={claimHolds} />
      )}
    </div>
  );
}

function Argument({
  report,
  blockers,
  claimHolds,
}: {
  report: ReconciliationReport;
  blockers: Blocker[];
  claimHolds: boolean;
}) {
  const basis = derivationBasis(report);
  const { keyed, unjoinable } = joinMatrix(report);
  const answered = blockers.filter((b) => b.answer !== null);
  const unanswered = blockers.filter((b) => b.answer === null);

  return (
    <>
      <RailSection n={1} title="Population">
        <p className={styles.railBody}>{report.population_name}</p>
        <p className={styles.railMeta}>
          <code className={styles.ref}>{report.population_id}</code> ·{" "}
          {report.population_type} · {report.tenant}
        </p>
        <p className={styles.railMeta}>period {formatPeriod(report.period)}</p>
      </RailSection>

      <RailSection n={2} title="Derivation basis">
        <p className={styles.railBody}>{basis.description}</p>
        <ul className={styles.railList}>
          {basis.authoritative.map((s) => (
            <li key={s.name}>
              <span className={styles.sourceName}>{s.name}</span>{" "}
              <span className={styles.sourceRole}>authoritative</span>
            </li>
          ))}
          {basis.corroborating.map((s) => (
            <li key={s.name}>
              <span className={styles.sourceName}>{s.name}</span>{" "}
              <span className={styles.sourceRole}>{s.role}</span>
            </li>
          ))}
        </ul>
        <p className={styles.caveat}>
          Invariant №3: a population has a derivation rule or an authoritative
          source — never neither.
        </p>
      </RailSection>

      <RailSection n={3} title="Join">
        <p className={styles.railBody}>{CANONICAL_RULE}</p>
        <p className={styles.railMeta}>
          {keyed.length} identities keyed; {unjoinable.length} could not be keyed.
        </p>
        {unjoinable.length > 0 && (
          <ul className={styles.railList}>
            {unjoinable.map((row) => {
              const classification = row.bucket ? d7Family(row.bucket) : null;
              return (
                <li key={row.key}>
                  <code className={styles.ref}>{row.key}</code>
                  {classification && (
                    <span className={styles.d7Chip}> {classification.family}</span>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </RailSection>

      <RailSection n={4} title="Reconciliation">
        <ul className={styles.railList}>
          {OPEN_BUCKETS.map((meta) => {
            const deltas = report.buckets[meta.bucket];
            return (
              <li key={meta.bucket}>
                <span className={styles.bucketName}>{meta.bucket}</span>
                {deltas.length === 0 ? (
                  <span className={styles.railMeta}> — none</span>
                ) : (
                  <ul className={styles.railSubList}>
                    {deltas.map((d) => (
                      <li key={d.member_ref}>
                        <code className={styles.ref}>{d.member_ref}</code>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            );
          })}
        </ul>
        <p className={styles.caveat}>
          Open deltas are named individually — a count would not tell you which
          member is unaccounted for.
        </p>
      </RailSection>

      <RailSection n={5} title="Dispositions">
        {blockers.length === 0 ? (
          <p className={styles.railBody}>No deltas blocked the ladder.</p>
        ) : (
          <ul className={styles.railList}>
            {blockers.map((blocker) => {
              const diverges = blocker.dispositioned !== (blocker.answer !== null);
              return (
                <li key={blocker.ref} className={styles.blockerRow}>
                  <code className={styles.ref}>{blocker.ref}</code>
                  <span className={styles.railMeta}>{blocker.bucket}</span>
                  {diverges && (
                    <p className={styles.divergence}>
                      Ladder divergence: the artifact says dispositioned={" "}
                      {String(blocker.dispositioned)}, the dispositions on file say{" "}
                      {String(blocker.answer !== null)}. The dispositions are the truth.
                    </p>
                  )}
                  {blocker.answer ? (
                    <>
                      <p className={styles.railMeta}>
                        <span className={styles.dispositionValue}>
                          {blocker.answer.record.value}
                        </span>{" "}
                        by {blocker.answer.record.owner}
                      </p>
                      <p className={styles.rationale}>
                        {blocker.answer.record.rationale ?? "no rationale recorded"}
                      </p>
                    </>
                  ) : (
                    <p className={styles.undispositioned}>
                      UNANSWERED — the ladder cannot advance
                    </p>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </RailSection>

      <RailSection n={6} title="Boundary exclusions">
        {report.boundary_exclusions.length === 0 ? (
          <p className={styles.railBody}>None ratified for this population.</p>
        ) : (
          <ul className={styles.railList}>
            {report.boundary_exclusions.map((exclusion) => (
              <li key={exclusion.member}>
                <code className={styles.ref}>{exclusion.member}</code>
                <p className={styles.railMeta}>
                  {exclusion.ref} · ratified by {exclusion.ratified_by}
                </p>
              </li>
            ))}
          </ul>
        )}
        <p className={styles.caveat}>
          D-9: exclusions enter already ratified — the engine never invents one.
        </p>
      </RailSection>

      <RailSection n={7} title="Conclusion">
        <p className={claimHolds ? styles.conclusionOk : styles.conclusionBad}>
          {claimHolds
            ? `${report.ladder.at_first_verdict} at first verdict → ${report.ladder.after_dispositions} after ${answered.length} ${
                answered.length === 1 ? "disposition" : "dispositions"
              }, each owned by a named human. ${
                ratifiedReached(report.ladder.after_dispositions)
                  ? "RATIFIED reached — the human freeze (D-L1)."
                  : "RATIFIED not reached."
              } No coverage percentage — V1 reports ladder states only.`
            : `Not reconciled: ${unanswered.length} of ${blockers.length} blocking ${
                blockers.length === 1 ? "delta is" : "deltas are"
              } unanswered (${unanswered.map((b) => b.ref).join(", ")}). The artifact claims ${report.ladder.after_dispositions}; the deltas do not support it.`}
        </p>
      </RailSection>
    </>
  );
}

function SelectedChain({
  report,
  memberRef,
  onClear,
}: {
  report: ReconciliationReport;
  memberRef: string;
  onClear: () => void;
}) {
  const delta = findDelta(report, memberRef);
  const answer = resolveDisposition(report, memberRef);
  const classification = delta ? d7Family(delta.bucket) : null;
  const meta = delta ? bucketMeta(delta.bucket) : null;
  const blocked = report.ladder.blocked_by_open_deltas.some((entry) => entry.ref === memberRef);
  const disagreements =
    delta?.bucket === "conflict" ? attributeDisagreements(report, memberRef) : [];
  const held = report.sources.filter((s) =>
    s.members.some(
      (m) => m.ref === memberRef || `email:${m.email.trim().toLowerCase()}` === memberRef,
    ),
  );
  const absent = report.sources.filter((s) => !held.includes(s));

  return (
    <>
      <p className={styles.railBody}>
        <code className={styles.ref}>{memberRef}</code>
      </p>

      <RailSection n={1} title="Sources">
        <p className={styles.railMeta}>
          held by: {held.length === 0 ? "none" : held.map((s) => s.name).join(", ")}
        </p>
        <p className={styles.railMeta}>
          absent from: {absent.length === 0 ? "none" : absent.map((s) => s.name).join(", ")}
        </p>
      </RailSection>

      <RailSection n={2} title="Bucket">
        {meta ? (
          <>
            <p className={styles.railBody}>
              <span className={styles.bucketName}>{meta.bucket}</span>
            </p>
            <p className={styles.railMeta}>{meta.rule}</p>
          </>
        ) : (
          <p className={styles.railBody}>No delta carries this ref.</p>
        )}
      </RailSection>

      {classification && (
        <RailSection n={3} title="Join-failure cause">
          <p className={styles.railBody}>
            <span className={styles.d7Family}>{classification.family}</span>{" "}
            <span className={styles.whyCode}>{classification.whyCode}</span>
          </p>
          <p className={styles.railMeta}>{classification.meaning}</p>
          <p className={styles.caveat}>{D7_INFERENCE_CAVEAT}</p>
        </RailSection>
      )}

      {disagreements.length > 0 && (
        <RailSection n={4} title="Attribute disagreement (D-8)">
          <ul className={styles.railList}>
            {disagreements.map((row) => (
              <li key={row.attribute}>
                <span className={styles.sourceName}>{row.attribute}</span>
                <ul className={styles.railSubList}>
                  {Object.entries(row.bySource).map(([source, value]) => (
                    <li key={source}>
                      {source}: {value}
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        </RailSection>
      )}

      <RailSection n={5} title="Ladder">
        <p className={styles.railBody}>
          {blocked
            ? "Blocked DISCOVERED→RECONCILED until dispositioned."
            : "Did not block the ladder."}
        </p>
      </RailSection>

      <RailSection n={6} title="Disposition">
        {answer ? (
          <>
            <p className={styles.railBody}>
              <span className={styles.dispositionValue}>{answer.record.value}</span> by{" "}
              {answer.record.owner}
            </p>
            <p className={styles.provenance}>
              recorded{" "}
              {answer.source === "inline"
                ? "inline on the delta"
                : "in the top-level dispositions map"}
            </p>
            <p className={styles.rationale}>
              {answer.record.rationale ?? "no rationale recorded"}
            </p>
          </>
        ) : (
          <p className={styles.undispositioned}>No disposition recorded.</p>
        )}
      </RailSection>

      <button type="button" className={styles.clearButton} onClick={onClear}>
        Clear selection
      </button>
    </>
  );
}

function RailSection({
  n,
  title,
  children,
}: {
  n: number;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className={styles.railSection}>
      <h3 className={styles.railSectionTitle}>
        <span className={styles.railNum}>{n}</span> {title}
      </h3>
      {children}
    </section>
  );
}
