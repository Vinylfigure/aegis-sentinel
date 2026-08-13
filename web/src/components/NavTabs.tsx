"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import styles from "./NavTabs.module.css";

const TABS = [
  { n: "1", label: "Scope", href: "/scope" },
  { n: "2", label: "Controls", href: "/controls" },
  { n: "3", label: "Datasets", href: "/datasets" },
  { n: "4", label: "Overlord", href: "/overlord" },
  { n: "5", label: "Process", href: "/process" },
];

export default function NavTabs() {
  const pathname = usePathname();
  return (
    <nav className={styles.stages}>
      {TABS.map((t) => {
        const on = pathname?.startsWith(t.href);
        return (
          <Link
            key={t.href}
            href={t.href}
            className={`${styles.stageTab} ${on ? styles.on : ""}`}
          >
            <span className={styles.n}>{t.n}</span>
            {t.label}
          </Link>
        );
      })}
    </nav>
  );
}
