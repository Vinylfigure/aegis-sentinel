"use client";

/* The assembled "why is this population complete" narrative: derivation
 * rule, source roles, bucket totals, disposition status, ladder state.
 * When a delta is focused, its story leads the panel. Shared component:
 * the reconciliation detail rail AND the proof graph's population
 * inspector both import THIS file. */

import { DELTA_BUCKETS } from "@/lib/types/artifacts";
import type { ReconciliationResult } from "@/lib/types/artifacts";
import type { Population } from "@/lib/types/ontology";
import { useEngagementStore } from "@/lib/state/engagementStore";
import {
  DispositionBadge,
  GhostChip,
  LadderChip,
  PresentChip,
  SourceRoleTag,
} from "./Badges";
import { BUCKET_LABEL } from "./ReconciliationBoard";
import styles from "./WhyCompletePanel.module.css";

const BUCKET_STORY: Record<string, string> = {
  intersection: "agreed by every declared source — membership corroborated.",
  left_only:
    "observed on the left side only. The absence chips are the negative space: an expected source failed to reconcile this member.",
  right_only:
    "observed downstream only — an account with no IdP anchor. Exactly what counts can never surface.",
  conflicts: "sources disagree on an attribute; a canonical value must be fixed and owned.",
  unresolvable:
    "the identity join failed — this member cannot be attached to the canonical universe. Routes to the human resolution queue (identity_fuzzy).",
  excluded: "removed from the universe by rule — visible, dispositioned, never silent.",
};

export default function WhyCompletePanel({
  population,
  recon,
}: {
  population: Population;
  recon?: ReconciliationResult;
}) {
  const selectedDeltaId = useEngagementStore((s) => s.selectedDeltaId);
  const focused = recon?.deltas.find((d) => d.delta_id === selectedDeltaId);

  const totals = DELTA_BUCKETS.map((b) => ({
    bucket: b,
    n: recon ? recon.deltas.filter((d) => d.bucket === b).length : 0,
  }));
  const needing = recon
    ? recon.deltas.filter((d) => d.bucket !== "intersection")
    : [];
  const open = needing.filter((d) => !d.disposition).length;
  const dispositioned = needing.length - open;

  return (
    <div className={styles.panel} data-testid="why-complete">
      <h2 className={styles.h2}>Why is this population complete?</h2>

      {focused && (
        <div className={styles.focus} data-testid="focused-delta">
          <div className={styles.focusHead}>
            <span className={styles.focusId}>{focused.delta_id}</span>
            <span className={styles.focusBucket}>{BUCKET_LABEL[focused.bucket]}</span>
          </div>
          <div className={styles.focusKey}>
            {focused.member_key}
            {focused.display_name ? ` — ${focused.display_name}` : ""}
          </div>
          <div className={styles.focusChips}>
            {focused.sources_present.map((s) => (
              <PresentChip key={s} source={s} />
            ))}
            {focused.sources_absent.map((s) => (
              <GhostChip key={s} source={s} />
            ))}
          </div>
          <p className={styles.focusStory}>{BUCKET_STORY[focused.bucket]}</p>
          {focused.disposition ? (
            <p className={styles.focusDisp}>
              <DispositionBadge disposition={focused.disposition} />
              <span>
                {focused.disposition.justification} — {focused.disposition.owner},
                review {focused.disposition.review_date}
              </span>
            </p>
          ) : focused.bucket !== "intersection" ? (
            <p className={styles.focusDisp}>
              <DispositionBadge />
              <span>
                Owner {focused.owner ?? "unassigned"} must disposition this delta
                before the ladder can advance.
              </span>
            </p>
          ) : null}
        </div>
      )}

      <div className={styles.block}>
        <label>Derivation rule</label>
        <p className={styles.rule}>{population.derivation_rule.rule_text}</p>
      </div>

      <div className={styles.block}>
        <label>Source roles</label>
        {population.sources.map((s) => (
          <div key={s.source_id} className={styles.srcRow}>
            <span className={styles.srcId}>{s.source_id}</span>
            <SourceRoleTag role={s.role} />
          </div>
        ))}
      </div>

      {recon && (
        <div className={styles.block}>
          <label>Bucket totals</label>
          <div className={styles.totals}>
            {totals.map((t) => (
              <div key={t.bucket} className={styles.total}>
                <b>{t.n}</b>
                <span>{BUCKET_LABEL[t.bucket]}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className={styles.block}>
        <label>Disposition status</label>
        <p className={open ? styles.dispOpen : styles.dispClear}>
          {recon
            ? open
              ? `${open} open · ${dispositioned} dispositioned — open dispositions block DISCOVERED → RECONCILED.`
              : `All ${dispositioned} non-intersection deltas dispositioned — nothing exits silently.`
            : "No reconciliation run recorded for this population yet."}
        </p>
      </div>

      <div className={styles.block}>
        <label>Ladder state</label>
        <div className={styles.ladderRow}>
          <LadderChip state={population.state} />
          <span className={styles.ladderNote}>
            {population.state === "RATIFIED"
              ? "coverage may be computed — the denominator is ratified."
              : "no coverage % against an unratified denominator."}
          </span>
        </div>
      </div>

      <p className={styles.closing}>
        {recon
          ? `The universe is ${
              population.derivation_rule.source_refs.length
            }-source derived, set-reconciled into six buckets, and every removal carries a rationale. Counts are a smell test; the buckets are the evidence.`
          : "Definition exists; discovery has not yet enumerated members from the declared sources."}
      </p>
    </div>
  );
}
