"use client";

/* Verdict table grouped by claim → assertion rows. Five verdict states
 * with unmistakably distinct treatments; compile-error rows styled as
 * what they are — compiler errors. Rows link to the proof lineage. */

import Link from "next/link";
import { loadEngagement } from "@/lib/data/engagement";
import { MiniChip, VerdictBadge } from "@/components/engagement/Badges";
import MutationScorecard from "@/components/engagement/MutationScorecard";
import SchemaDriftBanner from "@/components/engagement/SchemaDriftBanner";
import styles from "./Verdicts.module.css";

export default function VerdictsPage() {
  const load = loadEngagement();
  const { claims, verdicts, compile_errors } = load.artifacts;

  return (
    <div>
      <SchemaDriftBanner drift={load.drift} />
      <p className="sub">
        One verdict per (claim, assertion, population) triple, produced by the
        pure evaluator against the ratified snapshot. PASS · FAIL · UNKNOWN ·
        EXCLUDED · EXCEPTION — never interchangeable. An assertion that cannot
        be proven does not run and lie; it fails to compile.
      </p>

      {claims.map((claim) => {
        const claimErrors = compile_errors.filter((e) => e.claim_ref === claim.claim_id);
        return (
          <div key={claim.claim_id} className={styles.claim}>
            <div className={styles.claimHead}>
              <code className={styles.claimId}>{claim.claim_id}</code>
              <b className={styles.claimStmt}>{claim.statement}</b>
              <span className={styles.maps}>
                {claim.framework_mappings.map((m) => (
                  <MiniChip key={`${m.framework}-${m.control_id}`} tone="cyan">
                    {m.framework} {m.control_id}
                  </MiniChip>
                ))}
              </span>
            </div>

            {claim.assertions.map((a) => {
              const v = verdicts.find((x) => x.assertion_ref === a.assertion_id);
              const err = claimErrors.find((e) => e.assertion_ref === a.assertion_id);
              if (!v && err) {
                return (
                  <div key={a.assertion_id} className={styles.errRow} data-testid="compile-error-row">
                    <span className={styles.errCode}>{err.code}</span>
                    <div className={styles.errBody}>
                      <span className={styles.errAssert}>
                        {a.assertion_id} · {a.type} — did not compile
                      </span>
                      <p className={styles.errMsg}>{err.message}</p>
                      {err.suggestion && (
                        <p className={styles.errSuggest}>↳ {err.suggestion}</p>
                      )}
                    </div>
                  </div>
                );
              }
              if (!v) return null;
              const row = (
                <div className={styles.row} data-verdict-row={v.verdict_id}>
                  <div className={styles.rowL}>
                    <code className={styles.aid}>{a.assertion_id}</code>
                    <MiniChip tone={a.type === "TIMING" ? "purple" : "dim"}>{a.type}</MiniChip>
                  </div>
                  <div className={styles.pred}>
                    {a.predicate_text}
                    {v.message && <span className={styles.msg}>{v.message}</span>}
                  </div>
                  <div className={styles.rowR}>
                    <VerdictBadge state={v.state} />
                    {v.state === "UNKNOWN" && v.why_code && (
                      <MiniChip tone="amber">{v.why_code}</MiniChip>
                    )}
                    {v.state === "UNKNOWN" && v.d7_family && (
                      <MiniChip tone="dim" title="D-7 cause family">
                        {v.d7_family}
                      </MiniChip>
                    )}
                    {v.state === "EXCLUDED" && v.ratification_ref && (
                      <MiniChip tone="dim">{v.ratification_ref}</MiniChip>
                    )}
                    {v.state === "EXCEPTION" && v.disposition_ref && (
                      <MiniChip tone="purple">{v.disposition_ref}</MiniChip>
                    )}
                  </div>
                </div>
              );
              return (
                <Link
                  key={a.assertion_id}
                  href={`/proof/${v.verdict_id}`}
                  className={styles.rowLink}
                >
                  {row}
                </Link>
              );
            })}
          </div>
        );
      })}

      <MutationScorecard />
    </div>
  );
}
