"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import styles from "./NavTabs.module.css";

export interface NavEntry {
  href: string;
  label: string;
}

/** The planned route arc (A3–B4). Stub pages exist for each today. */
export const NAV_ENTRIES: NavEntry[] = [
  { href: "/scope", label: "Scope" },
  { href: "/controls", label: "Controls" },
  { href: "/process", label: "Process" },
  { href: "/reconciliation", label: "Reconciliation" },
  { href: "/verdicts", label: "Verdicts" },
  { href: "/registry", label: "Registry" },
  { href: "/proof", label: "Proof" },
];

export function NavTabs({ entries = NAV_ENTRIES }: { entries?: NavEntry[] }) {
  const pathname = usePathname();
  return (
    <nav className={styles.tabs} aria-label="Primary">
      {entries.map((entry) => {
        const active =
          pathname === entry.href || pathname.startsWith(`${entry.href}/`);
        return (
          <Link
            key={entry.href}
            href={entry.href}
            className={active ? `${styles.tab} ${styles.on}` : styles.tab}
            aria-current={active ? "page" : undefined}
          >
            {entry.label}
          </Link>
        );
      })}
    </nav>
  );
}
