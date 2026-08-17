import type { ReactNode } from "react";
import styles from "./RailLayout.module.css";

/**
 * Two-column page body from the prototypes: main content left, sticky
 * rail right; collapses to a single column under 1020px. Pages own
 * their rail content (the scope ledger on /scope; posture/dataset
 * gauges on the A4 pages; detail rails on A5/B2).
 */
export function RailLayout({
  children,
  rail,
  railLabel,
}: {
  children: ReactNode;
  rail: ReactNode;
  railLabel: string;
}) {
  return (
    <div className={styles.wrap}>
      <div className={styles.main}>{children}</div>
      <aside className={styles.railCol} aria-label={railLabel}>
        <div className={styles.railSticky}>{rail}</div>
      </aside>
    </div>
  );
}
