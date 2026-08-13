import Link from "next/link";
import type { Metadata } from "next";
import { loadEngagement, proofGraphFor, verdictSlug } from "@/lib/data/engagement";
import { detectionRate, mutationPoisons } from "@/lib/data/mutations";
import styles from "./Verdicts.module.css";

export const metadata: Metadata = { title: "Verdict ledger — Aegis" };

export default function VerdictsPage() {
  const load = loadEngagement();
  const { verdicts, compile_errors } = load.artifacts;
  const poisons = mutationPoisons(load);
  const rate = detectionRate(load);

  return (
    <main className="page">
      <div className="page-kicker">ledger</div>
      <h1>Sealed verdicts</h1>
      <p className="page-sub">
        Every row is a deterministic verdict record sealed under manifest{" "}
        {load.artifacts.manifest.manifest_version} — re-performable from the same
        snapshot, same contract, same code. Nothing here was written by an agent.
      </p>

      <div className="section-label">verdict records · {verdicts.length}</div>
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>State</th>
              <th>Assertion</th>
              <th>Finding</th>
              <th>Population</th>
              <th>Record hash</th>
              <th>Lineage</th>
            </tr>
          </thead>
          <tbody>
            {verdicts.map((v) => {
              const proof = proofGraphFor(load, v.record_hash);
              return (
                <tr key={v.record_hash}>
                  <td>
                    <span className={`state-badge state-${v.state}`}>{v.state}</span>
                  </td>
                  <td>
                    <div className={styles.assertion}>{v.assertion_ref}</div>
                    <div className={styles.claim}>
                      {v.claim_ref}
                      {v.why_code && <> · {v.why_code}</>}
                      {v.d7_family && <> · D-7 {v.d7_family}</>}
                      {v.disposition_ref && <> · {v.disposition_ref}</>}
                      {v.ratification_ref && <> · {v.ratification_ref}</>}
                    </div>
                  </td>
                  <td>
                    <div className={`${styles.msg} ${styles.msgClamp}`} title={v.message ?? ""}>
                      {v.message}
                    </div>
                  </td>
                  <td className={styles.refCell}>{v.population_ref}</td>
                  <td className={styles.hashCell}>{v.record_hash.slice(0, 12)}…</td>
                  <td>
                    {proof ? (
                      <Link href={`/proof/${verdictSlug(v)}`} className={styles.proofLink}>
                        proof →
                      </Link>
                    ) : (
                      <span className={styles.noProof}>none emitted</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="section-label">compile errors · claims that refused to evaluate</div>
      {compile_errors.map((e) => (
        <div key={e.code + e.claim_ref} className={styles.ecodeRow}>
          <span className={styles.ecode}>{e.code}</span>
          <span className={styles.ecodeText}>{e.rendered.replace(/^E\d+\s+/, "")}</span>
        </div>
      ))}

      <div className="section-label">mutation scorecard · seeded-poison detection</div>
      <div className={styles.scoreHead}>
        <div className={styles.scoreStat}>
          <span className={styles.scoreNum}>
            {rate.detected}
            <small>/{rate.total}</small>
          </span>
          <span className={styles.scoreMeter} aria-hidden>
            {Array.from({ length: rate.total }).map((_, i) => (
              <span
                key={i}
                className={`${styles.scoreSeg} ${i < rate.detected ? styles.scoreSegOn : ""}`}
              />
            ))}
          </span>
          <span className={styles.scoreLabel}>
            seeded defects that produced a compile error, UNKNOWN, or FAIL — a silent
            PASS is a build-stopping bug
          </span>
        </div>
      </div>
      <div className={styles.poisonGrid}>
        {poisons.map((p) => (
          <div key={p.id} className={styles.poisonRow}>
            <div className={styles.poisonName}>
              {p.poison}
              <div className={styles.poisonNote}>{p.detector.note}</div>
            </div>
            <span className={styles.detectorChip}>
              {p.detector.kind === "verdict" && <>caught by {p.detector.state}</>}
              {p.detector.kind === "ecode" && <>caught at compile · {p.detector.code}</>}
              {p.detector.kind === "missing" && <>NOT DETECTED</>}
            </span>
            <span className={styles.detected}>{p.detected ? "✓ detected" : "✗ missed"}</span>
          </div>
        ))}
      </div>
    </main>
  );
}
