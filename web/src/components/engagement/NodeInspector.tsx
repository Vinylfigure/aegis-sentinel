"use client";

/* Node inspector for the proof graph rail. Resolves the clicked node to
 * its underlying record. The population node embeds the SAME
 * WhyCompletePanel the reconciliation screen uses — one narrative, two
 * doors — plus a link to the acceptance screen. */

import Link from "next/link";
import type { ProofNode } from "@/lib/types/artifacts";
import {
  loadEngagement,
  populationById,
  reconciliationFor,
  verdictBySlug,
} from "@/lib/data/engagement";
import { LadderChip, MiniChip, SourceRoleTag, VerdictBadge } from "./Badges";
import WhyCompletePanel from "./WhyCompletePanel";
import styles from "./NodeInspector.module.css";

export default function NodeInspector({ node }: { node: ProofNode }) {
  const load = loadEngagement();
  const { artifacts } = load;

  const population = node.kind === "population" ? populationById(load, node.ref) : undefined;
  // Verdict nodes ref the full record_hash.
  const verdict = node.kind === "verdict" ? verdictBySlug(load, node.ref) : undefined;
  // Assertion nodes ref the assertion_id; its verdict carries the triple.
  const assertionVerdict =
    node.kind === "assertion"
      ? artifacts.verdicts.find((v) => v.assertion_ref === node.ref)
      : undefined;
  // Source nodes ref a population-yielding source id; the capability entry
  // that yields it is the underlying record.
  const capability =
    node.kind === "source"
      ? artifacts.capability_registry.find((e) =>
          e.populations_yielded.some((p) => p.name === node.ref)
        )
      : undefined;
  const sourceRole =
    node.kind === "source"
      ? artifacts.populations
          .flatMap((p) => p.sources)
          .find((s) => s.source_id === node.ref)?.role
      : undefined;

  return (
    <div className={styles.inspector} data-testid="node-inspector">
      <div className={styles.kind}>{node.kind}</div>
      <h3 className={styles.label}>{node.label}</h3>
      <code className={styles.ref}>{node.ref}</code>

      {node.kind === "verdict" && verdict && (
        <div className={styles.body}>
          <VerdictBadge state={verdict.state} size="lg" />
          {verdict.message && <p className={styles.msg}>{verdict.message}</p>}
          <div className={styles.frows}>
            <div className={styles.frow}>
              <label>triple</label>
              <div>
                {verdict.claim_ref} · {verdict.assertion_ref} · {verdict.population_ref}
              </div>
            </div>
            <div className={styles.frow}>
              <label>manifest / snapshot / contract</label>
              <div className={styles.hashes}>
                {verdict.manifest_version} · {verdict.snapshot_hash.slice(0, 12)}… ·{" "}
                {verdict.contract_hash.slice(0, 12)}…
              </div>
            </div>
            <div className={styles.frow}>
              <label>record_hash</label>
              <div className={styles.hashes}>{verdict.record_hash.slice(0, 24)}…</div>
            </div>
            <div className={styles.frow}>
              <label>evidence</label>
              <div className={styles.hashes}>
                {verdict.evidence_refs.map((r) => (
                  <div key={r}>{r.length > 40 ? `${r.slice(0, 38)}…` : r}</div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {node.kind === "population" && population && (
        <div className={styles.body}>
          <div className={styles.popRow}>
            <LadderChip state={population.state} />
            <Link
              href={`/reconciliation/${population.population_id}`}
              className={styles.popLink}
            >
              open acceptance screen →
            </Link>
          </div>
          <div className={styles.embed}>
            <WhyCompletePanel
              population={population}
              recon={reconciliationFor(load, population.population_id)}
            />
          </div>
        </div>
      )}

      {node.kind === "assertion" && (
        <div className={styles.body}>
          {assertionVerdict && (
            <div className={styles.popRow}>
              <MiniChip tone="purple">evaluated</MiniChip>
              <VerdictBadge state={assertionVerdict.state} />
            </div>
          )}
          <p className={styles.msg}>
            A lettered, typed, testable attribute of its claim — the type
            constrains what evidence may prove it.
          </p>
          {assertionVerdict && (
            <div className={styles.frow}>
              <label>population</label>
              <div>{assertionVerdict.population_ref}</div>
            </div>
          )}
        </div>
      )}

      {node.kind === "claim" && (
        <div className={styles.body}>
          <p className={styles.msg}>
            The semantic unit: a testable proposition over a subject population,
            decomposed into typed assertions. Framework mappings are
            projections onto the claim, never the claim itself.
          </p>
          <div className={styles.mapChips}>
            {artifacts.verdicts
              .filter((v) => v.claim_ref === node.ref)
              .map((v) => (
                <MiniChip key={v.record_hash} tone="cyan">
                  {v.assertion_ref}
                </MiniChip>
              ))}
          </div>
        </div>
      )}

      {node.kind === "source" && (
        <div className={styles.body}>
          {sourceRole && (
            <div className={styles.popRow}>
              <SourceRoleTag role={sourceRole} />
            </div>
          )}
          {capability ? (
            <div className={styles.frows}>
              <div className={styles.frow}>
                <label>capability entry</label>
                <div className={styles.hashes}>{capability.entry_id}</div>
              </div>
              <div className={styles.frow}>
                <label>surface</label>
                <div className={styles.hashes}>{capability.surface}</div>
              </div>
              <div className={styles.frow}>
                <label>temporal</label>
                <div>
                  {capability.temporal.kind}
                  {capability.temporal.window_days != null
                    ? ` (${capability.temporal.window_days}d window)`
                    : ""}
                </div>
              </div>
              {capability.history_caveats.length > 0 && (
                <p className={styles.caveat}>{capability.history_caveats[0]}</p>
              )}
              <Link href="/registry" className={styles.popLink}>
                open capability registry →
              </Link>
            </div>
          ) : (
            <p className={styles.caveat}>No ratified capability entry for this source.</p>
          )}
        </div>
      )}

      {(node.kind === "commitment" ||
        node.kind === "requirement" ||
        node.kind === "reconciliation" ||
        node.kind === "contract" ||
        node.kind === "snapshot") && (
        <div className={styles.body}>
          <p className={styles.msg}>
            {node.kind === "commitment" &&
              "The obligation chain starts here — scope provenance reads as a chain, never a data-tag reflex."}
            {node.kind === "requirement" &&
              "The obligation this commitment imposes, before it is mechanized as a testable claim."}
            {node.kind === "reconciliation" &&
              "Set-based reconciliation over the declared sources — the six buckets are the completeness argument."}
            {node.kind === "contract" &&
              "Evidence Quality Contract: identity + five quality properties. Declares which assertion types this evidence may prove."}
            {node.kind === "snapshot" &&
              "Immutable WORM snapshot — the artifact every verdict re-performs against. SHA-256 pinned in the manifest."}
          </p>
        </div>
      )}
    </div>
  );
}
