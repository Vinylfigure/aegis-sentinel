"use client";

import Link from "next/link";
import type { EngagementLoad } from "@/lib/data/engagement";
import {
  proofGraphFor,
  reconciliationFor,
  verdictSlug,
} from "@/lib/data/engagement";
import type { VerdictRecord } from "@/lib/types/ontology";
import type { CapabilityEntry } from "@/lib/types/artifacts";
import type { LaneEdgeModel, LaneGate, LaneModel, LaneSystem } from "@/components/flow/laneModel";
import Ladder from "@/components/ui/Ladder";
import { parseEvidence } from "./evidence";
import styles from "./inspector.module.css";

export type LaneSelection =
  | { kind: "gate"; gateId: string }
  | { kind: "node"; systemId: string }
  | { kind: "edge"; edgeId: string }
  | null;

/* ================= shared fragments ================= */

function Seal({ v }: { v: VerdictRecord }) {
  return (
    <>
      <div className={styles.sectionLabel}>sealed record · D-S1</div>
      <div className={styles.seal}>
        <div className={styles.sealRow}>
          <span className={styles.sealKey}>record_hash</span>
          <span className={`${styles.sealVal} ${styles.sealValStrong}`}>{v.record_hash}</span>
        </div>
        <div className={styles.sealRow}>
          <span className={styles.sealKey}>manifest</span>
          <span className={styles.sealVal}>{v.manifest_version}</span>
        </div>
        <div className={styles.sealRow}>
          <span className={styles.sealKey}>snapshot</span>
          <span className={styles.sealVal}>{v.snapshot_hash}</span>
        </div>
        <div className={styles.sealRow}>
          <span className={styles.sealKey}>contract</span>
          <span className={styles.sealVal}>{v.contract_hash}</span>
        </div>
        <div className={styles.sealRow}>
          <span className={styles.sealKey}>evaluated_at</span>
          <span className={styles.sealVal}>{v.evaluated_at}</span>
        </div>
      </div>
    </>
  );
}

function EvidenceRefs({ v }: { v: VerdictRecord }) {
  return (
    <>
      <div className={styles.sectionLabel}>evidence refs</div>
      <div className={styles.refList}>
        {v.evidence_refs.map((r) => (
          <span key={r} className={styles.refItem}>{r}</span>
        ))}
      </div>
    </>
  );
}

/* ================= gate panel ================= */

