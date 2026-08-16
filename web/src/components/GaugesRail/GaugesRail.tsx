import styles from "./GaugesRail.module.css";

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

/**
 * Placeholder gauges mirroring the workbench prototype's rail
 * (scope / posture / datasets / agents). A4 replaces these with
 * values derived from seed data; C2 with the real artifacts.
 */
const PLACEHOLDER_SECTIONS: GaugeSection[] = [
  {
    title: "Scope",
    gauges: [
      { label: "systems in scope", value: "—", tone: "ok" },
      { label: "unresolved — taints mappings", value: "—", tone: "warn" },
    ],
  },
  {
    title: "Control posture",
    gauges: [
      { label: "configurable · preventative", value: "—", tone: "ok" },
      { label: "manual controls — automation backlog", value: "—", tone: "fail" },
    ],
  },
  {
    title: "Datasets",
    gauges: [
      { label: "unique datasets", value: "—", tone: "info" },
      { label: "avg controls per dataset", value: "—", tone: "accent" },
    ],
  },
];

export function GaugesRail({
  sections = PLACEHOLDER_SECTIONS,
}: {
  sections?: GaugeSection[];
}) {
  return (
    <aside className={styles.rail} aria-label="Gauges">
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
    </aside>
  );
}
