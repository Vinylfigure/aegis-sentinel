"use client";

import type { EngagementManifest } from "@/lib/types/artifacts";
import { VERDICT_STATES } from "@/lib/types/ontology";
import styles from "./flow.module.css";

const CHIP_COLOR: Record<string, string> = {
  PASS: "var(--v-pass)",
  FAIL: "var(--v-fail)",
  UNKNOWN: "var(--v-unknown)",
  EXCEPTION: "var(--v-exception)",
  EXCLUDED: "var(--v-excluded)",
};

export default function HeaderStrip({
  manifest,
  counts,
  detection,
  overlay,
  onToggleOverlay,
}: {
  manifest: EngagementManifest;
  counts: Record<string, number>;
  detection: { detected: number; total: number; pct: number };
  overlay: boolean;
  onToggleOverlay: () => void;
}) {
  return (
    <header className={styles.header}>
      <div className={styles.wordmark}>
        <span className={styles.wordmarkName}>Aegis</span>
        <span className={styles.wordmarkLane}>termination lane</span>
      </div>

      <span className={styles.manifestBadge} title={manifest.snapshot_hash}>
        <span className={styles.ratifiedDot} aria-hidden />
        <b>{manifest.manifest_version}</b>
        <span className={styles.sep}>·</span>
        ratified
        <span className={styles.sep}>·</span>
        {manifest.snapshot_hash.slice(0, 12)}…
      </span>

      <div className={styles.headerSpacer} />

      <div className={styles.stateChips} aria-label="Verdict counts">
        {VERDICT_STATES.map((s) => (
          <span
            key={s}
            className={`${styles.stateChip} ${counts[s] === 0 ? styles.stateChipZero : ""}`}
            style={{ "--chip-color": CHIP_COLOR[s] } as React.CSSProperties}
          >
            <i>{counts[s]}</i> {s}
          </span>
        ))}
      </div>

      <span
        className={styles.detectStat}
        title="Seeded-poison detection: mutated defects that produced a compile error, UNKNOWN, or FAIL"
      >
        <span className={styles.detectMeter} aria-hidden>
          {Array.from({ length: detection.total }).map((_, i) => (
            <span
              key={i}
              className={`${styles.detectSeg} ${i < detection.detected ? styles.detectSegOn : ""}`}
            />
          ))}
        </span>
        <b>
          {detection.detected}/{detection.total}
        </b>
        · {detection.pct}% detected
      </span>

      <button
        type="button"
        className={`${styles.overlayToggle} ${overlay ? styles.overlayToggleOn : ""}`}
        onClick={onToggleOverlay}
        aria-pressed={overlay}
      >
        <span className={styles.toggleTrack} aria-hidden>
          <span className={styles.toggleThumb} />
        </span>
        Cohort flow
      </button>
    </header>
  );
}
