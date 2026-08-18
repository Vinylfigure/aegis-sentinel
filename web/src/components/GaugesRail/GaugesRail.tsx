import styles from "./GaugesRail.module.css";
import type { GaugesSeed, GaugeTone as SeedGaugeTone } from "@/data";

export type GaugeTone = "ok" | "warn" | "fail" | "accent" | "info" | "neutral";

export interface Gauge {
  /** Small uppercase caption under the value, e.g. "systems in scope". */
  label: string;
  /** Display value — a count, a percentage, or an em dash placeholder. */
  value: string;
  tone?: GaugeTone;
  /** Optional progress bar, 0–100 (the prototype's percent gauges). */
  bar?: number;
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
 * The A3 filter-out-what-you-can't pattern, shared: keep only the seed
 * gauges whose metric the page genuinely computed (a key in
 * `metricValues`), drop sections left empty. Numeric percent metrics
 * get a "%" suffix and, when the seed asks, the progress bar.
 */
export function sectionsFromSeed(
  seed: GaugesSeed,
  metricValues: Record<string, number | string>,
): GaugeSection[] {
  return seed.sections
    .map((section) => ({
      title: section.title,
      gauges: section.gauges.flatMap((gauge) => {
        const value = metricValues[gauge.metric];
        if (value === undefined) return [];
        const numeric = typeof value === "number";
        return [
          {
            label: gauge.label,
            value:
              numeric && gauge.kind === "percent" ? `${value}%` : String(value),
            tone: toneFromSeed(gauge.tone),
            bar: gauge.showBar && numeric ? value : undefined,
          },
        ];
      }),
    }))
    .filter((section) => section.gauges.length > 0);
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
              {gauge.bar !== undefined ? (
                <svg
                  className={styles.bar}
                  viewBox="0 0 100 4"
                  preserveAspectRatio="none"
                  aria-hidden="true"
                  focusable="false"
                >
                  <rect
                    className={styles.barFill}
                    x="0"
                    y="0"
                    width={Math.max(0, Math.min(100, gauge.bar))}
                    height="4"
                  />
                </svg>
              ) : null}
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
