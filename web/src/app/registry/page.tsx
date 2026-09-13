import type { Metadata } from "next";
import { loadEngagement } from "@/lib/data/engagement";
import styles from "./Registry.module.css";

export const metadata: Metadata = { title: "Capability registry — Aegis" };

const SYSTEM_NAMES: Record<string, string> = {
  gcp: "GCP",
  hris: "HRIS",
  github: "GitHub",
  okta: "Okta",
  slack: "Slack",
};

export default function RegistryPage() {
  const load = loadEngagement();
  const entries = load.artifacts.capability_registry;
  const errors = load.artifacts.compile_errors;
  const e204 = errors.find((e) => e.code === "E204");
  const okta = entries.find((e) => e.entry_id === "okta.system_log.api_v1");

  return (
    <main className="page">
      <div className="page-kicker">capability registry</div>
      <h1>What can actually be collected</h1>
      <p className="page-sub">
        Every entry is a researched, human-ratified description of a real API
        surface — its temporal shape, its pagination, its caveats. Claims compile
        against these physics, not against wishes.
      </p>

      <div className="section-label">the 90-day wall · why the six-month ask refused to compile</div>
      <div className={styles.exhibit}>
        <div className={styles.exhibitLeft}>
          <div className={styles.exhibitTitle}>
            Okta System Log retains <b>90 days</b>. The assertion needed 181.
          </div>
          <p className={styles.exhibitText}>
            <span className="mono">{okta?.entry_id}</span> yields{" "}
            <span className="mono">
              event-history(window={okta?.temporal.window_days}d)
            </span>
            . The TIMING assertion asked for transition timestamps across the full
            period {e204?.required_window?.start}..{e204?.required_window?.end}. No
            usable capability combination covers it — so the claim was re-scoped to
            an honest window, and the six-month ask stays on the books as the E204
            exhibit below.
          </p>
          <div className={styles.windowViz} aria-label="Required 181-day window vs available 90-day retention">
            <div className={styles.windowTrack}>
              <span className={styles.windowNeed} />
              <span className={styles.windowHave} />
            </div>
            <div className={styles.windowLegend}>
              <span>
                required <b>181 days</b> (2026-01-01 → 2026-06-30)
              </span>
              <span>
                available <b>90 days</b> of retention
              </span>
            </div>
          </div>
        </div>
        <div className={styles.exhibitRight}>
          <b>E204</b> {e204?.rendered.replace(/^E\d+\s+/, "")}
        </div>
      </div>

      <div className="section-label">ratified entries · {entries.length}</div>
      <div className={styles.entryGrid}>
        {entries.map((e) => (
          <article key={e.entry_id} className={styles.entry}>
            <div className={styles.entryHead}>
              <span className={styles.entrySystem}>{SYSTEM_NAMES[e.system] ?? e.system}</span>
              <span className={styles.entryId}>{e.entry_id}</span>
              <span
                className={`${styles.temporalChip} ${
                  e.temporal.window_days != null ? styles.temporalWindow : ""
                }`}
              >
                {e.temporal.kind}
                {e.temporal.window_days != null && ` · ${e.temporal.window_days}d`}
              </span>
            </div>
            <div className={styles.entrySurface}>{e.surface}</div>
            <div className={styles.entryMeta}>
              <div className={styles.metaRow}>
                <span className={styles.metaKey}>yields</span>
                <span className={styles.metaVal}>
                  {e.populations_yielded.map((p) => `${p.name} (${p.type})`).join(" · ")}
                </span>
              </div>
              <div className={styles.metaRow}>
                <span className={styles.metaKey}>join keys</span>
                <span className={`${styles.metaVal} mono`}>{e.join_keys.join(", ")}</span>
              </div>
              <div className={styles.metaRow}>
                <span className={styles.metaKey}>auth</span>
                <span className={styles.metaVal}>{e.auth_scope}</span>
              </div>
              <div className={styles.metaRow}>
                <span className={styles.metaKey}>pagination</span>
                <span className={styles.metaVal}>
                  {e.pagination.method} — {e.pagination.exhaustion_method}
                </span>
              </div>
              <div className={styles.metaRow}>
                <span className={styles.metaKey}>rate limits</span>
                <span className={styles.metaVal}>{e.rate_limits}</span>
              </div>
            </div>
            {e.history_caveats.map((c) => (
              <div key={c} className={styles.caveat}>
                {c}
              </div>
            ))}
            <div className={styles.provenance}>
              {e.provenance.doc_version} · ratified by {e.provenance.ratified_by} ·{" "}
              {e.provenance.source_citations.map((s, i) => (
                <span key={s.url}>
                  {i > 0 && " · "}
                  <a href={s.url} target="_blank" rel="noreferrer">
                    {s.title}
                  </a>
                </span>
              ))}
            </div>
          </article>
        ))}
      </div>

      <div className="section-label">compile errors · the registry saying no</div>
      {errors.map((e) => (
        <div key={e.code + e.claim_ref} className={styles.ecodeCard}>
          <span className={styles.ecodeTag}>{e.code}</span>
          <div className={styles.ecodeBody}>
            <div className={styles.ecodeName}>
              {e.code === "E204"
                ? "Assertion window exceeds capability retention"
                : e.code === "E117"
                  ? "Derivation source has no ratified capability entry"
                  : "Compile error"}
              {" · "}
              {e.claim_ref}
            </div>
            <div className={styles.ecodeText}>{e.rendered.replace(/^E\d+\s+/, "")}</div>
          </div>
        </div>
      ))}
    </main>
  );
}
