import Link from "next/link";
import styles from "./StageTabs.module.css";

export type StageNumber = 1 | 2 | 3 | 4;

/** The workbench pipeline: each stage feeds the next. */
export const STAGES: { number: StageNumber; href: string; label: string }[] = [
  { number: 1, href: "/scope", label: "Scope" },
  { number: 2, href: "/controls", label: "Controls" },
  { number: 3, href: "/datasets", label: "Datasets" },
  { number: 4, href: "/overlord", label: "Overlord" },
];

/**
 * The workbench prototype's four-stage tab strip, as routes: scope →
 * controls → datasets → overlord. The current stage is a page-level
 * fact, so it comes in as a prop instead of a pathname lookup.
 */
export function StageTabs({ current }: { current: StageNumber }) {
  return (
    <nav className={styles.stages} aria-label="Workbench stages">
      {STAGES.map((stage) => {
        const active = stage.number === current;
        return (
          <Link
            key={stage.href}
            href={stage.href}
            className={active ? `${styles.tab} ${styles.on}` : styles.tab}
            aria-current={active ? "page" : undefined}
          >
            <span className={styles.num}>{stage.number}</span>
            {stage.label}
          </Link>
        );
      })}
    </nav>
  );
}
