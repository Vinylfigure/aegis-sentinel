import Link from "next/link";
import type { Metadata } from "next";
import { loadEngagement } from "@/lib/data/engagement";
import styles from "./Proof.module.css";

export const metadata: Metadata = { title: "Proof lineage — Aegis" };

export default function ProofIndex() {
  const load = loadEngagement();
  const graphs = load.artifacts.proof_graphs;
  const { verdicts } = load.artifacts;

  return (
    <main className="page">
      <div className="page-kicker">lineage</div>
      <h1>Proof graphs</h1>
      <p className="page-sub">
        A verdict you cannot walk backwards is an opinion. Each lineage traces a
        sealed verdict through every artifact that produced it — commitment to
        requirement to claim, population to sources to reconciliation, contract to
        snapshot to assertion.
      </p>

      <div className="section-label">emitted lineages · {graphs.length}</div>
      {graphs.map((g) => {
        const v = verdicts.find((x) => x.record_hash === g.verdict_ref);
        const verdictNode = g.nodes.find((n) => n.kind === "verdict");
        return (
          <Link
            key={g.verdict_ref}
            href={`/proof/${g.verdict_ref.slice(0, 12)}`}
            className={styles.graphCard}
          >
            <div className={styles.graphHead}>
              {v && <span className={`state-badge state-${v.state}`}>{v.state}</span>}
              <span className={styles.graphAssertion}>{v?.assertion_ref}</span>
              <span className={styles.graphStages}>
                {g.nodes.length} stages · {g.edges.length} typed edges
              </span>
            </div>
            <div className={styles.graphLabel}>{verdictNode?.label}</div>
            <div className={styles.graphRef}>verdict {g.verdict_ref.slice(0, 16)}…</div>
          </Link>
        );
      })}

      <div className="section-label">not yet emitted</div>
      <p className={styles.honest}>
        The other {verdicts.length - graphs.length} sealed verdicts have no lineage
        graph in this engagement&apos;s artifacts yet — the pipeline emits P1 lineage
        for the TIMING exhibit first. Nothing is synthesized here: no artifact, no
        graph.
      </p>
    </main>
  );
}
