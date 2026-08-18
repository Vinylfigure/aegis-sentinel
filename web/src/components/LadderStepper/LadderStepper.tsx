import {
  LADDER_GATE_RULE,
  LADDER_RUNGS,
  type Blocker,
  type LadderRung,
} from "@/data";
import type { ReconciliationLadder } from "@/data";
import styles from "./LadderStepper.module.css";

/**
 * The assurance-state ladder as a stepper. Server-safe (no state, no
 * directive) so B3/B4 can mount it from a server component.
 *
 * Two things this deliberately does NOT do: it never renders a coverage
 * percentage (a denominator left of RATIFIED cannot carry one, PRD §2), and
 * it never echoes `after_dispositions` as fact — if a blocker went
 * unanswered, RECONCILED renders as claimed-but-contradicted.
 */

export type RungStatus = "reached" | "at first verdict" | "now" | "not reached";

function rungStatus(
  rung: LadderRung,
  current: string,
  atFirstVerdict: string,
): RungStatus {
  const order = LADDER_RUNGS.indexOf(rung);
  const currentIndex = LADDER_RUNGS.indexOf(current as LadderRung);
  if (rung === atFirstVerdict && rung !== current) return "at first verdict";
  if (rung === current) return "now";
  return order < currentIndex ? "reached" : "not reached";
}

const STATUS_CLASS: Record<RungStatus, string> = {
  reached: "reached",
  "at first verdict": "first",
  now: "now",
  "not reached": "future",
};

export function LadderStepper({
  ladder,
  blockers,
  claimHolds,
  variant = "full",
}: {
  ladder: ReconciliationLadder;
  blockers: Blocker[];
  /** False when a blocker has no disposition anywhere. */
  claimHolds: boolean;
  variant?: "full" | "condensed";
}) {
  const current = ladder.after_dispositions;
  const answered = blockers.filter((b) => b.answer !== null);
  const unanswered = blockers.filter((b) => b.answer === null);

  return (
    <div className={variant === "condensed" ? styles.condensed : styles.full}>
      <ol className={styles.rungs}>
        {LADDER_RUNGS.map((rung) => {
          const status = rungStatus(rung, current, ladder.at_first_verdict);
          const contradicted = rung === current && !claimHolds;
          return (
            <li
              key={rung}
              className={`${styles.rung} ${styles[STATUS_CLASS[status]] ?? ""}`}
              aria-current={status === "now" ? "step" : undefined}
            >
              <span className={styles.rungName}>{rung}</span>
              <span className={styles.rungStatus}>
                {contradicted ? "claimed — contradicted" : status}
              </span>
            </li>
          );
        })}
      </ol>

      {variant === "full" && (
        <div className={styles.gate}>
          <p className={styles.gateRule}>
            <span className={styles.gateEdge} aria-hidden="true">
              DISCOVERED → RECONCILED
            </span>{" "}
            {LADDER_GATE_RULE}
          </p>

          {blockers.length === 0 ? (
            <p className={styles.gateEmpty}>No deltas blocked this transition.</p>
          ) : (
            <ul className={styles.blockers}>
              {blockers.map((blocker) => (
                <li key={blocker.ref} className={styles.blocker}>
                  <code className={styles.ref}>{blocker.ref}</code>
                  <span className={styles.blockerBucket}>
                    {blocker.bucket ?? "no matching delta"}
                  </span>
                  {blocker.answer ? (
                    <span className={styles.answered}>
                      answered by {blocker.answer.record.owner} ·{" "}
                      {blocker.answer.record.value}
                    </span>
                  ) : (
                    <span className={styles.unanswered}>UNANSWERED — the ladder cannot advance</span>
                  )}
                </li>
              ))}
            </ul>
          )}

          <p className={claimHolds ? styles.verdictOk : styles.verdictBad}>
            {claimHolds
              ? `${answered.length} of ${blockers.length} blockers answered by a named human — ${current} holds.`
              : `${unanswered.length} of ${blockers.length} blockers unanswered — ${current} is claimed by the artifact but not supported by the deltas.`}
          </p>

          <p className={styles.ratified}>
            RATIFIED not reached — it is the human freeze (D-L1). No coverage
            percentage is computed: a denominator left of RATIFIED cannot carry
            one (PRD §2).
          </p>
        </div>
      )}
    </div>
  );
}