function GatePanel({
  gate,
  load,
  onSelect,
}: {
  gate: LaneGate;
  load: EngagementLoad;
  onSelect: (s: LaneSelection) => void;
}) {
  if (gate.kind === "compile-error" && gate.error) {
    const err = gate.error;
    return (
      <>
        <div className={styles.sectionLabel}>compiler output · verbatim</div>
        <div className={styles.compiler}>
          <b>{err.code}</b>
          {"  "}
          {err.rendered.replace(/^E\d+\s+/, "")}
        </div>
        <div className={styles.why}>
          <b>Why this cannot compile.</b> The population&apos;s derivation rule names{" "}
          <b>{err.missing_source}</b> as a contributing source, but no ratified
          capability entry exists for it — there is no researched, human-ratified
          surface to collect it from. Aegis refuses to plan a collector against an
          unratified surface, so the claim <b>{err.claim_ref}</b> never reaches
          evaluation: no verdict record exists, and none will be fabricated. The fix
          is an F-4 ratification task (draft the capability entry, ratify its hash),
          not a code change.
        </div>
        <div className={styles.actions}>
          <Link href="/registry" className={styles.action}>
            Capability registry — what IS ratified <span>→</span>
          </Link>
          <Link href="/verdicts" className={`${styles.action} ${styles.actionGhost}`}>
            All compile errors in the ledger <span>→</span>
          </Link>
        </div>
      </>
    );
  }

  const v = gate.verdict!;
  const parsed = parseEvidence(v.message);
  const proof = proofGraphFor(load, v.record_hash);
  const rec = reconciliationFor(load, v.population_ref);

  return (
    <>
      <div className={styles.verdictHead}>
        <span className={`state-badge state-${v.state}`}>{v.state}</span>
        <span className={styles.assertionId}>{v.assertion_ref}</span>
        {v.why_code && <span className={styles.roleChip}>{v.why_code}</span>}
        {v.d7_family && <span className={styles.roleChip}>D-7 {v.d7_family}</span>}
      </div>
      <div className={styles.claimRef}>
        {v.claim_ref} · over {v.population_ref}
        {v.disposition_ref && <> · {v.disposition_ref}</>}
        {v.ratification_ref && <> · {v.ratification_ref}</>}
      </div>

      {parsed.summary && <p className={styles.summary}>{parsed.summary}</p>}

      {parsed.rows.length > 0 && (
        <>
          <div className={styles.sectionLabel}>per-member evidence</div>
          <div className={styles.evidenceRows}>
            {parsed.rows.map((r) => (
              <div
                key={r.member + r.finding}
                className={`${styles.evidenceRow} ${r.emphasized ? styles.evidenceRowHot : ""}`}
              >
                <span className={styles.evidenceMember}>
                  {r.member}
                  {r.bucket && <span className={styles.evidenceBucket}>{r.bucket}</span>}
                </span>
                {r.finding && <span className={styles.evidenceFinding}>{r.finding}</span>}
              </div>
            ))}
          </div>
        </>
      )}

      {gate.related.length > 0 && (
        <>
          <div className={styles.sectionLabel}>sealed alongside</div>
          {gate.related.map((rv) => (
            <div key={rv.record_hash} className={styles.relatedCard}>
              <span className={`state-badge state-${rv.state}`}>{rv.state}</span>
              <span className={styles.relatedText}>
                <span className={styles.relatedAssertion}>{rv.assertion_ref}</span>
                <span className={styles.relatedNote}>{rv.message}</span>
              </span>
            </div>
          ))}
        </>
      )}

      <Seal v={v} />
      <EvidenceRefs v={v} />

      <div className={styles.actions}>
        {proof && (
          <Link href={`/proof/${verdictSlug(v)}`} className={styles.action}>
            Open proof lineage <span>→</span>
          </Link>
        )}
        {rec && (
          <Link
            href={`/reconciliation/${encodeURIComponent(v.population_ref)}`}
            className={`${styles.action} ${styles.actionGhost}`}
          >
            Open reconciliation <span>→</span>
          </Link>
        )}
        <button
          type="button"
          className={`${styles.action} ${styles.actionGhost}`}
          onClick={() => onSelect({ kind: "node", systemId: systemForPopulation(v.population_ref) })}
        >
          Inspect population node <span>→</span>
        </button>
      </div>
    </>
  );
}

function systemForPopulation(popRef: string): string {
  if (popRef.includes("github")) return "github";
  if (popRef.includes("gcp")) return "gcp";
  if (popRef.includes("slack")) return "slack";
  if (popRef.includes("identity-join")) return "okta";
  if (popRef.includes("corp-it")) return "corp-it";
  return "hris";
}

/* ================= node panel ================= */

