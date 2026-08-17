import styles from "./GaugesRail.module.css";
import type { GaugeTone as SeedGaugeTone } from "@/data";

export type GaugeTone = "ok" | "warn" | "fail" | "accent" | "info" | "neutral";

export interface Gauge {
  /** Small uppercase caption under the value, e.g. "systems in scope". */
  label: string;
  /** Display value — a count, a percentage, or an em dash placeholder. */
  value: string;
  tone?: GaugeTone;
}

export interface GaugeSection {
  title: string;
  gauges: Gauge[];
}

/** Seed gauge tones (prototype color names) → semantic rail tones. */
const SEED_TONES: Record<SeedGaugeTone, GaugeTone> = {
  green: "ok",
  amber: "warn",
  red: "fail",
  purple: "accent",
  cyan: "info",
};

export function toneFromSeed(tone: SeedGaugeTone): GaugeTone {
  return SEED_TONES[tone];
}

/**
 * Gauge sections without an aside wrapper — for embedding inside a
 * page's RailLayout rail alongside page-specific panels.
 */
export function GaugeList({ sections }: { sections: GaugeSection[] }) {
  return (
    <>
      {sections.map((section) => (
        <section key={section.title}>
          <h2 className={styles.title}>{section.title}</h2>
          {section.gauges.map((gauge) => (
            <div
              key={gauge.label}
              className={`${styles.gauge} ${styles[gauge.tone ?? "neutral"]}`}
            >
              <div className={styles.value}>{gauge.value}</div>
              <div className={styles.label}>{gauge.label}</div>
            </div>
          ))}
        </section>
      ))}
    </>
  );
}

/** Standalone gauges rail (workbench prototype) as its own aside. */
export function GaugesRail({ sections }: { sections: GaugeSection[] }) {
  return (
    <aside className={styles.rail} aria-label="Gauges">
      <GaugeList sections={sections} />
    </aside>
  );
}
