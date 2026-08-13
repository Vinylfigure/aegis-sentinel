"use client";

/* Capability Registry: what evidence each system is capable of yielding,
 * Cartographer-proposed, human-ratified. History caveats render
 * prominently amber — the 90-day trap is the whole point. Unresolved
 * E-codes render as compiler output. */

import { loadEngagement } from "@/lib/data/engagement";
import { MiniChip, TypeBadge } from "@/components/engagement/Badges";
import SchemaDriftBanner from "@/components/engagement/SchemaDriftBanner";
import styles from "./Registry.module.css";

export default function RegistryPage() {
  const load = loadEngagement();
  const { capability_registry, compile_errors } = load.artifacts;

  return (
    <div>
      <SchemaDriftBanner drift={load.drift} />
      <p className="sub">
        Per system, per surface: what populations it yields, its temporal shape,
        join keys, least-privilege scope, and — most load-bearing — its history
        caveats. The compiler type-checks every (claim, assertion, population)
        triple against these entries; the agent maps the territory, it does not
        annex it.
      </p>

      {compile_errors.length > 0 && (
        <>
          <div className="slab">Unresolved E-codes — the program does not fully compile</div>
          <div className={styles.compiler} data-testid="ecode-block">
            {compile_errors.map((e) => (
              <div key={e.code + (e.assertion_ref ?? "")} className={styles.ecode}>
                <span className={styles.code}>{e.code}</span>
                <div>
                  <p className={styles.emsg}>{e.message}</p>
                  {e.suggestion && <p className={styles.esuggest}>↳ {e.suggestion}</p>}
                  {(e.claim_ref || e.assertion_ref) && (
                    <p className={styles.eref}>
                      at {e.claim_ref}
                      {e.assertion_ref ? ` · ${e.assertion_ref}` : ""}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      <div className="slab">Ratified capability entries — {capability_registry.length}</div>
      <div className={styles.grid}>
        {capability_registry.map((e) => (
          <div key={e.entry_id} className={styles.card} data-entry={e.entry_id}>
            <div className={styles.cardHead}>
              <b className={styles.system}>{e.system}</b>
              <code className={styles.entryId}>{e.entry_id}</code>
            </div>
            <code className={styles.surface}>{e.surface}</code>

            <div className={styles.modes}>
              {e.access_modes.map((m) => (
                <MiniChip key={m} tone={m === "direct-api" ? "green" : "cyan"}>
                  {m}
                </MiniChip>
              ))}
              <MiniChip tone="purple">
                {e.temporal.shape}
                {e.temporal.window_days ? ` · ${e.temporal.window_days}d` : ""}
                {e.temporal.cadence ? ` · ${e.temporal.cadence}` : ""}
              </MiniChip>
            </div>

            <div className={styles.pops}>
              {e.populations_yielded.map((p) => (
                <span key={p.name} className={styles.pop}>
                  <TypeBadge type={p.type} /> {p.name}
                </span>
              ))}
            </div>

            <div className={styles.meta}>
              <div className={styles.mrow}>
                <label>join keys</label>
                <div>
                  {e.join_keys.map((k) => (
                    <code key={k}>{k}</code>
                  ))}
                </div>
              </div>
              <div className={styles.mrow}>
                <label>pagination</label>
                <div>{e.pagination}</div>
              </div>
              <div className={styles.mrow}>
                <label>auth scope</label>
                <div>{e.auth_scope}</div>
              </div>
              {e.rate_limits && (
                <div className={styles.mrow}>
                  <label>rate limits</label>
                  <div>{e.rate_limits}</div>
                </div>
              )}
            </div>

            {e.history_caveats.length > 0 && (
              <div className={styles.caveats}>
                {e.history_caveats.map((c, i) => (
                  <p key={i}>⚠ {c}</p>
                ))}
              </div>
            )}

            <div className={styles.prov}>
              {e.provenance.researched_by} · {e.provenance.researched_at} ·{" "}
              {e.provenance.doc_version} — ratified by{" "}
              <b>{e.provenance.ratified_by}</b>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
