"use client";

import { useState } from "react";
import { LadderStepper } from "@/components/LadderStepper/LadderStepper";
import { RailLayout } from "@/components/RailLayout/RailLayout";
import {
  formatPeriod,
  openBlockers,
  reconciledClaimHolds,
  type ReconciliationReport,
  type RegistryArtifact,
} from "@/data";
import { BucketBoard } from "./BucketBoard";
import { IdentityJoinPanel } from "./IdentityJoinPanel";
import { WhyCompleteRail } from "./WhyCompleteRail";
import styles from "../reconciliation.module.css";

/**
 * B2 detail host. Sole state holder: which member_ref is selected, shared by
 * the join matrix, the bucket board and the rail (A5's ProcessGraph shape).
 * Everything else is a pure function of `report`.
 *
 * Invariant №11 (docs/invariants.md): dispositions, ratification and
 * residual-UNKNOWN acceptance are manual by design. This surface DISPLAYS and
 * ATTRIBUTES the human act — there is no control anywhere on this page that
 * sets a disposition.
 */
export function ReconciliationDetail({
  report,
  registry,
}: {
  report: ReconciliationReport;
  registry: RegistryArtifact;
}) {
  const [selectedRef, setSelectedRef] = useState<string | null>(null);

  const blockers = openBlockers(report);
  const claimHolds = reconciledClaimHolds(report);

  const toggle = (ref: string) =>
    setSelectedRef((current) => (current === ref ? null : ref));

  const rail = (
    <WhyCompleteRail
      report={report}
      blockers={blockers}
      claimHolds={claimHolds}
      selectedRef={selectedRef}
      onClear={() => setSelectedRef(null)}
    />
  );

  return (
    <RailLayout rail={rail} railLabel="Why this population is complete">
      <div className={styles.main}>
        <h1 className={styles.h1}>{report.population_name}</h1>
        <p className={styles.sub}>{report.definition}</p>
        <p className={styles.cardMeta}>
          <code className={styles.ref}>{report.population_id}</code>
          <span className={styles.metaSep}>·</span>
          {report.population_type}
          <span className={styles.metaSep}>·</span>
          {report.tenant}
          <span className={styles.metaSep}>·</span>
          {formatPeriod(report.period)}
        </p>

        <section aria-labelledby="step-ladder" className={styles.section}>
          <h2 id="step-ladder" className={styles.step}>
            1 · Assurance ladder
          </h2>
          <LadderStepper ladder={report.ladder} blockers={blockers} claimHolds={claimHolds} />
        </section>

        <section aria-labelledby="step-join" className={styles.section}>
          <h2 id="step-join" className={styles.step}>
            2 · Canonical identity join
          </h2>
          <IdentityJoinPanel
            report={report}
            registry={registry}
            selectedRef={selectedRef}
            onSelect={toggle}
          />
        </section>

        <section aria-labelledby="step-buckets" className={styles.section}>
          <h2 id="step-buckets" className={styles.step}>
            3 · Deltas — the six buckets
          </h2>
          <BucketBoard report={report} selectedRef={selectedRef} onSelect={toggle} />
        </section>
      </div>
    </RailLayout>
  );
}
