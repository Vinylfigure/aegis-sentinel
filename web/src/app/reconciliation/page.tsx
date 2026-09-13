import Link from "next/link";
import type { Metadata } from "next";
import { loadEngagement, ladderCounts } from "@/lib/data/engagement";
import { ASSURANCE_STATES } from "@/lib/types/ontology";
import Ladder from "@/components/ui/Ladder";
import styles from "./Reconciliation.module.css";

export const metadata: Metadata = { title: "Reconciliation — Aegis" };

export default function ReconciliationIndex() {
  const load = loadEngagement();
  const recs = load.artifacts.reconciliations;
  const dist = ladderCounts(load);
  const maxCount = Math.max(...Object.values(dist), 1);

  return (
    <main className="page">
      <div className="page-kicker">populations</div>
      <h1>Reconciliation</h1>
      <p className="page-sub">
        A population is only as good as its denominator. Each board below reconciles
        every declared source into six buckets — and treats what is <em>absent</em>{" "}
        as loudly as what is present.
      </p>

      <div className="section-label">assurance ladder distribution</div>
      <div className={styles.dist}>
        {ASSURANCE_STATES.filter((s) => s !== "STALE" && s !== "UNDEFINED").map((s) => (
          <div key={s} className={styles.distRow}>
            <span className={styles.distLabel}>{s}</span>
            <span className={styles.distTrack}>
              <span
                className={`${styles.distBar} ${dist[s] === 0 ? styles.distBarZero : ""}`}
                style={{ width: `${(dist[s] / maxCount) * 100}%` }}
              />
              <span className={styles.distCount}>{dist[s]}</span>
            </span>
          </div>
        ))}
      </div>

      <div className="section-label">reconciled populations · {recs.length}</div>
      <div className={styles.grid}>
        {recs.map((r) => {
          const pop = load.artifacts.populations.find(
            (p) => p.population_id === r.population_ref
          );
          const open = r.deltas.filter((d) => !d.disposition).length;
          return (
            <Link
              key={r.population_ref}
              href={`/reconciliation/${encodeURIComponent(r.population_ref)}`}
              className={styles.popCard}
            >
              <div className={styles.popHead}>
                <span className={styles.popName}>{pop?.name ?? r.population_ref}</span>
                <span className={styles.popId}>{r.population_ref}</span>
              </div>
              <Ladder current={r.ladder_state} compact />
              <div className={styles.popMeta}>
                <span>
                  <b>{r.members.length}</b> members
                </span>
                <span>
                  <b>{Object.keys(r.source_counts).length}</b> sources
                </span>
                <span className={open > 0 ? styles.deltaWarn : styles.deltaClean}>
                  {open > 0 ? `${open} open delta${open > 1 ? "s" : ""}` : "zero open deltas"}
                </span>
                <span>
                  <b>{r.buckets.excluded.length}</b> excluded w/ disposition
                </span>
              </div>
            </Link>
          );
        })}
      </div>

      <div className="section-label">not reconcilable</div>
      <div className={styles.blockedCard}>
        <b>TERM.gcp.accounts</b> has no reconciliation board — its derivation rule
        names <span className="mono">breakglass.config</span>, which has no ratified
        capability entry (<b>E117</b>). A population that cannot be collected cannot
        be reconciled; the ladder is blocked at DEFINED.{" "}
        <Link href="/registry" style={{ color: "var(--brand)" }}>
          See the capability registry →
        </Link>
      </div>
    </main>
  );
}
