import type { ReactNode } from "react";
import Link from "next/link";
import { NavTabs } from "@/components/NavTabs/NavTabs";
import { GaugesRail } from "@/components/GaugesRail/GaugesRail";
import styles from "./AppShell.module.css";

/**
 * Two-column shell from the prototypes: main content left,
 * sticky gauges rail right, nav tabs under the brand line.
 */
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className={styles.wrap}>
      <div className={styles.main}>
        <header className={styles.header}>
          <Link href="/" className={styles.brand}>
            Aegis
          </Link>
          <span className={styles.tagline}>assurance compiler</span>
        </header>
        <NavTabs />
        <main className={styles.content}>{children}</main>
      </div>
      <GaugesRail />
    </div>
  );
}
