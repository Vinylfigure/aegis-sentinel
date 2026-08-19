"use client";

import { useState } from "react";
import Link from "next/link";
import { RailLayout } from "@/components/RailLayout/RailLayout";
import {
  EVIDENCE_KIND_LABEL,
  STAGE_ORDER,
  lineage,
  verdictStateMeta,
  type LineageNode,
  type LineageStageId,
  type PoisonsArtifact,
  type ReconciliationReport,
  type RegistryArtifact,
  type StageEvidence,
  type VerdictRecord,
} from "@/data";
import styles from "../proof.module.css";

/**
 * B4 — the ten-stage lineage as SVG, with a node inspector in the rail.
 * Sole state: which stage is selected (default: the verdict — the record
 * is the subject). Every node carries its evidence kind as TEXT on the
 * diagram; colour only reinforces it. The typed arrows are visible text
 * labels on the edges (UI01: "rendered with typed arrows").
 */

const NODE_W = 128;
const NODE_H = 64;
const GAP = 74;
const ARROW_Y = NODE_H / 2;

/** Stroke class per evidence kind — exhaustive, so a new kind fails tsc. */
const KIND_CLASS: Record<StageEvidence["kind"], string> = {
  emitted: "nodeEmitted",
  "identity-only": "nodeIdentity",
  "trace-only": "nodeTrace",
  "not-emitted": "nodeMissing",
};

export function ProofLineage({
  record,
  reconciliations,
  registry,
  poisons,
}: {
  record: VerdictRecord;
  reconciliations: ReconciliationReport[];
  registry: RegistryArtifact;
  poisons: PoisonsArtifact;
}) {
  const [selectedId, setSelectedId] = useState<LineageStageId>("verdict");

  const nodes = lineage(record, reconciliations, registry, poisons);
  const selected = nodes.find((n) => n.meta.id === selectedId) ?? null;
  const stateMeta = verdictStateMeta(record.status);

  const n = STAGE_ORDER.length;
  const width = n * NODE_W + (n - 1) * GAP;
  const height = NODE_H + 26;

  const rail = (
    <div aria-live="polite">
      <h2 className={styles.railTitle}>
        {selected ? `${selected.meta.ordinal} · ${selected.meta.title}` : "Node inspector"}
      </h2>
      {selected && (
        <StageInspector node={selected} record={record} reconciliations={reconciliations} />
      )}
    </div>
  );

  return (
    <RailLayout rail={rail} railLabel="Lineage node inspector">
      <div className={styles.main}>
        <h1 className={styles.h1}>
          Proof <span className={styles.h1Dot}>·</span> {record.record_id}
        </h1>
        <p className={styles.sub}>{record.message ?? "(no message on the record)"}</p>
        <p className={styles.meta}>
          <span className={styles.stateChip}>{record.status}</span>
          <span className={styles.metaSep}>·</span>
          {stateMeta.meaning}
        </p>

        <div className={styles.svgScroll}>
          <svg
            viewBox={`0 0 ${width} ${height}`}
            width={width}
            height={height}
            role="group"
            aria-label="Ten-stage proof lineage, commitment through verdict"
            className={styles.svg}
          >
            <defs>
              <marker
                id="lineage-arrow"
                viewBox="0 0 8 8"
                refX="7"
                refY="4"
                markerWidth="7"
                markerHeight="7"
                orient="auto"
              >
                <path d="M0,0 L8,4 L0,8 z" className={styles.arrowHead} />
              </marker>
            </defs>
            {nodes.map((node, i) => {
              const x = i * (NODE_W + GAP);
              const isSelected = node.meta.id === selectedId;
              const kindClass = styles[KIND_CLASS[node.evidence.kind]] ?? "";
              return (
                <g key={node.meta.id}>
                  {node.meta.arrowToNext !== null && i < n - 1 && (
                    <>
                      <line
                        x1={x + NODE_W}
                        y1={ARROW_Y}
                        x2={x + NODE_W + GAP - 2}
                        y2={ARROW_Y}
                        className={styles.edge}
                        markerEnd="url(#lineage-arrow)"
                      />
                      <text
                        x={x + NODE_W + GAP / 2}
                        y={ARROW_Y - 7}
                        textAnchor="middle"
                        className={styles.edgeLabel}
                      >
                        {node.meta.arrowToNext}
                      </text>
                    </>
                  )}
                  <g
                    role="button"
                    tabIndex={0}
                    aria-pressed={isSelected}
                    aria-label={`stage ${node.meta.ordinal} — ${node.meta.title} (${EVIDENCE_KIND_LABEL[node.evidence.kind]})`}
                    className={`${styles.node} ${kindClass} ${isSelected ? (styles.nodeSelected ?? "") : ""}`}
                    onClick={() => setSelectedId(node.meta.id)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        setSelectedId(node.meta.id);
                      }
                    }}
                  >
                    <rect x={x} y={0} width={NODE_W} height={NODE_H} rx={8} />
                    <text x={x + 10} y={18} className={styles.nodeOrdinal}>
                      {node.meta.ordinal}
                    </text>
                    <text x={x + 10} y={36} className={styles.nodeTitle}>
                      {node.meta.title}
                    </text>
                    <text x={x + 10} y={52} className={styles.nodeKind}>
                      {EVIDENCE_KIND_LABEL[node.evidence.kind]}
                    </text>
                  </g>
                </g>
              );
            })}
          </svg>
        </div>

        <p className={styles.legend}>
          Stage backing, as text on every node: <em>emitted</em> — real on the wire ·{" "}
          <em>identity only</em> — named by a hash, content not emitted ·{" "}
          <em>trace only</em> — inferred from another artifact ·{" "}
          <em>not yet emitted</em> — nothing on the wire (Q14–Q16).
        </p>
      </div>
    </RailLayout>
  );
}

