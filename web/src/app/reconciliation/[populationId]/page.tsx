import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { loadEngagement, populationById, reconciliationFor } from "@/lib/data/engagement";
import type { Delta } from "@/lib/types/ontology";
import type { DeltaBucket } from "@/lib/types/artifacts";
import Ladder from "@/components/ui/Ladder";
import styles from "./PopulationDetail.module.css";

export const metadata: Metadata = { title: "Reconciliation board — Aegis" };

export function generateStaticParams() {
  const load = loadEngagement();
  return load.artifacts.reconciliations.map((r) => ({
    populationId: r.population_id,
  }));
}

/** Sources that have — and lack — a member sharing this delta's canonical
 * email. Only meaningful for email-joined identities (D-8): an
 * UNRESOLVABLE delta preserves its raw source ref instead (no canonical
 * key was derivable), so there is nothing to compare across sources. */
function presenceAcrossSources(
  delta: Delta,
  sources: { name: string; members: { email: string }[] }[]
): { present: string[]; absent: string[] } | null {
  if (!delta.member_ref.startsWith("email:")) return null;
  const email = delta.member_ref.slice("email:".length);
  const present: string[] = [];
  const absent: string[] = [];
  for (const s of sources) {
    if (s.members.some((m) => m.email === email)) present.push(s.name);
    else absent.push(s.name);
  }
  return { present, absent };
}

function DeltaCard({
  delta,
  sources,
}: {
  delta: Delta;
  sources: { name: string; members: { email: string }[] }[];
}) {
  const open = !delta.disposition;
  const bucketClass =
    delta.bucket === "excluded"
      ? styles.bucketTagExcluded
      : delta.bucket === "unresolvable"
        ? styles.bucketTagUnresolvable
        : "";
  const presence = presenceAcrossSources(delta, sources);
  return (
    <article className={`${styles.deltaCard} ${open ? styles.deltaCardOpen : ""}`}>
      <div className={styles.deltaHead}>
        <span className={styles.deltaMember}>{delta.member_ref}</span>
        <span className={`${styles.bucketTag} ${bucketClass}`}>{delta.bucket}</span>
      </div>

      {presence ? (
        <div className={styles.presence}>
          <div className={styles.presCol}>
            <div className={`${styles.presLabel} ${styles.presLabelGhost}`}>present in</div>
            <div className={styles.presChips}>
              {presence.present.length ? (
                presence.present.map((s) => (
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
              {presence.absent.length ? (
                presence.absent.map((s) => (
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
      ) : (
        <p className={styles.emptyBucket}>
          no canonical email was derivable for this member — it cannot be joined
          against the other sources (cause: identity-fuzzy or basis-missing)
        </p>
      )}

      <div className={styles.deltaFoot}>
        {delta.disposition ? (
          <>
            <span className={styles.dispRef}>
              {delta.member_ref} · {delta.disposition.value}
            </span>
            <span className={styles.dispJust}>{delta.disposition.rationale}</span>
            <span className={styles.ownerTag}>owner {delta.disposition.owner}</span>
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

  const openBuckets = (Object.keys(rec.buckets) as DeltaBucket[]).filter(
    (b) => b !== "intersection"
  );
  const allDeltas = openBuckets.flatMap((b) => rec.buckets[b]);
  const openDeltas = allDeltas.filter((d) => !d.disposition);
  const dispositioned = allDeltas.filter((d) => d.disposition);
  const blockedByOpen = rec.ladder.blocked_by_open_deltas.filter((d) => !d.dispositioned);
  const blocked = blockedByOpen.length > 0;
  const currentState = blocked ? rec.ladder.at_first_verdict : rec.ladder.after_dispositions;

  return (
    <main className="page">
      <div className="page-kicker">reconciliation board</div>
      <h1>{pop?.name ?? id}</h1>
      <p className="page-sub">{pop?.definition}</p>

      <div className={styles.ladderWrap}>
        <Ladder
          current={currentState}
          blockedAfter={blocked ? rec.ladder.at_first_verdict : undefined}
          blockedLabel={blocked ? `${blockedByOpen.length} open` : undefined}
        />
      </div>

      <div className={styles.sourceStrip}>
        {rec.sources.map((s) => (
          <span key={s.name} className={styles.sourceChip}>
            {s.name} <b>{s.members.length}</b>
          </span>
        ))}
        <span className={styles.sourceChip}>joined on canonical email (D-8)</span>
      </div>

      <div className={styles.layout}>
        <div>
          {openDeltas.length > 0 && (
            <>
              <div className="section-label">
                open deltas · {openDeltas.length} — what the sources cannot account for
              </div>
              {openDeltas.map((d) => (
                <DeltaCard key={d.member_ref} delta={d} sources={rec.sources} />
              ))}
            </>
          )}

          {dispositioned.length > 0 && (
            <>
              <div className="section-label">
                dispositioned · {dispositioned.length} — owned, justified, dated
              </div>
              {dispositioned.map((d) => (
                <DeltaCard key={d.member_ref} delta={d} sources={rec.sources} />
              ))}
            </>
          )}

          <div className="section-label">
            intersection · {rec.buckets.intersection.length} members in every expected
            source
          </div>
          {rec.buckets.intersection.length ? (
            <div className={styles.memberGrid}>
              {rec.buckets.intersection.map((d) => (
                <span key={d.member_ref} className={styles.memberChip}>
                  {d.member_ref}
                </span>
              ))}
            </div>
          ) : (
            <p className={styles.emptyBucket}>empty</p>
          )}

          <div className="section-label">conflict · {rec.buckets.conflict.length}</div>
          {rec.buckets.conflict.length ? (
            <div className={styles.memberGrid}>
              {rec.buckets.conflict.map((d) => (
                <span key={d.member_ref} className={styles.memberChip}>
                  {d.member_ref}
                </span>
              ))}
            </div>
          ) : (
            <p className={styles.emptyBucket}>no attribute conflicts between sources</p>
          )}
        </div>

        <aside className={styles.why}>
          <div className={styles.whyTitle}>Why this board is complete</div>
          {!blocked && <div className={styles.whyBasis}>basis complete</div>}
          <p className={styles.whyText}>
            Every declared source was collected <b>to exhaustion</b> — pagination
            drained, counts checked — before a single member was compared. The board
            derives from{" "}
            {rec.sources.map((s) => `${s.name} (${s.members.length})`).join(", ")}
            , joined on <span className="mono">canonical email</span>.
          </p>
          <ul className={styles.whyList}>
            <li>
              <b>{rec.canonical_members.length}</b> members resolved into the population
            </li>
            <li>
              <b>{rec.buckets.intersection.length}</b> corroborated by every expected
              source
            </li>
            <li>
              <b>{allDeltas.length}</b> delta{allDeltas.length === 1 ? "" : "s"} —{" "}
              {openDeltas.length} open, {dispositioned.length} dispositioned; a delta
              is never silently dropped
            </li>
            <li>
              open deltas <b>block the ladder</b>: {blocked ? "this population holds at DISCOVERED until every delta is owned or ratified away" : "none — the board can advance"}
            </li>
          </ul>
          <div className="section-label">counts · diagnostics only</div>
          <div className={styles.diagList}>
            {(Object.entries(rec.counts) as [DeltaBucket, number][]).map(([bucket, n]) => (
              <span key={bucket} className={styles.diagItem}>
                {bucket}: {n}
              </span>
            ))}
          </div>
          <div className={styles.diagMore}>{rec.counts_note}</div>
        </aside>
      </div>
    </main>
  );
}
