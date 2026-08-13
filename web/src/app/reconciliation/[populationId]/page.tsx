import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { loadEngagement, populationById, reconciliationFor } from "@/lib/data/engagement";
import type { DeltaObject } from "@/lib/types/artifacts";
import Ladder from "@/components/ui/Ladder";
import styles from "./PopulationDetail.module.css";

export const metadata: Metadata = { title: "Reconciliation board — Aegis" };

export function generateStaticParams() {
  const load = loadEngagement();
  return load.artifacts.reconciliations.map((r) => ({
    populationId: r.population_ref,
  }));
}

function DeltaCard({ delta }: { delta: DeltaObject }) {
  const open = !delta.disposition;
  const bucketClass =
    delta.bucket === "excluded"
      ? styles.bucketTagExcluded
      : delta.bucket === "unresolvable"
        ? styles.bucketTagUnresolvable
        : "";
  return (
    <article className={`${styles.deltaCard} ${open ? styles.deltaCardOpen : ""}`}>
      <div className={styles.deltaHead}>
        <span className={styles.deltaMember}>{delta.display_name}</span>
        <span className={`${styles.bucketTag} ${bucketClass}`}>{delta.bucket}</span>
        <span className={styles.deltaId}>{delta.delta_id}</span>
      </div>

      <div className={styles.presence}>
        <div className={styles.presCol}>
          <div className={`${styles.presLabel} ${styles.presLabelGhost}`}>present in</div>
          <div className={styles.presChips}>
            {delta.sources_present.length ? (
              delta.sources_present.map((s) => (
                <span key={s} className={`${styles.presChip} ${styles.presChipGhost}`}>
                  {s}
                </span>
              ))
            ) : (
              <span className={styles.presEmpty}>nowhere</span>
            )}
          </div>
        </div>
        <div className={styles.presCol}>
          <div className={`${styles.presLabel} ${styles.presLabelAbsent}`}>
            absent from — the negative space
          </div>
          <div className={styles.presChips}>
            {delta.sources_absent.length ? (
              delta.sources_absent.map((s) => (
                <span key={s} className={`${styles.presChip} ${styles.presChipAbsent}`}>
                  {s}
                </span>
              ))
            ) : (
              <span className={styles.presEmpty}>present everywhere expected</span>
            )}
          </div>
        </div>
      </div>

      <div className={styles.deltaFoot}>
        {delta.disposition ? (
          <>
            <span className={styles.dispRef}>
              {delta.disposition_ref} · {delta.disposition.value}
            </span>
            <span className={styles.dispJust}>{delta.disposition.justification}</span>
            <span className={styles.ownerTag}>
              owner {delta.disposition.owner} · review {delta.disposition.review_date}
            </span>
          </>
        ) : (
          <>
            <span className={styles.undisp}>UNDISPOSITIONED</span>
            <span>
              blocks RECONCILED — a population with an unowned delta cannot be shown
              complete
            </span>
            <span className={styles.ownerTag}>owner {delta.owner ?? "unassigned"}</span>
          </>
        )}
      </div>
    </article>
  );
}