function NodePanel({ system }: { system: LaneSystem }) {
  const pop = system.population;
  const rec = system.reconciliation;
  const blocked = system.tint === "UNCOMPILED";

  if (!pop) {
    return (
      <>
        <p className={styles.defText}>
          {system.name} is outside the termination lane&apos;s boundary for this
          engagement — excluded by ratification <span className="mono">RAT-2026-031</span>:
          device deprovisioning is covered by the endpoint lane, not TA-3.
        </p>
        <div className={styles.actions}>
          <Link href="/verdicts" className={`${styles.action} ${styles.actionGhost}`}>
            See the EXCLUDED verdict in the ledger <span>→</span>
          </Link>
        </div>
      </>
    );
  }

  const openDeltas = pop.open_deltas;

  return (
    <>
      <p className={styles.defText}>{pop.definition}</p>
      <div className={styles.popId}>
        {pop.population_id} · {pop.type} ·{" "}
        {pop.size != null ? `${pop.size} members` : "size unknown (uncompiled)"} ·{" "}
        {pop.period.start} → {pop.period.end}
      </div>

      <div className={styles.sectionLabel}>assurance ladder</div>
      <Ladder
        current={pop.state}
        blockedAfter={blocked ? "DEFINED" : undefined}
        blockedLabel={blocked ? "E117" : undefined}
      />

      <div className={styles.sectionLabel}>sources</div>
      {pop.sources.map((s) => (
        <div key={s.source_id} className={styles.sourceRow}>
          <span className={styles.sourceId}>{s.source_id}</span>
          <span className={`${styles.roleChip} ${styles[`role${s.role}`] ?? ""}`}>
            {s.role}
          </span>
        </div>
      ))}

      {rec && (
        <>
          <div className={styles.sectionLabel}>reconciliation buckets</div>
          <div className={styles.bucketGrid}>
            {(
              ["intersection", "left_only", "right_only", "conflicts", "unresolvable", "excluded"] as const
            ).map((b) => (
              <div key={b} className={styles.bucketCell}>
                <div
                  className={`${styles.bucketCount} ${
                    b !== "intersection" && b !== "excluded" && rec.buckets[b].length > 0
                      ? styles.bucketCountHot
                      : ""
                  }`}
                >
                  {rec.buckets[b].length}
                </div>
                <div className={styles.bucketName}>{b}</div>
              </div>
            ))}
          </div>
        </>
      )}

      {openDeltas.length > 0 && (
        <>
          <div className={styles.sectionLabel}>open deltas · owners</div>
          {openDeltas.map((d) => (
            <div key={d.delta_id} className={styles.ownerRow}>
              <b>{d.delta_id.split("#").slice(1).join(" · ")}</b> — {d.owner}
            </div>
          ))}
        </>
      )}

      <div className={styles.actions}>
        {rec && (
          <Link
            href={`/reconciliation/${encodeURIComponent(pop.population_id)}`}
            className={styles.action}
          >
            Open reconciliation <span>→</span>
          </Link>
        )}
      </div>
    </>
  );
}

/* ================= edge panel ================= */

const EQC_PROPS: {
  prop: string;
  render: (cap: CapabilityEntry) => React.ReactNode;
}[] = [
  {
    prop: "provenance",
    render: (c) => (
      <>
        {c.provenance.doc_version} — researched {c.provenance.researched_at.slice(0, 10)},
        ratified by {c.provenance.ratified_by ?? "— unratified —"}
      </>
    ),
  },
  {
    prop: "integrity",
    render: (c) => <>{c.pagination.method} pagination · {c.pagination.exhaustion_method}</>,
  },
  {
    prop: "population",
    render: (c) => (
      <>
        yields {c.populations_yielded.map((p) => `${p.name} (${p.type})`).join(", ")} ·
        join keys <span className="mono">{c.join_keys.join(", ")}</span>
      </>
    ),
  },
  {
    prop: "semantics",
    render: (c) => (
      <span className="mono">
        {c.attributes[0]?.fields_exposed.join(" · ") ?? "—"}
      </span>
    ),
  },
  {
    prop: "temporal",
    render: (c) => (
      <>
        {c.temporal.kind}
        {c.temporal.window_days != null && ` · ${c.temporal.window_days}-day window`}
        {c.history_caveats[0] && <> — {c.history_caveats[0]}</>}
      </>
    ),
  },
];