function StageInspector({
  node,
  record,
  reconciliations,
}: {
  node: LineageNode;
  record: VerdictRecord;
  reconciliations: ReconciliationReport[];
}) {
  const { evidence } = node;
  const report =
    reconciliations.find((r) => r.population_id === record.population_id) ?? null;

  return (
    <div className={styles.inspector}>
      <p className={styles.kindLine}>
        <span className={styles.kindChip}>{EVIDENCE_KIND_LABEL[evidence.kind]}</span>
      </p>

      {evidence.kind !== "not-emitted" && evidence.fields.length > 0 && (
        <dl className={styles.fields}>
          {evidence.fields.map((field, i) => (
            <div key={`${field.label}-${i}`} className={styles.field}>
              <dt>{field.label}</dt>
              <dd className={field.mono ? styles.mono : undefined}>
                {field.value}
                {field.diagnostic && <span className={styles.diagnostic}> diagnostic</span>}
              </dd>
            </div>
          ))}
        </dl>
      )}

      {"note" in evidence && <p className={styles.note}>{evidence.note}</p>}

      {node.meta.id === "population" && report && (
        <p className={styles.jump}>
          <Link
            className={styles.jumpLink}
            href={`/reconciliation/${record.population_id}`}
          >
            Why is this population complete? →
          </Link>
        </p>
      )}

      {node.meta.id === "verdict" && (
        <>
          <dl className={styles.fields}>
            <div className={styles.field}>
              <dt>re-performance</dt>
              <dd>
                {record.source} v{record.source_version} · test fn v
                {record.test_function_version} · schema {record.schema_version}
              </dd>
            </div>
            <div className={styles.field}>
              <dt>evidence_refs</dt>
              <dd className={styles.mono}>{record.evidence_refs.join(" · ")}</dd>
            </div>
            {record.unknown_cause && (
              <div className={styles.field}>
                <dt>unknown_cause</dt>
                <dd className={styles.mono}>{record.unknown_cause}</dd>
              </div>
            )}
            {record.ratification_ref && (
              <div className={styles.field}>
                <dt>ratification_ref</dt>
                <dd className={styles.mono}>{record.ratification_ref}</dd>
              </div>
            )}
            {record.disposition_ref && (
              <div className={styles.field}>
                <dt>disposition_ref</dt>
                <dd className={styles.mono}>{record.disposition_ref}</dd>
              </div>
            )}
          </dl>
        </>
      )}
    </div>
  );
}
