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
  const okta = entries.find((e) => e.id === "okta.system_log");

  return (
    <main className="page">
      <div className="page-kicker">capability registry</div>
      <h1>What can actually be collected</h1>
      <p className="page-sub">
        Every entry is a researched, human-ratified description of a real API
        surface — its temporal shape, its pagination, its caveats. Claims compile
        against these physics, not against wishes.
      </p>

      <div className="section-label">the retention wall · a capability&apos;s own physics</div>
      <div className={styles.exhibit}>
        <div className={styles.exhibitLeft}>
          <div className={styles.exhibitTitle}>
            Okta System Log retains <b>{okta?.temporal.window_days ?? "?"} days</b> —
            {okta ? " event-history, not full-history." : " capability not found in this engagement."}
          </div>
          <p className={styles.exhibitText}>
            <span className="mono">{okta?.id}</span> yields{" "}
            <span className="mono">
              {okta?.temporal.kind}(window={okta?.temporal.window_days}d)
            </span>
            . A TIMING assertion asking for a window beyond that retention has no
            usable capability combination to compile against — the compiler emits an
            E204 finding rather than silently truncating the claim.
          </p>
        </div>
        <div className={styles.exhibitRight}>
          {e204 ? (
            <>
              <b>E204</b> {e204.message}
              {e204.suggestion && (
                <div className={styles.exhibitText}>suggestion: {e204.suggestion}</div>
              )}
            </>
          ) : (
            <p className={styles.exhibitText}>
              No E204 (temporal insufficiency) finding in this engagement&apos;s
              compile_errors — the wall above is illustrative of the capability&apos;s
              retention physics, not a claim compiled against it this run.
            </p>
          )}
        </div>
      </div>

      <div className="section-label">ratified entries · {entries.length}</div>
      <div className={styles.entryGrid}>
        {entries.map((e) => (
          <article key={e.id} className={styles.entry}>
            <div className={styles.entryHead}>
              <span className={styles.entrySystem}>{SYSTEM_NAMES[e.system] ?? e.system}</span>
              <span className={styles.entryId}>{e.id}</span>
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
                  {e.populations_yielded.map((p) => `${p.description} (${p.type})`).join(" · ")}
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
              {e.provenance.doc_version ?? "no doc version on record"} · ratified by{" "}
              {e.ratified_by ?? "not yet ratified (draft)"} ·{" "}
              {e.provenance.citations.map((url, i) => (
                <span key={url}>
                  {i > 0 && " · "}
                  <a href={url} target="_blank" rel="noreferrer">
                    {url}
                  </a>
                </span>
              ))}
            </div>
          </article>
        ))}
      </div>

      <div className="section-label">compile errors · the registry saying no</div>
      {errors.map((e) => (
        <div key={e.code + e.claim_id} className={styles.ecodeCard}>
          <span className={styles.ecodeTag}>{e.code}</span>
          <div className={styles.ecodeBody}>
            <div className={styles.ecodeName}>
              {e.code === "E204"
                ? "Assertion window exceeds capability retention"
                : e.code === "E117"
                  ? "Derivation source has no ratified capability entry"
                  : "Compile error"}
              {" · "}
              {e.claim_id}
            </div>
            <div className={styles.ecodeText}>{e.message}</div>
            {e.suggestion && <div className={styles.ecodeText}>suggestion: {e.suggestion}</div>}
          </div>
        </div>
      ))}
    </main>
  );
}