export default async function PopulationDetail({
  params,
}: {
  params: Promise<{ populationId: string }>;
}) {
  const { populationId } = await params;
  const id = decodeURIComponent(populationId);
  const load = loadEngagement();
  const rec = reconciliationFor(load, id);
  const pop = populationById(load, id);
  if (!rec) notFound();

  const openDeltas = rec.deltas.filter((d) => !d.disposition);
  const dispositioned = rec.deltas.filter((d) => d.disposition);
  const blocked = openDeltas.length > 0;
  const shownDiags = rec.diagnostics.slice(0, 4);

  return (
    <main className="page">
      <div className="page-kicker">reconciliation board</div>
      <h1>{pop?.name ?? id}</h1>
      <p className="page-sub">{pop?.definition}</p>

      <div className={styles.ladderWrap}>
        <Ladder
          current={rec.ladder_state}
          blockedAfter={blocked ? "DISCOVERED" : undefined}
          blockedLabel={blocked ? `${openDeltas.length} open` : undefined}
        />
      </div>

      <div className={styles.sourceStrip}>
        {Object.entries(rec.source_counts).map(([src, n]) => (
          <span key={src} className={styles.sourceChip}>
            {src} <b>{n}</b>
          </span>
        ))}
        <span className={styles.sourceChip}>
          keys <b>{rec.canonical_identity_keys.join(" · ")}</b>
        </span>
      </div>

      <div className={styles.layout}>
        <div>
          {openDeltas.length > 0 && (
            <>
              <div className="section-label">
                open deltas · {openDeltas.length} — what the sources cannot account for
              </div>
              {openDeltas.map((d) => (
                <DeltaCard key={d.delta_id} delta={d} />
              ))}
            </>
          )}

          {dispositioned.length > 0 && (
            <>
              <div className="section-label">
                dispositioned · {dispositioned.length} — owned, justified, dated
              </div>
              {dispositioned.map((d) => (
                <DeltaCard key={d.delta_id} delta={d} />
              ))}
            </>
          )}

          <div className="section-label">
            intersection · {rec.buckets.intersection.length} members in every expected
            source
          </div>
          {rec.buckets.intersection.length ? (
            <div className={styles.memberGrid}>
              {rec.buckets.intersection.map((m) => (
                <span key={m} className={styles.memberChip}>
                  {m}
                </span>
              ))}
            </div>
          ) : (
            <p className={styles.emptyBucket}>empty</p>
          )}

          <div className="section-label">conflicts · {rec.buckets.conflicts.length}</div>
          {rec.buckets.conflicts.length ? (
            <div className={styles.memberGrid}>
              {rec.buckets.conflicts.map((m) => (
                <span key={m} className={styles.memberChip}>
                  {m}
                </span>
              ))}
            </div>
          ) : (
            <p className={styles.emptyBucket}>no attribute conflicts between sources</p>
          )}
        </div>

        <aside className={styles.why}>
          <div className={styles.whyTitle}>Why this board is complete</div>
          {rec.basis_complete && (
            <div className={styles.whyBasis}>basis complete</div>
          )}
          <p className={styles.whyText}>
            Every declared source was collected <b>to exhaustion</b> — pagination
            drained, counts checked — before a single member was compared. The board
            derives from{" "}
            {Object.entries(rec.source_counts)
              .map(([s, n]) => `${s} (${n})`)
              .join(", ")}
            , joined on{" "}
            <span className="mono">{rec.canonical_identity_keys.join(", ")}</span>.
          </p>
          <ul className={styles.whyList}>
            <li>
              <b>{rec.members.length}</b> members resolved into the population
            </li>
            <li>
              <b>{rec.buckets.intersection.length}</b> corroborated by every expected
              source
            </li>
            <li>
              <b>{rec.deltas.length}</b> delta{rec.deltas.length === 1 ? "" : "s"} —{" "}
              {openDeltas.length} open, {dispositioned.length} dispositioned; a delta
              is never silently dropped
            </li>
            <li>
              open deltas <b>block the ladder</b>: {blocked ? "this population holds at DISCOVERED until every delta is owned or ratified away" : "none — the board can advance"}
            </li>
          </ul>
          {rec.diagnostics.length > 0 && (
            <>
              <div className="section-label">diagnostics · non-blocking</div>
              <div className={styles.diagList}>
                {shownDiags.map((d) => (
                  <span key={d} className={styles.diagItem}>
                    {d}
                  </span>
                ))}
              </div>
              {rec.diagnostics.length > shownDiags.length && (
                <div className={styles.diagMore}>
                  + {rec.diagnostics.length - shownDiags.length} more out-of-scope
                  observations
                </div>
              )}
            </>
          )}
        </aside>
      </div>
    </main>
  );
}
