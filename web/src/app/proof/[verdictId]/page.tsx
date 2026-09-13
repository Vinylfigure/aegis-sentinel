import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { loadEngagement, proofGraphFor, verdictBySlug } from "@/lib/data/engagement";
import ProofCanvas from "@/components/flow/ProofCanvas";
import styles from "../Proof.module.css";

export const metadata: Metadata = { title: "Proof lineage — Aegis" };

export function generateStaticParams() {
  const load = loadEngagement();
  return load.artifacts.proof_graphs.map((g) => ({
    verdictId: g.verdict_ref.slice(0, 12),
  }));
}

export default async function ProofDetail({
  params,
}: {
  params: Promise<{ verdictId: string }>;
}) {
  const { verdictId } = await params;
  const load = loadEngagement();
  const graph = proofGraphFor(load, verdictId);
  if (!graph) notFound();
  const verdict = verdictBySlug(load, verdictId);

  return (
    <main className="page">
      <div className="page-kicker">proof lineage</div>
      <h1>{verdict?.assertion_ref ?? graph.verdict_ref.slice(0, 12)}</h1>
      <p className="page-sub">
        {graph.nodes.length} stages, every edge typed — walk the sealed verdict back
        to the commitment that demanded it. Same canvas language as the lane: this{" "}
        <em>is</em> the flow, zoomed into one verdict.
      </p>

      <div className={styles.verdictStrip}>
        {verdict && (
          <>
            <span className={`state-badge state-${verdict.state}`}>{verdict.state}</span>
            <span className={styles.stripAssertion}>{verdict.assertion_ref}</span>
            <span className={styles.stripHash}>record {verdict.record_hash.slice(0, 16)}…</span>
            <Link href="/verdicts" className={styles.backLink}>
              open in ledger →
            </Link>
            <span className={styles.stripMsg}>{verdict.message}</span>
          </>
        )}
      </div>

      <ProofCanvas graph={graph} />
    </main>
  );
}
