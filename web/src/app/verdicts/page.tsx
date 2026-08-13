"use client";

/* Verdict table grouped by claim → assertion rows, rendered from the
 * REAL pipeline verdicts (identity = record_hash; rows route on its
 * URL-safe prefix). Five verdict states with unmistakably distinct
 * treatments; compile-error rows render the compiler's `rendered`
 * string verbatim — an assertion that cannot be proven does not run
 * and lie; it fails to compile. */

import Link from "next/link";
import { loadEngagement, verdictSlug } from "@/lib/data/engagement";
import type { CompileError } from "@/lib/types/artifacts";
import type { VerdictRecord } from "@/lib/types/ontology";
import { MiniChip, VerdictBadge } from "@/components/engagement/Badges";
import MutationScorecard from "@/components/engagement/MutationScorecard";
import SchemaDriftBanner from "@/components/engagement/SchemaDriftBanner";
import styles from "./Verdicts.module.css";

interface ClaimGroup {
  claim_ref: string;
  population_ref: string | null;
  verdicts: VerdictRecord[];
  errors: CompileError[];
}

function groupByClaim(
  verdicts: VerdictRecord[],
  errors: CompileError[]
): ClaimGroup[] {
  const order: string[] = [];
  const byClaim = new Map<string, ClaimGroup>();
  const groupFor = (claim_ref: string): ClaimGroup => {
    let g = byClaim.get(claim_ref);
    if (!g) {
      g = { claim_ref, population_ref: null, verdicts: [], errors: [] };
      byClaim.set(claim_ref, g);
      order.push(claim_ref);
    }
    return g;
  };
  for (const v of verdicts) {
    const g = groupFor(v.claim_ref);
    g.verdicts.push(v);
    g.population_ref ??= v.population_ref;
  }
  for (const e of errors) groupFor(e.claim_ref).errors.push(e);
  return order.map((c) => byClaim.get(c)!);
}

export default function VerdictsPage() {
  const load = loadEngagement();
  const { verdicts, compile_errors } = load.artifacts;
  const groups = groupByClaim(verdicts, compile_errors);

  return (
    <div>
      <SchemaDriftBanner drift={load.drift} />
      <p className="sub">
        One sealed record per (claim, assertion, population) triple, produced by
        the pure evaluator against the ratified snapshot — {verdicts.length}{" "}
        records, identity = record_hash. PASS · FAIL · UNKNOWN · EXCLUDED ·
        EXCEPTION — never interchangeable. An assertion that cannot be proven
        does not run and lie; it fails to compile.
      </p>

      {groups.map((group) => (
        <div key={group.claim_ref} className={styles.claim}>
          <div className={styles.claimHead}>
            <code className={styles.claimId}>{group.claim_ref}</code>
            {group.population_ref && (
              <span className={styles.maps}>
                <MiniChip tone="cyan">{group.population_ref}</MiniChip>
              </span>
            )}
          </div>

          {group.verdicts.map((v) => {
            const slug = verdictSlug(v);
            return (
              <Link key={v.record_hash} href={`/proof/${slug}`} className={styles.rowLink}>
                <div className={styles.row} data-verdict-row={slug}>
                  <div className={styles.rowL}>
                    <code className={styles.aid}>{v.assertion_ref}</code>
                    <code className={styles.hash} title={`record_hash ${v.record_hash}`}>
                      {slug}…
                    </code>
                  </div>
                  <div className={styles.pred}>
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
              </Link>
            );
          })}

          {group.errors.map((err) => (
            <div
              key={`${err.code}-${err.assertion_ref ?? err.claim_ref}`}
              className={styles.errRow}
              data-testid="compile-error-row"
            >
              <div className={styles.errBody}>
                <span className={styles.errAssert}>
                  {err.assertion_ref ?? err.claim_ref} — did not compile
                  {err.code === "E204" && group.verdicts.length > 0
                    ? " as asked; the verdict above covers the re-scoped honest window"
                    : ""}
                </span>
                <pre className={styles.errRendered}>{err.rendered}</pre>
                {err.satisfiable_via && err.satisfiable_via.length > 0 && (
                  <p className={styles.errSuggest}>
                    ↳ satisfiable via {err.satisfiable_via.join(", ")}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      ))}

      <MutationScorecard />
    </div>
  );
}
