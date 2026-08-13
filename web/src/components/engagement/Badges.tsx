"use client";

/* Engagement badge kit — the five verdict treatments, source roles,
 * ladder chips, population types, ghost chips (negative space), and
 * disposition badges. Shared across every Phase B screen. */

import type {
  AssuranceState,
  PopulationType,
  SourceRole,
  VerdictState,
} from "@/lib/types/ontology";
import type { DeltaDisposition } from "@/lib/types/artifacts";
import styles from "./Badges.module.css";

const VB_CLASS: Record<VerdictState, string> = {
  PASS: styles.vbPass,
  FAIL: styles.vbFail,
  UNKNOWN: styles.vbUnknown,
  EXCLUDED: styles.vbExcluded,
  EXCEPTION: styles.vbException,
};

export function VerdictBadge({
  state,
  size = "sm",
}: {
  state: VerdictState;
  size?: "sm" | "lg";
}) {
  return (
    <span
      className={`${styles.vb} ${VB_CLASS[state]} ${size === "lg" ? styles.vbLg : ""}`}
      data-verdict={state}
    >
      {state}
    </span>
  );
}

export function MiniChip({
  tone,
  children,
  title,
}: {
  tone: "amber" | "dim" | "purple" | "cyan" | "green" | "red";
  children: React.ReactNode;
  title?: string;
}) {
  const map = {
    amber: styles.mAmber,
    dim: styles.mDim,
    purple: styles.mPurple,
    cyan: styles.mCyan,
    green: styles.mGreen,
    red: styles.mRed,
  } as const;
  return (
    <span className={`${styles.mchip} ${map[tone]}`} title={title}>
      {children}
    </span>
  );
}

export function SourceRoleTag({ role }: { role: SourceRole }) {
  return <span className={`${styles.role} ${styles[`role${role}`]}`}>{role}</span>;
}

export function LadderChip({ state }: { state: AssuranceState }) {
  return <span className={`${styles.ladder} ${styles[`l${state}`]}`}>{state}</span>;
}

export function TypeBadge({ type }: { type: PopulationType }) {
  return <span className={`${styles.ptype} ${styles[`pt${type}`]}`}>{type}</span>;
}

/** Negative space: a source where the member was expected but absent. */
export function GhostChip({ source }: { source: string }) {
  return (
    <span className={styles.ghost} title={`expected in ${source} — absent (negative space)`}>
      {source}
    </span>
  );
}

export function PresentChip({ source }: { source: string }) {
  return <span className={styles.present}>{source}</span>;
}

export function DispositionBadge({
  disposition,
}: {
  disposition?: DeltaDisposition;
}) {
  if (!disposition) {
    return (
      <span className={`${styles.disp} ${styles.dispOpen}`}>
        <i className={styles.dispDot} /> disposition open
      </span>
    );
  }
  return (
    <span
      className={`${styles.disp} ${styles.dispSet}`}
      title={`${disposition.justification} — ${disposition.owner}, review ${disposition.review_date}`}
    >
      <i className={styles.dispDot} /> {disposition.value}
    </span>
  );
}

/** Hover tooltip (CSS-only) — used for the deliberate "—" coverage cells. */
export function Tip({ tip, children }: { tip: string; children: React.ReactNode }) {
  return (
    <span className={styles.tip} data-tip={tip}>
      {children}
    </span>
  );
}
