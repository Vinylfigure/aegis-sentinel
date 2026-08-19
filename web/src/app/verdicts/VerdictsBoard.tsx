"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { RailLayout } from "@/components/RailLayout/RailLayout";
import {
  VERDICT_STATES,
  conditionalBreaches,
  detectionRateText,
  orderedCases,
  recordsByState,
  scorecard,
  splitClassification,
  unknownCauses,
  verdictRuns,
  crossRunControl,
  verdictRecordAnchor,
  verdictRecordHref,
  verdictStateMeta,
  type PoisonCase,
  type PoisonsArtifact,
  type VerdictRecord,
  type VerdictsArtifact,
} from "@/data";
import styles from "./verdicts.module.css";

/**
 * The five states are never interchangeable (HANDOFF §2), so each renders
 * its own section with its own definition on screen, and every state label
 * is text — colour is redundant encoding. VERDICT_STATES is exhaustive by
 * construction, so a sixth state would fail the build rather than vanish.
 */
export function VerdictsBoard({
  records,
  verdicts,
  poisons,
  knownPopulationIds,
}: {
  /** The combined roster (all runs). */
  records: VerdictRecord[];
  verdicts: VerdictsArtifact;
  poisons: PoisonsArtifact;
  /** Population ids with a reconciliation report on the wire — the only ids
   * a why-complete link may target (dynamicParams=false 404s the rest). */
  knownPopulationIds: string[];
}) {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // C3 deep links: /verdicts#record=<encoded id> opens with that record
  // selected and scrolled into view; selecting writes the hash back.
  useEffect(() => {
    const raw = window.location.hash;
    if (!raw.startsWith("#record=")) return;
    const id = (() => {
      try {
        return decodeURIComponent(raw.slice("#record=".length));
      } catch {
        return raw.slice("#record=".length);
      }
    })();
    if (!records.some((r) => r.record_id === id)) return;
    setSelectedId(id);
    document.getElementById(verdictRecordAnchor(id))?.scrollIntoView({ block: "center" });
    // records is stable per render of a static page; run once on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const select = (id: string | null) => {
    setSelectedId(id);
    if (typeof window !== "undefined") {
      window.history.replaceState(
        null,
        "",
        id === null ? window.location.pathname : `#record=${encodeURIComponent(id)}`,
      );
    }
  };

  const card = scorecard(poisons);
  const breaches = conditionalBreaches(records);
  const causes = unknownCauses(records);
  const selected = records.find((r) => r.record_id === selectedId) ?? null;
  const runs = verdictRuns(verdicts, poisons);
  const control = crossRunControl(runs);

  const toggle = (id: string) => select(selectedId === id ? null : id);

  const rail = (
    <div aria-live="polite">
      <h2 className={styles.railTitle}>
        {selected ? "Verdict record" : "Mutation scorecard"}
      </h2>
      {selected ? (
        <RecordDetail
          record={selected}
          knownPopulationIds={knownPopulationIds}
          onClear={() => select(null)}
        />
      ) : (
        <Scorecard poisons={poisons} />
      )}
    </div>
  );

  return (
    <RailLayout rail={rail} railLabel="Mutation scorecard and verdict detail">
      <div className={styles.main}>
        <h1 className={styles.h1}>
          Verdicts <span className={styles.h1Dot}>·</span> five states, never interchangeable
        </h1>
        <p className={styles.sub}>
          Every record is a re-performable output of a pure function. A state is
          never a synonym for another: FAIL is a finding, UNKNOWN is an
          unanswered question, EXCLUDED is a ratified boundary decision.
        </p>
        <p className={styles.meta}>
          control {control.values.join(", ") || "—"}
          <span className={styles.metaSep}>·</span>
          {runs.length} {runs.length === 1 ? "run" : "runs"}
          <span className={styles.metaSep}>·</span>
          {records.length} records
          <span className={styles.diagnostic}> diagnostic</span>
        </p>

        <ul className={styles.runLegend}>
          {runs.map((group) => (
            <li key={group.runId} className={styles.runItem}>
              <code className={styles.ref}>{group.runId}</code>
              <span className={styles.runMeta}>
                {group.records.length}{" "}
                {group.records.length === 1 ? "record" : "records"}
                <span className={styles.diagnostic}> diagnostic</span> · collected{" "}
                {group.collectedAt}
              </span>
            </li>
          ))}
        </ul>
        {!control.consistent && (
          <p className={styles.breach}>
            Runs disagree on control id ({control.values.join(" vs ")}) — every
            run in this engagement should test the same control. Two run ids are
            data (walking-skeleton + poison runs, README Q17); a control
            disagreement is not.
          </p>
        )}

        {breaches.length > 0 && (
          <section aria-labelledby="breaches" className={styles.breachBox}>
            <h2 id="breaches" className={styles.breachTitle}>
              Schema violations — a state without its required justification
            </h2>
            <ul className={styles.breachList}>
              {breaches.map((b) => (
                <li key={b.record.record_id}>
                  <code className={styles.ref}>{b.record.record_id}</code> is{" "}
                  {b.record.status} but carries no <code>{b.missing}</code>.
                </li>
              ))}
            </ul>
          </section>
        )}

        <p className={styles.scoreLine}>
          Assurance defect detection rate{" "}
          <strong className={card.misses.length === 0 ? styles.scoreOk : styles.scoreBad}>
            {detectionRateText(card)}
          </strong>{" "}
          — {card.renderedDetected} of {card.renderedTotal} seeded defects caught.
          {card.misses.length > 0 && " Any silent PASS is a build-stopping bug (PRD §7)."}
        </p>

        {VERDICT_STATES.map((meta) => {
          const inState = recordsByState(records, meta.state);
          return (
            <section
              key={meta.state}
              aria-labelledby={`state-${meta.state}`}
              className={`${styles.stateSection} ${styles[meta.tone] ?? ""}`}
            >
              <h2 id={`state-${meta.state}`} className={styles.stateTitle}>
                <span className={styles.stateName}>{meta.state}</span>
                <span className={styles.stateCount}>
                  {inState.length} {inState.length === 1 ? "record" : "records"}
                  <span className={styles.diagnostic}> · diagnostic</span>
                </span>
              </h2>
              <p className={styles.stateMeaning}>{meta.meaning}</p>
              {inState.length === 0 ? (
                <p className={styles.empty}>No records in this state.</p>
              ) : (
                <ul className={styles.recordList}>
                  {inState.map((record) => (
                    <li key={record.record_id} id={verdictRecordAnchor(record.record_id)}>
                      <RecordCard
                        record={record}
                        selected={selectedId === record.record_id}
                        showRun={runs.length > 1}
                        onSelect={toggle}
                      />
                    </li>
                  ))}
                </ul>
              )}
            </section>
          );
        })}

        {causes.length > 0 && (
          <section aria-labelledby="why-codes" className={styles.causes}>
            <h2 id="why-codes" className={styles.stateTitle}>
              <span className={styles.stateName}>UNKNOWN why-codes</span>
            </h2>
            <p className={styles.stateMeaning}>
              D-U1 makes the why-code the axis: UNKNOWN never maps to satisfied,
              and the per-cause rate is itself a verdict input (D-7 §5).
            </p>
            <ul className={styles.causeList}>
              {causes.map((group) => (
                <li key={group.cause} className={styles.causeItem}>
                  <span className={styles.whyCode}>{group.cause}</span>
                  <ul className={styles.causeRefs}>
                    {group.records.map((r) => (
                      <li key={r.record_id}>
                        <code className={styles.ref}>{r.record_id}</code>
                      </li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </RailLayout>
  );
}

function RecordCard({
  record,
  selected,
  showRun,
  onSelect,
}: {
  record: VerdictRecord;
  selected: boolean;
  /** Only label runs when more than one exists — a chip on every card in a
   * single-run engagement is noise. */
  showRun: boolean;
  onSelect: (id: string) => void;
}) {
  const meta = verdictStateMeta(record.status);
  const companion = meta.requires ? record[meta.requires] : null;

  return (
    <div className={selected ? `${styles.record} ${styles.recordSelected}` : styles.record}>
      <button
        type="button"
        className={styles.recordButton}
        aria-pressed={selected}
        aria-label={`Select verdict ${record.record_id}`}
        onClick={() => onSelect(record.record_id)}
      >
        <code className={styles.ref}>{record.record_id}</code>
      </button>
      <p className={styles.recordMessage}>{record.message ?? "(no message on the record)"}</p>
      <p className={styles.recordChips}>
        <span className={styles.stateChip}>{record.status}</span>
        {showRun && <span className={styles.runChip}>{record.run_id}</span>}
        {record.unknown_cause && (
          <span className={styles.whyCode}>{record.unknown_cause}</span>
        )}
        <span className={styles.severity}>severity {record.severity ?? "not recorded"}</span>
        {meta.requires && (
          <span className={companion ? styles.companion : styles.companionMissing}>
            {meta.requires}: {companion ? String(companion) : "MISSING"}
          </span>
        )}
      </p>
    </div>
  );
}

function RecordDetail({
  record,
  knownPopulationIds,
  onClear,
}: {
  record: VerdictRecord;
  knownPopulationIds: string[];
  onClear: () => void;
}) {
  const meta = verdictStateMeta(record.status);
  // `support` is optional on the wire and `field_values` optional within it.
  const fields = record.support?.field_values ?? {};

  return (
    <>
      <p className={styles.railBody}>
        <code className={styles.ref}>{record.record_id}</code>
      </p>
      <RailRow label="State">
        <span className={styles.stateChip}>{record.status}</span>
        <p className={styles.railMeta}>{meta.meaning}</p>
      </RailRow>
      <RailRow label="Message">
        <p className={styles.railMeta}>{record.message ?? "(no message on the record)"}</p>
      </RailRow>
      <RailRow label="Population">
        <p className={styles.railMeta}>
          {knownPopulationIds.includes(record.population_id) ? (
            <Link
              className={styles.popLink}
              href={`/reconciliation/${record.population_id}`}
            >
              {record.population_id}
            </Link>
          ) : (
            <>
              {record.population_id}{" "}
              <span className={styles.diagnostic}>
                (no reconciliation report on the wire for this population)
              </span>
            </>
          )}{" "}
          · {record.population_count} members
          <span className={styles.diagnostic}> diagnostic</span>
        </p>
        <p className={styles.railMeta}>
          completeness: {record.completeness_ref}
          <span className={styles.diagnostic}>
            {" "}
            (ref string, not a URL — resolved via population_id)
          </span>
        </p>
      </RailRow>
      <RailRow label="Spec">
        <p className={styles.railMeta}>{record.spec_id}</p>
        <p className={styles.hash}>{record.spec_hash}</p>
      </RailRow>
      <RailRow label="Re-performance">
        <p className={styles.railMeta}>
          {record.source} v{record.source_version} · test fn v
          {record.test_function_version} · schema {record.schema_version}
        </p>
        <p className={styles.hash}>record_hash {record.record_hash}</p>
        <p className={styles.railMeta}>
          chain_prev {record.chain_prev ?? "none — first in chain"}
        </p>
      </RailRow>
      {Object.keys(fields).length > 0 && (
        <RailRow label="Support">
          <ul className={styles.railList}>
            {Object.entries(fields).map(([key, value]) => (
              <li key={key}>
                {key}: {Array.isArray(value) ? value.join(", ") : String(value)}
              </li>
            ))}
          </ul>
        </RailRow>
      )}
      <RailRow label="Evidence">
        <ul className={styles.railList}>
          {record.evidence_refs.map((ref) => (
            <li key={ref} className={styles.hash}>
              {ref}
            </li>
          ))}
        </ul>
      </RailRow>
      <p className={styles.jump}>
        <Link
          className={styles.popLink}
          href={`/proof/${encodeURIComponent(record.record_id)}`}
        >
          Full lineage →
        </Link>
      </p>
      <button type="button" className={styles.clearButton} onClick={onClear}>
        Clear selection
      </button>
    </>
  );
}

function Scorecard({ poisons }: { poisons: PoisonsArtifact }) {
  const card = scorecard(poisons);
  const cases = orderedCases(poisons);

  return (
    <>
      <p className={card.misses.length === 0 ? styles.scoreOk : styles.scoreBad}>
        {detectionRateText(card)} — {card.renderedDetected} of {card.renderedTotal}{" "}
        seeded defects caught.
      </p>
      {!card.agrees && (
        <p className={styles.breach}>
          The artifact states {card.statedDetected}/{card.statedTotal} at rate{" "}
          {card.statedRate}; the cases on screen say {card.renderedDetected}/
          {card.renderedTotal}. The cases are the truth.
        </p>
      )}
      {card.misses.length > 0 && (
        <p className={styles.breach}>
          Misses: {card.misses.join(", ")} — any silent PASS is a build-stopping
          bug (PRD §7).
        </p>
      )}
      <ul className={styles.caseList}>
        {cases.map((poisonCase) => {
          const cls = splitClassification(poisonCase.actual_class);
          return (
            <li
              key={poisonCase.id}
              className={poisonCase.detected ? styles.caseOk : styles.caseMiss}
            >
              <p className={styles.caseHead}>
                <code className={styles.ref}>{poisonCase.id}</code>
                <span className={styles.caseStage}>{poisonCase.stage}</span>
                <span className={poisonCase.detected ? styles.caught : styles.missed}>
                  {poisonCase.detected ? "caught" : "MISSED"}
                </span>
              </p>
              <p className={styles.railMeta}>{poisonCase.poison}</p>
              <p className={styles.railMeta}>
                expected {poisonCase.expected} · actual{" "}
                <span className={styles.stateChip}>{cls.head}</span>
                {cls.cause && <span className={styles.whyCode}> {cls.cause}</span>}
              </p>
              <CaseLinks poisonCase={poisonCase} />
            </li>
          );
        })}
      </ul>
    </>
  );
}

/** Where a poison case's proof lives. Switches on the discriminated
 * PoisonActual kind with a never arm — a third kind fails tsc rather than
 * silently rendering no link. */
function CaseLinks({ poisonCase }: { poisonCase: PoisonCase }) {
  const actual = poisonCase.actual;
  switch (actual.kind) {
    case "verdict":
      return (
        <p className={styles.caseLinks}>
          <Link
            className={styles.popLink}
            href={verdictRecordHref(actual.record.record_id)}
          >
            verdict record →
          </Link>{" "}
          <Link
            className={styles.popLink}
            href={`/proof/${encodeURIComponent(actual.record.record_id)}`}
          >
            lineage →
          </Link>
        </p>
      );
    case "compile_error":
      return (
        <p className={styles.caseLinks}>
          <Link className={styles.popLink} href="/registry">
            E-code on /registry →
          </Link>
        </p>
      );
    default: {
      const exhaustive: never = actual;
      return exhaustive;
    }
  }
}

function RailRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <section className={styles.railSection}>
      <h3 className={styles.railSectionTitle}>{label}</h3>
      {children}
    </section>
  );
}
