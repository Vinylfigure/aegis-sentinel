"use client";

/* THE acceptance screen: a practitioner looks at this and says "now I
 * know why the population is complete." Ladder stepper (open
 * dispositions visibly block DISCOVERED→RECONCILED), identity-join
 * panel, and the six-bucket set-reconciliation board. The rail carries
 * the assembled WhyCompletePanel narrative; clicking a delta focuses
 * its story there. */

import { useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  loadEngagement,
  populationById,
  reconciliationFor,
} from "@/lib/data/engagement";
import { useEngagementStore } from "@/lib/state/engagementStore";
import { LadderChip, Tip, TypeBadge } from "@/components/engagement/Badges";
import LadderStepper from "@/components/engagement/LadderStepper";
import IdentityJoinPanel from "@/components/engagement/IdentityJoinPanel";
import ReconciliationBoard from "@/components/engagement/ReconciliationBoard";
import SchemaDriftBanner from "@/components/engagement/SchemaDriftBanner";
import styles from "./PopulationDetail.module.css";

export default function PopulationDetailPage() {
  const params = useParams<{ populationId: string }>();
  const populationId = decodeURIComponent(params?.populationId ?? "");
  const load = loadEngagement();
  const population = populationById(load, populationId);
  const recon = reconciliationFor(load, populationId);
  const selectDelta = useEngagementStore((s) => s.selectDelta);

  // Reset delta focus when switching populations.
  useEffect(() => {
    selectDelta(null);
  }, [populationId, selectDelta]);

  if (!population) {
    return (
      <div>
        <SchemaDriftBanner drift={load.drift} />
        <p className="sub">
          No population <code>{populationId}</code> in the engagement bundle.{" "}
          <Link href="/reconciliation">Back to the index.</Link>
        </p>
      </div>
    );
  }

  const openDispositions = recon
    ? recon.deltas.filter((d) => d.bucket !== "intersection" && !d.disposition).length
    : population.open_deltas.length;
  const ratified = population.state === "RATIFIED";

  return (
    <div>
      <SchemaDriftBanner drift={load.drift} />

      <div className={styles.head}>
        <div className={styles.headL}>
          <div className={styles.badges}>
            <TypeBadge type={population.type} />
            <LadderChip state={population.state} />
          </div>
          <h2 className={styles.title}>{population.name}</h2>
          <code className={styles.pid}>{population.population_id}</code>
          <p className={styles.def}>{population.definition}</p>
        </div>
        <div className={styles.headR}>
          <div className={styles.kpi}>
            {ratified && population.size !== null ? (
              <b>{population.size}</b>
            ) : (
              <b className={styles.dash}>
                <Tip tip="Size is withheld until the denominator is RATIFIED — no count is published against an unratified population.">
                  —
                </Tip>
              </b>
            )}
            <span>size</span>
          </div>
          <div className={styles.kpi} data-testid="coverage-kpi">
            {ratified ? (
              <b className={styles.green}>100%</b>
            ) : (
              <b className={styles.dash}>
                <Tip tip="Coverage percentages are never computed against an unratified denominator. This population must reach RATIFIED — every non-intersection delta dispositioned, then a human ratifies the snapshot — before any % renders here.">
                  —
                </Tip>
              </b>
            )}
            <span>coverage</span>
          </div>
          <div className={styles.kpi}>
            <b>
              {population.period.start.slice(5)}–{population.period.end.slice(5)}
            </b>
            <span>period {population.period.start.slice(0, 4)}</span>
          </div>
        </div>
      </div>

      <LadderStepper
        state={population.state}
        openDispositions={openDispositions}
        ratifiedBy={load.artifacts.manifest.ratified_by}
        manifestVersion={load.artifacts.manifest.manifest_version}
      />

      <IdentityJoinPanel population={population} recon={recon} />

      <div className="slab">Set reconciliation — six buckets</div>
      {recon ? (
        <ReconciliationBoard recon={recon} />
      ) : (
        <p className={styles.norecon}>
          No reconciliation run recorded for this population — the reconciler
          runs at DISCOVERED, and this population is {population.state}.
        </p>
      )}

      {population.exclusions.length > 0 && (
        <>
          <div className="slab">Exclusions — never silent</div>
          {population.exclusions.map((x) => (
            <div key={x.member_id} className={styles.exclusion}>
              <code>{x.member_id}</code>
              <span>{x.rationale}</span>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
