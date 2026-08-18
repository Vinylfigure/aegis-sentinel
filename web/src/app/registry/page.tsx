import type { Metadata } from "next";
import {
  draftCaveats,
  engagementRegistry,
  groupedCompileErrors,
  historyCaveats,
  registryHealth,
  usability,
  type RegistryEntry,
} from "@/data";
import { RailLayout } from "@/components/RailLayout/RailLayout";
import styles from "./registry.module.css";

export const metadata: Metadata = { title: "Registry" };

/**
 * B3 — /registry: capability entries with their ratification state, and
 * E-codes rendered as compiler errors rather than warnings.
 *
 * Deliberately a server component with no state: nothing here needs
 * selection, and a page that renders its whole argument without interaction
 * is one fewer thing to get wrong.
 *
 * Two hard requirements, both from web/README.md:
 *   1. The artifact's top-level `note` renders VERBATIM.
 *   2. Every DRAFT caveat renders VERBATIM beside the lifecycle badge.
 * A page showing DRAFT entries as usable without their caveats
 * misrepresents ratification state — a demo-correctness bug, not styling.
 * Usability is therefore derived (SCH02: unratified entries are
 * mechanically unusable), never asserted.
 */
export default function RegistryPage() {
  const artifact = engagementRegistry;
  const health = registryHealth(artifact);
  const errorGroups = groupedCompileErrors(artifact);

  const rail = (
    <div>
      <h2 className={styles.railTitle}>Registry health</h2>
      <ul className={styles.healthList}>
        <li>
          {health.usable} of {health.total} entries usable by the compiler
          <span className={styles.diagnostic}> diagnostic</span>
        </li>
        <li>{health.draft} draft (mechanically excluded — SCH02)</li>
        <li>{health.withDraftCaveats} carrying DRAFT caveats</li>
        <li>{health.compileErrors} unresolved compile errors</li>
      </ul>

      <section className={styles.railSection}>
        <h3 className={styles.railSectionTitle}>E-codes as compiler errors</h3>
        <p className={styles.railMeta}>
          An E-code is a refusal, not a warning: zero collectors execute for a
          claim carrying an unresolved one (TYP01).
        </p>
        {errorGroups.length === 0 ? (
          <p className={styles.empty}>No unresolved compile errors.</p>
        ) : (
          <ul className={styles.errorList}>
            {errorGroups.map((group) => (
              <li key={group.meta.code} className={styles.errorGroup}>
                <p className={styles.errorHead}>
                  <span className={styles.code}>{group.meta.code}</span>
                  <span className={styles.errorTitle}>{group.meta.title}</span>
                </p>
                <p className={styles.railMeta}>{group.meta.consequence}</p>
                <ul className={styles.railList}>
                  {group.errors.map((error) => (
                    <li key={`${error.claim_id}-${error.code}`}>
                      <code className={styles.ref}>{error.claim_id}</code>
                      <p className={styles.errorMessage}>{error.message}</p>
                      <p className={styles.suggestion}>
                        {error.suggestion
                          ? `satisfiable via: ${error.suggestion}`
                          : "no satisfying combination suggested"}
                      </p>
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );

  return (
    <RailLayout rail={rail} railLabel="Registry health and compile errors">
      <div className={styles.main}>
        <h1 className={styles.h1}>
          Capability registry <span className={styles.h1Dot}>·</span> what the
          compiler may use
        </h1>
        <p className={styles.sub}>
          Cartographer proposes from vendor docs with citations, a human
          ratifies, and only then may the compiler use an entry. Ratification is
          the freeze (D-L1).
        </p>

        {/* README hard requirement 1: the DEMO-ONLY note, verbatim. */}
        <p className={styles.note}>{artifact.note}</p>

        <ul className={styles.entries}>
          {artifact.entries.map((entry) => (
            <li key={entry.id}>
              <EntryCard entry={entry} />
            </li>
          ))}
        </ul>
        {artifact.entries.length === 0 && (
          <p className={styles.empty}>No capability entries in the registry.</p>
        )}
      </div>
    </RailLayout>
  );
}

function EntryCard({ entry }: { entry: RegistryEntry }) {
  const status = usability(entry);
  const drafts = draftCaveats(entry);
  const history = historyCaveats(entry);

  return (
    <article
      className={status.usable ? styles.entry : `${styles.entry} ${styles.entryBlocked}`}
    >
      <h2 className={styles.entryTitle}>
        <code className={styles.entryId}>{entry.id}</code>
        <span className={styles.lifecycle}>{entry.lifecycle}</span>
        <span className={status.usable ? styles.usable : styles.unusable}>
          {status.usable ? "usable" : "NOT usable"}
        </span>
      </h2>
      <p className={styles.reason}>{status.reason}</p>

      {/* README hard requirement 2: DRAFT caveats, verbatim, beside the badge. */}
      {drafts.length > 0 && (
        <ul className={styles.draftCaveats}>
          {drafts.map((caveat) => (
            <li key={caveat}>{caveat}</li>
          ))}
        </ul>
      )}

      <dl className={styles.facts}>
        <div className={styles.fact}>
          <dt>System</dt>
          <dd>
            {entry.system} · {entry.surface}
          </dd>
        </div>
        <div className={styles.fact}>
          <dt>Auth scope</dt>
          <dd>{entry.auth_scope}</dd>
        </div>
        <div className={styles.fact}>
          <dt>Access</dt>
          <dd>{entry.access_modes.join(", ")}</dd>
        </div>
        <div className={styles.fact}>
          <dt>Join keys</dt>
          <dd>{entry.join_keys.join(", ")}</dd>
        </div>
        <div className={styles.fact}>
          <dt>Pagination</dt>
          <dd>
            {entry.pagination.method} — {entry.pagination.exhaustion_method}
          </dd>
        </div>
        <div className={styles.fact}>
          <dt>Temporal</dt>
          <dd>
            {entry.temporal.kind}
            {entry.temporal.cadence ? ` · ${entry.temporal.cadence}` : ""}
            {entry.temporal.window_days === null
              ? " · no window limit recorded"
              : ` · ${entry.temporal.window_days}-day window`}
          </dd>
        </div>
        <div className={styles.fact}>
          <dt>Rate limits</dt>
          <dd>{entry.rate_limits ?? "none recorded"}</dd>
        </div>
      </dl>

      {history.length > 0 && (
        <div className={styles.caveats}>
          <h3 className={styles.caveatTitle}>History caveats</h3>
          <ul className={styles.caveatList}>
            {history.map((caveat) => (
              <li key={caveat}>{caveat}</li>
            ))}
          </ul>
        </div>
      )}

      <div className={styles.yields}>
        <h3 className={styles.caveatTitle}>Populations yielded</h3>
        <ul className={styles.caveatList}>
          {entry.populations_yielded.map((pop) => (
            <li key={pop.description}>
              <span className={styles.popType}>{pop.type}</span> {pop.description}
              <span className={styles.attrs}> ({pop.attributes.join(", ")})</span>
            </li>
          ))}
        </ul>
      </div>

      <div className={styles.provenance}>
        <h3 className={styles.caveatTitle}>Provenance</h3>
        <p className={styles.railMeta}>
          researched by {entry.provenance.researched_by} on{" "}
          {entry.provenance.researched_at} · doc version{" "}
          {entry.provenance.doc_version}
        </p>
        <ul className={styles.citations}>
          {entry.provenance.citations.map((citation) => (
            <li key={citation}>{citation}</li>
          ))}
        </ul>
        <p className={styles.railMeta}>
          ratified by {entry.ratified_by ?? "— not ratified"}
        </p>
      </div>
    </article>
  );
}
