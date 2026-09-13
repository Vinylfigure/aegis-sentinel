"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import styles from "./RailNav.module.css";

interface Item {
  href: string;
  label: string;
  icon: React.ReactNode;
  match: (path: string) => boolean;
}

const ic = {
  flow: (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden>
      <circle cx="3.5" cy="9" r="2" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="14.5" cy="4" r="2" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="14.5" cy="14" r="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M5.5 9h3m0 0 4-4.2M8.5 9l4 4.2" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  ),
  verdicts: (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden>
      <rect x="2.5" y="2.5" width="13" height="13" rx="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M5.5 7h7M5.5 10h7M5.5 13h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  ),
  recon: (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden>
      <circle cx="7" cy="9" r="4.5" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="11" cy="9" r="4.5" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  ),
  proof: (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden>
      <path d="M9 2 15 5v4c0 3.6-2.4 6-6 7-3.6-1-6-3.4-6-7V5l6-3Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
      <path d="m6.5 9 1.8 1.8L11.8 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  registry: (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden>
      <ellipse cx="9" cy="4.5" rx="6" ry="2.5" stroke="currentColor" strokeWidth="1.5" />
      <path d="M3 4.5v9c0 1.4 2.7 2.5 6 2.5s6-1.1 6-2.5v-9M3 9c0 1.4 2.7 2.5 6 2.5S15 10.4 15 9" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  ),
  program: (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden>
      <rect x="2.5" y="2.5" width="5.5" height="5.5" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
      <rect x="10" y="2.5" width="5.5" height="5.5" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
      <rect x="2.5" y="10" width="5.5" height="5.5" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
      <rect x="10" y="10" width="5.5" height="5.5" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  ),
};

const ITEMS: Item[] = [
  { href: "/", label: "Flow", icon: ic.flow, match: (p) => p === "/" },
  { href: "/verdicts", label: "Verdicts", icon: ic.verdicts, match: (p) => p.startsWith("/verdicts") },
  { href: "/reconciliation", label: "Reconciliation", icon: ic.recon, match: (p) => p.startsWith("/reconciliation") },
  { href: "/proof", label: "Proof", icon: ic.proof, match: (p) => p.startsWith("/proof") },
  { href: "/registry", label: "Registry", icon: ic.registry, match: (p) => p.startsWith("/registry") },
  { href: "/program", label: "Program", icon: ic.program, match: (p) => p.startsWith("/program") },
];

export default function RailNav({ manifestVersion }: { manifestVersion: string }) {
  const path = usePathname();
  return (
    <nav className={styles.rail} aria-label="Primary">
      <Link href="/" className={styles.brand}>
        <span className={styles.brandMark}>A</span>
        <span className={styles.brandName}>Aegis</span>
      </Link>
      <div className={styles.nav}>
        {ITEMS.map((it) => (
          <Link
            key={it.href}
            href={it.href}
            className={`${styles.item} ${it.match(path) ? styles.active : ""}`}
            aria-current={it.match(path) ? "page" : undefined}
            title={it.label}
          >
            {it.icon}
            <span className={styles.itemLabel}>{it.label}</span>
          </Link>
        ))}
      </div>
      <div className={styles.foot}>
        <div className={styles.manifest}>
          <span className={styles.manifestDot} aria-hidden />
          <span className={styles.manifestText}>manifest {manifestVersion}</span>
        </div>
      </div>
    </nav>
  );
}