function EdgePanel({ edge, load }: { edge: LaneEdgeModel; load: EngagementLoad }) {
  const pop = edge.populationRef
    ? load.artifacts.populations.find((p) => p.population_id === edge.populationRef)
    : undefined;
  const cap = edge.capability;
  const contractHash = edge.gate?.verdict?.contract_hash;

  return (
    <>
      <div className={styles.kv}>
        <div className={styles.kvRow}>
          <span className={styles.kvKey}>event kind</span>
          <span className={styles.kvVal}>{edge.eventKind}</span>
        </div>
        <div className={styles.kvRow}>
          <span className={styles.kvKey}>flowing population</span>
          <span className={`${styles.kvVal} mono`}>{edge.populationRef ?? "—"}</span>
        </div>
        {pop && (
          <div className={styles.kvRow}>
            <span className={styles.kvKey}>members</span>
            <span className={styles.kvVal}>
              {pop.size != null ? pop.size : "unknown — did not compile"}
            </span>
          </div>
        )}
        <div className={styles.kvRow}>
          <span className={styles.kvKey}>cohort</span>
          <span className={styles.kvVal}>{edge.cohort.label}</span>
        </div>
      </div>

      {cap && (
        <>
          <div className={styles.sectionLabel}>evidence contract · EQC</div>
          <div>
            {EQC_PROPS.map(({ prop, render }) => (
              <div key={prop} className={styles.eqcRow}>
                <span className={styles.eqcProp}>{prop}</span>
                <span className={styles.eqcVal}>{render(cap)}</span>
              </div>
            ))}
          </div>
          {contractHash && (
            <div className={styles.seal} style={{ marginTop: 12 }}>
              <div className={styles.sealRow}>
                <span className={styles.sealKey}>contract_hash</span>
                <span className={`${styles.sealVal} ${styles.sealValStrong}`}>{contractHash}</span>
              </div>
              <div className={styles.sealRow}>
                <span className={styles.sealKey}>surface</span>
                <span className={styles.sealVal}>{cap.surface}</span>
              </div>
            </div>
          )}
        </>
      )}
      {!cap && (
        <p className={styles.summary}>
          No ratified capability entry backs this edge — this is the E117 condition:
          the flow is declared but cannot be collected.
        </p>
      )}
    </>
  );
}

/* ================= the drawer ================= */

export default function InspectorDrawer({
  load,
  model,
  selection,
  onClose,
  onSelect,
}: {
  load: EngagementLoad;
  model: LaneModel;
  selection: LaneSelection;
  onClose: () => void;
  onSelect: (s: LaneSelection) => void;
}) {
  let kicker = "";
  let title = "";
  let subtitle = "";
  let content: React.ReactNode = null;

  if (selection?.kind === "gate") {
    const gate = model.gates[selection.gateId];
    if (gate) {
      kicker = `control point · ${gate.label}`;
      title =
        gate.kind === "compile-error"
          ? "Did not compile"
          : `${gate.verdict?.assertion_ref}`;
      subtitle =
        gate.kind === "compile-error"
          ? `${gate.error?.code} · ${gate.error?.claim_ref}`
          : gate.summary;
      content = <GatePanel gate={gate} load={load} onSelect={onSelect} />;
    }
  } else if (selection?.kind === "node") {
    const system = model.systems[selection.systemId];
    if (system) {
      kicker = "system";
      title = system.name;
      subtitle = system.descriptor;
      content = <NodePanel system={system} />;
    }
  } else if (selection?.kind === "edge") {
    const edge = model.edges.find((e) => e.edgeId === selection.edgeId);
    if (edge) {
      kicker = "flow edge";
      title = edge.eventKind;
      subtitle = `${edge.source} → ${edge.target}`;
      content = <EdgePanel edge={edge} load={load} />;
    }
  }

  return (
    <aside
      className={`${styles.drawer} ${selection ? styles.drawerOpen : ""}`}
      inert={!selection || undefined}
      aria-label="Inspector"
    >
      <div className={styles.head}>
        <div className={styles.headText}>
          <div className={styles.kicker}>{kicker}</div>
          <div className={styles.title}>{title}</div>
          {subtitle && <div className={styles.subtitle}>{subtitle}</div>}
        </div>
        <button type="button" className={styles.close} onClick={onClose} aria-label="Close inspector">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden>
            <path d="m1.5 1.5 9 9m0-9-9 9" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
          </svg>
        </button>
      </div>
      <div className={styles.body}>{content}</div>
    </aside>
  );
}
