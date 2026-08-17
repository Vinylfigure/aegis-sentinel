import type { ReactNode } from "react";
import Link from "next/link";
import { NavTabs } from "@/components/NavTabs/NavTabs";
import styles from "./AppShell.module.css";

/**
 * App chrome: brand line + nav tabs over the full width, page body
 * below. Pages that need the prototypes' sticky right rail compose it
 * themselves with RailLayout — the rail's content is page-specific
 * (scope ledger, posture gauges, detail panels), so it lives with the
 * page, not the shell.
 */
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <Link href="/" className={styles.brand}>
          Aegis
        </Link>
        <span className={styles.tagline}>assurance compiler</span>
      </header>
      <NavTabs />
      <main className={styles.content}>{children}</main>
    </div>
  );
}
